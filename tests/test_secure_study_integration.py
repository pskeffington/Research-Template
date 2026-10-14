"""Security-aware end-to-end contracts for generic study and opt-in packs."""

from __future__ import annotations

import json
from pathlib import Path

from research_template.cli import main


def test_security_banner_precedes_study_features():
    text = (Path(__file__).resolve().parents[1] / "README.md").read_text()
    assert text.index("## Research data access and security") < text.index("## Start a new study")
    assert text.index("## Research data access and security") < text.index("## Publicly documented cancer")
    assert "docs/DATA_ACCESS_AND_SECURITY.md" in text


def test_blank_study_and_pack_plan_do_not_grant_access(tmp_path, capsys):
    study = tmp_path / "blank-study"
    assert main([
        "init-study", "--out", str(study), "--title", "Synthetic setup only",
        "--objective", "descriptive", "--analysis-unit", "one participant-year",
    ]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["scientific_validation"] == "NOT_ASSESSED"
    assert result["data_access"] == "NOT_ASSESSED"
    assert result["public_release"] == "BLOCKED"
    assert main(["pack", "plan", "--id", "nhanes-2017-2018"]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["weighted_inference"] == "NOT_AUTHORIZED"
    assert plan["data_ingestion"] == "USER_CONTROLLED_NOT_EXECUTED"
    assert all(not any((study / folder).iterdir()) for folder in ("data", "outputs", "private"))
    assert main(["sectors", "plan", "--id", "SGN-02"]) == 0
    reference = json.loads(capsys.readouterr().out)
    assert reference["analysis_execution"] == "DISABLED"
    assert reference["input_data_loaded"] is False
    assert reference["public_release"] == "BLOCKED"


def test_new_study_explains_security_and_release_gate(tmp_path):
    study = tmp_path / "blank"
    assert main([
        "init-study", "--out", str(study), "--title", "Independent analysis",
        "--objective", "inferential", "--analysis-unit", "sample",
    ]) == 0
    readme = (study / "README.md").read_text()
    protocol = (study / "PROTOCOL.md").read_text()
    assert "approved protected storage" in readme
    assert "Data-source permissions independently reviewed" in protocol
    assert "Privacy and publication approvals recorded" in protocol


def test_local_csv_review_requires_explicit_security_acknowledgement(tmp_path, capsys):
    filename = tmp_path / "DEMO_J.csv"
    filename.write_text("SEQN\n90001\n", encoding="utf-8")
    assert main([
        "pack", "validate", "--id", "nhanes-2017-2018",
        "--table", "DEMO_J", "--csv", str(filename),
    ]) == 2
    blocked = json.loads(capsys.readouterr().out)
    assert blocked["status"] == "BLOCKED"
    assert "confirm-authorized-local-use" in blocked["reason"]
    # No raw data or participant values were emitted.
    assert "90001" not in json.dumps(blocked)
