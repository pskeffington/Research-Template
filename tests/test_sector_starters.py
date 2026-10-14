"""Synthetic-only generation and fail-closed validation of four oncology starter recipes."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from research_template.cli import main
from research_template.sector_starters import (
    RecipeError,
    create_recipe_workspace,
    get_recipe,
    list_recipes,
    validate_recipe_workspace,
)

IDS = ("CPS-02", "SGN-02", "ICI-02", "TEC-01")


@pytest.mark.parametrize("recipe_id", IDS)
def test_each_sector_produces_reproducible_blank_starter(recipe_id, tmp_path):
    root = create_recipe_workspace(recipe_id, tmp_path / "study")
    report = validate_recipe_workspace(root)
    assert report["status"] == "REFERENCE_WORKSPACE_PASS_NO_ANALYSIS"
    assert report["input_rows_read"] == 0
    assert report["analyses_executed"] is False
    assert report["public_release"] == "BLOCKED"
    study = json.loads((root / "study.json").read_text())
    assert study["public_release"] == "BLOCKED"
    assert study["scientific_validation"] == "NOT_ASSESSED"
    assert study["data_access"] == "NOT_ASSESSED"
    for name in ("data", "private", "outputs"):
        assert list((root / name).iterdir()) == []
    recipe, _ = get_recipe(recipe_id)
    with (root / "VARIABLE_MAPPING.csv").open(newline="") as stream:
        mappings = list(csv.DictReader(stream))
    assert [m["role"] for m in mappings] == [
        m["role"] for m in recipe["variable_roles"]
    ]
    assert all(not m["source_column"] for m in mappings)
    assert "BLOCKED" in (root / "ANALYSIS_PLAN.md").read_text()
    assert "PLANNING ONLY" in (root / "FIGURE_PLAN.md").read_text()
    assert recipe["source_access_url"] in (root / "SECURITY_AND_APPROVALS.md").read_text()


def test_recipes_cover_four_independent_scientific_programs():
    result = list_recipes()
    assert result["status"] == "REFERENCE_WORKSPACE_TEMPLATES_ONLY"
    assert [r["id"] for r in result["recipes"]] == list(IDS)
    assert {r["program_id"] for r in result["recipes"]} == {
        "CPS", "SGN", "ICI", "TEC"
    }
    assert result["actual_data_loaded"] is False
    assert result["analyses_executed"] is False
    assert result["public_release"] == "BLOCKED"


def test_transcriptomics_preconditions_distinguish_count_and_intensity():
    recipe, digest = get_recipe("SGN-02")
    assert len(digest) == 64
    assert {m["method"] for m in recipe["method_choices"]} == {"DESeq2", "limma"}
    assert "integer" in recipe["method_choices"][0]["preconditions"]
    assert all(m["execution"] == "DISABLED_PENDING_DESIGN_REVIEW"
               for m in recipe["method_choices"])
    assert all(x["render_status"] == "PLAN_ONLY" for x in recipe["figure_recipes"])


def test_ici_disallows_cell_pseudoreplication_and_tec_requires_patient_level_split():
    immunology, _ = get_recipe("ICI-02")
    imaging, _ = get_recipe("TEC-01")
    assert "independent replicates" in " ".join(immunology["review_gates"])
    assert "patient-level split" in " ".join(imaging["review_gates"])


def test_population_recipe_requires_survey_weights_psu_and_stratum():
    recipe, _ = get_recipe("CPS-02")
    roles = {r["role"] for r in recipe["variable_roles"]}
    assert {"survey_weight", "psu", "stratum", "screening_status"} <= roles
    assert "confidence interval" in recipe["figure_recipes"][0]["uncertainty"]


def test_existing_path_is_never_overwritten(tmp_path):
    path = tmp_path / "existing"
    path.mkdir()
    (path / "sentinel.txt").write_text("must survive")
    with pytest.raises(RecipeError, match="never overwrite"):
        create_recipe_workspace("SGN-02", path)
    assert (path / "sentinel.txt").read_text() == "must survive"


def test_unknown_undocumented_recipe_is_blocked(tmp_path):
    with pytest.raises(RecipeError, match="Unknown"):
        create_recipe_workspace("TEC-03", tmp_path / "nope")
    assert not (tmp_path / "nope").exists()


def test_parent_symlink_is_not_allowed(tmp_path):
    directory = tmp_path / "actual"
    directory.mkdir()
    link = tmp_path / "redirect"
    link.symlink_to(directory, target_is_directory=True)
    with pytest.raises(RecipeError, match="symlink"):
        create_recipe_workspace("SGN-02", link / "child")
    assert not (directory / "child").exists()


def test_fake_data_access_and_figure_approvals_are_rejected(tmp_path):
    path = create_recipe_workspace("CPS-02", tmp_path / "study")
    state = path / "RECIPE_STATE.json"
    data = json.loads(state.read_text())
    data["data_access"] = "APPROVED"
    data["figure_rendering"] = "ENABLED"
    state.write_text(json.dumps(data))
    result = validate_recipe_workspace(path)
    assert result["status"] == "REFERENCE_WORKSPACE_BLOCKED"
    assert any("provenance" in e for e in result["errors"])


def test_reference_dictionary_tampering_is_rejected(tmp_path):
    path = create_recipe_workspace("TEC-01", tmp_path / "study")
    reference = path / "SECTOR_RECIPE.json"
    data = json.loads(reference.read_text())
    data["source_access_url"] = "https://example.org/not-source"
    reference.write_text(json.dumps(data))
    assert validate_recipe_workspace(path)["status"] == "REFERENCE_WORKSPACE_BLOCKED"


def test_duplicate_variable_roles_and_changed_header_rejected(tmp_path):
    path = create_recipe_workspace("ICI-02", tmp_path / "study")
    mapping = path / "VARIABLE_MAPPING.csv"
    lines = mapping.read_text().splitlines()
    lines[0] = "field_name,variable,unit"
    mapping.write_text("\n".join(lines) + "\n")
    result = validate_recipe_workspace(path)
    assert result["status"] == "REFERENCE_WORKSPACE_BLOCKED"
    assert any("columns" in e for e in result["errors"])


def test_user_mapping_can_be_filled_without_approving_inference(tmp_path):
    path = create_recipe_workspace("SGN-02", tmp_path / "study")
    mapping = path / "VARIABLE_MAPPING.csv"
    with mapping.open(newline="") as file:
        rows = list(csv.DictReader(file))
    rows[0]["source_column"] = "GSE1234"
    with mapping.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = validate_recipe_workspace(path)
    assert result["status"] == "REFERENCE_WORKSPACE_PASS_NO_ANALYSIS"
    assert result["scientific_validation"] == "NOT_ASSESSED"
    assert result["analyses_executed"] is False


def test_cli_lists_and_scaffolds_with_no_private_input(tmp_path, capsys):
    assert main(["sectors", "recipes"]) == 0
    listing = json.loads(capsys.readouterr().out)
    assert len(listing["recipes"]) == 4
    root = tmp_path / "study"
    assert main(["sectors", "scaffold", "--id", "TEC-01", "--out", str(root)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "REFERENCE_WORKSPACE_PASS_NO_ANALYSIS"
    assert main(["sectors", "check-scaffold", "--root", str(root)]) == 0
    assert json.loads(capsys.readouterr().out)["public_release"] == "BLOCKED"


def test_cli_refuses_repeated_starter_and_unlisted_recipe(tmp_path, capsys):
    root = tmp_path / "study"
    assert main(["sectors", "scaffold", "--id", "CPS-02", "--out", str(root)]) == 0
    capsys.readouterr()
    assert main(["sectors", "scaffold", "--id", "CPS-02", "--out", str(root)]) == 2
    assert "never overwrite" in capsys.readouterr().out
    assert main(["sectors", "scaffold", "--id", "SGN-99",
                 "--out", str(tmp_path / "other")]) == 2
    assert not (tmp_path / "other").exists()


def test_sectors_scaffold_does_not_modify_original_catalog(tmp_path):
    from research_template.sector_catalog import read_sector_catalog

    before = read_sector_catalog()
    create_recipe_workspace("SGN-02", tmp_path / "study")
    after = read_sector_catalog()
    assert after == before
