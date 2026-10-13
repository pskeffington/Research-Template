"""Synthetic journal-wide comparison gates; no private research data."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.compare_journal_requirements import (
    ProofBlocked,
    compare,
    evaluate_row,
    positive_optional,
)
from scripts.tests.test_manuscript_physical import fixture


class JournalComparisonTests(unittest.TestCase):
    def setup_fixture(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name) / "figures"
        self.folder.mkdir()
        fixture(self.folder)
        self.matrix = Path(temp.name) / "policies.csv"
        self.matrix.write_text(
            "id,journal,policy_authority,verification_status,research_scope,"
            "primary_source_url,accessed_on,max_width_in,max_height_in,"
            "double_column_mm,raster_min_dpi,figure_formats\n"
            "J03,Test PLOS,JOURNAL_OFFICIAL,VERIFIED_JOURNAL_PAGE,Original research,"
            "https://example.org/plos,2026-10-12,1.0,0.5,,300,TIFF or EPS only\n"
            "J05,Test Columns,JOURNAL_OFFICIAL,VERIFIED_JOURNAL_PAGE,Original research,"
            "https://example.org/columns,2026-10-12,,,20,350,EPS acceptable\n"
            "J06,Test Scope,JOURNAL_OFFICIAL,VERIFIED_JOURNAL_PAGE,"
            "Review only; NOT pure original-research target,"
            "https://example.org/scope,2026-10-12,7.5,8.75,,300,TIFF or EPS only\n"
            "J09,Test Publisher,PUBLISHER_GENERAL_NOT_JOURNAL,"
            "JOURNAL_SPECIFIC_REVIEW_REQUIRED,Original research,"
            "https://example.org/publisher,2026-10-12,,,,200,TIFF\n",
            encoding="utf-8",
        )

    def test_read_only_matrix_allows_no_release_or_selection(self) -> None:
        self.setup_fixture()
        before = sorted((p.name, p.stat().st_size) for p in self.folder.iterdir())
        summary = compare(self.folder, self.matrix)
        after = sorted((p.name, p.stat().st_size) for p in self.folder.iterdir())
        self.assertEqual(before, after)
        self.assertEqual(summary["status"], "JOURNAL_COMPARISON_READ_ONLY")
        self.assertEqual(summary["policy_count"], 4)
        self.assertEqual(summary["figure_count"], 3)
        self.assertFalse(summary["journal_selected"])
        self.assertEqual(summary["public_release"], "BLOCKED")
        self.assertEqual(len(summary["journal_policy_matrix_sha256"]), 64)

    def test_maximum_artwork_geometry_requires_r_redesign(self) -> None:
        self.setup_fixture()
        result = compare(self.folder, self.matrix)
        plos = result["policies"][0]
        self.assertEqual(plos["status"], "ORIGINAL_R_RELAYOUT_REQUIRED")
        self.assertTrue(all(row["requires_relayout"]
                            for row in plos["figure_checks"].values()))
        self.assertTrue(any("TIFF/EPS" in msg for msg in plos["review_flags"]))

    def test_double_column_width_is_scenario_not_page_max(self) -> None:
        self.setup_fixture()
        result = compare(self.folder, self.matrix)
        column = result["policies"][1]
        self.assertEqual(column["status"], "ORIGINAL_R_RELAYOUT_REQUIRED")
        stats = column["figure_checks"]["paired_effects"]
        self.assertEqual(stats["scale_to_explicit_maximum"], 1)
        self.assertEqual(stats["double_column_width_mm_if_provided"], 20)
        self.assertLess(stats["projected_font_at_double_column_pt"], 8)

    def test_reviewer_hold_overrides_possible_artwork_sizes(self) -> None:
        self.setup_fixture()
        result = compare(self.folder, self.matrix)
        self.assertEqual(result["policies"][2]["status"], "ARTICLE_SCOPE_REVIEW_REQUIRED")
        self.assertEqual(result["policies"][3]["status"], "UNVERIFIED_POLICY_HOLD")
        for entry in result["policies"]:
            self.assertFalse(entry["journal_selected"])
            self.assertEqual(entry["public_release"], "BLOCKED")

    def test_duplicate_journal_id_fails_closed(self) -> None:
        self.setup_fixture()
        self.matrix.write_text(self.matrix.read_text() + self.matrix.read_text().splitlines()[1] + "\n")
        with self.assertRaisesRegex(ProofBlocked, "Duplicate"):
            compare(self.folder, self.matrix)

    def test_bad_nan_numeric_fails_closed(self) -> None:
        with self.assertRaisesRegex(ProofBlocked, "Invalid"):
            positive_optional("nan", "min_dpi")

    def test_missing_detailed_rule_never_earns_mechanical_pass(self) -> None:
        row = {
            "id": "J01", "journal": "Synthetic",
            "policy_authority": "JOURNAL_OFFICIAL",
            "verification_status": "VERIFIED_JOURNAL_PAGE",
            "primary_source_url": "https://example.org",
        }
        x = evaluate_row(row, {"paired_effects": {
            "width_in": 9, "height_in": 13, "minimum_font_pt": 10,
        }})
        self.assertEqual(x["status"], "ARTWORK_POLICY_INCOMPLETE")

    def test_corrupted_source_pdf_blocks_all_journal_comparison(self) -> None:
        self.setup_fixture()
        pdf = self.folder / "PAM50_paired_effects.pdf"
        pdf.write_bytes(pdf.read_bytes() + b"tamper")
        with self.assertRaises(ValueError):
            compare(self.folder, self.matrix)


if __name__ == "__main__":
    unittest.main()
