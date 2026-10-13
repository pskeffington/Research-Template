"""Validate publisher/journal-source provenance in the public policy matrices.

Author: Paul Skeffington. Prepared with OpenAI.
No private research data or journal acceptance claim is embedded here.
"""
from __future__ import annotations

import csv
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "references" / "JOURNAL_FIGURE_REQUIREMENTS_MATRIX_2026-10-12.csv"
REPORTING = ROOT / "references" / "JOURNAL_REPORTING_FRAMEWORKS_2026-10-12.csv"
DATE = "2026-10-12"


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError(f"Empty policy matrix {path.name}")
    return rows


class JournalRequirementsMatrixTests(unittest.TestCase):
    def test_sources_are_https_and_dated(self) -> None:
        for path in (FIGURES, REPORTING):
            rows = load_rows(path)
            self.assertTrue(all(None not in row for row in rows))
            self.assertEqual(len(rows), len({row["id"] for row in rows}))
            for row in rows:
                with self.subTest(matrix=path.name, id=row["id"]):
                    self.assertEqual(row["accessed_on"], DATE)
                    url = urlparse(row["primary_source_url"])
                    self.assertEqual(url.scheme, "https")
                    self.assertTrue(url.netloc)

    def test_journal_status_prevents_unverified_publisher_promotion(self) -> None:
        rows = load_rows(FIGURES)
        self.assertGreaterEqual(len(rows), 8)
        for row in rows:
            with self.subTest(journal=row["journal"]):
                self.assertIn(row["verification_status"], {
                    "VERIFIED_JOURNAL_PAGE", "PUBLISHER_POLICY_ONLY",
                    "JOURNAL_SPECIFIC_REVIEW_REQUIRED",
                })
                self.assertIn(row["policy_authority"], {
                    "JOURNAL_OFFICIAL", "PUBLISHER_COMMON",
                    "PUBLISHER_GENERAL_NOT_JOURNAL",
                })
                if row["policy_authority"] != "JOURNAL_OFFICIAL":
                    self.assertNotEqual(row["verification_status"], "VERIFIED_JOURNAL_PAGE")
                self.assertTrue(row["general_adaptation_notes"].strip())

    def test_unknown_numerical_constraints_remain_unknown(self) -> None:
        rows = load_rows(FIGURES)
        numbers = (
            "raster_min_dpi", "line_art_min_dpi", "single_column_mm",
            "double_column_mm", "max_width_in", "max_height_in", "legend_max_words",
        )
        for row in rows:
            for key in numbers:
                value = row[key]
                if value:
                    with self.subTest(journal=row["journal"], field=key):
                        self.assertGreater(float(value), 0)
        self.assertEqual(next(r for r in rows if r["journal"] == "BMC Cancer")[
            "verification_status"
        ], "JOURNAL_SPECIFIC_REVIEW_REQUIRED")

    def test_reporting_guidelines_are_conditional(self) -> None:
        rows = load_rows(REPORTING)
        self.assertEqual({r["framework"] for r in rows if r["id"] != "G05"},
                         {"STROBE", "STREGA", "REMARK", "TRIPOD+AI"})
        for row in rows:
            self.assertTrue(row["not_a_requirement_when"].strip())
            self.assertIn(row["status"], {
                "APPLICABILITY_REQUIRES_METHODS_REVIEW", "JOURNAL_WORKFLOW_SPECIFIC",
            })


if __name__ == "__main__":
    unittest.main()
