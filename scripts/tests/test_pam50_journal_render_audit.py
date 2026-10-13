"""Fail-closed synthetic vector-proof audit regression checks."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.audit_pam50_journal_proofs import PageBlocked, audit, inspect_page

SOURCE = Path("artifacts/ci_figure_review/pam50_journal/J03")
STEM = "SYN_J03_paired_effects_p1"


class JournalRenderedProofTests(unittest.TestCase):
    def setup_fixture(self) -> None:
        if not (SOURCE / f"{STEM}.pdf").is_file():
            self.skipTest("R has not yet generated the synthetic-only journal pages")
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        for suffix in (".pdf", ".png", ".metadata.json"):
            shutil.copy2(SOURCE / f"{STEM}{suffix}",
                         self.folder / f"{STEM}{suffix}")

    def test_four_real_synthetic_renders_audit_independently(self) -> None:
        self.setup_fixture()
        result = audit(SOURCE)
        self.assertEqual(result["status"], "SYNTHETIC_COMPLEXHEATMAP_PROOFS_PASS")
        self.assertEqual(len(result["pages"]), 4)
        self.assertEqual(result["public_release"], "BLOCKED")
        self.assertTrue(all(page["gene_labels_verified"] == 30
                            and page["minimum_label_pt"] >= 8.5
                            and page["minimum_legend_gap_pt"] >= 12
                            for page in result["pages"]))

    def test_corrupted_vector_pdf_rejected(self) -> None:
        self.setup_fixture()
        with (self.folder / f"{STEM}.pdf").open("ab") as file:
            file.write(b"tamper")
        with self.assertRaisesRegex(PageBlocked, "modified source"):
            inspect_page(self.folder, STEM)

    def test_fake_approval_rejected(self) -> None:
        self.setup_fixture()
        metadata = self.folder / f"{STEM}.metadata.json"
        record = json.loads(metadata.read_text(encoding="utf-8"))
        record["figure_review"] = "APPROVED"
        metadata.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(PageBlocked, "no automated approval"):
            inspect_page(self.folder, STEM)

    def test_duplicate_gene_label_rejected(self) -> None:
        self.setup_fixture()
        metadata = self.folder / f"{STEM}.metadata.json"
        record = json.loads(metadata.read_text(encoding="utf-8"))
        record["gene_labels"][0] = record["gene_labels"][1]
        metadata.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(PageBlocked, "lost or duplicated"):
            inspect_page(self.folder, STEM)

    def test_changed_order_rejected(self) -> None:
        self.setup_fixture()
        metadata = self.folder / f"{STEM}.metadata.json"
        record = json.loads(metadata.read_text(encoding="utf-8"))
        record["gene_order"] = list(reversed(record["gene_order"]))
        metadata.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(PageBlocked, "order was changed"):
            inspect_page(self.folder, STEM)

    def test_missing_legend_semantics_rejected(self) -> None:
        self.setup_fixture()
        metadata = self.folder / f"{STEM}.metadata.json"
        record = json.loads(metadata.read_text(encoding="utf-8"))
        record["signed_scale"] = "color only"
        metadata.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(PageBlocked, "noncolor legends"):
            inspect_page(self.folder, STEM)


if __name__ == "__main__":
    unittest.main()
