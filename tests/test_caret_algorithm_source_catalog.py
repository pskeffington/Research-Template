"""Validate the reference-only caret model method catalog and primary documentation links."""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references" / "CARET_MODEL_METHODS_2026-10-15.csv"
REVISION = "cf7bf44c27c66b88618f8050d3b112df40f48ef1"
EXPECTED = {
    "null", "lm", "glm", "glmnet", "lda", "qda", "rpart", "C5.0", "rf",
    "ranger", "gbm", "xgbTree", "svmRadial", "knn", "pls", "pcr", "nnet",
    "naive_bayes", "earth", "qrf",
}
FIELDS = [
    "id", "method", "family", "name", "task", "implementation_packages",
    "tuning_parameters", "algorithm_mechanics", "biomedical_use_case",
    "preconditions", "limitation", "source_url", "upstream_revision",
    "bibliographic_status", "runtime_test_status",
]


def test_catalog_identity_and_scientific_release_boundaries():
    with CATALOG.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == FIELDS
        rows = list(reader)
    assert len(rows) == 20
    assert {item["method"] for item in rows} == EXPECTED
    assert len({item["id"] for item in rows}) == 20
    for item in rows:
        assert item["task"] in {"classification", "regression", "both"}
        assert all(
            item[key].strip() for key in FIELDS
            if key not in {"implementation_packages", "tuning_parameters"}
        )
        assert item["upstream_revision"] == REVISION
        assert item["source_url"] == (
            f"https://github.com/topepo/caret/blob/{REVISION}/man/models.Rd"
        )
        assert item["bibliographic_status"] == "OFFICIAL_MODEL_MANUAL_CHECKED"
        assert item["runtime_test_status"] == "CATALOG_ONLY_NOT_FITTED"


def test_algorithm_guides_and_tests_are_linked():
    for path in (
        "R/caret_algorithm_catalog.R",
        "R/tests/test_caret_algorithm_catalog.R",
        "docs/CARET_ALGORITHM_CATALOG.md",
        "docs/R_PROGRAMMING_MECHANICS.md",
    ):
        assert (ROOT / path).is_file()
    doc = (ROOT / "docs/CARET_ALGORITHM_CATALOG.md").read_text(encoding="utf-8")
    assert "CARET_MODEL_METHODS_2026-10-15.csv" in doc
    assert "rt_audit_caret_algorithm_catalog" in doc
    assert "external" in doc.lower()
    mechanics = (ROOT / "docs/R_PROGRAMMING_MECHANICS.md").read_text(
        encoding="utf-8"
    )
    for token in ("vapply()", "drop=FALSE", "groupKFold()", "is.na()"):
        assert token in mechanics
