"""Synthetic-only tests for sourced data-dictionary packs and CSV admission."""

from __future__ import annotations

import csv
import json

import pytest

from research_template.cli import main
from research_template.study_packs import PackError, list_packs, load_pack, plan_pack, validate_csv

PACK = "nhanes-2017-2018"


def make_csv(folder, table, rows):
    path = folder / f"{table}.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def demo_row():
    return {
        "SEQN": "90001", "RIDAGEYR": "55", "RIAGENDR": "2",
        "SDMVPSU": "1", "SDMVSTRA": "100", "WTINT2YR": "330.5",
        "WTMEC2YR": "300.2",
    }


def test_registry_has_source_urls_without_auto_download():
    packs = list_packs()
    assert [x["pack_id"] for x in packs] == [PACK]
    pack = load_pack(PACK)
    assert pack["status"] == "SCHEMA_VALIDATION_PILOT"
    assert pack["data_download"] == "DISABLED"
    assert set(pack["tables"]) == {"DEMO_J", "ALB_CR_J", "KIQ_U_J"}
    assert all(x["source_url"].startswith("https://wwwn.cdc.gov/")
               for x in pack["tables"].values())


def test_source_dictionary_retains_codes_units_and_weight_guard():
    pack = load_pack(PACK)
    demo = pack["tables"]["DEMO_J"]["columns"]
    assert demo["WTMEC2YR"]["role"] == "examination_weight"
    assert demo["SDMVPSU"]["role"] == "survey_psu"
    laboratory = pack["tables"]["ALB_CR_J"]["columns"]
    assert laboratory["URXUMA"]["unit"] == "ug/mL"
    assert laboratory["URDACT"]["unit"] == "mg/g"
    questionnaire = pack["tables"]["KIQ_U_J"]["columns"]["KIQ022"]
    assert questionnaire["special_codes"] == {"7": "Refused", "9": "Don't know"}
    assert pack["survey_design"]["required_review"] is True


def test_review_only_join_plan_not_claiming_inference():
    plan = plan_pack(PACK)
    assert plan["status"] == "REFERENCE_PLAN_ONLY"
    assert plan["join_plan"]["join_key"] == "SEQN"
    assert plan["join_plan"]["status"] == "PLAN_ONLY_NOT_EXECUTED"
    assert plan["weighted_inference"] == "NOT_AUTHORIZED"
    assert plan["public_release"] == "BLOCKED"


def test_synthetic_demographics_pass_and_no_write(tmp_path):
    rows = [demo_row(), dict(demo_row(), SEQN="90002", RIDAGEYR=".")]
    path = make_csv(tmp_path, "DEMO_J", rows)
    original = path.read_bytes()
    result = validate_csv(PACK, "DEMO_J", path)
    assert result["status"] == "STRUCTURE_PASS_ANALYSIS_REVIEW_REQUIRED"
    assert result["row_count"] == 2
    assert result["missing_counts"]["RIDAGEYR"] == 1
    assert result["raw_rows_exported"] is False
    assert result["public_release"] == "BLOCKED"
    assert path.read_bytes() == original
    assert "90001" not in json.dumps(result)


def test_duplicated_join_key_blocks(tmp_path):
    path = make_csv(tmp_path, "DEMO_J", [demo_row(), demo_row()])
    report = validate_csv(PACK, "DEMO_J", path)
    assert report["status"] == "STRUCTURE_BLOCKED"
    assert any("duplicate join key" in x for x in report["errors"])


def test_bad_coded_value_blocks(tmp_path):
    path = make_csv(tmp_path, "DEMO_J", [dict(demo_row(), RIAGENDR="8")])
    report = validate_csv(PACK, "DEMO_J", path)
    assert report["status"] == "STRUCTURE_BLOCKED"
    assert any("RIAGENDR" in x for x in report["errors"])


def test_questionnaire_special_nonresponse_codes_are_flagged_not_reclassified(tmp_path):
    path = make_csv(tmp_path, "KIQ_U_J", [
        {"SEQN": "90001", "KIQ022": "7"},
        {"SEQN": "90002", "KIQ022": "9"},
    ])
    report = validate_csv(PACK, "KIQ_U_J", path)
    assert report["status"] == "STRUCTURE_PASS_ANALYSIS_REVIEW_REQUIRED"
    assert report["special_code_counts"]["KIQ022"] == 2
    assert report["missing_counts"]["KIQ022"] == 0


def test_lab_study_variables_and_units(tmp_path):
    path = make_csv(tmp_path, "ALB_CR_J", [
        {"SEQN": "90001", "URXUMA": "12.5", "URXUCR": "70",
         "URDACT": "17.9"}
    ])
    assert validate_csv(PACK, "ALB_CR_J", path)["status"] == (
        "STRUCTURE_PASS_ANALYSIS_REVIEW_REQUIRED"
    )


def test_missing_required_field_blocks(tmp_path):
    row = demo_row()
    row.pop("WTMEC2YR")
    path = make_csv(tmp_path, "DEMO_J", [row])
    report = validate_csv(PACK, "DEMO_J", path)
    assert report["status"] == "STRUCTURE_BLOCKED"
    assert report["missing_columns"] == ["WTMEC2YR"]


def test_wrong_study_cycle_filename_blocks(tmp_path):
    path = make_csv(tmp_path, "DEMO_J", [demo_row()])
    wrong = tmp_path / "P_DEMO.csv"
    path.rename(wrong)
    with pytest.raises(PackError, match="Wrong filename/cycle"):
        validate_csv(PACK, "DEMO_J", wrong)


def test_missing_or_redirected_csv_blocks(tmp_path):
    external = tmp_path / "external.csv"
    external.write_text("SEQN\n90001\n")
    linked = tmp_path / "DEMO_J.csv"
    linked.symlink_to(external)
    with pytest.raises(PackError, match="symlink"):
        validate_csv(PACK, "DEMO_J", linked)


def test_invalid_pack_id_rejected_without_path_traversal():
    with pytest.raises(PackError, match="Invalid"):
        load_pack("../nhanes")
    with pytest.raises(PackError, match="Unknown"):
        load_pack("unavailable-dataset")


def test_cli_pack_listing_and_validation(tmp_path, capsys):
    assert main(["pack", "list"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["pack_id"] == PACK
    assert main(["pack", "plan", "--id", PACK]) == 0
    assert json.loads(capsys.readouterr().out)["weighted_inference"] == "NOT_AUTHORIZED"
    path = make_csv(tmp_path, "DEMO_J", [demo_row()])
    assert main([
        "pack", "validate", "--id", PACK, "--table", "DEMO_J", "--csv", str(path)
    ]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "STRUCTURE_PASS_ANALYSIS_REVIEW_REQUIRED"
    assert output["analysis_approved"] is False


def test_cli_invalid_csv_fails_closed(tmp_path, capsys):
    path = make_csv(tmp_path, "DEMO_J", [dict(demo_row(), RIDAGEYR="x")])
    assert main([
        "pack", "validate", "--id", PACK, "--table", "DEMO_J", "--csv", str(path)
    ]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "STRUCTURE_BLOCKED"
