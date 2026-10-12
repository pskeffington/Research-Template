"""Synthetic, nonclinical TIFF/EPS proof feasibility and isolation regressions."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import pymupdf
from PIL import Image

from scripts.build_journal_proofs import (
    ProofBlocked,
    execute,
    journal_rule,
    layout_plan,
)
from scripts.tests.test_manuscript_physical import fixture

POLICY = (
    "id,journal,policy_authority,verification_status,figure_formats,"
    "max_width_in,max_height_in,raster_min_dpi,primary_source_url,accessed_on\n"
    "J03,Synthetic Journal,JOURNAL_OFFICIAL,VERIFIED_JOURNAL_PAGE,"
    "TIFF or EPS only,1.8,0.9,300,https://example.org/figures,2026-10-12\n"
    "J09,Unverified Publisher,PUBLISHER_GENERAL_NOT_JOURNAL,"
    "JOURNAL_SPECIFIC_REVIEW_REQUIRED,TIFF or EPS only,1.8,0.9,300,"
    "https://example.org/general,2026-10-12\n"
)


class JournalProofSyntheticTests(unittest.TestCase):
    def setup_fixture(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name) / "source"
        self.folder.mkdir()
        fixture(self.folder)
        self.policy = Path(temporary.name) / "journals.csv"
        self.policy.write_text(POLICY, encoding="utf-8")
        self.output = Path(temporary.name) / "review_proofs"

    def test_no_journal_produces_only_read_only_report(self) -> None:
        self.setup_fixture()
        record = execute(self.folder)
        self.assertEqual(record["status"], "JOURNAL_NOT_SELECTED_MASTER_ONLY")
        self.assertFalse(self.output.exists())
        self.assertEqual(record["public_release"], "BLOCKED")
        self.assertEqual(len(record["figures"]), 3)

    def test_source_bound_feasibility_is_not_release(self) -> None:
        self.setup_fixture()
        result = execute(self.folder, matrix=self.policy, journal_id="J03")
        self.assertEqual(result["status"], "FEASIBILITY_REVIEW_ONLY")
        self.assertEqual(result["public_release"], "BLOCKED")
        self.assertFalse(self.output.exists())
        self.assertTrue(all(
            plan["status"] == "PROOF_GEOMETRY_FEASIBLE_REVIEW_REQUIRED"
            for plan in result["figure_plans"].values()
        ))

    def test_generates_tiff_lzw_and_eps_from_untouched_pdf(self) -> None:
        self.setup_fixture()
        original = self.folder / "PAM50_paired_effects.pdf"
        original_sha = hashlib.sha256(original.read_bytes()).hexdigest()
        result = execute(self.folder, matrix=self.policy, journal_id="J03",
                         output=self.output)
        self.assertEqual(result["status"], "REVIEW_PROOFS_GENERATED_NOT_APPROVED")
        self.assertEqual(result["public_release"], "BLOCKED")
        self.assertEqual(len(result["proofs"]), 3)
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), original_sha)
        for record in result["proofs"]:
            self.assertEqual(record["status"], "REVIEW_PROOF_ONLY_NOT_PRODUCTION_CERTIFIED")
            with Image.open(self.output / record["tiff"]) as figure:
                self.assertEqual(figure.format, "TIFF")
                self.assertEqual(figure.mode, "RGB")
                self.assertEqual(figure.tag_v2[259], 5)
                self.assertLessEqual(figure.width / 300, 1.81)
                self.assertLessEqual(figure.height / 300, 0.91)
            self.assertIn(b"%%BoundingBox:",
                          (self.output / record["eps"]).read_bytes()[:4096])
        self.assertTrue((self.output / "PROOF_MANIFEST.json").is_file())

    def test_no_implicit_journal_or_proof_path(self) -> None:
        self.setup_fixture()
        with self.assertRaisesRegex(ProofBlocked, "explicit journal"):
            execute(self.folder, output=self.output)
        with self.assertRaisesRegex(ProofBlocked, "cannot authorize"):
            execute(self.folder, matrix=self.policy, journal_id="J09",
                    output=self.output)
        self.assertFalse(self.output.exists())

    def test_refuse_overwriting_or_using_master_directory(self) -> None:
        self.setup_fixture()
        self.output.mkdir()
        with self.assertRaisesRegex(ProofBlocked, "overwrite"):
            execute(self.folder, matrix=self.policy, journal_id="J03",
                    output=self.output)
        with self.assertRaisesRegex(ProofBlocked, "immutable source"):
            execute(self.folder, matrix=self.policy, journal_id="J03",
                    output=self.folder / "proofs")

    def test_small_font_requires_r_layout_redesign(self) -> None:
        self.setup_fixture()
        pdf = self.folder / "small.pdf"
        with pymupdf.open() as doc:
            page = doc.new_page(width=648, height=936)
            page.insert_text((60, 80), "Synthetic gene label", fontsize=9)
            doc.save(pdf)
        rule = journal_rule(self.policy, "J03")
        plan = layout_plan(pdf, rule)
        self.assertEqual(plan["status"], "NEEDS_ORIGINAL_R_LAYOUT_REDESIGN")
        self.assertLess(plan["projected_smallest_font_pt"], 8)

    def test_policy_requires_explicit_dimensions_and_direct_source(self) -> None:
        self.setup_fixture()
        self.policy.write_text(POLICY.replace("1.8,0.9,300", ",0.9,300", 1))
        with self.assertRaisesRegex(ProofBlocked, "incomplete"):
            journal_rule(self.policy, "J03")

    def test_false_approval_on_original_blocks_proofs(self) -> None:
        self.setup_fixture()
        meta = self.folder / "PAM50_six_contrasts.metadata.json"
        record = json.loads(meta.read_text())
        record["figure_review"] = "APPROVED"
        meta.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaises(ValueError):
            execute(self.folder, matrix=self.policy, journal_id="J03",
                    output=self.output)


if __name__ == "__main__":
    unittest.main()
