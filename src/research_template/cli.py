"""Executable research starter CLI. No external datasets or secrets required."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .provenance import create_manifest, save_json
from .quality import REQUIRED_COLUMNS, validate_cohort
from .synthetic import make_cohort


def demo(out: Path, *, n: int = 120, seed: int = 711, plots: bool = False, ml: bool = False) -> None:
    rows = make_cohort(n=n, seed=seed)
    summary = validate_cohort(rows)
    out.mkdir(parents=True, exist_ok=True)
    dataset = out / "synthetic_cohort.csv"
    with dataset.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    artifacts = [dataset, save_json(out / "quality_summary.json", summary)]
    if plots:
        import matplotlib.pyplot as plt

        from .plots import group_box, heatmap, histogram, save_figure, scatter

        graph_calls = [
            (histogram(rows, "measurement_mg_dl", name="Simulated measurement", unit="mg/dL"),
             out / "measurement_histogram.png"),
            (group_box(rows, "measurement_mg_dl", "site", name="Simulated measurement", unit="mg/dL"),
             out / "measurement_by_site.pdf"),
            (scatter(rows, "age_years", "measurement_mg_dl", x_name="Age", x_unit="years",
                     y_name="Simulated measurement", y_unit="mg/dL"),
             out / "age_measurement_scatter.png"),
            (heatmap([[1, 2, 3], [2, 4, 3], [3, 5, 7]], row_labels=["F1", "F2", "F3"],
                     col_labels=["S1", "S2", "S3"], name="Synthetic signal", unit="unitless"),
             out / "signal_heatmap.pdf"),
        ]
        for fig, destination in graph_calls:
            artifacts.append(save_figure(fig, destination))
            plt.close(fig)
    if ml:
        from .ml import run_classification
        artifacts.append(save_json(out / "ml_demo_metrics.json", run_classification(rows, seed=seed)))
    manifest = create_manifest(out, artifacts, seed=seed, purpose="Synthetic research-template smoke run")
    save_json(out / "run_manifest.json", manifest)
    print(json.dumps({"quality": summary, "manifest": str(out / "run_manifest.json")}, indent=2))


def audit(root: Path, *, require_release: bool = False) -> int:
    required = [
        "README.md", "pyproject.toml", "docs/PROTOCOL.md", "docs/DATA_DICTIONARY.md",
        "docs/SOURCE_REGISTER.md", "docs/RELEASE_GATES.md", "references/LITERATURE_MATRIX.csv",
        ".github/workflows/ci.yml",
    ]
    missing = [path for path in required if not (root / path).is_file()]
    result = {
        "scaffold_status": "FAIL" if missing else "PASS",
        "missing_files": missing,
        "scientific_release_status": "BLOCKED",
        "reason": "Default template contains no approved study, reviewed data, model or public claims.",
        "require_release": require_release,
    }
    print(json.dumps(result, indent=2))
    return int(bool(missing) or require_release)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic research starter and scaffold audit")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("demo", help="Execute reproducible synthetic example")
    run.add_argument("--out", type=Path, default=Path("artifacts/demo"))
    run.add_argument("--n", type=int, default=120)
    run.add_argument("--seed", type=int, default=711)
    run.add_argument("--plots", action="store_true", help="Requires pip install -e '.[plot]'")
    run.add_argument("--ml", action="store_true", help="Requires pip install -e '.[ml]'")
    check = commands.add_parser("audit", help="Check scaffold; scientific release is blocked by default")
    check.add_argument("--root", type=Path, default=Path("."))
    check.add_argument("--require-release", action="store_true", help="Exit nonzero without approved science")
    args = parser.parse_args(argv)
    if args.command == "demo":
        demo(args.out, n=args.n, seed=args.seed, plots=args.plots, ml=args.ml)
        return 0
    return audit(args.root, require_release=args.require_release)


if __name__ == "__main__":
    raise SystemExit(main())
