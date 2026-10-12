#!/usr/bin/env python3
"""Fail-closed PDF-geometry check for frozen PAM50 manuscript heatmaps.

Author: Paul Skeffington. Prepared with OpenAI.
Uses Poppler to inspect real PDF text positions. No imaging, private-file upload,
external requests, or scientific interpretation.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"x": "http://www.w3.org/1999/xhtml"}
KINDS = ("paired_effects", "six_contrasts")


def _poppler(pdf: Path, option: str) -> str:
    try:
        command = subprocess.run(
            ["pdftotext", option, str(pdf), "-"],
            capture_output=True, text=True, check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise ValueError("Poppler PDF text extraction unavailable or failed") from error
    return command.stdout


def _page_words(pdf: Path) -> tuple[float, float, list[tuple[float, float, float, float]]]:
    try:
        root = ET.fromstring(_poppler(pdf, "-bbox-layout"))
    except ET.ParseError as error:
        raise ValueError("Invalid PDF text geometry") from error
    pages = root.findall(".//x:page", NS)
    if len(pages) != 1:
        raise ValueError("PAM50 PDF must have exactly one page")
    page = pages[0]
    width, height = float(page.attrib["width"]), float(page.attrib["height"])
    if not (math.isfinite(width) and math.isfinite(height) and width > 0 and height > 0):
        raise ValueError("Invalid manuscript page dimensions")
    boxes = []
    for word in page.findall(".//x:word", NS):
        bounds = tuple(float(word.attrib[name]) for name in ("xMin", "xMax", "yMin", "yMax"))
        if not all(map(math.isfinite, bounds)):
            raise ValueError("Non-finite PDF text box")
        if bounds[0] >= bounds[1] or bounds[2] >= bounds[3]:
            raise ValueError("Nonpositive PDF text box")
        boxes.append(bounds)
    if not boxes:
        raise ValueError("PDF is text-empty; cannot verify manuscript labels")
    return width, height, boxes


def _paired_label_to_legend_gap(pdf: Path) -> float:
    """Measure the vertical clearance between subtype n-labels and legend title.

    Outer page margin checks cannot detect collisions INSIDE the figure.
    The frozen 60x4 paired-effect layout has four explicit "n=... pairs" labels.
    """
    root = ET.fromstring(_poppler(pdf, "-bbox-layout"))
    lines = []
    for line in root.findall(".//x:line", NS):
        words = line.findall("x:word", NS)
        if not words:
            continue
        label = " ".join((w.text or "") for w in words)
        ymin = min(float(w.attrib["yMin"]) for w in words)
        ymax = max(float(w.attrib["yMax"]) for w in words)
        lines.append((label, ymin, ymax))
    counts = []
    for text, _, ymax in lines:
        if re.search(r"n\s*=\s*(?:16|9|59|22)\s+pairs\b", text):
            counts.append(ymax)
    titles = [ymin for text, ymin, _ in lines
              if "Paired tumor - adjacent normal" in text]
    if len(counts) != 4 or len(titles) != 1:
        raise ValueError("Cannot identify all four subtype labels or continuous legend heading")
    return min(titles) - max(counts)


def _matrix_to_column_labels_gap(pdf: Path, kind: str) -> float:
    """Measure true vector-cell-to-column-text clearance for BOTH layouts.

    Heatmap rows are 60 frozen genes. The paired panel has 240 vector cells
    and four horizontal subtype labels; the contrast panel has 360 vector
    cells and six rotated comparison labels. All displayed labels must match
    the declared figure type; distant annotation-legend labels do not count.
    """
    try:
        import pymupdf
    except ImportError as error:
        raise ValueError("PyMuPDF is required for matrix/label overlap QA") from error
    display_labels = {
        "paired_effects": ("Basal", "Her2", "LumA", "LumB"),
        "six_contrasts": (
            "Basal - LumA", "Her2 - LumA", "LumB - LumA",
            "Basal - Her2", "Basal - LumB", "Her2 - LumB",
        ),
    }
    if kind not in display_labels:
        raise ValueError("Unknown PAM50 heatmap kind")
    expected_count = 60 * len(display_labels[kind])
    with pymupdf.open(pdf) as document:
        if len(document) != 1:
            raise ValueError("PAM50 PDF must contain one page")
        page = document[0]
        candidates = []
        for drawing in page.get_drawings():
            rect = drawing["rect"]
            if (drawing.get("fill") is not None
                    and 35 <= rect.width <= 120
                    and 4 <= rect.height <= 24):
                candidates.append(rect)
        from collections import Counter
        sizes = Counter((round(r.width, 1), round(r.height, 1))
                        for r in candidates)
        if not sizes:
            raise ValueError("Cannot identify heatmap cell rectangles")
        common_size, _ = sizes.most_common(1)[0]
        cells = [r for r in candidates
                 if (round(r.width, 1), round(r.height, 1)) == common_size]
        if len(cells) != expected_count:
            raise ValueError(
                f"{kind}: expected {expected_count} vector cells, got {len(cells)}"
            )
        left = min(r.x0 for r in cells)
        right = max(r.x1 for r in cells)
        bottom = max(r.y1 for r in cells)
        matches = {name: [] for name in display_labels[kind]}
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    name = span.get("text", "").strip()
                    if name not in matches:
                        continue
                    box = span["bbox"]
                    # Paired labels are horizontal below cells; contrast
                    # labels are rotated and can project left of the matrix.
                    in_band = bottom - 65 <= box[1] <= bottom + 90
                    if kind == "paired_effects":
                        in_band = in_band and left <= box[0] <= right
                    else:
                        in_band = in_band and box[2] >= left - 80 and box[0] <= right + 80
                        direction = line.get("dir", (1.0, 0.0))
                        in_band = in_band and abs(direction[1]) >= 0.2
                    if in_band:
                        matches[name].append(box)
        if any(len(boxes) != 1 for boxes in matches.values()):
            raise ValueError(
                f"{kind}: must identify each of {len(matches)} matrix column labels once"
            )
        return min(boxes[0][1] for boxes in matches.values()) - bottom

def audit_folder(folder: Path, min_margin_pt: float = 12.0,
                 check_labels: bool = False,
                 min_footer_gap_pt: float = 12.0,
                 min_matrix_label_gap_pt: float = 12.0) -> dict:
    if not math.isfinite(min_margin_pt) or not (0 < min_margin_pt <= 72):
        raise ValueError("Margin must be between 0 and 72 points")
    if not math.isfinite(min_footer_gap_pt) or not (0 < min_footer_gap_pt <= 72):
        raise ValueError("Footer gap must be between 0 and 72 points")
    if not math.isfinite(min_matrix_label_gap_pt) or not (0 < min_matrix_label_gap_pt <= 72):
        raise ValueError("Matrix-to-column-label clearance must be between 0 and 72 points")
    summaries = {}
    metadata = {}
    for kind in KINDS:
        stem = folder / f"PAM50_{kind}"
        pdf = stem.with_suffix(".pdf")
        sidecar = stem.with_suffix(".metadata.json")
        if not pdf.is_file() or not sidecar.is_file():
            raise ValueError(f"Missing PDF or metadata for {kind}")
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
        metadata[kind] = meta
        if meta.get("figure_review") != "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW":
            raise ValueError("Automated layout validation cannot grant release approval")
        if meta.get("inferential_status") != "POST_SELECTION_DESCRIPTIVE_ONLY":
            raise ValueError("Unexpected inferential status for post-selection figure")
        if meta.get("sample_level_columns") is not False:
            raise ValueError("Model effect columns must not be labeled as samples")
        if meta.get("matrix_to_column_names_padding_mm") != 7:
            raise ValueError("Expected dedicated 7-mm gap between matrix and column names")
        if meta.get("internal_bottom_legend_gap_mm") != 12:
            raise ValueError("Internal legend clearance must be 12 mm")
        if meta.get("anchor_legend_alignment") != "heatmap_top":
            raise ValueError("Categorical anchor key must align with heatmap top")
        if meta.get("anchor_legend") != "GENE_ANCHOR_15_PER_GROUP_SHOWN_LEFT":
            raise ValueError("On-page gene-anchor key is not declared")
        if meta.get("caption_review") != "PENDING_AUTHOR_AND_SCIENTIFIC_REVIEW":
            raise ValueError("Caption review state cannot be automatically approved")
        caption_path = stem.with_suffix(".caption.txt")
        if not caption_path.is_file():
            raise ValueError("Missing separate manuscript caption")
        caption = " ".join(caption_path.read_text(encoding="utf-8").split())
        if caption != " ".join(str(meta.get("manuscript_caption", "")).split()):
            raise ValueError("Manuscript caption and provenance sidecar disagree")
        required_caption = (
            "106 matched", "15-gene subtype-anchor", "post-selection",
            "Color does not encode significance or uncertainty"
        )
        if not all(fragment.lower() in caption.lower() for fragment in required_caption):
            raise ValueError("Caption does not explain the fixed cohort, anchors and limitations")
        if Path(str(meta.get("caption_file", ""))).name != caption_path.name:
            raise ValueError("Caption path reference does not match exported figure")
        if meta.get("n_features") != 60 or meta.get("n_columns") != (4 if kind == "paired_effects" else 6):
            raise ValueError("Incorrect PAM50 figure matrix dimensions")
        if len(meta.get("gene_labels", [])) != 60 or len(set(meta["gene_labels"])) != 60:
            raise ValueError("Expected 60 unique gene labels in the sidecar")
        if meta.get("n_formal_subtype_pairs") != 106 or meta.get("n_primary_discovery_pairs") != 109:
            raise ValueError("Research population denominator inconsistency")
        w, h, boxes = _page_words(pdf)
        if abs(w - 72 * float(meta["width_in"])) > 1 or abs(h - 72 * float(meta["height_in"])) > 1:
            raise ValueError("PDF page dimensions disagree with manifest")
        observed = [
            min(box[0] for box in boxes),
            min(box[2] for box in boxes),
            w - max(box[1] for box in boxes),
            h - max(box[3] for box in boxes),
        ]
        if min(observed) < min_margin_pt:
            raise ValueError(
                f"{kind} has text within {min_margin_pt:g}pt of page edge; minimum {min(observed):.2f}pt"
            )
        if check_labels:
            page_text = _poppler(pdf, "-layout")
            if "Gene anchor" not in page_text:
                raise ValueError("On-page categorical anchor legend is missing")
            for label in meta["gene_labels"]:
                if label not in page_text:
                    raise ValueError("A declared gene label was lost during PDF export")
        measured_footer_gap = (
            _paired_label_to_legend_gap(pdf) if kind == "paired_effects" else None
        )
        if measured_footer_gap is not None and measured_footer_gap < min_footer_gap_pt:
            raise ValueError(
                f"Subtype labels and bottom legend are only "
                f"{measured_footer_gap:.2f}pt apart; require {min_footer_gap_pt:.1f}pt"
            )
        matrix_gap = _matrix_to_column_labels_gap(pdf, kind)
        if matrix_gap < min_matrix_label_gap_pt:
            raise ValueError(
                f"{kind}: bottom heatmap cells overlap/crowd column names: "
                f"{matrix_gap:.2f}pt (minimum {min_matrix_label_gap_pt:.1f}pt)"
            )
        summaries[kind] = {
            "matrix_bottom_to_column_label_gap_pt": round(matrix_gap, 2),
            "matrix_bottom_to_subtype_label_gap_pt": (
                round(matrix_gap, 2) if kind == "paired_effects" else None
            ),
            "measured_subtype_label_to_legend_gap_pt": (
                round(measured_footer_gap, 2) if measured_footer_gap is not None else None
            ),
            "pdf_page_in": [float(meta["width_in"]), float(meta["height_in"])],
            "min_observed_text_margin_pt": round(min(observed), 2),
            "text_box_count": len(boxes),
            "gene_count": 60,
            "status": "STRUCTURAL_TEXT_LAYOUT_PASS",
        }
    paired, contrast = (metadata[k] for k in KINDS)
    if paired.get("gene_order") != contrast.get("gene_order"):
        raise ValueError("The 60 rows are not in an identical order in both panels")
    if paired.get("anchor_order") != contrast.get("anchor_order"):
        raise ValueError("The panels use incompatible anchor orders")
    if paired.get("shared_color_scale") is True and paired.get("color_breaks") != contrast.get("color_breaks"):
        raise ValueError("Shared-scale declaration conflicts with exported color limits")
    if paired.get("n_pairs_by_subtype") != contrast.get("n_pairs_by_subtype"):
        raise ValueError("Subtype denominators differ between paired and contrast panels")
    if contrast.get("contrast_order") != [
        "Basal_vs_LumA", "Her2_vs_LumA", "LumB_vs_LumA",
        "Basal_vs_Her2", "Basal_vs_LumB", "Her2_vs_LumB"
    ]:
        raise ValueError("The six planned contrasts are not ordered correctly")
    return {
        "status": "STRUCTURAL_LAYOUT_PASS",
        "human_visual_review": "PENDING",
        "scientific_review": "PENDING",
        "min_margin_required_pt": min_margin_pt,
        "min_footer_gap_required_pt": min_footer_gap_pt,
        "min_matrix_label_gap_required_pt": min_matrix_label_gap_pt,
        "figures": summaries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="Directory with two PAM50 manuscript PDF/metadata pairs")
    parser.add_argument("--min-margin-pt", type=float, default=12.0)
    parser.add_argument("--min-footer-gap-pt", type=float, default=12.0,
                        help="Minimum distance between the paired subtype labels and bottom legend title")
    parser.add_argument("--min-matrix-label-gap-pt", type=float, default=12.0,
                        help="Minimum actual PDF-vector cell-to-column-label clearance")
    parser.add_argument("--check-labels", action="store_true",
                        help="Require all 60 gene labels within extracted PDF text")
    args = parser.parse_args()
    try:
        review = audit_folder(args.folder, args.min_margin_pt, args.check_labels,
                              args.min_footer_gap_pt,
                              args.min_matrix_label_gap_pt)
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"MANUSCRIPT LAYOUT BLOCKED: {error}", file=sys.stderr)
        return 1
    print(json.dumps(review, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
