"""Synthetic, nonclinical physical-export and journal-policy regression tests."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pymupdf

from scripts.audit_manuscript_physical import (
    PhysicalAuditBlocked,
    audit,
    journal_advisory,
    sha256,
)

FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


def fixture(folder: Path, *, dpi: int = 300, embedded: bool = True) -> None:
    for kind in ("paired_effects", "six_contrasts", "scale_diagnostic"):
        stem = folder / f"PAM50_{kind}"
        pdf = Path(f"{stem}.pdf")
        png = Path(f"{stem}.png")
        doc = pymupdf.open()
        page = doc.new_page(width=144, height=72)
        name = "helv"
        if embedded:
            name = "DejaVuTest"
            page.insert_font(fontname=name, fontfile=str(FONT))
        page.insert_text((15, 24), "Synthetic figure", fontname=name, fontsize=10)
        page.draw_rect(pymupdf.Rect(15, 30, 42, 49), color=None, fill=(0.2, 0.6, 0.7))
        doc.save(pdf)
        doc.close()
        pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 2 * dpi, dpi), False)
        pix.clear_with(255)
        pix.save(png)
        record = {
            "figure_review": "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW",
            "width_in": 2,
            "height_in": 1,
            "dpi": 300,
            "files": [pdf.name, png.name],
            "sha256": [sha256(pdf), sha256(png)],
        }
        Path(f"{stem}.metadata.json").write_text(json.dumps(record), encoding="utf-8")


class PhysicalExportsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        fixture(self.folder)

    def test_clean_three_panel_audit_keeps_review_pending(self) -> None:
        result = audit(self.folder)
        self.assertEqual(result["status"], "PHYSICAL_EXPORTS_VERIFIED_MANUAL_REVIEW_PENDING")
        self.assertEqual(result["public_release"], "BLOCKED")
        self.assertEqual(len(result["figures"]), 3)
        self.assertEqual(result["figures"][0]["effective_png_dpi"], [300.0, 300.0])
        self.assertTrue(result["figures"][0]["fonts"][0]["embedded"])

    def test_tampered_png_rejected(self) -> None:
        with (self.folder / "PAM50_six_contrasts.png").open("ab") as handle:
            handle.write(b"changed")
        with self.assertRaises(PhysicalAuditBlocked):
            audit(self.folder)

    def test_actual_raster_resolution_not_declared_dpi_controls_gate(self) -> None:
        second = tempfile.TemporaryDirectory()
        self.addCleanup(second.cleanup)
        folder = Path(second.name)
        fixture(folder, dpi=150)
        with self.assertRaisesRegex(PhysicalAuditBlocked, "insufficient effective"):
            audit(folder)

    def test_unembedded_pdf_font_rejected(self) -> None:
        second = tempfile.TemporaryDirectory()
        self.addCleanup(second.cleanup)
        folder = Path(second.name)
        fixture(folder, embedded=False)
        with self.assertRaisesRegex(PhysicalAuditBlocked, "unembedded"):
            audit(folder)

    def test_false_pdf_dimensions_rejected(self) -> None:
        path = self.folder / "PAM50_paired_effects.metadata.json"
        record = json.loads(path.read_text())
        record["width_in"] = 3
        path.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(PhysicalAuditBlocked, "PDF physical size"):
            audit(self.folder)

    def test_rejected_automatic_scientific_approval(self) -> None:
        path = self.folder / "PAM50_scale_diagnostic.metadata.json"
        record = json.loads(path.read_text())
        record["figure_review"] = "APPROVED"
        path.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(PhysicalAuditBlocked, "automatic approval"):
            audit(self.folder)

    def test_journal_comparison_never_confers_distribution(self) -> None:
        physical = audit(self.folder)
        csv_file = self.folder / "journal.csv"
        csv_file.write_text(
            "id,journal,verification_status,max_width_in,max_height_in,raster_min_dpi,"
            "figure_formats,primary_source_url,accessed_on\n"
            "J03,Synthetic,VERIFIED_JOURNAL_PAGE,1,1,350,TIFF or EPS only,"
            "https://example.org,2026-10-12\n",
            encoding="utf-8",
        )
        result = journal_advisory(csv_file, "J03", physical["figures"])
        self.assertEqual(result["status"], "DERIVATIVE_OR_EDITORIAL_REVIEW_REQUIRED")
        self.assertEqual(result["release"], "BLOCKED")
        self.assertTrue(any("format" in n.lower() for n in result["notices"]))
        self.assertTrue(any("width" in n for n in result["notices"]))

    def test_missing_selected_journal_blocked(self) -> None:
        with self.assertRaisesRegex(PhysicalAuditBlocked, "matrix"):
            audit(self.folder, journal_id="J03")


if __name__ == "__main__":
    unittest.main()
