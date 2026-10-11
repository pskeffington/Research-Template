"""Backward-compatible plotting calls routed through the full figure design system.

For a defined biomedical project, prefer FigureKit with a study dictionary.
"""

from __future__ import annotations

from pathlib import Path

from .biomed import FigureKit, Study, Variable


def axis_label(name: str, unit: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Explicit nonempty variable label required")
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("Explicit unit required; use 'unitless' if appropriate")
    return f"{name} ({unit})"


def _study() -> Study:
    return Study(
        "Standalone plotting example", "record", "caller-supplied observations",
        status="DESCRIPTIVE ONLY / SOURCE VALIDATION REQUIRED",
    )


def histogram(rows: list[dict], value: str, *, name: str, unit: str, bins: int = 12):
    kit = FigureKit(rows, variables={value: Variable(name, unit)}, study=_study())
    return kit.histogram(value, bins=bins)


def scatter(rows: list[dict], x: str, y: str, *, x_name: str, x_unit: str,
            y_name: str, y_unit: str):
    kit = FigureKit(
        rows, variables={x: Variable(x_name, x_unit), y: Variable(y_name, y_unit)},
        study=_study(),
    )
    return kit.scatter(x, y)


def group_box(rows: list[dict], value: str, group: str, *, name: str, unit: str):
    kit = FigureKit(
        rows, variables={value: Variable(name, unit),
                         group: Variable(group, "category", kind="categorical")},
        study=_study(),
    )
    return kit.box(value, group=group)


def heatmap(matrix, *, row_labels: list[str], col_labels: list[str], name: str,
            unit: str, mode: str = "sequential", center: float | None = None):
    """Diverging mode now requires explicit center to prevent misleading scales."""
    return FigureKit.matrix_heatmap(
        matrix, row_labels=row_labels, col_labels=col_labels, name=name,
        unit=unit, mode=mode, center=center, study=_study(),
    )


def save_figure(fig, path, *, dpi: int = 300):
    """Legacy single-format file export. Use FigureKit.save for dual formats + trace."""
    target = Path(path)
    if target.suffix.lower() not in {".png", ".pdf", ".svg"}:
        raise ValueError("Figure suffix must be png, pdf or svg")
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=dpi, bbox_inches="tight", facecolor="white")
    return target
