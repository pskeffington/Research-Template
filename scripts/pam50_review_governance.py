"""Prepare unsigned human-review and journal-profile records for a PRIVATE PAM50 packet.

Author: Paul Skeffington. Prepared with OpenAI.
This tool never authorizes publication, merges PRs, verifies identities, or signs a decision.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

if __package__:
    from .build_pam50_review_packet import ReviewBlocked, read_json, sha256, verify_packet
else:
    from build_pam50_review_packet import ReviewBlocked, read_json, sha256, verify_packet

DECISIONS = (
    "figure_legibility",
    "scientific_effect_interpretation",
    "caption_and_cohort_accuracy",
    "privacy_and_distribution",
    "journal_placement",
)
STATES = ("PENDING", "ACCEPTED", "REVISIONS_REQUIRED", "REJECTED")
SHA = re.compile(r"[0-9a-f]{64}\Z")
DECISIONS_TEMPLATE = "PAM50_REVIEW_DECISIONS.template.json"
JOURNAL_TEMPLATE = "PAM50_JOURNAL_PROFILE.template.json"
PREFLIGHT = "PAM50_JOURNAL_PREFLIGHT.json"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ReviewBlocked(message)


def packet_anchor(folder: Path) -> tuple[dict, str]:
    verify_packet(folder)
    packet_file = folder / "PAM50_REVIEW_PACKET.json"
    packet = read_json(packet_file)
    require(packet.get("status") == "REVIEW_REQUIRED_NOT_APPROVED"
            and packet.get("public_release") == "BLOCKED",
            "An approved or released packet cannot enter the unsigned review flow")
    return packet, sha256(packet_file)


def decision_template(digest: str) -> dict:
    return {
        "schema_version": 1,
        "type": "UNSIGNED_HUMAN_DECISION_RECORD",
        "packet_sha256": digest,
        "revision": 1,
        "previous_revision_sha256": None,
        "decisions": {
            key: {
                "state": "PENDING",
                "reviewer": None,
                "reviewed_at_utc": None,
                "rationale": None,
            } for key in DECISIONS
        },
        "merge_authorization": "NOT_GRANTED",
        "public_release": "BLOCKED",
        "authenticity": "NOT_CRYPTOGRAPHICALLY_VERIFIED",
    }


def journal_template(digest: str) -> dict:
    return {
        "schema_version": 1,
        "type": "AUTHOR_SUPPLIED_JOURNAL_FIGURE_PROFILE",
        "packet_sha256": digest,
        "journal_title": None,
        "instructions_url": None,
        "checked_on": None,
        "checked_by": None,
        "max_width_in": None,
        "max_height_in": None,
        "min_raster_dpi": None,
        "accepted_formats": None,
        "notes": "Copy this template outside the CI artifact; fill from current editorial rules.",
    }


def empty_preflight(packet: dict, digest: str) -> dict:
    return {
        "packet_sha256": digest,
        "status": "JOURNAL_PROFILE_PENDING",
        "release": "BLOCKED",
        "profile_verified_by_editor": False,
        "figure_ids": [v["figure_id"] for v in packet["figures"].values()],
        "note": "No target journal or confirmed specifications supplied.",
    }


def check_prepared(folder: Path, packet: dict, digest: str) -> None:
    expected = {
        DECISIONS_TEMPLATE: decision_template(digest),
        JOURNAL_TEMPLATE: journal_template(digest),
        PREFLIGHT: empty_preflight(packet, digest),
    }
    for filename, value in expected.items():
        path = folder / filename
        require(path.is_file() and not path.is_symlink(),
                f"Missing or redirected review preparation: {filename}")
        require(read_json(path) == value,
                f"Unsigned handoff document altered after assembly: {filename}")


def prepare(folder: Path, packet: dict, digest: str) -> None:
    documents = {
        DECISIONS_TEMPLATE: decision_template(digest),
        JOURNAL_TEMPLATE: journal_template(digest),
        PREFLIGHT: empty_preflight(packet, digest),
    }
    paths = [folder / name for name in documents]
    require(not any(path.exists() or path.is_symlink() for path in paths),
            "Refusing to overwrite a review handoff")
    created = []
    try:
        for name, value in documents.items():
            path = folder / name
            with path.open("x", encoding="utf-8") as output:
                json.dump(value, output, indent=2)
                output.write("\n")
            created.append(path)
        check_prepared(folder, packet, digest)
    except (OSError, ReviewBlocked):
        for path in created:
            path.unlink(missing_ok=True)
        raise


def validate_decisions(record: dict, digest: str, previous: dict | None = None,
                       previous_digest: str | None = None) -> dict:
    require(record.get("schema_version") == 1
            and record.get("type") == "UNSIGNED_HUMAN_DECISION_RECORD"
            and record.get("packet_sha256") == digest,
            "Decision record is not bound to this exact packet")
    require(record.get("merge_authorization") == "NOT_GRANTED"
            and record.get("public_release") == "BLOCKED"
            and record.get("authenticity") == "NOT_CRYPTOGRAPHICALLY_VERIFIED",
            "Review records cannot authorize merge, release or identities")
    revision = record.get("revision")
    require(type(revision) is int and revision >= 1,
            "Revision must be a positive integer")
    if revision == 1:
        require(record.get("previous_revision_sha256") is None and previous is None,
                "Revision one cannot claim a predecessor")
    else:
        require(previous is not None and previous_digest is not None,
                "A revised record requires an independently retained predecessor")
        require(record.get("previous_revision_sha256") == previous_digest
                and previous.get("revision") == revision - 1
                and previous.get("packet_sha256") == digest,
                "Revision chain or packet anchor changed")
    decisions = record.get("decisions")
    require(isinstance(decisions, dict) and set(decisions) == set(DECISIONS),
            "Exactly five named human decisions are required")
    remaining = []
    for key in DECISIONS:
        item = decisions[key]
        require(isinstance(item, dict)
                and set(item) == {"state", "reviewer", "reviewed_at_utc", "rationale"},
                f"{key}: unknown or absent decision fields")
        state = item["state"]
        require(state in STATES, f"{key}: invalid review state")
        if state == "PENDING":
            require(all(item[field] is None
                        for field in ("reviewer", "reviewed_at_utc", "rationale")),
                    f"{key}: pending decision must remain unsigned")
            remaining.append(key)
            continue
        for field in ("reviewer", "reviewed_at_utc", "rationale"):
            value = item[field]
            require(isinstance(value, str) and len(value.strip()) >= 3,
                    f"{key}: reviewed decisions need reviewer, UTC date and rationale")
        try:
            when = datetime.fromisoformat(item["reviewed_at_utc"])
        except ValueError as exc:
            raise ReviewBlocked(f"{key}: invalid review datetime") from exc
        require(when.tzinfo is not None and when.utcoffset() == timezone.utc.utcoffset(when),
                f"{key}: record timezone must be UTC")
        if state != "ACCEPTED":
            remaining.append(key)
    return {
        "record_structure": "VALIDATED_NOT_AUTHENTICATED",
        "human_review_complete": not remaining,
        "outstanding_decisions": remaining,
        "merge_authorization": "NOT_GRANTED",
        "public_release": "BLOCKED",
    }


def journal_preflight(folder: Path, profile: dict, digest: str) -> dict:
    require(profile.get("schema_version") == 1
            and profile.get("type") == "AUTHOR_SUPPLIED_JOURNAL_FIGURE_PROFILE"
            and profile.get("packet_sha256") == digest,
            "Journal profile does not reference this packet")
    for field in ("journal_title", "instructions_url", "checked_by"):
        require(isinstance(profile.get(field), str)
                and len(profile[field].strip()) >= 3,
                f"Confirmed journal profile must supply {field}")
    require(profile["instructions_url"].startswith("https://"),
            "Journal instructions must have an HTTPS source URL")
    try:
        date.fromisoformat(profile["checked_on"])
    except (TypeError, ValueError) as exc:
        raise ReviewBlocked("Journal instructions require a valid review date") from exc
    for field in ("max_width_in", "max_height_in", "min_raster_dpi"):
        value = profile.get(field)
        require(type(value) in (float, int) and math.isfinite(value) and value > 0,
                f"Journal figure policy requires a positive finite {field}")
    formats = profile.get("accepted_formats")
    require(isinstance(formats, list) and len(formats) > 0
            and len(set(formats)) == len(formats)
            and set(formats).issubset({"PDF", "PNG"}),
            "Only explicitly selected PDF and/or PNG formats supported")
    problems = []
    for kind in ("paired_effects", "six_contrasts"):
        meta = read_json(folder / f"PAM50_{kind}.metadata.json")
        if meta["width_in"] > profile["max_width_in"]:
            problems.append(f"{kind}: width exceeds target")
        if meta["height_in"] > profile["max_height_in"]:
            problems.append(f"{kind}: height exceeds target")
        if meta["dpi"] < profile["min_raster_dpi"]:
            problems.append(f"{kind}: raster DPI below target")
    if "PDF" not in formats:
        problems.append("Vector PDF not accepted by supplied journal profile")
    return {
        "status": "TECHNICAL_METADATA_PREFLIGHT_PASS" if not problems else "EDITORIAL_FIT_BLOCKED",
        "problems": problems,
        "journal_title": profile["journal_title"],
        "requires_human_print_size_and_editorial_review": True,
        "measurements": "Declared figure metadata, independently integrity-verified; not a publisher audit",
        "merge_authorization": "NOT_GRANTED",
        "public_release": "BLOCKED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="Existing private validated manuscript directory")
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--prepare", action="store_true")
    options.add_argument("--verify", action="store_true")
    options.add_argument("--validate-decisions", type=Path, metavar="JSON")
    options.add_argument("--check-profile", type=Path, metavar="JSON")
    parser.add_argument("--previous-decisions", type=Path)
    args = parser.parse_args()
    try:
        require(args.folder.is_dir(), "Private manuscript directory not found")
        packet, digest = packet_anchor(args.folder)
        require(args.previous_decisions is None or args.validate_decisions is not None,
                "Previous revision only applies to human decision validation")
        if args.prepare:
            prepare(args.folder, packet, digest)
        elif args.verify:
            check_prepared(args.folder, packet, digest)
        elif args.validate_decisions is not None:
            previous = (read_json(args.previous_decisions)
                        if args.previous_decisions is not None else None)
            previous_hash = (sha256(args.previous_decisions)
                             if args.previous_decisions is not None else None)
            outcome = validate_decisions(
                read_json(args.validate_decisions), digest, previous, previous_hash
            )
            print(json.dumps(outcome, indent=2))
        else:
            outcome = journal_preflight(args.folder, read_json(args.check_profile), digest)
            print(json.dumps(outcome, indent=2))
            require(not outcome["problems"], "Editorial profile dimensions/formats unmet")
    except (OSError, ReviewBlocked, KeyError, TypeError) as exc:
        print(f"PRIVATE REVIEW HANDOFF BLOCKED: {exc}", file=sys.stderr)
        return 1
    if args.prepare or args.verify:
        print("PRIVATE UNSIGNED HANDOFF VERIFIED; all human decisions remain PENDING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
