"""Build a PRIVATE unsigned review packet from already-validated PAM50 figures.

Author: Paul Skeffington. Prepared with OpenAI.
This script neither grants review approval nor authenticates original patient data.
It never contacts the network, publishes figures, or modifies research inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

SUBTYPES = ("Basal", "Her2", "LumA", "LumB")
PAIRS = {"Basal": 16, "Her2": 9, "LumA": 59, "LumB": 22}
KINDS = ("paired_effects", "six_contrasts")
CONTRASTS = (
    "Basal_vs_LumA", "Her2_vs_LumA", "LumB_vs_LumA",
    "Basal_vs_Her2", "Basal_vs_LumB", "Her2_vs_LumB",
)
FIGURE_PENDING = "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW"
CAPTION_PENDING = "PENDING_AUTHOR_AND_SCIENTIFIC_REVIEW"
INFERENCE = "POST_SELECTION_DESCRIPTIVE_ONLY"
SHA = re.compile(r"[0-9a-f]{64}\Z")

EVIDENCE_FILES = (
    "source_validation.json",
    "layout_audit.json",
    "PAM50_paired_effects.pdf",
    "PAM50_paired_effects.png",
    "PAM50_paired_effects.caption.txt",
    "PAM50_paired_effects.metadata.json",
    "PAM50_six_contrasts.pdf",
    "PAM50_six_contrasts.png",
    "PAM50_six_contrasts.caption.txt",
    "PAM50_six_contrasts.metadata.json",
    "PAM50_scale_diagnostic.pdf",
    "PAM50_scale_diagnostic.png",
    "PAM50_scale_diagnostic.metadata.json",
    "PAM50_scale_summary.json",
)


class ReviewBlocked(ValueError):
    """A source, geometry, privacy or attestation check failed."""


def require(condition: bool, explanation: str) -> None:
    if not condition:
        raise ReviewBlocked(explanation)


def read_json(path: Path) -> dict:
    if not path.is_file():
        raise ReviewBlocked(f"Missing {path.name}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReviewBlocked(f"Invalid JSON: {path.name}") from exc
    require(isinstance(data, dict), f"Expected a JSON object: {path.name}")
    return data


def sha256(path: Path) -> str:
    require(path.is_file() and path.stat().st_size > 0,
            f"Missing or empty figure: {path.name}")
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_evidence_hashes(folder: Path) -> dict[str, str]:
    """Inventory validated output bytes without copying private research data."""
    return {name: sha256(folder / name) for name in EVIDENCE_FILES}


def verify_packet(folder: Path) -> None:
    """Reject packet changes since assembly. Not a signature or human approval."""
    expected_packet, expected_worksheet = assemble(folder)
    saved_packet = read_json(folder / "PAM50_REVIEW_PACKET.json")
    require(saved_packet == expected_packet,
            "Review packet differs from verified current source evidence")
    worksheet = folder / "PAM50_MANUSCRIPT_REVIEW.md"
    require(worksheet.is_file() and not worksheet.is_symlink(),
            "Unsigned reviewer worksheet missing or redirected")
    require(worksheet.read_bytes() == expected_worksheet.encode("utf-8"),
            "Unsigned reviewer worksheet changed after packet assembly")


def check_files(folder: Path, stem: str, meta: dict) -> tuple[str, str]:
    expected = [stem + ".pdf", stem + ".png"]
    files = meta.get("files")
    require(isinstance(files, list) and len(files) == 2
            and [Path(p).name for p in files] == expected,
            f"{stem}: figure path contract failed")
    hashes = meta.get("sha256")
    require(isinstance(hashes, list) and len(hashes) == 2
            and all(isinstance(x, str) and SHA.fullmatch(x) for x in hashes),
            f"{stem}: two SHA-256 digests required")
    for name, digest in zip(expected, hashes, strict=True):
        require(sha256(folder / name) == digest,
                f"{stem}: figure checksum mismatch")
    return hashes[0], hashes[1]


def check_panel(folder: Path, kind: str, source: dict, audit: dict) -> dict:
    stem = "PAM50_" + kind
    meta = read_json(folder / (stem + ".metadata.json"))
    require(meta.get("figure_id") == stem and meta.get("data_status") == "PRIVATE",
            f"{stem}: private figure identity mismatch")
    require(meta.get("figure_review") == FIGURE_PENDING
            and meta.get("caption_review") == CAPTION_PENDING
            and meta.get("public_release_requested") is False,
            f"{stem}: review or distribution was marked approved")
    require(meta.get("inferential_status") == INFERENCE
            and meta.get("sample_level_columns") is False,
            f"{stem}: model effects must not be described as patients")
    require(meta.get("n_features") == 60
            and meta.get("selected_gene_count") == 60
            and meta.get("n_columns") == (4 if kind == "paired_effects" else 6),
            f"{stem}: frozen matrix dimensions changed")
    require(meta.get("n_pairs_by_subtype") == PAIRS == source.get("subtype_pairs")
            and meta.get("n_formal_subtype_pairs") == 106
            and meta.get("n_primary_discovery_pairs") == 109,
            f"{stem}: frozen cohort denominators mismatch")
    require(meta.get("anchor_order") == list(SUBTYPES)
            and meta.get("anchor_counts") == dict.fromkeys(SUBTYPES, 15),
            f"{stem}: frozen anchor identity or size changed")
    if kind == "six_contrasts":
        require(meta.get("contrast_order") == list(CONTRASTS),
                "Planned first-minus-second contrasts reordered")
    ids = meta.get("gene_order")
    require(isinstance(ids, list) and len(ids) == 60
            and len(set(ids)) == 60 and all(isinstance(g, str) and g for g in ids),
            f"{stem}: missing or duplicate frozen gene identifiers")
    require(meta.get("anchor_legend") == "GENE_ANCHOR_15_PER_GROUP_SHOWN_LEFT"
            and meta.get("shared_color_scale") is True
            and meta.get("scale_policy") == "FULL_OBSERVED_RANGE_NO_CLIPPING",
            f"{stem}: heatmap palette or anchor-key contract changed")
    require(meta.get("width_in") == 9 and meta.get("height_in") == 13
            and meta.get("dpi", 0) >= 300, f"{stem}: manuscript dimensions changed")
    caption_path = folder / (stem + ".caption.txt")
    require(caption_path.is_file()
            and Path(str(meta.get("caption_file", ""))).name == caption_path.name,
            f"{stem}: missing or mismatched manuscript caption")
    caption = " ".join(caption_path.read_text(encoding="utf-8").split())
    require(caption == " ".join(str(meta.get("manuscript_caption", "")).split())
            and all(t in caption.lower()
                    for t in ("106 matched", "15-gene subtype-anchor", "post-selection")),
            f"{stem}: manuscript caption scientific contract failed")
    pdf_hash, png_hash = check_files(folder, stem, meta)
    measured = audit.get("figures", {}).get(kind, {})
    require(measured.get("status") == "STRUCTURAL_TEXT_LAYOUT_PASS",
            f"{stem}: PDF layout gate did not pass")
    for key in ("matrix_bottom_to_column_label_gap_pt", "min_observed_text_margin_pt"):
        value = measured.get(key)
        require(type(value) in (int, float) and math.isfinite(value) and value >= 12,
                f"{stem}: PDF layout measured <12 pt clearance")
    if kind == "paired_effects":
        value = measured.get("measured_subtype_label_to_legend_gap_pt")
        require(type(value) in (int, float) and math.isfinite(value) and value >= 12,
                "Subtype labels overlap continuous heatmap legend")
    return {
        "figure_id": stem, "pdf": stem + ".pdf", "png": stem + ".png",
        "caption": caption_path.name,
        "pdf_sha256": pdf_hash, "png_sha256": png_hash,
        "matrix_to_label_pt": measured["matrix_bottom_to_column_label_gap_pt"],
        "edge_clearance_pt": measured["min_observed_text_margin_pt"],
        "_genes": ids, "_scale": meta.get("color_breaks"),
    }


def assemble(folder: Path) -> tuple[dict, str]:
    """Return a pending machine-readable packet and an unsigned reviewer checklist."""
    source = read_json(folder / "source_validation.json")
    geometry = read_json(folder / "layout_audit.json")
    require(source.get("status") == "PRIVATE_FROZEN_DESCRIPTIVE_FIGURES_STRUCTURALLY_VERIFIED"
            and source.get("data_status") == "PRIVATE"
            and source.get("public_release") == "NOT_AUTHORIZED",
            "Frozen private source admission/release hold not established")
    require(source.get("scientific_review") == "PENDING"
            and source.get("visual_review") == "PENDING"
            and source.get("caption_review") == CAPTION_PENDING
            and source.get("inference") == INFERENCE,
            "Human review was inappropriately preapproved")
    for field, value in (
        ("n_genes", 60), ("n_subtype_effects", 240), ("n_planned_contrasts", 360),
        ("n_full_genes", 21432), ("n_full_contrast_tests", 128592)
    ):
        require(source.get(field) == value, "Frozen gene/effect source counts disagree")
    hashes = source.get("input_hashes")
    require(isinstance(hashes, dict) and set(hashes) == {"ST06", "ST07", "ST09"}
            and all(isinstance(v, str) and SHA.fullmatch(v) for v in hashes.values()),
            "Frozen full-source SHA-256 pins unavailable")
    require(geometry.get("status") == "STRUCTURAL_LAYOUT_PASS"
            and geometry.get("scientific_review") == "PENDING"
            and geometry.get("human_visual_review") == "PENDING",
            "Automated PDF QA is not scientific or visual sign-off")
    panels = {kind: check_panel(folder, kind, source, geometry) for kind in KINDS}
    paired, contrasts = (panels[k] for k in KINDS)
    require(paired["_genes"] == contrasts["_genes"],
            "Frozen gene order differs between panels")
    scale = paired["_scale"]
    require(scale == contrasts["_scale"] and isinstance(scale, list)
            and len(scale) == 3 and scale[1] == 0
            and type(scale[0]) in (int, float)
            and type(scale[2]) in (int, float)
            and math.isclose(scale[0], -scale[2]),
            "Panel effects must retain the shared symmetric zero-centered scale")
    supp = read_json(folder / "PAM50_scale_diagnostic.metadata.json")
    require(supp.get("figure_id") == "PAM50_Scale_Diagnostic"
            and supp.get("data_status") == "PRIVATE"
            and supp.get("figure_review") == FIGURE_PENDING
            and supp.get("inference") == "DESCRIPTIVE_ONLY"
            and supp.get("n_analyzed") == 600
            and "effect cell" in supp.get("analysis_unit", ""),
            "Supplementary diagnostic is not 600 descriptive effect cells")
    check_files(folder, "PAM50_scale_diagnostic", supp)
    summary = read_json(folder / "PAM50_scale_summary.json")
    require(summary.get("status") == "SUPPLEMENTARY_POST_SELECTION_SCALE_DIAGNOSTIC"
            and summary.get("public_release") == "NOT_AUTHORIZED"
            and summary.get("effect_cells") == 600
            and summary.get("independence") == "NOT_INDEPENDENT_PATIENT_OBSERVATIONS",
            "Supplementary review cannot imply 600 independent patients")
    safe_panels = {
        kind: {k: v for k, v in meta.items() if not k.startswith("_")}
        for kind, meta in panels.items()
    }
    packet = {
        "packet_type": "PAM50_PRIVATE_MANUSCRIPT_REVIEW",
        "status": "REVIEW_REQUIRED_NOT_APPROVED",
        "merge_authorization": "NOT_GRANTED",
        "public_release": "BLOCKED",
        "scope": "TCGA_BRCA_FROZEN_DISCOVERY_NOT_INDEPENDENT_REPLICATION",
        "inference": INFERENCE,
        "source_pins": hashes,
        "figures": safe_panels,
        "supplement": "PAM50_scale_diagnostic.pdf",
        "human_reviews": {
            "figure_legibility": "PENDING",
            "scientific_effect_interpretation": "PENDING",
            "caption_and_cohort_accuracy": "PENDING",
            "privacy_and_distribution": "PENDING",
            "journal_placement": "PENDING",
        },
    }
    rows = [
        f"| {kind} | {panels[kind]['matrix_to_label_pt']:.2f} pt | "
        f"{panels[kind]['edge_clearance_pt']:.2f} pt | "
        f"{panels[kind]['pdf']}, {panels[kind]['caption']} |"
        for kind in KINDS
    ]
    note = "\n".join([
        "# Private PAM50 manuscript-review worksheet", "",
        "**REVIEW PENDING — this is not publication, merge or scientific approval.**",
        "",
        "The private frozen R11 ST06/ST07/ST09 hashes were matched to the operator-reviewed",
        "R19 policy. This is discovery-cohort provenance, **not independent replication**.",
        "106 formal paired patients (16 Basal, 9 Her2, 59 LumA, 22 LumB) must not",
        "be confused with the separate primary 109-pair discovery cohort.",
        "", "| Figure | Cell-to-label clearance | Minimum page text margin | Evidence |",
        "| --- | ---: | ---: | --- |", *rows, "",
        "## Human decisions — remain unchecked until personally reviewed", "",
        "- [ ] Inspect both vector PDFs at intended manuscript/column print size;",
        "      confirm all gene labels, named anchor key, rotated comparisons, legends",
        "      and color accessibility beyond automated text-geometry checks.",
        "- [ ] Confirm the four tumor-minus-adjacent-normal paired subtype effects and",
        "      the six first-minus-second effect contrasts preserve the frozen analysis.",
        "- [ ] Review both captions, formal 106-pair cohort counts, post-selection",
        "      uncertainty limits, model interpretation and supplementary cell counts.",
        "- [ ] Approve data handling/privacy/disclosure separately; PRIVATE by default.",
        "- [ ] Choose journal requirements, figure numbers and supplement references.",
        "", "Author/reviewer: __________________   Date: ______________",
        "Scientific reviewer: _____________   Date: ______________",
        "Disclosure reviewer: ____________   Date: ______________",
        "Required revisions: ________________________________________",
        "", "**No checkboxes are automatically selected or approvals inferred.**", "",
    ])
    packet["evidence_sha256"] = collect_evidence_hashes(folder)
    packet["worksheet_sha256"] = hashlib.sha256(note.encode("utf-8")).hexdigest()
    return packet, note


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="An existing PRIVATE validated output directory")
    parser.add_argument(
        "--verify", action="store_true",
        help="Reject changes to an existing unsigned packet or its evidence",
    )
    args = parser.parse_args()
    try:
        require(args.folder.is_dir(), "Private figure directory does not exist")
        if args.verify:
            verify_packet(args.folder)
        else:
            packet, worksheet = assemble(args.folder)
            markdown = args.folder / "PAM50_MANUSCRIPT_REVIEW.md"
            data = args.folder / "PAM50_REVIEW_PACKET.json"
            require(not markdown.exists() and not data.exists(),
                    "Reviewer packet already exists; refusing to overwrite")
            try:
                with markdown.open("x", encoding="utf-8") as output:
                    output.write(worksheet)
                with data.open("x", encoding="utf-8") as output:
                    json.dump(packet, output, indent=2)
                    output.write("\n")
                verify_packet(args.folder)
            except (OSError, ReviewBlocked):
                markdown.unlink(missing_ok=True)
                data.unlink(missing_ok=True)
                raise
    except (OSError, ReviewBlocked) as error:
        print(f"PRIVATE REVIEW PACKET BLOCKED: {error}", file=sys.stderr)
        return 1
    if args.verify:
        print("PRIVATE REVIEW PACKET INTEGRITY VERIFIED; approvals remain PENDING")
    else:
        print("PRIVATE MANUSCRIPT REVIEW PACKET PREPARED; approvals remain PENDING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
