"""Contract tests for the discovery-only biomedical AI literature register."""

import csv
from pathlib import Path
from urllib.parse import urlparse

CORPUS = Path(__file__).resolve().parents[1] / "references" / (
    "BIOMEDICAL_AI_RAG_LITERATURE_2026-10-14.csv"
)
REQUIRED = {
    "id", "year", "domain", "evidence_type", "citation_short", "title",
    "doi", "publication_url", "upstream_code_url", "code_link_status",
    "rights_review", "method_to_extract", "independent_validation_gate",
    "key_limitation", "bibliography_status", "local_execution_status",
    "reviewed_utc",
}


def test_corpus_metadata_and_stable_identifiers():
    with CORPUS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        assert set(reader.fieldnames) == REQUIRED
        rows = list(reader)
    assert len(rows) >= 27
    assert len({row["id"] for row in rows}) == len(rows)
    assert len({row["doi"].lower() for row in rows}) == len(rows)
    for row in rows:
        assert all(row[field].strip() for field in REQUIRED - {"upstream_code_url"})
        assert row["publication_url"] == f"https://doi.org/{row['doi']}"
        assert urlparse(row["publication_url"]).netloc == "doi.org"
        assert 2000 <= int(row["year"]) <= 2026
        assert row["rights_review"] == "REVIEW_PENDING"
        assert row["local_execution_status"] == "NOT_EXECUTED"
        assert row["bibliography_status"] in {
            "PUBLISHER_RECORD_VERIFIED", "CANDIDATE_LINK_UNVERIFIED",
        }
        if row["upstream_code_url"]:
            url = urlparse(row["upstream_code_url"])
            assert url.scheme == "https"
            assert url.netloc == "github.com"


def test_reproduction_must_not_be_claimed_from_bibliography():
    with CORPUS.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert all(row["local_execution_status"] == "NOT_EXECUTED" for row in rows)
    assert all(row["rights_review"] == "REVIEW_PENDING" for row in rows)
