"""Synthetic, non-clinical cohort generator for demonstrations and tests."""

from __future__ import annotations

import math
import random


def make_cohort(n: int = 120, seed: int = 711) -> list[dict]:
    """Return synthetic independent records with declared units and missingness.

    Numeric distributions and outcome probabilities are arbitrary learning devices.
    They have no clinical interpretation. IDs are fabricated and unique.
    """
    if not isinstance(n, int) or isinstance(n, bool) or n < 40:
        raise ValueError("n must be an integer of at least 40")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be an integer")
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        age = round(rng.uniform(22, 79), 1)
        measurement = round(0.5 + rng.random() * 1.2 + (age - 50) * 0.002, 3)
        # Pseudo-outcome is an intentionally simulated mathematical function.
        z = -1.4 + 0.025 * (age - 45) + 0.95 * (measurement - 1.0)
        prob = 1.0 / (1.0 + math.exp(-z))
        rows.append(
            {
                "participant_id": f"SIM-{i + 1:05d}",
                "site": ("North", "South", "West")[i % 3],
                "age_years": age if i % 29 else None,
                "measurement_mg_dl": measurement if i % 17 else None,
                "outcome": int(rng.random() < prob),
            }
        )
    return rows
