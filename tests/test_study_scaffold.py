"""Public, synthetic-only onboarding and scaffold-safety tests."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from research_template.cli import main
from research_template.study import (
    DATA_DICTIONARY_COLUMNS,
    SOURCE_REGISTER_COLUMNS,
    StudyScaffoldError,
    create_study,
    validate_study,
)


def make_study(path: Path):
    return create_study(
        path, title="Researcher-defined example", objective="descriptive",
        analysis_unit="One observation per survey response",
    )


def test_init_study_creates_blank_reusable_workspace(tmp_path):
    project = make_study(tmp_path / "my-study")
    assert project.is_dir()
    manifest = json.loads((project / "study.json").read_text(encoding="utf-8"))
    assert manifest["title"] == "Researcher-defined example"
    assert manifest["objective"] == "descriptive"
    assert manifest["analysis_unit"] == "One observation per survey response"
    assert manifest["public_release"] == "BLOCKED"
    assert validate_study(project)["scaffold_status"] == "PASS"
    assert not list((project / "data").iterdir())
    assert not list((project / "private").iterdir())
    assert not list((project / "outputs").iterdir())


def test_csv_templates_have_explicit_schema_and_no_data(tmp_path):
    project = make_study(tmp_path / "study")
    for name, columns in (
        ("data_dictionary.csv", DATA_DICTIONARY_COLUMNS),
        ("source_register.csv", SOURCE_REGISTER_COLUMNS),
    ):
        with (project / name).open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        assert rows == [list(columns)]


def test_creation_refuses_existing_directory_without_changes(tmp_path):
    path = tmp_path / "existing"
    path.mkdir()
    sentinel = path / "KEEP.txt"
    sentinel.write_text("original")
    with pytest.raises(StudyScaffoldError, match="already exists"):
        make_study(path)
    assert sentinel.read_text() == "original"
    assert list(path.iterdir()) == [sentinel]


def test_creation_rejects_invalid_objective_without_writing(tmp_path):
    path = tmp_path / "invalid"
    with pytest.raises(StudyScaffoldError, match="Objective"):
        create_study(path, title="Example", objective="unvalidated",
                     analysis_unit="participant")
    assert not path.exists()


def test_reject_control_characters_in_user_supplied_title(tmp_path):
    path = tmp_path / "unsafe"
    with pytest.raises(StudyScaffoldError, match="control"):
        create_study(path, title="Report\nHidden authorization",
                     objective="descriptive", analysis_unit="site")
    assert not path.exists()


def test_preserve_supplied_variable_case(tmp_path):
    path = create_study(tmp_path / "case", title="MiXeD Title",
                        objective="inferential", analysis_unit="Patient_ID")
    manifest = json.loads((path / "study.json").read_text())
    assert manifest["title"] == "MiXeD Title"
    assert manifest["analysis_unit"] == "Patient_ID"


def test_altered_release_flag_is_rejected(tmp_path):
    project = make_study(tmp_path / "study")
    manifest_path = project / "study.json"
    data = json.loads(manifest_path.read_text())
    data["public_release"] = "APPROVED"
    manifest_path.write_text(json.dumps(data))
    report = validate_study(project)
    assert report["scaffold_status"] == "FAIL"
    assert report["public_release"] == "BLOCKED"
    assert any("release" in error for error in report["errors"])


def test_modified_csv_header_is_rejected(tmp_path):
    project = make_study(tmp_path / "study")
    (project / "data_dictionary.csv").write_text("gene,sample,subject\n")
    report = validate_study(project)
    assert report["scaffold_status"] == "FAIL"
    assert any("data_dictionary.csv" in error for error in report["errors"])


def test_missing_or_redirected_metadata_rejected(tmp_path):
    project = make_study(tmp_path / "study")
    (project / "source_register.csv").unlink()
    (project / "source_register.csv").symlink_to(project / "study.json")
    assert validate_study(project)["scaffold_status"] == "FAIL"


def test_missing_workspace_does_not_create_files(tmp_path):
    missing = tmp_path / "missing"
    assert validate_study(missing)["scaffold_status"] == "FAIL"
    assert not missing.exists()


def test_cli_init_and_check_study_roundtrip(tmp_path, capsys):
    output = tmp_path / "research"
    code = main([
        "init-study", "--out", str(output), "--title", "Generic Study",
        "--objective", "predictive", "--analysis-unit", "person-year",
    ])
    assert code == 0
    response = json.loads(capsys.readouterr().out)
    assert response["scaffold_status"] == "PASS"
    assert response["public_release"] == "BLOCKED"
    code = main(["check-study", "--root", str(output)])
    assert code == 0
    assert json.loads(capsys.readouterr().out)["scaffold_status"] == "PASS"


def test_cli_refuses_duplicate_study(tmp_path, capsys):
    output = tmp_path / "research"
    make_study(output)
    exit_code = main([
        "init-study", "--out", str(output), "--title", "Not Overwriting",
        "--objective", "descriptive", "--analysis-unit", "sample",
    ])
    assert exit_code == 2
    assert "already exists" in capsys.readouterr().err
