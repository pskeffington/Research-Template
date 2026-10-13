"""Synthetic-only negative gates for unsigned private journal render requests."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_pam50_review_packet import ReviewBlocked, assemble, sha256
from scripts.pam50_review_governance import packet_anchor, prepare as prepare_review
from scripts.prepare_private_journal_gate import (
    OUTPUT_GATE,
    OUTPUT_REQUEST,
    prepare,
    verify,
)
from scripts.tests.test_pam50_review_packet import fixture

TEMPLATE = "a" * 40
SCENARIOS = ("J01", "J03", "J04", "J05")


def save(folder: Path, name: str, value: dict) -> None:
    (folder / name).write_text(json.dumps(value), encoding="utf-8")


class PrivateJournalAuthorizationGateTests(unittest.TestCase):
    def setup_fixture(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name) / "private"
        self.folder.mkdir()
        self.matrix = Path(temp.name) / "journals.csv"
        self.matrix.write_text("id,source\nJ01,https://example.org\n", encoding="utf-8")
        fixture(self.folder)
        packet, worksheet = assemble(self.folder)
        save(self.folder, "PAM50_REVIEW_PACKET.json", packet)
        (self.folder / "PAM50_MANUSCRIPT_REVIEW.md").write_text(worksheet)
        upstream, digest = packet_anchor(self.folder)
        prepare_review(self.folder, upstream, digest)
        save(self.folder, "PAM50_PHYSICAL_EXPORT_AUDIT.json", {
            "status": "PHYSICAL_EXPORTS_VERIFIED_MANUAL_REVIEW_PENDING",
            "public_release": "BLOCKED", "figures": [{}, {}, {}],
        })
        save(self.folder, "PAM50_JOURNAL_READINESS.json", {
            "status": "JOURNAL_NOT_SELECTED_MASTER_ONLY",
            "public_release": "BLOCKED",
            "figures": {"paired": {}, "contrasts": {}, "diagnostic": {}},
        })
        save(self.folder, "PAM50_JOURNAL_COMPARISON.json", {
            "status": "JOURNAL_COMPARISON_READ_ONLY", "policy_count": 9,
            "figure_count": 3, "journal_selected": False,
            "public_release": "BLOCKED",
            "journal_policy_matrix_sha256": sha256(self.matrix),
            "policies": [{"id": f"J{i:02d}", "journal_selected": False,
                          "public_release": "BLOCKED"} for i in range(1, 10)],
        })
        plan = {
            "status": "R_LAYOUT_PLAN_ONLY_NOT_RENDERED",
            "scientific_estimates_recomputed": False,
            "original_files_modified": False,
            "total_review_pages": 4,
            "public_release": "BLOCKED",
            "pages": [{"row_start": 1, "row_end": 30},
                      {"row_start": 31, "row_end": 60}],
            "complete_gene_order_sha256": "b" * 64,
            "shared_color_breaks": [-12, 0, 12],
        }
        save(self.folder, "PAM50_JOURNAL_R_LAYOUT_PLANS.json", {
            "status": "REVIEW_ONLY_R_LAYOUT_SCENARIOS_VALIDATED",
            "journal_selected": False, "figure_values_exported": False,
            "public_release": "BLOCKED",
            "plans": {key: dict(plan, journal_scenario=key) for key in SCENARIOS},
        })

    def mutate(self, name: str, field: str, value: object) -> None:
        path = self.folder / name
        data = json.loads(path.read_text())
        data[field] = value
        save(self.folder, name, data)

    def test_pending_gate_round_trip_does_not_export(self) -> None:
        self.setup_fixture()
        prepare(self.folder, self.matrix, TEMPLATE)
        verify(self.folder, self.matrix, TEMPLATE)
        request = json.loads((self.folder / OUTPUT_REQUEST).read_text())
        gate = json.loads((self.folder / OUTPUT_GATE).read_text())
        self.assertIsNone(request["target_journal_id"])
        self.assertEqual(request["render_authorization"], "NOT_GRANTED")
        self.assertEqual(request["public_release"], "BLOCKED")
        self.assertEqual(gate["status"], "PRIVATE_JOURNAL_DERIVATIVE_RENDER_BLOCKED")
        self.assertEqual(gate["render_execution"], "DISABLED")
        self.assertEqual(gate["generated_derivative_count"], 0)
        self.assertEqual(request["source_gene_order_sha256"], "b" * 64)

    def test_refuse_overwrite_or_approval_flag(self) -> None:
        self.setup_fixture()
        prepare(self.folder, self.matrix, TEMPLATE)
        with self.assertRaisesRegex(ReviewBlocked, "overwrite"):
            prepare(self.folder, self.matrix, TEMPLATE)
        self.mutate(OUTPUT_REQUEST, "render_authorization", "GRANTED")
        with self.assertRaisesRegex(ReviewBlocked, "altered"):
            verify(self.folder, self.matrix, TEMPLATE)

    def test_false_signed_claim_rejected(self) -> None:
        self.setup_fixture()
        prepare(self.folder, self.matrix, TEMPLATE)
        self.mutate(OUTPUT_REQUEST, "human_approval_authentication", "VERIFIED")
        with self.assertRaises(ReviewBlocked):
            verify(self.folder, self.matrix, TEMPLATE)

    def test_policy_file_change_rejected(self) -> None:
        self.setup_fixture()
        prepare(self.folder, self.matrix, TEMPLATE)
        self.matrix.write_text(self.matrix.read_text() + "# changed\n")
        with self.assertRaisesRegex(ReviewBlocked, "comparison"):
            verify(self.folder, self.matrix, TEMPLATE)

    def test_human_worksheet_tamper_rejected(self) -> None:
        self.setup_fixture()
        prepare(self.folder, self.matrix, TEMPLATE)
        path = self.folder / "PAM50_MANUSCRIPT_REVIEW.md"
        path.write_text(path.read_text() + "\ncheckbox touched")
        with self.assertRaises(ReviewBlocked):
            verify(self.folder, self.matrix, TEMPLATE)

    def test_wrong_template_revision_rejected(self) -> None:
        self.setup_fixture()
        prepare(self.folder, self.matrix, TEMPLATE)
        with self.assertRaisesRegex(ReviewBlocked, "altered"):
            verify(self.folder, self.matrix, "f" * 40)
        with self.assertRaisesRegex(ReviewBlocked, "40-hex"):
            verify(self.folder, self.matrix, "no_commit")

    def test_modified_anchor_boundary_rejected(self) -> None:
        self.setup_fixture()
        path = self.folder / "PAM50_JOURNAL_R_LAYOUT_PLANS.json"
        doc = json.loads(path.read_text())
        doc["plans"]["J03"]["pages"][1]["row_start"] = 29
        save(self.folder, path.name, doc)
        with self.assertRaisesRegex(ReviewBlocked, "boundaries"):
            prepare(self.folder, self.matrix, TEMPLATE)

    def test_unverified_missing_journal_record_rejected(self) -> None:
        self.setup_fixture()
        path = self.folder / "PAM50_JOURNAL_COMPARISON.json"
        doc = json.loads(path.read_text())
        doc["policies"].pop()
        save(self.folder, path.name, doc)
        with self.assertRaisesRegex(ReviewBlocked, "nine"):
            prepare(self.folder, self.matrix, TEMPLATE)

    def test_source_metadata_hash_change_rejected(self) -> None:
        self.setup_fixture()
        prepare(self.folder, self.matrix, TEMPLATE)
        path = self.folder / "PAM50_JOURNAL_READINESS.json"
        data = json.loads(path.read_text())
        data["status"] = "APPROVED"
        save(self.folder, path.name, data)
        with self.assertRaises(ReviewBlocked):
            verify(self.folder, self.matrix, TEMPLATE)

    def test_no_tiff_eps_or_unapproved_journal_files(self) -> None:
        self.setup_fixture()
        (self.folder / "unapproved.eps").write_text("synthetic")
        with self.assertRaisesRegex(ReviewBlocked, "Unexpected derivative"):
            prepare(self.folder, self.matrix, TEMPLATE)
        (self.folder / "unapproved.eps").unlink()
        prepare(self.folder, self.matrix, TEMPLATE)
        (self.folder / "unapproved.tif").write_bytes(b"synthetic")
        with self.assertRaisesRegex(ReviewBlocked, "Unexpected derivative"):
            verify(self.folder, self.matrix, TEMPLATE)


if __name__ == "__main__":
    unittest.main()
