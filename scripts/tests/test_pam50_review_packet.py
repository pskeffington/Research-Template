"""Synthetic, nonclinical negative gates for the private manuscript-review packet."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_pam50_review_packet import ReviewBlocked, assemble

SUBTYPES = ("Basal", "Her2", "LumA", "LumB")
PAIRS = {"Basal": 16, "Her2": 9, "LumA": 59, "LumB": 22}
CONTRASTS = [
    "Basal_vs_LumA", "Her2_vs_LumA", "LumB_vs_LumA",
    "Basal_vs_Her2", "Basal_vs_LumB", "Her2_vs_LumB",
]


def save(folder: Path, name: str, data: dict) -> None:
    (folder / name).write_text(json.dumps(data), encoding="utf-8")


def file_pair(folder: Path, stem: str) -> tuple[list[str], list[str]]:
    names = [stem + ".pdf", stem + ".png"]
    for name in names:
        (folder / name).write_bytes(b"synthetic placeholder, not a clinical image" + name.encode())
    hashes = [hashlib.sha256((folder / name).read_bytes()).hexdigest() for name in names]
    return names, hashes


def fixture(folder: Path) -> None:
    source = {
        "status": "PRIVATE_FROZEN_DESCRIPTIVE_FIGURES_STRUCTURALLY_VERIFIED",
        "data_status": "PRIVATE", "public_release": "NOT_AUTHORIZED",
        "scientific_review": "PENDING", "visual_review": "PENDING",
        "caption_review": "PENDING_AUTHOR_AND_SCIENTIFIC_REVIEW",
        "inference": "POST_SELECTION_DESCRIPTIVE_ONLY",
        "n_genes": 60, "n_subtype_effects": 240,
        "n_planned_contrasts": 360, "n_full_genes": 21432,
        "n_full_contrast_tests": 128592, "subtype_pairs": PAIRS,
        "input_hashes": dict.fromkeys(("ST06", "ST07", "ST09"), "a" * 64),
    }
    save(folder, "source_validation.json", source)
    audit = {
        "status": "STRUCTURAL_LAYOUT_PASS",
        "human_visual_review": "PENDING", "scientific_review": "PENDING",
        "figures": {
            kind: {
                "status": "STRUCTURAL_TEXT_LAYOUT_PASS",
                "matrix_bottom_to_column_label_gap_pt": 14.0,
                "min_observed_text_margin_pt": 18.0,
                "measured_subtype_label_to_legend_gap_pt": 30.0,
            } for kind in ("paired_effects", "six_contrasts")
        },
    }
    save(folder, "layout_audit.json", audit)
    for kind in ("paired_effects", "six_contrasts"):
        stem = "PAM50_" + kind
        names, hashes = file_pair(folder, stem)
        caption = (
            "Synthetic 106 matched cohort with 15-gene subtype-anchor. "
            "Scientific post-selection descriptive interpretation only."
        )
        (folder / (stem + ".caption.txt")).write_text(caption, encoding="utf-8")
        meta = {
            "figure_id": stem, "data_status": "PRIVATE",
            "figure_review": "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW",
            "caption_review": "PENDING_AUTHOR_AND_SCIENTIFIC_REVIEW",
            "public_release_requested": False,
            "inferential_status": "POST_SELECTION_DESCRIPTIVE_ONLY",
            "sample_level_columns": False, "n_features": 60,
            "selected_gene_count": 60,
            "n_columns": 4 if kind == "paired_effects" else 6,
            "n_pairs_by_subtype": PAIRS, "n_formal_subtype_pairs": 106,
            "n_primary_discovery_pairs": 109,
            "anchor_order": list(SUBTYPES),
            "anchor_counts": dict.fromkeys(SUBTYPES, 15),
            "contrast_order": CONTRASTS if kind == "six_contrasts" else {},
            "gene_order": [f"SYNTHETIC_G{n:03d}" for n in range(60)],
            "anchor_legend": "GENE_ANCHOR_15_PER_GROUP_SHOWN_LEFT",
            "shared_color_scale": True, "scale_policy": "FULL_OBSERVED_RANGE_NO_CLIPPING",
            "width_in": 9, "height_in": 13, "dpi": 300,
            "caption_file": str(folder / (stem + ".caption.txt")),
            "manuscript_caption": caption, "files": names, "sha256": hashes,
            "color_breaks": [-11.0, 0, 11.0],
        }
        save(folder, stem + ".metadata.json", meta)
    stem = "PAM50_scale_diagnostic"
    names, hashes = file_pair(folder, stem)
    save(folder, stem + ".metadata.json", {
        "figure_id": "PAM50_Scale_Diagnostic",
        "data_status": "PRIVATE", "figure_review": "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW",
        "inference": "DESCRIPTIVE_ONLY", "n_analyzed": 600,
        "analysis_unit": "modeled effect cell (not a person)",
        "files": names, "sha256": hashes,
    })
    save(folder, "PAM50_scale_summary.json", {
        "status": "SUPPLEMENTARY_POST_SELECTION_SCALE_DIAGNOSTIC",
        "public_release": "NOT_AUTHORIZED", "effect_cells": 600,
        "independence": "NOT_INDEPENDENT_PATIENT_OBSERVATIONS",
    })


class PendingReviewPacketTests(unittest.TestCase):
    def setup_fixture(self) -> None:
        self.working = tempfile.TemporaryDirectory()
        self.addCleanup(self.working.cleanup)
        self.folder = Path(self.working.name)
        fixture(self.folder)

    def mutate(self, name: str, field: str, value: object) -> None:
        path = self.folder / name
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc[field] = value
        save(self.folder, name, doc)

    def assert_blocked(self) -> None:
        with self.assertRaises(ReviewBlocked):
            assemble(self.folder)

    def test_clean_synthetic_packet_is_still_pending(self) -> None:
        self.setup_fixture()
        result, checklist = assemble(self.folder)
        self.assertEqual(result["status"], "REVIEW_REQUIRED_NOT_APPROVED")
        self.assertEqual(result["public_release"], "BLOCKED")
        self.assertEqual(result["merge_authorization"], "NOT_GRANTED")
        self.assertTrue(all(x == "PENDING" for x in result["human_reviews"].values()))
        self.assertNotIn("SYNTHETIC_G000", json.dumps(result))
        self.assertIn("- [ ]", checklist)
        self.assertNotIn("- [x]", checklist.lower())

    def test_corrupted_pdf_checksum_rejected(self) -> None:
        self.setup_fixture()
        with (self.folder / "PAM50_paired_effects.pdf").open("ab") as file:
            file.write(b"tamper")
        self.assert_blocked()

    def test_missing_caption_rejected(self) -> None:
        self.setup_fixture()
        (self.folder / "PAM50_six_contrasts.caption.txt").unlink()
        self.assert_blocked()

    def test_fake_scientific_approval_rejected(self) -> None:
        self.setup_fixture()
        self.mutate("source_validation.json", "scientific_review", "APPROVED")
        self.assert_blocked()

    def test_public_release_flag_rejected(self) -> None:
        self.setup_fixture()
        self.mutate("source_validation.json", "public_release", "AUTHORIZED")
        self.assert_blocked()

    def test_rotated_label_overlap_rejected(self) -> None:
        self.setup_fixture()
        path = self.folder / "layout_audit.json"
        doc = json.loads(path.read_text())
        doc["figures"]["six_contrasts"]["matrix_bottom_to_column_label_gap_pt"] = 7
        save(self.folder, "layout_audit.json", doc)
        self.assert_blocked()

    def test_gene_order_disagreement_rejected(self) -> None:
        self.setup_fixture()
        path = self.folder / "PAM50_six_contrasts.metadata.json"
        doc = json.loads(path.read_text())
        doc["gene_order"].reverse()
        save(self.folder, path.name, doc)
        self.assert_blocked()

    def test_supplement_cannot_count_independent_patients(self) -> None:
        self.setup_fixture()
        self.mutate("PAM50_scale_summary.json", "independence", "INDEPENDENT_PATIENTS")
        self.assert_blocked()

    def test_missing_source_pin_rejected(self) -> None:
        self.setup_fixture()
        self.mutate("source_validation.json", "input_hashes", {"ST06": "b" * 64})
        self.assert_blocked()


if __name__ == "__main__":
    unittest.main()
