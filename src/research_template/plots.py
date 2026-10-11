"""One-call, standards-oriented plots. Matplotlib is an optional extra."""

from __future__ import annotations

import math

# Okabe-Ito is a widely used color-vision-accessible categorical palette.
OKABE_ITO = ("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000", "#F0E442")


def axis_label(name: str, unit: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Explicit nonempty variable label required")
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("Explicit unit required; use 'unitless' if appropriate")
    return f"{name} ({unit})"


def _plotter():
    import matplotlib.pyplot as plt
    return plt


def _finite_pairs(rows: list[dict], x: str, y: str) -> tuple[list[float], list[float]]:
    pairs = [(r.get(x), r.get(y)) for r in rows]
    clean = [
        (float(a), float(b)) for a, b in pairs
        if isinstance(a, (float, int)) and not isinstance(a, bool)
        and isinstance(b, (float, int)) and not isinstance(b, bool)
        and math.isfinite(a) and math.isfinite(b)
    ]
    if not clean:
        raise ValueError("No finite complete x/y pairs to plot")
    return [a for a, _ in clean], [b for _, b in clean]


def histogram(rows: list[dict], value: str, *, name: str, unit: str, bins: int = 12):
    """Distribution of measured values with denominator and missing count."""
    if not isinstance(bins, int) or bins < 2:
        raise ValueError("bins must be an integer >=2")
    numeric = [
        float(r[value]) for r in rows if r.get(value) is not None
        and isinstance(r[value], (int, float)) and not isinstance(r[value], bool)
        and math.isfinite(r[value])
    ]
    if not numeric:
        raise ValueError("No finite observed measurements")
    plt = _plotter()
    fig, ax = plt.subplots(figsize=(7, 5), constrained_layout=True)
    ax.hist(numeric, bins=bins, color=OKABE_ITO[0], edgecolor="white")
    ax.set(title=f"{name} distribution", xlabel=axis_label(name, unit), ylabel="Observations (count)")
    fig.text(0.01, 0.01, f"Measured n={len(numeric)}/{len(rows)}; excluded={len(rows)-len(numeric)}; descriptive only", fontsize=8)
    return fig


def scatter(rows: list[dict], x: str, y: str, *, x_name: str, x_unit: str, y_name: str, y_unit: str):
    """Scatter with explicit complete-pair n; does not assume causal association."""
    xs, ys = _finite_pairs(rows, x, y)
    plt = _plotter()
    fig, ax = plt.subplots(figsize=(7, 5), constrained_layout=True)
    ax.scatter(xs, ys, color=OKABE_ITO[0], alpha=0.72, edgecolors="white")
    ax.set(title=f"{y_name} versus {x_name}", xlabel=axis_label(x_name, x_unit), ylabel=axis_label(y_name, y_unit))
    fig.text(0.01, 0.01, f"Complete pairs n={len(xs)}/{len(rows)}; descriptive association; not causal", fontsize=8)
    return fig


def group_box(rows: list[dict], value: str, group: str, *, name: str, unit: str):
    """Group boxplots, preserving category order and explicitly omitting missing values."""
    groups = sorted({str(r[group]) for r in rows if r.get(group) is not None})
    if not 1 < len(groups) <= len(OKABE_ITO):
        raise ValueError("Require between 2 and 8 groups; facet larger comparisons")
    values = [
        [float(r[value]) for r in rows if str(r.get(group)) == g
         and isinstance(r.get(value), (int, float)) and not isinstance(r.get(value), bool)
         and math.isfinite(r[value])] for g in groups
    ]
    if any(len(v) < 2 for v in values):
        raise ValueError("Each group needs >=2 finite observations")
    plt = _plotter()
    fig, ax = plt.subplots(figsize=(7, 5), constrained_layout=True)
    boxes = ax.boxplot(values, labels=groups, patch_artist=True, showfliers=True)
    for patch, color in zip(boxes["boxes"], OKABE_ITO):
        patch.set_facecolor(color)
        patch.set_alpha(0.8)
    ax.set(title=f"{name} by {group}", xlabel=f"{group} (category)", ylabel=axis_label(name, unit))
    fig.text(0.01, 0.01, "Measured by group: " + ", ".join(f"{g}={len(v)}" for g, v in zip(groups, values)), fontsize=8)
    return fig


def heatmap(matrix, *, row_labels: list[str], col_labels: list[str], name: str, unit: str, mode: str = "sequential"):
    """Heatmap uses viridis for magnitude or centered RdBu_r for signed deviation."""
    import numpy as np
    a = np.asarray(matrix, dtype=float)
    if a.ndim != 2 or a.shape != (len(row_labels), len(col_labels)) or not np.isfinite(a).all():
        raise ValueError("2D finite matrix and matching row/column labels required")
    if mode not in {"sequential", "diverging"}:
        raise ValueError("mode must be sequential or diverging")
    plt = _plotter()
    fig, ax = plt.subplots(figsize=(max(7, len(col_labels) * 0.45), 5), constrained_layout=True)
    vmax = float(np.max(np.abs(a))) if mode == "diverging" else None
    image = ax.imshow(a, aspect="auto", cmap="RdBu_r" if mode == "diverging" else "viridis",
                      vmin=-vmax if mode == "diverging" else None, vmax=vmax)
    ax.set(xticks=range(len(col_labels)), yticks=range(len(row_labels)),
           xticklabels=col_labels, yticklabels=row_labels, title=name,
           xlabel="Sample (identifier)", ylabel="Feature (identifier)")
    ax.tick_params(axis="x", labelrotation=90)
    fig.colorbar(image, ax=ax, label=axis_label(name, unit))
    return fig


def save_figure(fig, path, *, dpi: int = 300):
    """Save high-resolution raster or vector PDF; call only on approved outputs."""
    from pathlib import Path
    path = Path(path)
    if path.suffix.lower() not in {".png", ".pdf", ".svg"}:
        raise ValueError("Figure suffix must be png, pdf or svg")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    return path
