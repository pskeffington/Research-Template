"""Independent physical export audit for manuscript PDF/PNG masters.

Author: Paul Skeffington. Prepared with OpenAI.
This is an offline read-only preflight, not editorial or scientific approval.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

KINDS = ("paired_effects", "six_contrasts", "scale_diagnostic")
MIN_EFFECTIVE_DPI = 300.0


class PhysicalAuditBlocked(ValueError):
    """An export violates a verified mechanical property."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PhysicalAuditBlocked(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as data:
        for block in iter(lambda: data.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_metadata(path: Path) -> dict:
    require(path.is_file() and not path.is_symlink(), "Missing or redirected figure metadata")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise PhysicalAuditBlocked("Malformed metadata JSON") from error
    require(isinstance(record, dict), "Expected figure metadata object")
    return record


def _positive(value: object, field: str) -> float:
    require(type(value) in (int, float) and math.isfinite(value) and value > 0,
            f"Invalid positive dimension/resolution: {field}")
    return float(value)


def inspect_pair(pdf: Path, png: Path, meta: dict, kind: str) -> dict:
    """Inspect actual media bytes independently of R export declarations."""
    try:
        import pymupdf
    except ImportError as error:
        raise PhysicalAuditBlocked("PyMuPDF is required for independent media QA") from error

    require(pdf.is_file() and png.is_file() and not pdf.is_symlink()
            and not png.is_symlink(), f"{kind}: missing/redirected PDF or PNG")
    width = _positive(meta.get("width_in"), "width_in")
    height = _positive(meta.get("height_in"), "height_in")
    claimed_dpi = _positive(meta.get("dpi"), "dpi")
    require(meta.get("figure_review") == "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW",
            f"{kind}: no automatic approval of a figure")
    expected = [pdf.name, png.name]
    files = meta.get("files")
    checksums = meta.get("sha256")
    require(isinstance(files, list) and len(files) == 2
            and [Path(str(path)).name for path in files] == expected,
            f"{kind}: filenames disagree with sidecar")
    require(isinstance(checksums, list) and len(checksums) == 2
            and all(isinstance(value, str) and len(value) == 64 for value in checksums),
            f"{kind}: missing PDF/PNG source digests")
    actual_hashes = [sha256(pdf), sha256(png)]
    require(actual_hashes == checksums, f"{kind}: changed PDF/PNG bytes")

    try:
        with pymupdf.open(pdf) as document:
            require(len(document) == 1, f"{kind}: PDF must have one page")
            page = document[0]
            physical_w = page.rect.width / 72.0
            physical_h = page.rect.height / 72.0
            require(abs(physical_w - width) <= 1 / 72
                    and abs(physical_h - height) <= 1 / 72,
                    f"{kind}: PDF physical size differs from metadata")
            require(page.get_text("text").strip(), f"{kind}: no selectable PDF text")
            require(bool(page.get_drawings()), f"{kind}: no vector drawings present")
            fonts = page.get_fonts(full=True)
            require(bool(fonts), f"{kind}: no text-font resources")
            font_records = []
            for item in fonts:
                xref, descriptor = item[0], item[3]
                require(xref > 0, f"{kind}: font {descriptor} has no embedded font reference")
                _, font_ext, _, content = document.extract_font(xref)
                require(bool(content), f"{kind}: unembedded PDF font {descriptor}")
                font_records.append({"name": descriptor, "format": font_ext,
                                     "embedded": True})
            pdf_size_pt = [round(page.rect.width, 3), round(page.rect.height, 3)]
    except (RuntimeError, TypeError, ValueError) as error:
        if isinstance(error, PhysicalAuditBlocked):
            raise
        raise PhysicalAuditBlocked(f"{kind}: unreadable PDF or font metadata") from error

    try:
        raster = pymupdf.Pixmap(str(png))
        pixels = [raster.width, raster.height]
        color_components = raster.colorspace.n if raster.colorspace else 0
        alpha = bool(raster.alpha)
    except (RuntimeError, ValueError) as error:
        raise PhysicalAuditBlocked(f"{kind}: PNG cannot be decoded") from error
    require(color_components in (1, 3), f"{kind}: unsupported PNG color space")
    dpi = [pixels[0] / physical_w, pixels[1] / physical_h]
    require(min(dpi) >= MIN_EFFECTIVE_DPI - 0.5,
            f"{kind}: insufficient effective PNG resolution")
    require(all(abs(value - claimed_dpi) / claimed_dpi <= 0.025 for value in dpi),
            f"{kind}: PNG pixel resolution contradicts DPI sidecar")
    return {
        "figure": kind,
        "status": "PHYSICAL_BYTES_PASS_NOT_SCIENTIFIC_APPROVAL",
        "pdf_page_pt": pdf_size_pt,
        "png_pixels": pixels,
        "effective_png_dpi": [round(value, 2) for value in dpi],
        "png_channels_without_alpha": color_components,
        "png_alpha_present": alpha,
        "fonts": font_records,
        "sha256": dict(zip(expected, actual_hashes, strict=True)),
    }


def journal_advisory(matrix_path: Path, journal_id: str, figures: list[dict]) -> dict:
    """Compare only explicit numeric journal fields; never infer missing policy."""
    require(matrix_path.is_file(), "Journal policy matrix unavailable")
    with matrix_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("id") == journal_id]
    require(len(rows) == 1, "Unknown or duplicate journal policy ID")
    row = rows[0]
    notices = []
    if row.get("verification_status") != "VERIFIED_JOURNAL_PAGE":
        notices.append("Journal-specific authority not verified")
    if row.get("max_width_in"):
        allowed = _positive(float(row["max_width_in"]), "journal max width")
        for figure in figures:
            if figure["pdf_page_pt"][0] / 72 > allowed + 0.01:
                notices.append(f"{figure['figure']}: master exceeds stated max width")
    if row.get("max_height_in"):
        allowed = _positive(float(row["max_height_in"]), "journal max height")
        for figure in figures:
            if figure["pdf_page_pt"][1] / 72 > allowed + 0.01:
                notices.append(f"{figure['figure']}: master exceeds stated max height")
    if row.get("raster_min_dpi"):
        allowed = _positive(float(row["raster_min_dpi"]), "journal raster minimum")
        for figure in figures:
            if min(figure["effective_png_dpi"]) + 0.5 < allowed:
                notices.append(f"{figure['figure']}: current PNG resolution below stated minimum")
    formats = row.get("figure_formats", "")
    if "PDF not accepted" in formats or "TIFF or EPS only" in formats:
        notices.append("The master PDF/PNG pair is not the journal-required final format")
    return {
        "policy_id": journal_id,
        "journal": row.get("journal"),
        "source": row.get("primary_source_url"),
        "source_checked_on": row.get("accessed_on"),
        "status": "DERIVATIVE_OR_EDITORIAL_REVIEW_REQUIRED" if notices else "POLICY_NUMERIC_PREFLIGHT_ONLY",
        "notices": notices,
        "release": "BLOCKED",
    }


def audit(folder: Path, *, journal_id: str | None = None,
          policy_path: Path | None = None) -> dict:
    require(folder.is_dir(), "Manuscript figure directory does not exist")
    findings = []
    for kind in KINDS:
        stem = folder / f"PAM50_{kind}"
        meta = _read_metadata(Path(f"{stem}.metadata.json"))
        findings.append(inspect_pair(Path(f"{stem}.pdf"), Path(f"{stem}.png"), meta, kind))
    report = {
        "status": "PHYSICAL_EXPORTS_VERIFIED_MANUAL_REVIEW_PENDING",
        "scope": "BOTH_PAM50_HEATMAPS_AND_SCALE_SUPPLEMENT",
        "minimum_effective_dpi": MIN_EFFECTIVE_DPI,
        "figures": findings,
        "journal": None,
        "color_accessibility_review": "HUMAN_REVIEW_REQUIRED",
        "font_legibility_at_print_size": "HUMAN_REVIEW_REQUIRED",
        "scientific_review": "PENDING",
        "public_release": "BLOCKED",
    }
    if journal_id:
        require(policy_path is not None, "Journal policy matrix is required")
        report["journal"] = journal_advisory(policy_path, journal_id, findings)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="Private manuscript figure output directory")
    parser.add_argument("--journal-id", help="Existing policy matrix ID; no journal inferred")
    parser.add_argument("--policy-matrix", type=Path)
    args = parser.parse_args()
    try:
        result = audit(args.folder, journal_id=args.journal_id, policy_path=args.policy_matrix)
    except (OSError, PhysicalAuditBlocked) as error:
        print(f"PHYSICAL MANUSCRIPT EXPORT BLOCKED: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
