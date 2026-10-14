"""Fail-closed, synthetic-only public cancer-sector discovery tests."""

from __future__ import annotations

import json
from importlib import resources

import pytest

from research_template.cli import main
from research_template.sector_catalog import (
    CatalogError,
    list_sectors,
    plan_sector,
    read_sector_catalog,
)

PROGRAMS = {"CPS", "SGN", "ICI", "TEC"}


def test_four_publicly_sourced_programs_and_14_prestaged_deployables():
    catalog = read_sector_catalog()
    assert {p["id"] for p in catalog["programs"]} == PROGRAMS
    assert len(catalog["deployables"]) == 14
    assert {d["program_id"] for d in catalog["deployables"]} == PROGRAMS
    assert all(p["url"].startswith("https://cancer.dartmouth.edu/")
               for p in catalog["programs"])


def test_each_candidate_has_source_and_method_reference():
    for row in read_sector_catalog()["deployables"]:
        assert row["dictionary_url"].startswith("https://")
        assert row["method_source_url"].startswith("https://")
        assert row["data_access_url"].startswith("https://")
        assert row["analysis_unit"].strip()
        assert row["expected_contract"].strip()
        assert row["candidate_figures"].strip()
        assert row["access_gate"].strip()


def test_no_deployable_is_implicitly_active_or_authorized():
    catalog = read_sector_catalog()
    assert catalog["institutional_approval"] == "NOT_CLAIMED"
    assert catalog["data_download"] == "DISABLED"
    for item in catalog["deployables"]:
        assert item["state"] == "PRESTAGED_METADATA_ONLY"
        assert item["automatic_analysis"] == "DISABLED"
        assert item["user_data_access"] == "NOT_GRANTED"
        assert item["publication"] == "BLOCKED"


def test_cancer_programs_are_distinct_from_patient_datasets():
    groups = list_sectors()
    assert groups["status"] == "DISCOVERY_ONLY"
    assert groups["count"] == 14
    assert groups["analysis_execution"] == "DISABLED"
    assert groups["public_release"] == "BLOCKED"
    assert all("source_name" in d for d in groups["deployables"])


def test_sector_filter_restricts_to_one_official_program():
    result = list_sectors("TEC")
    assert result["count"] == 4
    assert {d["program_id"] for d in result["deployables"]} == {"TEC"}
    assert len(result["research_programs"]) == 1


def test_prestaged_plan_never_loads_data_or_certifies_science():
    result = plan_sector("SGN-02")
    assert result["status"] == "PRESTAGED_REFERENCE_PLAN_ONLY"
    assert result["input_data_loaded"] is False
    assert result["analysis_execution"] == "DISABLED"
    assert result["public_release"] == "BLOCKED"
    assert len(result["mandatory_review"]) >= 5
    assert result["deployable"]["source_name"] == "NCBI Gene Expression Omnibus"


def test_unknown_catalog_ids_block():
    with pytest.raises(CatalogError, match="Unknown"):
        list_sectors("NOT_A_PROGRAM")
    with pytest.raises(CatalogError, match="Unknown"):
        plan_sector("SGN-999")


def test_cli_sector_discovery_and_plan(capsys):
    assert main(["sectors", "list", "--program", "ICI"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["count"] == 3
    assert main(["sectors", "plan", "--id", "TEC-01"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["input_data_loaded"] is False


def test_cli_invalid_sector_blocks_without_download(capsys):
    assert main(["sectors", "plan", "--id", "SGN-404"]) == 2
    response = json.loads(capsys.readouterr().out)
    assert response["status"] == "BLOCKED"


def test_catalog_is_bundled_as_text_metadata_only():
    item = resources.files("research_template").joinpath("sector_catalog.json")
    assert item.is_file()
    document = json.loads(item.read_text(encoding="utf-8"))
    assert document["catalog_id"] == "cancer-program-study-deployables"
    assert "Not affiliated" in document["disclaimer"]
    assert document["scientific_release"] == "BLOCKED"
