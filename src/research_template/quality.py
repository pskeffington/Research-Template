"""Data contract validation with explicit missingness and identity checks."""

from __future__ import annotations

import math
from collections import Counter

REQUIRED_COLUMNS = (
    "participant_id",
    "site",
    "age_years",
    "measurement_mg_dl",
    "outcome",
)


class DataContractError(ValueError):
    """The input violates the declared schema or unit contract."""


def validate_cohort(rows: list[dict]) -> dict:
    """Check the synthetic example schema without silently coercing types.

    Replace or extend the contract when introducing real permitted data.
    Never infer measurement units or convert missing values to zero.
    """
    if not isinstance(rows, list) or not rows:
        raise DataContractError("Expected a non-empty list of observations")
    seen: set[str] = set()
    missing = Counter()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise DataContractError(f"Row {index}: expected mapping")
        absent = set(REQUIRED_COLUMNS) - row.keys()
        if absent:
            raise DataContractError(f"Row {index}: missing fields {sorted(absent)}")
        pid = row["participant_id"]
        if not isinstance(pid, str) or not pid.strip():
            raise DataContractError(f"Row {index}: participant_id required")
        if pid in seen:
            raise DataContractError(f"Row {index}: duplicate participant_id")
        seen.add(pid)
        if not isinstance(row["site"], str) or not row["site"].strip():
            raise DataContractError(f"Row {index}: nonempty site required")
        for key in ("age_years", "measurement_mg_dl"):
            value = row[key]
            if value is None:
                missing[key] += 1
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise DataContractError(f"Row {index}: {key} must be finite numeric or null")
            if value < 0:
                raise DataContractError(f"Row {index}: {key} cannot be negative")
        if type(row["outcome"]) is not int or row["outcome"] not in (0, 1):
            raise DataContractError(f"Row {index}: outcome must be exactly 0 or 1")
    return {
        "n_rows": len(rows),
        "n_participants": len(seen),
        "outcome_counts": dict(Counter(row["outcome"] for row in rows)),
        "missing_counts": {key: missing[key] for key in ("age_years", "measurement_mg_dl")},
        "units": {"age_years": "years", "measurement_mg_dl": "mg/dL"},
        "data_classification": "synthetic",
    }
