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


def audit_folder(folder: Path, min_margin_pt: float = 12.0,
                 check_labels: bool = False) -> dict:
    if not math.isfinite(min_margin_pt) or not (0 < min_margin_pt <= 72):
        raise ValueError("Margin must be between 0 and 72 points")
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
            for label in meta["gene_labels"]:
                if label not in page_text:
                    raise ValueError("A declared gene label was lost during PDF export")
        summaries[kind] = {
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
        "figures": summaries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="Directory with two PAM50 manuscript PDF/metadata pairs")
    parser.add_argument("--min-margin-pt", type=float, default=12.0)
    parser.add_argument("--check-labels", action="store_true",
                        help="Require all 60 gene labels within extracted PDF text")
    args = parser.parse_args()
    try:
        review = audit_folder(args.folder, args.min_margin_pt, args.check_labels)
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"MANUSCRIPT LAYOUT BLOCKED: {error}", file=sys.stderr)
        return 1
    print(json.dumps(review, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
