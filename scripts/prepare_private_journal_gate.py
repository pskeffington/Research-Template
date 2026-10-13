"""Prepare and revalidate a PRIVATE, unsigned journal-derivative authorization request.

Author: Paul Skeffington. Prepared with OpenAI.
This command never selects a journal, renders, uploads, signs or releases figures.
A later protected workflow must separately authenticate human approvals.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if __package__:
    from .build_pam50_review_packet import ReviewBlocked, read_json, sha256
    from .pam50_review_governance import check_prepared, packet_anchor
else:
    from build_pam50_review_packet import ReviewBlocked, read_json, sha256
    from pam50_review_governance import check_prepared, packet_anchor

SHA = re.compile(r"[a-f0-9]{64}\Z")
OUTPUT_REQUEST = "PAM50_JOURNAL_DERIVATIVE_REQUEST.json"
OUTPUT_GATE = "PAM50_JOURNAL_DERIVATIVE_GATE.json"
DEPENDENCIES = (
    "PAM50_REVIEW_PACKET.json",
    "PAM50_REVIEW_DECISIONS.template.json",
    "PAM50_JOURNAL_PROFILE.template.json",
    "PAM50_JOURNAL_PREFLIGHT.json",
    "PAM50_PHYSICAL_EXPORT_AUDIT.json",
    "PAM50_JOURNAL_READINESS.json",
    "PAM50_JOURNAL_COMPARISON.json",
    "PAM50_JOURNAL_R_LAYOUT_PLANS.json",
)
REQUIRED_SCENARIOS = {"J01", "J03", "J04", "J05"}
DECISIONS = (
    "figure_legibility", "scientific_effect_interpretation",
    "caption_and_cohort_accuracy", "privacy_and_distribution",
    "journal_placement",
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ReviewBlocked(message)


def ensure_no_derivatives(folder: Path) -> None:
    """Reject any unapproved private or synthetic journal derivative."""
    for pattern in (
        "*.tif", "*.tiff", "*.eps", "SYN_J03*",
        "*_REVIEW_ONLY.pdf", "*_REVIEW_ONLY.png",
        "PAM50_journal_page_*.pdf", "PAM50_journal_page_*.png",
    ):
        require(not list(folder.rglob(pattern)),
                f"Unexpected derivative matching {pattern} in private review tree")


def upstream_state(folder: Path, matrix: Path, template_sha: str) -> dict:
    require(re.fullmatch(r"[a-f0-9]{40}", template_sha) is not None,
            "Exactly one pinned, 40-hex public template Git commit is required")
    require(folder.is_dir() and not folder.is_symlink(), "Missing private output directory")
    require(matrix.is_file() and not matrix.is_symlink(), "Missing dated journal policy matrix")
    packet, digest = packet_anchor(folder)
    check_prepared(folder, packet, digest)
    require(all(packet["human_reviews"].get(k) == "PENDING" for k in DECISIONS),
            "Formal author reviews must remain pending")
    require(packet["merge_authorization"] == "NOT_GRANTED"
            and packet["public_release"] == "BLOCKED",
            "Private manuscript approval or release status was altered")
    p = read_json(folder / "PAM50_PHYSICAL_EXPORT_AUDIT.json")
    require(p.get("status") == "PHYSICAL_EXPORTS_VERIFIED_MANUAL_REVIEW_PENDING"
            and p.get("public_release") == "BLOCKED"
            and len(p.get("figures", [])) == 3,
            "Real PDF/PNG physical audit did not pass")
    readiness = read_json(folder / "PAM50_JOURNAL_READINESS.json")
    require(readiness.get("status") == "JOURNAL_NOT_SELECTED_MASTER_ONLY"
            and readiness.get("public_release") == "BLOCKED"
            and len(readiness.get("figures", {})) == 3,
            "Master-only journal readiness is absent")
    comparison = read_json(folder / "PAM50_JOURNAL_COMPARISON.json")
    require(comparison.get("status") == "JOURNAL_COMPARISON_READ_ONLY"
            and comparison.get("policy_count") == 9
            and comparison.get("figure_count") == 3
            and comparison.get("journal_selected") is False
            and comparison.get("public_release") == "BLOCKED"
            and comparison.get("journal_policy_matrix_sha256") == sha256(matrix),
            "Journal comparison or source matrix changed")
    require({v.get("id") for v in comparison.get("policies", [])}
            == {"J01", "J02", "J03", "J04", "J05", "J06", "J07", "J08", "J09"}
            and all(v.get("journal_selected") is False
                    and v.get("public_release") == "BLOCKED"
                    for v in comparison["policies"]),
            "Exactly nine unselected nonreleasing journal scenarios are required")
    plans = read_json(folder / "PAM50_JOURNAL_R_LAYOUT_PLANS.json")
    require(plans.get("status") == "REVIEW_ONLY_R_LAYOUT_SCENARIOS_VALIDATED"
            and plans.get("journal_selected") is False
            and plans.get("figure_values_exported") is False
            and plans.get("public_release") == "BLOCKED"
            and set(plans.get("plans", {})) == REQUIRED_SCENARIOS,
            "Read-only four-journal R plans must be verified")
    source_gene_hashes = set()
    shared_breaks = set()
    for key, plan in plans["plans"].items():
        require(plan.get("status") == "R_LAYOUT_PLAN_ONLY_NOT_RENDERED"
                and plan.get("journal_scenario") == key
                and plan.get("scientific_estimates_recomputed") is False
                and plan.get("original_files_modified") is False
                and plan.get("total_review_pages") == 4
                and plan.get("public_release") == "BLOCKED",
                f"{key}: frozen layout not read-only")
        pages = plan.get("pages")
        require(isinstance(pages, list) and len(pages) == 2
                and [(v.get("row_start"), v.get("row_end"))
                     for v in pages] == [(1, 30), (31, 60)],
                f"{key}: changed subtype-anchor page boundaries")
        gene_hash = plan.get("complete_gene_order_sha256")
        require(isinstance(gene_hash, str) and SHA.fullmatch(gene_hash),
                f"{key}: no frozen gene-order binding")
        source_gene_hashes.add(gene_hash)
        shared_breaks.add(tuple(plan.get("shared_color_breaks", [])))
    require(len(source_gene_hashes) == 1 and len(shared_breaks) == 1,
            "Frozen source order or shared color scale varies by journal")
    ensure_no_derivatives(folder)
    return {
        "packet_sha256": digest,
        "journal_policy_matrix_sha256": sha256(matrix),
        "public_template_git_sha": template_sha,
        "upstream_evidence_sha256": {
            name: sha256(folder / name) for name in DEPENDENCIES
        },
        "source_gene_order_sha256": next(iter(source_gene_hashes)),
    }


def expected_documents(state: dict) -> dict[str, dict]:
    request = {
        "schema_version": 1,
        "record_type": "PRIVATE_JOURNAL_DERIVATIVE_REQUEST_UNSIGNED",
        "packet_sha256": state["packet_sha256"],
        "public_template_git_sha": state["public_template_git_sha"],
        "journal_policy_matrix_sha256": state["journal_policy_matrix_sha256"],
        "source_gene_order_sha256": state["source_gene_order_sha256"],
        "target_journal_id": None,
        "target_journal_policy_verified": False,
        "reviewed_pdf_png_feedback": "VISUAL_INSPECTION_REPORTED_NOT_SIGNED",
        "scientific_interpretation_approval": "PENDING",
        "caption_and_cohort_approval": "PENDING",
        "privacy_distribution_approval": "PENDING",
        "render_authorization": "NOT_GRANTED",
        "human_approval_authentication": "NOT_VERIFIED",
        "production_submission": "BLOCKED",
        "public_release": "BLOCKED",
        "note": (
            "Unsigned authorization request only. A target journal, authenticated "
            "author and disclosure reviews, and a protected runner are separate gates."
        ),
    }
    gate = {
        "schema_version": 1,
        "status": "PRIVATE_JOURNAL_DERIVATIVE_RENDER_BLOCKED",
        "packet_sha256": state["packet_sha256"],
        "public_template_git_sha": state["public_template_git_sha"],
        "upstream_evidence_sha256": state["upstream_evidence_sha256"],
        "target_journal_selected": False,
        "full_human_approval_present": False,
        "human_identity_authenticated": False,
        "release_authorized": False,
        "render_execution": "DISABLED",
        "generated_derivative_count": 0,
        "master_data_modified": False,
        "public_release": "BLOCKED",
    }
    return {OUTPUT_REQUEST: request, OUTPUT_GATE: gate}


def prepare(folder: Path, matrix: Path, template_sha: str) -> None:
    state = upstream_state(folder, matrix, template_sha)
    documents = expected_documents(state)
    require(all(not (folder / name).exists()
                and not (folder / name).is_symlink() for name in documents),
            "Refusing to overwrite unsigned journal authorization material")
    created = []
    try:
        for name, value in documents.items():
            path = folder / name
            with path.open("x", encoding="utf-8") as file:
                json.dump(value, file, indent=2)
                file.write("\n")
            created.append(path)
        verify(folder, matrix, template_sha)
    except (OSError, ReviewBlocked):
        for path in created:
            path.unlink(missing_ok=True)
        raise


def verify(folder: Path, matrix: Path, template_sha: str) -> None:
    state = upstream_state(folder, matrix, template_sha)
    for name, expected in expected_documents(state).items():
        path = folder / name
        require(path.is_file() and not path.is_symlink(),
                f"Missing or redirected unsigned file: {name}")
        require(read_json(path) == expected,
                f"Unsigned journal authorization material altered: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--policy-matrix", type=Path, required=True)
    parser.add_argument("--template-sha", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        if args.prepare:
            prepare(args.folder, args.policy_matrix, args.template_sha)
        else:
            verify(args.folder, args.policy_matrix, args.template_sha)
    except (ReviewBlocked, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"PRIVATE JOURNAL DERIVATIVE GATE BLOCKED: {exc}", file=sys.stderr)
        return 1
    print("PRIVATE JOURNAL DERIVATIVE REQUEST VERIFIED; NO AUTHORIZATION OR RENDER")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
