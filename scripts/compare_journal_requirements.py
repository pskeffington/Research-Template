"""Read-only, source-qualified journal feasibility matrix for verified manuscript masters.

Author: Paul Skeffington. Prepared with OpenAI.
Never chooses a journal, exports figures, signs a review or grants distribution.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

try:
    from .audit_manuscript_physical import PhysicalAuditBlocked, audit
    from .build_journal_proofs import KINDS, MIN_READABLE_FONT_PT, ProofBlocked, font_size_summary
except ImportError:
    from audit_manuscript_physical import PhysicalAuditBlocked, audit
    from build_journal_proofs import KINDS, MIN_READABLE_FONT_PT, ProofBlocked, font_size_summary


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProofBlocked(message)


def positive_optional(value: str | None, field: str) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ProofBlocked(f"Invalid {field} in journal policy matrix") from exc
    require(math.isfinite(parsed) and parsed > 0, f"Invalid {field} in journal policy matrix")
    return parsed


def evaluate_row(row: dict, figures: dict) -> dict:
    """Only explicit rules are compared; a column width is not a page maximum."""
    journal_id = row.get("id", "").strip()
    require(bool(journal_id and row.get("journal")), "Missing journal policy identity")
    authority = row.get("verification_status")
    verified = (
        row.get("policy_authority") == "JOURNAL_OFFICIAL"
        and authority == "VERIFIED_JOURNAL_PAGE"
    )
    source = row.get("primary_source_url", "")
    require(source.startswith("https://"), f"{journal_id}: missing official source link")
    width_limit = positive_optional(row.get("max_width_in"), "max_width_in")
    height_limit = positive_optional(row.get("max_height_in"), "max_height_in")
    column_mm = positive_optional(row.get("double_column_mm"), "double_column_mm")
    raster_dpi = positive_optional(row.get("raster_min_dpi"), "raster_min_dpi")
    reasons = []
    if not verified:
        reasons.append("Journal-specific policy not verified; publisher guidance only")
    if "NOT pure original-research target" in row.get("research_scope", ""):
        reasons.append("Article type may be outside journal scope")
    if width_limit is None and height_limit is None and column_mm is None:
        reasons.append("No verified journal-specific width/height or column limit")
    if "TIFF or EPS only" in row.get("figure_formats", ""):
        reasons.append("New TIFF/EPS derivative required; existing PDF/PNG is not production output")
    if "PDF not accepted" in row.get("figure_formats", ""):
        reasons.append("PDF source is not an accepted final artwork format")
    evaluations = {}
    redesign = False
    for name, value in figures.items():
        factor = 1.0
        for maximum, observed in (
            (width_limit, value["width_in"]),
            (height_limit, value["height_in"]),
        ):
            if maximum is not None:
                factor = min(factor, maximum / observed)
        # A double-column width is a *planning scenario*, not a universal max.
        column_factor = (
            min(1.0, column_mm / 25.4 / value["width_in"])
            if column_mm is not None else None
        )
        projected = value["minimum_font_pt"] * factor
        column_projected = (
            value["minimum_font_pt"] * column_factor
            if column_factor is not None else None
        )
        unsafe = projected < MIN_READABLE_FONT_PT - 1e-6
        column_unsafe = (
            column_projected is not None
            and column_projected < MIN_READABLE_FONT_PT - 1e-6
        )
        redesign = redesign or unsafe or column_unsafe
        if unsafe:
            reasons.append(f"{name}: shrinking to maximum artwork dimensions would crowd text")
        if column_unsafe:
            reasons.append(f"{name}: double-column layout would crowd text")
        evaluations[name] = {
            "source_width_in": value["width_in"],
            "source_height_in": value["height_in"],
            "source_smallest_font_pt": value["minimum_font_pt"],
            "scale_to_explicit_maximum": round(factor, 5),
            "projected_font_at_maximum_pt": round(projected, 3),
            "double_column_width_mm_if_provided": column_mm,
            "projected_font_at_double_column_pt": (
                round(column_projected, 3) if column_projected is not None else None
            ),
            "minimum_engineering_font_pt": MIN_READABLE_FONT_PT,
            "requires_relayout": unsafe or column_unsafe,
        }
    if not verified:
        state = "UNVERIFIED_POLICY_HOLD"
    elif "NOT pure original-research target" in row.get("research_scope", ""):
        state = "ARTICLE_SCOPE_REVIEW_REQUIRED"
    elif redesign:
        state = "ORIGINAL_R_RELAYOUT_REQUIRED"
    elif width_limit is None and height_limit is None and column_mm is None:
        state = "ARTWORK_POLICY_INCOMPLETE"
    else:
        state = "MECHANICAL_SCENARIO_POSSIBLE_NOT_APPROVED"
    return {
        "id": journal_id,
        "journal": row["journal"],
        "source_url": source,
        "accessed_on": row.get("accessed_on"),
        "policy_authority": row.get("policy_authority"),
        "verification_status": authority,
        "status": state,
        "format_notes": row.get("figure_formats"),
        "raster_minimum_dpi_if_provided": raster_dpi,
        "figure_checks": evaluations,
        "review_flags": sorted(set(reasons)),
        "journal_selected": False,
        "editorial_acceptance": "NOT_ASSESSED",
        "public_release": "BLOCKED",
    }


def compare(folder: Path, matrix: Path) -> dict:
    """No writes; binds row interpretations to a SHA-256 of a dated source matrix."""
    checked = audit(folder)
    require(matrix.is_file() and not matrix.is_symlink(), "Journal policy matrix unavailable")
    with matrix.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    require(rows and all(None not in row for row in rows), "Invalid journal source matrix CSV")
    ids = [row.get("id") for row in rows]
    require(len(ids) == len(set(ids)), "Duplicate journal policy IDs")
    sizes = {name: font_size_summary(folder / f"PAM50_{name}.pdf") for name in KINDS}
    report = {
        "status": "JOURNAL_COMPARISON_READ_ONLY",
        "journal_selected": False,
        "master_media_status": checked["status"],
        "journal_policy_matrix_sha256": hashlib.sha256(matrix.read_bytes()).hexdigest(),
        "policy_count": len(rows),
        "figure_count": len(sizes),
        "policies": [evaluate_row(row, sizes) for row in rows],
        "engineering_font_threshold_pt": MIN_READABLE_FONT_PT,
        "note": (
            "Mechanical scenarios only; do not rank editorial fit or infer approval. "
            "Double-column width is a proof-sizing scenario, not a universal limit."
        ),
        "human_review": "PENDING",
        "scientific_review": "PENDING",
        "public_release": "BLOCKED",
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--policy-matrix", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = compare(args.folder, args.policy_matrix)
    except (OSError, ValueError, PhysicalAuditBlocked) as error:
        print(f"JOURNAL COMPARISON BLOCKED: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
