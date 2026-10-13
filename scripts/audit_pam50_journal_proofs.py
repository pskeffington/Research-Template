"""Independent vector geometry and noncolor-cue checks for SYNTHETIC journal proofs.

Author: Paul Skeffington. Prepared with OpenAI.
No clinical figures, submission-ready artwork, approvals, or publisher claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

PROOF_TYPES = ("paired_effects", "six_contrasts")
SCALE_COLORS = ("#2166AC", "#F7F7F7", "#B2182B")
MAXIMUM_TEXT_MARGIN_PT = 8.0
MINIMUM_ROW_LABEL_PT = 8.5
MINIMUM_ROW_GAP_PT = 0.5
MINIMUM_LEGEND_GAP_PT = 12.0


class PageBlocked(ValueError):
    """Reject malformed, tampered, crowded, or implicitly approved figure proofs."""


def require(ok: bool, message: str) -> None:
    if not ok:
        raise PageBlocked(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _spans(page) -> list[dict]:
    return [
        span
        for block in page.get_text("dict")["blocks"]
        for line in block.get("lines", [])
        for span in line.get("spans", [])
        if span.get("text", "").strip()
    ]


def _luminance(hex_color: str) -> float:
    components = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92
              for v in components]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def inspect_page(folder: Path, stem: str) -> dict:
    try:
        import pymupdf
    except ImportError as exc:
        raise PageBlocked("PyMuPDF required for independent proof checks") from exc
    path = folder / stem
    pdf, png, sidecar = (
        Path(f"{path}.pdf"), Path(f"{path}.png"), Path(f"{path}.metadata.json")
    )
    for file in (pdf, png, sidecar):
        require(file.is_file() and not file.is_symlink(), f"{stem}: missing/redirected file")
    try:
        metadata = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PageBlocked(f"{stem}: invalid sidecar JSON") from exc
    require(metadata.get("status") == "SYNTHETIC_REVIEW_PROOF_NOT_PRODUCTION_CERTIFIED"
            and metadata.get("public_release") == "BLOCKED"
            and metadata.get("figure_review") == "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW",
            f"{stem}: no automated approval or public release")
    require(metadata.get("pdf_sha256") == sha256(pdf)
            and metadata.get("png_sha256") == sha256(png),
            f"{stem}: modified source PDF/PNG bytes")
    kind = metadata.get("kind")
    page_num = metadata.get("page")
    require(kind in PROOF_TYPES and type(page_num) is int and page_num in (1, 2),
            f"{stem}: invalid page and comparison kind")
    require(metadata.get("journal_scenario") == "J03"
            and stem == f"SYN_J03_{kind}_p{page_num}",
            f"{stem}: proof identity and journal scenario disagree")
    labels = metadata.get("gene_labels")
    ids = metadata.get("gene_order")
    require(isinstance(labels, list) and len(labels) == 30
            and len(set(labels)) == 30
            and isinstance(ids, list) and len(ids) == 30
            and len(set(ids)) == 30,
            f"{stem}: lost or duplicated synthetic gene rows")
    expected_range = range(1, 31) if page_num == 1 else range(31, 61)
    require(ids == [f"SYN_G{i:03d}" for i in expected_range],
            f"{stem}: expected frozen synthetic order was changed")
    require(labels == [f"Synthetic_{i}" for i in expected_range],
            f"{stem}: gene-label order differs from source")
    require(metadata.get("row_anchor_groups")
            == (["Basal", "Her2"] if page_num == 1 else ["LumA", "LumB"]),
            f"{stem}: anchor group identity or order changed")
    require(metadata.get("n_genes") == 30
            and metadata.get("n_columns") == (4 if kind == "paired_effects" else 6),
            f"{stem}: matrix dimensions changed")
    require(metadata.get("color_palette") == list(SCALE_COLORS)
            and metadata.get("signed_scale") == "negative / zero / positive",
            f"{stem}: numeric and noncolor legends must remain linked")
    breaks = metadata.get("color_breaks")
    require(isinstance(breaks, list) and len(breaks) == 3
            and all(type(x) in (float, int) and math.isfinite(x) for x in breaks)
            and breaks[0] < 0 and breaks[1] == 0
            and abs(breaks[0] + breaks[2]) < 1e-10,
            f"{stem}: a centered common signed scale is mandatory")
    # Red and blue must remain dark enough against white; neutral cells rely
    # on the rendered white border and signed tick marks, not color alone.
    require(all((1.05 / (_luminance(color) + 0.05)) >= 3.0
                for color in (SCALE_COLORS[0], SCALE_COLORS[2])),
            f"{stem}: palette extremes lack contrast against page white")

    try:
        with pymupdf.open(pdf) as document:
            require(len(document) == 1, f"{stem}: PDF must contain one vector page")
            page = document[0]
            width, height = page.rect.width, page.rect.height
            expected_w = float(metadata["width_in"]) * 72.0
            expected_h = float(metadata["height_in"]) * 72.0
            require(abs(width - expected_w) < 1 and abs(height - expected_h) < 1,
                    f"{stem}: page differs from publication-sized proof plan")
            spans = _spans(page)
            content = page.get_text("text")
            require(all(s in content for s in ("negative", "zero", "positive"))
                    and "Signed log2 effect" in content,
                    f"{stem}: explicit signed-effect legend is missing")
            require(all(anchor in content for anchor in metadata["row_anchor_groups"]),
                    f"{stem}: noncolor anchor text is missing")
            genes = []
            for label in labels:
                matches = [s for s in spans if s["text"].strip() == label]
                require(len(matches) == 1, f"{stem}: gene label {label} missing or repeated")
                span = matches[0]
                require(span["size"] >= MINIMUM_ROW_LABEL_PT,
                        f"{stem}: gene labels smaller than print proof threshold")
                box = span["bbox"]
                require(min(box[0], box[1], width - box[2], height - box[3])
                        >= MAXIMUM_TEXT_MARGIN_PT,
                        f"{stem}: gene label lies outside proof text margins")
                genes.append((box[1], box[3]))
            for previous, current in zip(genes, genes[1:], strict=False):
                require(current[0] - previous[1] >= MINIMUM_ROW_GAP_PT,
                        f"{stem}: overlapping or out-of-order gene labels")
            fonts = page.get_fonts(full=True)
            require(bool(fonts), f"{stem}: no PDF text fonts")
            for font in fonts:
                _, _, _, embedded = document.extract_font(font[0])
                require(bool(embedded), f"{stem}: unembedded font in synthetic proof")
            drawings = [
                d["rect"] for d in page.get_drawings()
                if d.get("fill") is not None
                and 24 <= d["rect"].width <= 90
                and 6 <= d["rect"].height <= 30
            ]
            require(bool(drawings), f"{stem}: no heatmap vector cells")
            common, _ = Counter(
                (round(d.width, 1), round(d.height, 1)) for d in drawings
            ).most_common(1)[0]
            cells = [d for d in drawings
                     if (round(d.width, 1), round(d.height, 1)) == common]
            require(len(cells) >= 30 * metadata["n_columns"],
                    f"{stem}: missing true vector heatmap cells")
            bottom = max(d.y1 for d in cells)
            legend_spans = [s for s in spans if "Signed log2 effect" in s["text"]]
            require(len(legend_spans) == 1,
                    f"{stem}: signed legend title not individually identifiable")
            gap = legend_spans[0]["bbox"][1] - bottom
            require(gap >= MINIMUM_LEGEND_GAP_PT,
                    f"{stem}: legend overlaps column label track")
            pdf_page_pt = [round(width, 2), round(height, 2)]
    except (RuntimeError, KeyError, TypeError) as exc:
        raise PageBlocked(f"{stem}: invalid PDF physical geometry") from exc
    try:
        pixmap = pymupdf.Pixmap(str(png))
        actual_dpi = [pixmap.width / (expected_w / 72),
                      pixmap.height / (expected_h / 72)]
    except (RuntimeError, ValueError) as exc:
        raise PageBlocked(f"{stem}: unreadable PNG") from exc
    require(min(actual_dpi) >= 299,
            f"{stem}: PNG pixel density below 300 DPI proof target")
    return {
        "name": stem,
        "status": "SYNTHETIC_PHYSICAL_PROOF_PASS_HUMAN_REVIEW_PENDING",
        "gene_labels_verified": 30,
        "vector_cells_observed": len(cells),
        "minimum_label_pt": min(s["size"] for s in spans
                                if s["text"].strip() in set(labels)),
        "minimum_legend_gap_pt": round(gap, 2),
        "page_size_pt": pdf_page_pt,
        "png_effective_dpi": [round(v, 2) for v in actual_dpi],
        "source_order": ids,
        "color_palette": list(SCALE_COLORS),
        "human_accessibility_review": "PENDING",
        "public_release": "BLOCKED",
    }


def audit(folder: Path) -> dict:
    require(folder.is_dir(), "Missing synthetic proof directory")
    required = [f"SYN_J03_{k}_p{i}" for k in PROOF_TYPES for i in (1, 2)]
    pages = [inspect_page(folder, stem) for stem in required]
    require(len({x["name"] for x in pages}) == 4, "Repeated proof pages")
    return {
        "status": "SYNTHETIC_COMPLEXHEATMAP_PROOFS_PASS",
        "pages": pages,
        "journal_selected_for_submission": False,
        "external_research_data_used": False,
        "real_private_heatmaps_modified": False,
        "human_print_and_cvd_review": "PENDING",
        "scientific_review": "PENDING",
        "public_release": "BLOCKED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    try:
        report = audit(args.folder)
    except (PageBlocked, OSError, ValueError) as exc:
        print(f"SYNTHETIC JOURNAL PROOF BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
