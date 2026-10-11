import json

import pytest

from research_template.cli import audit, demo
from research_template.plots import axis_label
from research_template.provenance import create_manifest
from research_template.quality import DataContractError, validate_cohort
from research_template.synthetic import make_cohort


def test_synthetic_is_deterministic():
    assert make_cohort(seed=34) == make_cohort(seed=34)
    assert make_cohort(seed=35) != make_cohort(seed=34)


def test_schema_and_missingness():
    rows = make_cohort()
    summary = validate_cohort(rows)
    assert summary["n_participants"] == 120
    assert summary["missing_counts"]["age_years"] > 0


def test_duplicate_id_refused():
    rows = make_cohort()
    rows[1]["participant_id"] = rows[0]["participant_id"]
    with pytest.raises(DataContractError, match="duplicate"):
        validate_cohort(rows)


def test_wrong_unit_type_and_bool_outcome_refused():
    rows = make_cohort()
    rows[1]["measurement_mg_dl"] = "1.0"
    with pytest.raises(DataContractError, match="finite numeric"):
        validate_cohort(rows)
    rows = make_cohort()
    rows[1]["outcome"] = True
    with pytest.raises(DataContractError, match="0 or 1"):
        validate_cohort(rows)


def test_axis_label_requires_units():
    assert axis_label("Age", "years") == "Age (years)"
    with pytest.raises(ValueError):
        axis_label("Age", "")


def test_core_demo_produces_checksums(tmp_path):
    out = tmp_path / "synthetic"
    demo(out, n=60, seed=9)
    manifest = json.loads((out / "run_manifest.json").read_text())
    assert manifest["status"] == "DEMONSTRATION_ONLY"
    assert manifest["scientific_release"] == "BLOCKED_UNTIL_REVIEWED"
    assert len(manifest["artifacts"]) == 2


def test_manifest_refuses_outside_directory(tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("no")
    target = tmp_path / "target"
    target.mkdir()
    with pytest.raises(ValueError, match="within"):
        create_manifest(target, [outside], seed=1, purpose="test")


def test_scaffold_audit_blocks_scientific_release(tmp_path):
    assert audit(tmp_path) == 1
    assert audit(tmp_path, require_release=True) == 1


def test_n_invalid():
    with pytest.raises(ValueError):
        make_cohort(10)
