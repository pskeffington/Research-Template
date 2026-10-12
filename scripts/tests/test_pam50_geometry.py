"""Synthetic vector-PDF regression tests for both PAM50 column-label layouts.

No patient data, frozen signatures, or historical private PDFs are embedded.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pymupdf

from scripts.audit_pam50_layout import _matrix_to_column_labels_gap


LABELS = {
    "paired_effects": ("Basal", "Her2", "LumA", "LumB"),
    "six_contrasts": (
        "Basal - LumA", "Her2 - LumA", "LumB - LumA",
        "Basal - Her2", "Basal - LumB", "Her2 - LumB",
    ),
}


def create_fixture(path: Path, kind: str, separation: str = "valid",
                   missing_label: bool = False,
                   missing_cell: bool = False) -> None:
    """Create 60 complete vector cell rows and native-PDF column text."""
    names = LABELS[kind]
    count = len(names)
    width = 314.4 / count
    row_height = 7.4
    bottom = 60 + row_height * 60
    doc = pymupdf.open()
    page = doc.new_page(width=648, height=936)
    for row in range(60):
        for col in range(count):
            if missing_cell and row == 0 and col == 0:
                continue
            left = 134 + col * width
            top = 60 + row * row_height
            page.draw_rect(
                pymupdf.Rect(left, top, left + width, top + row_height),
                color=None, fill=(0.7, 0.8, 0.9),
            )
    for col, label in enumerate(names):
        if missing_label and col == count - 1:
            continue
        left = 130 + col * width
        baseline = bottom + (65 if kind == "six_contrasts" else 32)
        if separation == "overlap":
            baseline = bottom + (32 if kind == "six_contrasts" else 1)
        point = pymupdf.Point(left, baseline)
        kwargs = {}
        if kind == "six_contrasts":
            # Match the manuscript's approximately 35-degree label rotation.
            kwargs["morph"] = (
                point, pymupdf.Matrix(1, 0.7, -0.7, 1, 0, 0)
            )
        page.insert_text(point, label, fontsize=9, **kwargs)
    doc.save(path)
    doc.close()


class MatrixLabelClearanceRegression(unittest.TestCase):
    def test_both_valid_layouts_have_at_least_twelve_points(self) -> None:
        with tempfile.TemporaryDirectory() as location:
            for kind in LABELS:
                with self.subTest(kind=kind):
                    path = Path(location) / (kind + ".pdf")
                    create_fixture(path, kind)
                    self.assertGreaterEqual(
                        _matrix_to_column_labels_gap(path, kind), 12
                    )

    def test_both_overlapped_layouts_fail_clearance(self) -> None:
        with tempfile.TemporaryDirectory() as location:
            for kind in LABELS:
                with self.subTest(kind=kind):
                    path = Path(location) / (kind + ".pdf")
                    create_fixture(path, kind, separation="overlap")
                    self.assertLess(
                        _matrix_to_column_labels_gap(path, kind), 12
                    )

    def test_missing_label_is_not_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as location:
            for kind in LABELS:
                with self.subTest(kind=kind):
                    path = Path(location) / (kind + ".pdf")
                    create_fixture(path, kind, missing_label=True)
                    with self.assertRaisesRegex(ValueError, "column labels once"):
                        _matrix_to_column_labels_gap(path, kind)

    def test_missing_vector_cell_is_not_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as location:
            for kind in LABELS:
                with self.subTest(kind=kind):
                    path = Path(location) / (kind + ".pdf")
                    create_fixture(path, kind, missing_cell=True)
                    with self.assertRaisesRegex(ValueError, "vector cells"):
                        _matrix_to_column_labels_gap(path, kind)

    def test_unknown_figure_type_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as location:
            path = Path(location) / "unknown.pdf"
            create_fixture(path, "paired_effects")
            with self.assertRaisesRegex(ValueError, "Unknown PAM50 heatmap kind"):
                _matrix_to_column_labels_gap(path, "unknown")


if __name__ == "__main__":
    unittest.main()
