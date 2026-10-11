"""Standard-library descriptive summaries with explicit denominators and exclusions.

These are unweighted, descriptive calculations for independent rows. They are
not substitutes for survey-weighted, clustered, longitudinal or assay analyses.
"""

from __future__ import annotations

import math
import statistics
from collections import Counter


def _numeric(rows: list[dict], column: str) -> tuple[list[float], int]:
    if not rows or any(column not in row for row in rows):
        raise ValueError(f"Nonempty records with '{column}' are required")
    values: list[float] = []
    for index, row in enumerate(rows):
        value = row[column]
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (float, int)):
            raise ValueError(f"{column}: nonnumeric at row {index}; only None denotes missing")
        if not math.isfinite(value):
            raise ValueError(f"{column}: nonfinite number at row {index}; normalize source missing codes")
        values.append(float(value))
    return values, len(rows) - len(values)


def _percentile(sorted_values: list[float], proportion: float) -> float:
    """Linear interpolation at rank (n-1)*p (NumPy's usual linear method)."""
    pos = (len(sorted_values) - 1) * proportion
    low = math.floor(pos)
    high = math.ceil(pos)
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * (pos - low)


def numeric_summary(rows: list[dict], column: str, *, unit: str) -> dict:
    """Return n, missing, mean, sample SD, median, quartiles, IQR and range.

    One observation is one row. SD uses n-1; SD is null when n<2.
    """
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("Explicit unit required; use 'unitless' where appropriate")
    values, missing = _numeric(rows, column)
    if not values:
        raise ValueError(f"{column}: no measured observations")
    ordered = sorted(values)
    q1, q3 = _percentile(ordered, 0.25), _percentile(ordered, 0.75)
    return {
        "variable": column,
        "unit": unit,
        "n_total": len(rows),
        "n_measured": len(values),
        "n_missing": missing,
        "percent_missing": 100 * missing / len(rows),
        "mean": statistics.mean(values),
        "sd": statistics.stdev(values) if len(values) > 1 else None,
        "median": statistics.median(values),
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
        "minimum": ordered[0],
        "maximum": ordered[-1],
        "denominator_note": "Unweighted row-level descriptive summary; sample SD uses n-1.",
    }


def category_summary(rows: list[dict], column: str, *, levels: tuple[str, ...] | None = None) -> dict:
    """Preserve declared category order; include missing and zero-count categories."""
    if not rows or any(column not in row for row in rows):
        raise ValueError(f"Nonempty records with '{column}' are required")
    counts: Counter[str] = Counter()
    missing = 0
    for row in rows:
        value = row[column]
        if value is None:
            missing += 1
        elif not isinstance(value, str) or not value.strip():
            raise ValueError(f"{column}: categorical values must be nonempty strings or None")
        else:
            counts[value] += 1
    if levels is None:
        levels = tuple(sorted(counts))
    if not levels or len(set(levels)) != len(levels) or set(counts) - set(levels):
        raise ValueError("levels must uniquely cover the observed nonmissing categories")
    return {
        "variable": column,
        "n_total": len(rows),
        "n_missing": missing,
        "categories": [
            {"category": cat, "n": counts[cat], "percent_of_total": 100 * counts[cat] / len(rows)}
            for cat in levels
        ],
    }


def grouped_numeric_summary(
    rows: list[dict], value: str, group: str, *, unit: str, levels: tuple[str, ...] | None = None
) -> dict:
    """Compute descriptive summaries for each category and count omitted group labels."""
    categories = category_summary(rows, group, levels=levels)
    stats = []
    for category in categories["categories"]:
        subset = [r for r in rows if r[group] == category["category"]]
        stats.append({
            "group": category["category"],
            "n_group_total": len(subset),
            "numeric": numeric_summary(subset, value, unit=unit) if subset else None,
        })
    return {
        "variable": value,
        "group": group,
        "unit": unit,
        "n_total": len(rows),
        "n_missing_group": categories["n_missing"],
        "groups": stats,
    }


def complete_pair_summary(rows: list[dict], x: str, y: str) -> dict:
    """Number of rows where *both* numeric measurements are observed."""
    if x == y:
        raise ValueError("Select two distinct variables")
    vx, _ = _numeric(rows, x)
    vy, _ = _numeric(rows, y)
    complete = sum(row[x] is not None and row[y] is not None for row in rows)
    return {
        "x": x,
        "y": y,
        "n_total": len(rows),
        "n_complete_pairs": complete,
        "n_excluded": len(rows) - complete,
        "n_x_measured": len(vx),
        "n_y_measured": len(vy),
    }
