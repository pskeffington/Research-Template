"""Journal proof planning and opt-in TIFF/EPS rendering from verified private masters.

Author: Paul Skeffington. Prepared with OpenAI.
Proofs are NOT production-ready, and this tool never signs off or publishes.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from .audit_manuscript_physical import PhysicalAuditBlocked, audit, sha256
except ImportError:
    from audit_manuscript_physical import PhysicalAuditBlocked, audit, sha256

KINDS = ("paired_effects", "six_contrasts", "scale_diagnostic")
MIN_READABLE_FONT_PT = 8.0
MAX_DPI = 600


class ProofBlocked(ValueError):
    """A journal proof cannot safely be produced."""


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ProofBlocked(reason)


def _pymupdf():
    try:
        import pymupdf
    except ImportError as error:
        raise ProofBlocked("PyMuPDF must be installed") from error
    return pymupdf


def font_size_summary(pdf: Path) -> dict:
    """Read actual font spans; do not substitute declared font sizes."""
    pymupdf = _pymupdf()
    with pymupdf.open(pdf) as doc:
        require(len(doc) == 1, "Expected a single-page manuscript figure")
        page = doc[0]
        values = [
            float(span["size"])
            for block in page.get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line.get("spans", [])
            if span.get("text", "").strip()
        ]
        require(values and all(math.isfinite(v) and v > 0 for v in values),
                "Missing or invalid selectable text glyph sizes")
        return {
            "width_in": round(page.rect.width / 72, 4),
            "height_in": round(page.rect.height / 72, 4),
            "minimum_font_pt": round(min(values), 3),
        }


def journal_rule(csv_file: Path, journal_id: str) -> dict:
    """Only precise, first-party-journal rules can drive TIFF/EPS proofs."""
    require(csv_file.is_file(), "Journal literature matrix missing")
    with csv_file.open(encoding="utf-8-sig", newline="") as source:
        rows = [row for row in csv.DictReader(source) if row.get("id") == journal_id]
    require(len(rows) == 1, "Unknown or duplicate journal identifier")
    record = rows[0]
    require(record.get("policy_authority") == "JOURNAL_OFFICIAL"
            and record.get("verification_status") == "VERIFIED_JOURNAL_PAGE",
            "Publisher-general/unverified requirements cannot authorize proofs")
    formats = record.get("figure_formats", "")
    require("TIFF or EPS only" in formats,
            "Current proof renderer is limited to explicitly declared TIFF/EPS-only policies")
    try:
        max_width = float(record["max_width_in"])
        max_height = float(record["max_height_in"])
        dpi = max(300, math.ceil(float(record["raster_min_dpi"])))
    except (ValueError, TypeError) as error:
        raise ProofBlocked("Journal size and raster policy incomplete") from error
    require(all(math.isfinite(v) and v > 0 for v in (max_width, max_height, dpi))
            and dpi <= MAX_DPI, "Unsupported journal size or pixel density")
    require(record.get("primary_source_url", "").startswith("https://"),
            "Journal policy must retain its direct source URL")
    return {
        "id": journal_id,
        "journal": record["journal"],
        "source_url": record["primary_source_url"],
        "source_accessed": record["accessed_on"],
        "max_width_in": max_width,
        "max_height_in": max_height,
        "dpi": int(dpi),
    }


def layout_plan(pdf: Path, rule: dict, minimum_font_pt: float = MIN_READABLE_FONT_PT) -> dict:
    source = font_size_summary(pdf)
    factor = min(
        1.0,
        rule["max_width_in"] / source["width_in"],
        rule["max_height_in"] / source["height_in"],
    )
    projected = source["minimum_font_pt"] * factor
    safe = projected + 1e-6 >= minimum_font_pt
    return {
        "original": source,
        "scale_factor": round(factor, 6),
        "target_width_in": round(source["width_in"] * factor, 4),
        "target_height_in": round(source["height_in"] * factor, 4),
        "projected_smallest_font_pt": round(projected, 3),
        "minimum_proof_font_pt": minimum_font_pt,
        "status": "PROOF_GEOMETRY_FEASIBLE_REVIEW_REQUIRED" if safe
                  else "NEEDS_ORIGINAL_R_LAYOUT_REDESIGN",
        "not_publication_approved": True,
    }


def _make_proof(pdf: Path, destination: Path, rule: dict, plan: dict) -> dict:
    """Recompose vector page, then rasterize LZW TIFF and export vector EPS."""
    require(plan["status"] == "PROOF_GEOMETRY_FEASIBLE_REVIEW_REQUIRED",
            "Reduced figure text would be illegible: R rerender needed")
    try:
        from PIL import Image
    except ImportError as error:
        raise ProofBlocked("Pillow must be installed for TIFF proof generation") from error
    pymupdf = _pymupdf()
    stem = destination / f"{pdf.stem}_{rule['id']}_REVIEW_ONLY"
    tiff, eps = Path(f"{stem}.tif"), Path(f"{stem}.eps")
    require(not tiff.exists() and not eps.exists(), "Refusing to overwrite proof")
    with tempfile.TemporaryDirectory(prefix="journal_proof_") as temp:
        proof_pdf = Path(temp) / "scaled.pdf"
        with pymupdf.open(pdf) as source:
            page = source[0]
            with pymupdf.open() as doc:
                target = doc.new_page(
                    width=page.rect.width * plan["scale_factor"],
                    height=page.rect.height * plan["scale_factor"],
                )
                target.show_pdf_page(target.rect, source, 0)
                doc.save(proof_pdf)
        with pymupdf.open(proof_pdf) as proof:
            page = proof[0]
            image = page.get_pixmap(dpi=rule["dpi"], colorspace=pymupdf.csRGB,
                                    alpha=False)
            Image.frombytes("RGB", (image.width, image.height), image.samples).save(
                tiff, format="TIFF", compression="tiff_lzw",
                dpi=(rule["dpi"], rule["dpi"]),
            )
        try:
            subprocess.run(
                ["pdftops", "-eps", str(proof_pdf), str(eps)],
                check=True, capture_output=True, text=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            tiff.unlink(missing_ok=True)
            eps.unlink(missing_ok=True)
            raise ProofBlocked("Poppler EPS export failed") from error
    try:
        with Image.open(tiff) as actual:
            require(actual.format == "TIFF" and actual.mode == "RGB",
                    "TIFF proof lacks 8-bit RGB pixels")
            require(actual.tag_v2.get(259) == 5, "TIFF must use LZW compression")
            require(actual.width / rule["dpi"] <= rule["max_width_in"] + 0.01
                    and actual.height / rule["dpi"] <= rule["max_height_in"] + 0.01,
                    "TIFF proof exceeds target dimensions")
            size = [actual.width, actual.height]
        header = eps.read_bytes()[:4096]
        require(header.startswith(b"%!PS-Adobe") and b"%%BoundingBox:" in header,
                "EPS proof has no proper PostScript header or bounding box")
    except (OSError, ProofBlocked):
        tiff.unlink(missing_ok=True)
        eps.unlink(missing_ok=True)
        raise
    return {
        "status": "REVIEW_PROOF_ONLY_NOT_PRODUCTION_CERTIFIED",
        "source_pdf_sha256": sha256(pdf),
        "tiff": tiff.name,
        "tiff_pixels": size,
        "tiff_sha256": sha256(tiff),
        "eps": eps.name,
        "eps_sha256": sha256(eps),
        "public_release": "BLOCKED",
    }


def execute(folder: Path, *, matrix: Path | None = None, journal_id: str | None = None,
            output: Path | None = None) -> dict:
    """Never write a derivative without an explicit journal AND proof destination."""
    audit(folder)
    if journal_id is None:
        require(output is None, "Cannot export without an explicit journal selection")
        return {
            "status": "JOURNAL_NOT_SELECTED_MASTER_ONLY",
            "figures": {
                kind: font_size_summary(folder / f"PAM50_{kind}.pdf") for kind in KINDS
            },
            "scientific_review": "PENDING",
            "public_release": "BLOCKED",
        }
    require(matrix is not None, "Journal requirements matrix required")
    rule = journal_rule(matrix, journal_id)
    plans = {kind: layout_plan(folder / f"PAM50_{kind}.pdf", rule) for kind in KINDS}
    result = {
        "status": "FEASIBILITY_REVIEW_ONLY",
        "journal_rule": rule,
        "figure_plans": plans,
        "proofs": [],
        "scientific_review": "PENDING",
        "public_release": "BLOCKED",
    }
    if output is None:
        return result
    require(output.resolve() != folder.resolve()
            and folder.resolve() not in output.resolve().parents,
            "Proofs must not be written inside the immutable source directory")
    require(not output.exists(), "Refusing to overwrite any existing proof directory")
    require(all(p["status"] == "PROOF_GEOMETRY_FEASIBLE_REVIEW_REQUIRED"
                for p in plans.values()),
            "At least one figure requires R layout redesign before proof export")
    output.mkdir(parents=True)
    try:
        for kind in KINDS:
            figure = folder / f"PAM50_{kind}.pdf"
            result["proofs"].append(_make_proof(figure, output, rule, plans[kind]))
        result["status"] = "REVIEW_PROOFS_GENERATED_NOT_APPROVED"
        with (output / "PROOF_MANIFEST.json").open("x", encoding="utf-8") as target:
            json.dump(result, target, indent=2)
            target.write("\n")
    except (OSError, ProofBlocked):
        for item in output.iterdir():
            item.unlink()
        output.rmdir()
        raise
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="Already verified private research output")
    parser.add_argument("--policy-matrix", type=Path)
    parser.add_argument("--journal-id")
    parser.add_argument("--proof-output", type=Path,
                        help="Opt-in NEW private directory for REVIEW-ONLY TIFF/EPS proofs")
    args = parser.parse_args()
    try:
        result = execute(args.folder, matrix=args.policy_matrix, journal_id=args.journal_id,
                         output=args.proof_output)
    except (OSError, ValueError, PhysicalAuditBlocked) as error:
        print(f"JOURNAL PROOF BLOCKED: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
