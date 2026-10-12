"""Synthetic review decisions, revision-chain and journal metadata preflight tests."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_pam50_review_packet import ReviewBlocked, assemble
from scripts.pam50_review_governance import (
    DECISIONS,
    DECISIONS_TEMPLATE,
    JOURNAL_TEMPLATE,
    check_prepared,
    decision_template,
    journal_preflight,
    journal_template,
    packet_anchor,
    prepare,
    validate_decisions,
)
from scripts.tests.test_pam50_review_packet import fixture


class ReviewGovernanceTests(unittest.TestCase):
    def setup_fixture(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        fixture(self.folder)
        packet, worksheet = assemble(self.folder)
        (self.folder / "PAM50_REVIEW_PACKET.json").write_text(
            json.dumps(packet, indent=2) + "\n", encoding="utf-8"
        )
        (self.folder / "PAM50_MANUSCRIPT_REVIEW.md").write_text(
            worksheet, encoding="utf-8"
        )
        self.packet, self.digest = packet_anchor(self.folder)

    def test_unsigned_preparation_never_selects_decisions(self) -> None:
        self.setup_fixture()
        prepare(self.folder, self.packet, self.digest)
        check_prepared(self.folder, self.packet, self.digest)
        contents = json.loads((self.folder / DECISIONS_TEMPLATE).read_text())
        self.assertEqual(set(contents["decisions"]), set(DECISIONS))
        self.assertTrue(all(v["state"] == "PENDING" for v in contents["decisions"].values()))
        self.assertEqual(contents["public_release"], "BLOCKED")
        with self.assertRaises(ReviewBlocked):
            prepare(self.folder, self.packet, self.digest)

    def test_modified_preparation_is_rejected(self) -> None:
        self.setup_fixture()
        prepare(self.folder, self.packet, self.digest)
        path = self.folder / DECISIONS_TEMPLATE
        contents = json.loads(path.read_text())
        contents["decisions"]["figure_legibility"]["state"] = "ACCEPTED"
        path.write_text(json.dumps(contents))
        with self.assertRaises(ReviewBlocked):
            check_prepared(self.folder, self.packet, self.digest)

    def test_any_change_to_unsigned_packet_invalidates_handoff(self) -> None:
        self.setup_fixture()
        prepare(self.folder, self.packet, self.digest)
        path = self.folder / "PAM50_MANUSCRIPT_REVIEW.md"
        path.write_text(path.read_text() + "changed", encoding="utf-8")
        with self.assertRaises(ReviewBlocked):
            packet_anchor(self.folder)

    def test_unapproved_decisions_remain_nonreleasing(self) -> None:
        self.setup_fixture()
        record = decision_template(self.digest)
        result = validate_decisions(record, self.digest)
        self.assertFalse(result["human_review_complete"])
        self.assertEqual(result["outstanding_decisions"], list(DECISIONS))
        self.assertEqual(result["merge_authorization"], "NOT_GRANTED")

    def test_human_review_structural_checks_do_not_authorize_release(self) -> None:
        self.setup_fixture()
        record = decision_template(self.digest)
        for item in record["decisions"].values():
            item.update(
                state="ACCEPTED", reviewer="Example synthetic reviewer",
                reviewed_at_utc="2026-10-12T20:00:00+00:00",
                rationale="Synthetic reviewer acceptance for validation tests.",
            )
        result = validate_decisions(record, self.digest)
        self.assertTrue(result["human_review_complete"])
        self.assertEqual(result["public_release"], "BLOCKED")
        self.assertEqual(result["record_structure"], "VALIDATED_NOT_AUTHENTICATED")
        record["public_release"] = "AUTHORIZED"
        with self.assertRaises(ReviewBlocked):
            validate_decisions(record, self.digest)

    def test_review_cannot_be_attributed_without_identity_and_utc(self) -> None:
        self.setup_fixture()
        record = decision_template(self.digest)
        record["decisions"]["figure_legibility"]["state"] = "ACCEPTED"
        with self.assertRaises(ReviewBlocked):
            validate_decisions(record, self.digest)
        record["decisions"]["figure_legibility"].update(
            reviewer="Synthetic reviewer", rationale="Reviewed synthetic figure",
            reviewed_at_utc="2026-10-12T12:00:00",
        )
        with self.assertRaises(ReviewBlocked):
            validate_decisions(record, self.digest)

    def test_revision_requires_exact_predecessor(self) -> None:
        self.setup_fixture()
        previous = decision_template(self.digest)
        path = self.folder / "review1.json"
        path.write_text(json.dumps(previous), encoding="utf-8")
        previous_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        revised = copy.deepcopy(previous)
        revised["revision"] = 2
        revised["previous_revision_sha256"] = previous_digest
        result = validate_decisions(revised, self.digest, previous, previous_digest)
        self.assertFalse(result["human_review_complete"])
        with self.assertRaises(ReviewBlocked):
            validate_decisions(revised, self.digest)
        with self.assertRaises(ReviewBlocked):
            validate_decisions(revised, self.digest, previous, "f" * 64)

    def test_journal_policy_unset_and_source_bound(self) -> None:
        self.setup_fixture()
        template = journal_template(self.digest)
        self.assertIsNone(template["journal_title"])
        with self.assertRaises(ReviewBlocked):
            journal_preflight(self.folder, template, self.digest)
        template["packet_sha256"] = "f" * 64
        with self.assertRaises(ReviewBlocked):
            journal_preflight(self.folder, template, self.digest)

    def test_journal_declared_dimensions_and_dpi_are_checked(self) -> None:
        self.setup_fixture()
        profile = journal_template(self.digest)
        profile.update(
            journal_title="Synthetic editorial profile (not actual journal)",
            instructions_url="https://example.org/author-instructions",
            checked_on="2026-10-12", checked_by="Synthetic editorial reviewer",
            max_width_in=9, max_height_in=13, min_raster_dpi=300,
            accepted_formats=["PDF", "PNG"],
        )
        passed = journal_preflight(self.folder, profile, self.digest)
        self.assertEqual(passed["status"], "TECHNICAL_METADATA_PREFLIGHT_PASS")
        self.assertEqual(passed["public_release"], "BLOCKED")
        profile["max_width_in"] = 3.5
        blocked = journal_preflight(self.folder, profile, self.digest)
        self.assertEqual(blocked["status"], "EDITORIAL_FIT_BLOCKED")
        self.assertEqual(len(blocked["problems"]), 2)
        profile["max_width_in"] = 9
        profile["min_raster_dpi"] = 600
        self.assertEqual(len(journal_preflight(
            self.folder, profile, self.digest
        )["problems"]), 2)

    def test_journal_profile_template_immutable(self) -> None:
        self.setup_fixture()
        prepare(self.folder, self.packet, self.digest)
        path = self.folder / JOURNAL_TEMPLATE
        profile = json.loads(path.read_text())
        profile["journal_title"] = "Fake journal"
        path.write_text(json.dumps(profile), encoding="utf-8")
        with self.assertRaises(ReviewBlocked):
            check_prepared(self.folder, self.packet, self.digest)


if __name__ == "__main__":
    unittest.main()
