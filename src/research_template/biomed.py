"""Schema-driven biomedical figures with complete default captions and metadata.

Author: Paul Skeffington. Prepared with OpenAI.
No plot module imports Matplotlib or NumPy until explicitly called.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .provenance import sha256_file
from .summary import (
    _numeric,
    category_summary,
    complete_pair_summary,
    grouped_numeric_summary,
    numeric_summary,
)

# Accessibility-oriented categories. The yellow is deliberately last: on a
# white canvas it needs secondary encodings such as shape, position and labels.
OKABE_ITO = (
    "#0072B2", "#D55E00", "#009E73", "#CC79A7",
    "#E69F00", "#56B4E9", "#000000", "#F0E442",
)
NEUTRAL_MISSING = "#CED4DC"
SEQUENTIAL = "viridis"
DIVERGING = "RdBu_r"


@dataclass(frozen=True)
class Variable:
    """Declared column contract; unit is required even if it is 'unitless'."""

    label: str
    unit: str
    kind: str = "numeric"
    levels: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.label.strip() or not self.unit.strip():
            raise ValueError("Variable label and unit are mandatory")
        if self.kind not in {"numeric", "categorical"}:
            raise ValueError("Variable.kind must be numeric or categorical")
        if self.kind == "categorical" and self.unit != "category":
            raise ValueError("Categorical variables must declare unit='category'")
        if self.kind == "numeric" and self.levels:
            raise ValueError("Only categorical variables may declare levels")
        if len(set(self.levels)) != len(self.levels) or any(not x.strip() for x in self.levels):
            raise ValueError("Unique nonempty category levels required")


@dataclass(frozen=True)
class Study:
    """Human-readable study context stamped onto every figure."""

    title: str
    observation_unit: str
    source: str
    status: str = "SYNTHETIC / DESCRIPTIVE ONLY"

    def __post_init__(self):
        if any(not isinstance(s, str) or not s.strip() for s in asdict(self).values()):
            raise ValueError("Study requires title, observation unit, source and status")


class FigureKit:
    """One-call figures from a declared dictionary; no missing labels or units."""

    def __init__(self, rows: list[dict], *, variables: dict[str, Variable], study: Study):
        if not isinstance(study, Study) or not variables:
            raise ValueError("Study and variable dictionary required")
        if not rows or any(not isinstance(r, dict) for r in rows):
            raise ValueError("Nonempty list of observation records required")
        for key, spec in variables.items():
            if not isinstance(spec, Variable) or any(key not in r for r in rows):
                raise ValueError(f"Column '{key}' missing or lacks valid specification")
            if spec.kind == "numeric":
                _numeric(rows, key)
            else:
                category_summary(rows, key, levels=spec.levels or None)
        self.rows = rows
        self.variables = variables
        self.study = study

    def _variable(self, key: str, kind: str) -> Variable:
        if key not in self.variables or self.variables[key].kind != kind:
            raise ValueError(f"Declare '{key}' as {kind} in the study dictionary")
        return self.variables[key]

    def _levels(self, key: str) -> tuple[str, ...]:
        spec = self._variable(key, "categorical")
        levels = spec.levels or tuple(sorted({r[key] for r in self.rows if r[key] is not None}))
        if not 2 <= len(levels) <= len(OKABE_ITO):
            raise ValueError("2–8 declared categories needed; facet or redesign larger comparisons")
        return levels

    @staticmethod
    def _mpl():
        import matplotlib.pyplot as plt
        return plt

    def _canvas(self, *, wide: bool = False):
        plt = self._mpl()
        with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 10,
                             "axes.spines.top": False, "axes.spines.right": False,
                             "axes.titleweight": "bold", "savefig.facecolor": "white"}):
            fig, ax = plt.subplots(figsize=(9.4, 5.8) if wide else (8.0, 5.4))
        fig.subplots_adjust(left=0.12, right=0.88 if wide else 0.94, top=0.72, bottom=0.24)
        ax.grid(axis="y", color="#DEE2E6", alpha=0.6, linewidth=0.65)
        ax.set_axisbelow(True)
        return fig, ax

    def _finish(self, fig, ax, *, kind: str, title: str, subtitle: str, caption: str,
                n_used: int, variables: tuple[str, ...], excluded: int):
        if not 0 <= n_used <= len(self.rows):
            raise ValueError("Invalid denominator")
        ax.set_title("")
        fig.text(0.12, 0.91, title, fontsize=14, weight="bold", color="#14233B")
        fig.text(0.12, 0.855, f"{self.study.title} | {subtitle}", fontsize=10, color="#3D4D60")
        fig.text(0.12, 0.80, f"Unit: {self.study.observation_unit}  |  "
                 f"Included n={n_used}/{len(self.rows)}  |  Excluded n={excluded}", fontsize=9, color="#3D4D60")
        fig.text(0.12, 0.095, caption, fontsize=8.5, color="#35445B", wrap=True)
        fig.text(0.12, 0.045, f"Source: {self.study.source}   •   {self.study.status}",
                 fontsize=8, color="#5B6374")
        fig._research_meta = {
            "kind": kind,
            "title": title,
            "subtitle": subtitle,
            "caption": caption,
            "study": asdict(self.study),
            "variables": {v: asdict(self.variables[v]) for v in variables},
            "n_total": len(self.rows),
            "n_used": n_used,
            "n_excluded": excluded,
            "palette": {"categorical": "Okabe–Ito", "sequential": SEQUENTIAL,
                        "diverging": DIVERGING, "missing": NEUTRAL_MISSING},
            "release": "NOT SCIENTIFICALLY APPROVED BY AUTOMATED PLOTTING",
        }
        return fig

    @staticmethod
    def _label(spec: Variable) -> str:
        return f"{spec.label} ({spec.unit})"

    def summary(self, value: str, *, group: str | None = None) -> dict:
        spec = self._variable(value, "numeric")
        if group is None:
            return numeric_summary(self.rows, value, unit=spec.unit)
        return grouped_numeric_summary(
            self.rows, value, group, unit=spec.unit, levels=self._levels(group)
        )

    def histogram(self, value: str, *, bins: int = 12):
        if type(bins) is not int or bins < 2:
            raise ValueError("bins must be an integer >=2")
        spec = self._variable(value, "numeric")
        obs, _ = _numeric(self.rows, value)
        if not obs:
            raise ValueError("No measurements")
        stats = self.summary(value)
        fig, ax = self._canvas()
        ax.hist(obs, bins=bins, color=OKABE_ITO[0], edgecolor="white", linewidth=0.8)
        ax.axvline(stats["median"], color=OKABE_ITO[1], linewidth=1.7,
                   linestyle="--", label=f"Median {stats['median']:.2f} {spec.unit}")
        ax.legend(frameon=False, loc="upper right")
        ax.set(xlabel=self._label(spec), ylabel="Observations (count)")
        return self._finish(
            fig, ax, kind="histogram", title=f"{spec.label} | distribution",
            subtitle=f"Mean {stats['mean']:.2f} • SD {stats['sd']:.2f}" if stats["sd"] is not None else
                     f"Mean {stats['mean']:.2f} • SD undefined (n<2)",
            caption="Histogram binning is descriptive; median shown as dashed line. Missing values excluded.",
            n_used=len(obs), excluded=len(self.rows)-len(obs), variables=(value,),
        )

    def scatter(self, x: str, y: str, *, group: str | None = None):
        xs = self._variable(x, "numeric")
        ys = self._variable(y, "numeric")
        counts = complete_pair_summary(self.rows, x, y)
        if not counts["n_complete_pairs"]:
            raise ValueError("No complete pairs")
        fig, ax = self._canvas()
        if group is None:
            points = [r for r in self.rows if r[x] is not None and r[y] is not None]
            ax.scatter([r[x] for r in points], [r[y] for r in points],
                       c=OKABE_ITO[0], alpha=0.78, edgecolors="white", linewidths=0.4)
        else:
            levels = self._levels(group)
            markers = ("o", "s", "^", "D", "P", "X", "v", "h")
            for i, level in enumerate(levels):
                points = [r for r in self.rows if r[x] is not None and
                          r[y] is not None and r[group] == level]
                ax.scatter([r[x] for r in points], [r[y] for r in points],
                           c=OKABE_ITO[i], marker=markers[i], alpha=0.8, s=38,
                           edgecolors="#303030", linewidths=0.35,
                           label=f"{level} (n={len(points)})")
            ax.legend(loc="best", fontsize=8, frameon=False)
        ax.set(xlabel=self._label(xs), ylabel=self._label(ys))
        return self._finish(
            fig, ax, kind="scatter", title=f"{ys.label} versus {xs.label}",
            subtitle="Complete-pair, unweighted descriptive association",
            caption="No regression, confidence band or causal inference is implied."
                    + (" Records with missing group are excluded." if group else ""),
            n_used=counts["n_complete_pairs"] if not group else
                   sum(r[x] is not None and r[y] is not None and r[group] is not None for r in self.rows),
            excluded=counts["n_excluded"] if not group else
                     sum(r[x] is None or r[y] is None or r[group] is None for r in self.rows),
            variables=(x, y) if group is None else (x, y, group),
        )

    def box(self, value: str, *, group: str, violin: bool = False):
        spec = self._variable(value, "numeric")
        levels = self._levels(group)
        values = [[r[value] for r in self.rows if r[group] == level and r[value] is not None]
                  for level in levels]
        if any(len(v) < 2 for v in values):
            raise ValueError("Each displayed group needs >=2 observed measurements")
        fig, ax = self._canvas()
        if violin:
            parts = ax.violinplot(values, positions=range(1, len(levels)+1),
                                  showmeans=False, showmedians=True, showextrema=False)
            for patch, color in zip(parts["bodies"], OKABE_ITO, strict=False):
                patch.set_facecolor(color)
                patch.set_edgecolor("#2E3A44")
                patch.set_alpha(0.63)
            parts["cmedians"].set_color("#111827")
        else:
            boxes = ax.boxplot(values, patch_artist=True, showfliers=True,
                               medianprops={"color": "#151A23", "linewidth": 1.7})
            for patch, color in zip(boxes["boxes"], OKABE_ITO, strict=False):
                patch.set_facecolor(color)
                patch.set_alpha(0.75)
        ax.set_xticks(list(range(1, len(levels)+1)), levels)
        ax.set(xlabel=self.variables[group].label + " (category)", ylabel=self._label(spec))
        n_used = sum(map(len, values))
        return self._finish(
            fig, ax, kind="violin" if violin else "box",
            title=f"{spec.label} by {self.variables[group].label}",
            subtitle="Measured per group: " + "; ".join(
                f"{level} n={len(v)}" for level, v in zip(levels, values, strict=False)
            ),
            caption="Violin width reflects smoothed sample distribution; assess with small n."
                    if violin else "Boxes show quartiles and median; whiskers are not confidence intervals.",
            n_used=n_used, excluded=len(self.rows)-n_used, variables=(value, group),
        )

    def category_bar(self, group: str):
        levels = self._levels(group)
        stats = category_summary(self.rows, group, levels=levels)
        counts = [r["n"] for r in stats["categories"]]
        fig, ax = self._canvas()
        ax.bar(levels, counts, color=OKABE_ITO[:len(levels)], edgecolor="#313E4A", linewidth=0.6)
        for i, n in enumerate(counts):
            ax.annotate(f"{n}", (i, n), ha="center", va="bottom", xytext=(0, 4),
                        textcoords="offset points", fontsize=9)
        ax.set(xlabel=self.variables[group].label + " (category)", ylabel="Records (count)")
        ax.set_ylim(bottom=0, top=max(counts) * 1.19 if max(counts) else 1)
        return self._finish(
            fig, ax, kind="category_bar",
            title=f"{self.variables[group].label} | category counts",
            subtitle="Denominator: all records; categories retain declared order",
            caption="Missing group records are excluded from bars and disclosed in the denominator.",
            n_used=len(self.rows)-stats["n_missing"], excluded=stats["n_missing"],
            variables=(group,),
        )

    def missingness(self, *columns: str):
        """Compact variable-level missingness heatmap: percent missing, not observations."""
        import numpy as np

        selected = columns or tuple(self.variables)
        if any(c not in self.variables for c in selected) or not selected:
            raise ValueError("Select documented variable names")
        values = [
            100 * sum(r[c] is None for r in self.rows) / len(self.rows) for c in selected
        ]
        fig, ax = self._canvas(wide=True)
        matrix = np.asarray([values], dtype=float)
        image = ax.imshow(matrix, cmap=SEQUENTIAL, vmin=0, vmax=100, aspect="auto")
        ax.grid(False)
        ax.set_xticks(range(len(selected)), [self.variables[c].label for c in selected],
                      rotation=45, ha="right")
        ax.set_yticks([0], ["Missing %"])
        for idx, value in enumerate(values):
            ax.text(idx, 0, f"{value:.1f}%", color="#202A36" if value > 65 else "white",
                    weight="bold", ha="center", va="center", fontsize=9)
        fig.colorbar(image, ax=ax, label="Missing observations (%)", fraction=0.035, pad=0.03)
        return self._finish(
            fig, ax, kind="missingness", title="Missingness | selected variables",
            subtitle="Column-level percentage of omitted/null records",
            caption="Zero means no missing values, not zero measurement. Any source-specific"
                    " missing codes must be normalized explicitly before plotting.",
            n_used=len(self.rows), excluded=0, variables=tuple(selected),
        )

    def correlation_heatmap(self, *columns: str):
        """Pairwise-complete Pearson r; n shown in every cell, no p-values."""
        import numpy as np

        selected = columns or tuple(k for k, spec in self.variables.items()
                                    if spec.kind == "numeric")
        if len(selected) < 2 or len(set(selected)) != len(selected):
            raise ValueError("Select at least two distinct numeric columns")
        for col in selected:
            self._variable(col, "numeric")
        correlation = np.zeros((len(selected), len(selected)), dtype=float)
        counts = np.zeros_like(correlation, dtype=int)
        for i, left in enumerate(selected):
            for j, right in enumerate(selected):
                pairs = [(r[left], r[right]) for r in self.rows
                         if r[left] is not None and r[right] is not None]
                counts[i, j] = len(pairs)
                if len(pairs) >= 3 and len({v[0] for v in pairs}) > 1 and len(
                    {v[1] for v in pairs}
                ) > 1:
                    correlation[i, j] = float(np.corrcoef(np.asarray(pairs).T)[0, 1])
                else:
                    correlation[i, j] = np.nan
        if np.isnan(correlation).all():
            raise ValueError("Insufficient pairwise variation for Pearson correlation")
        import matplotlib as mpl

        fig, ax = self._canvas(wide=True)
        cmap = mpl.colormaps[DIVERGING].with_extremes(bad=NEUTRAL_MISSING)
        image = ax.imshow(np.ma.masked_invalid(correlation), vmin=-1, vmax=1, cmap=cmap)
        ax.grid(False)
        ax.set_xticks(range(len(selected)), [self.variables[c].label for c in selected],
                      rotation=40, ha="right")
        ax.set_yticks(range(len(selected)), [self.variables[c].label for c in selected])
        for i in range(len(selected)):
            for j in range(len(selected)):
                val = correlation[i, j]
                label = f"{val:.2f}\nn={counts[i,j]}" if np.isfinite(val) else f"NA\nn={counts[i,j]}"
                ax.text(j, i, label, ha="center", va="center", fontsize=9,
                        color="white" if np.isfinite(val) and abs(val) > 0.65 else "#1D2632")
        fig.colorbar(image, ax=ax, label="Pearson r (unitless)", fraction=0.044, pad=0.03)
        return self._finish(
            fig, ax, kind="correlation",
            title="Pairwise correlation matrix",
            subtitle="Pearson r; each cell displays its own complete-pair denominator",
            caption="Pairwise complete cases can differ between cells. Correlation does not establish causation.",
            n_used=len(self.rows), excluded=0, variables=tuple(selected),
        )

    @staticmethod
    def matrix_heatmap(matrix, *, row_labels, col_labels, name: str, unit: str,
                       mode: str = "sequential", center: float | None = None,
                       study: Study):
        """Numeric assay-like matrix with gray NA cells and explicit colorbar.

        Diverging mode requires an explicit meaningful center; never auto-z-score.
        """
        import matplotlib as mpl
        import numpy as np

        if not isinstance(study, Study) or not name.strip() or not unit.strip():
            raise ValueError("Study, matrix label and unit required")
        data = np.asarray(matrix, dtype=float)
        if data.ndim != 2 or not 0 < data.size <= 40000:
            raise ValueError("2D matrix with 1–40000 cells required")
        if data.shape != (len(row_labels), len(col_labels)):
            raise ValueError("Matrix shape and axis-label counts must match")
        if any(not str(z).strip() for z in (*row_labels, *col_labels)):
            raise ValueError("Nonempty row/column labels required")
        if np.isinf(data).any() or not np.isfinite(data).any():
            raise ValueError("Infinity or all-missing matrix rejected")
        if mode not in {"sequential", "diverging"}:
            raise ValueError("mode must be sequential or diverging")
        if mode == "diverging" and (center is None or not np.isfinite(center)):
            raise ValueError("Diverging heatmap requires an explicit meaningful center")
        if mode == "sequential" and center is not None:
            raise ValueError("Only diverging heatmaps accept center")
        plt = FigureKit._mpl()
        fig, ax = plt.subplots(figsize=(max(8, min(16, data.shape[1] * 0.55)), 6.2))
        fig.subplots_adjust(left=0.18, right=0.83, top=0.75, bottom=0.26)
        finite = data[np.isfinite(data)]
        cmap = mpl.colormaps[SEQUENTIAL if mode == "sequential" else DIVERGING].with_extremes(bad=NEUTRAL_MISSING)
        if mode == "diverging":
            radius = max(float(np.max(np.abs(finite - center))), 1e-9)
            norm = mpl.colors.TwoSlopeNorm(vmin=center-radius, vcenter=center,
                                           vmax=center+radius)
            im = ax.imshow(np.ma.masked_invalid(data), cmap=cmap, norm=norm, aspect="auto")
        else:
            im = ax.imshow(np.ma.masked_invalid(data), cmap=cmap, aspect="auto")
        ax.set_xticks(range(data.shape[1]), col_labels, rotation=90)
        ax.set_yticks(range(data.shape[0]), row_labels)
        ax.set(xlabel="Sample identifier", ylabel="Feature identifier")
        ax.tick_params(labelsize=8)
        fig.colorbar(im, ax=ax, label=f"{name} ({unit})", fraction=0.046, pad=0.03)
        n_missing = int(np.isnan(data).sum())
        fig.text(0.18, 0.91, name, fontsize=14, weight="bold", color="#14233B")
        fig.text(0.18, 0.84, f"{study.title} | {data.shape[0]} features × "
                 f"{data.shape[1]} samples | NA cells={n_missing}", fontsize=10)
        caption = ("Diverging values centered at an explicit scientific reference: "
                   f"{center} {unit}." if mode == "diverging"
                   else "Sequential color represents measurement magnitude.") + (
                       f" Missing cells shown in neutral gray ({NEUTRAL_MISSING})."
                   )
        fig.text(0.18, 0.105, caption, fontsize=8.5, wrap=True)
        fig.text(0.18, 0.05, f"Source: {study.source}   •   {study.status}", fontsize=8)
        fig._research_meta = {
            "kind": "matrix_heatmap", "title": name, "caption": caption,
            "study": asdict(study), "unit": unit, "mode": mode,
            "center": center, "shape": list(data.shape), "missing_cells": n_missing,
            "release": "NOT SCIENTIFICALLY APPROVED BY AUTOMATED PLOTTING",
        }
        return fig

    def save(self, fig, stem: str | Path, *, formats: tuple[str, ...] = ("png", "pdf"),
             dpi: int = 300) -> list[Path]:
        """Export complete figure formats plus an adjacent JSON trace/manifest."""
        metadata = getattr(fig, "_research_meta", None)
        if not isinstance(metadata, dict):
            raise TypeError("Use a FigureKit figure to export traceable graphics")
        root = Path(stem)
        if root.suffix:
            raise ValueError("Supply a filename stem without extension")
        if not formats or any(kind not in {"png", "pdf", "svg"} for kind in formats):
            raise ValueError("Supported formats are png, pdf, svg")
        root.parent.mkdir(parents=True, exist_ok=True)
        paths = []
        for fmt in dict.fromkeys(formats):
            dest = root.with_suffix(f".{fmt}")
            fig.savefig(dest, dpi=dpi, facecolor="white")
            paths.append(dest)
        meta = dict(metadata)
        meta["files"] = [
            {"filename": path.name, "sha256": sha256_file(path)} for path in paths
        ]
        manifest = root.with_suffix(".figure.json")
        manifest.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        return [*paths, manifest]


def synthetic_kit(rows: list[dict]) -> FigureKit:
    """Preloaded *synthetic-only* dictionary; not reusable for real cohort semantics."""
    return FigureKit(
        rows, variables={
            "participant_id": Variable("Synthetic participant", "category",
                                        kind="categorical"),
            "site": Variable("Enrollment site", "category", kind="categorical",
                             levels=("North", "South", "West")),
            "age_years": Variable("Age", "years"),
            "measurement_mg_dl": Variable("Simulated measurement", "mg/dL"),
            "outcome": Variable("Simulated outcome", "unitless"),
        },
        study=Study(title="Synthetic cohort", observation_unit="simulated person",
                    source="research_template.synthetic.make_cohort"),
    )
