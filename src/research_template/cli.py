"""Executable research starter CLI. No external datasets or secrets required."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from .provenance import create_manifest, save_json
from .quality import REQUIRED_COLUMNS, validate_cohort
from .synthetic import make_cohort
from .study import StudyScaffoldError, create_study, validate_study


def demo(out: Path, *, n: int = 120, seed: int = 711,
         plots: bool = False, ml: bool = False) -> None:
    """Write a synthetic research gallery, descriptive tables and provenance manifest."""
    from .biomed import synthetic_kit

    rows = make_cohort(n=n, seed=seed)
    summary = validate_cohort(rows)
    out.mkdir(parents=True, exist_ok=True)
    dataset = out / "synthetic_cohort.csv"
    with dataset.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    artifacts = [dataset, save_json(out / "quality_summary.json", summary)]
    kit = synthetic_kit(rows)
    artifacts.append(save_json(out / "summary_numeric.json", kit.summary("measurement_mg_dl")))
    artifacts.append(save_json(
        out / "summary_by_site.json", kit.summary("measurement_mg_dl", group="site")
    ))
    if plots:
        import matplotlib.pyplot as plt

        plots_to_export = [
            ("measurement_histogram", kit.histogram("measurement_mg_dl")),
            ("measurement_box", kit.box("measurement_mg_dl", group="site")),
            ("measurement_violin", kit.box("measurement_mg_dl", group="site", violin=True)),
            ("age_scatter", kit.scatter("age_years", "measurement_mg_dl", group="site")),
            ("site_counts", kit.category_bar("site")),
            ("missingness", kit.missingness("age_years", "measurement_mg_dl", "outcome")),
            ("correlation", kit.correlation_heatmap("age_years", "measurement_mg_dl")),
            ("sequential_heatmap", kit.matrix_heatmap(
                [[1.2, 2.0, 3.2], [2.1, None, 3.6], [3.0, 5.0, 7.0]],
                row_labels=["Feature A", "Feature B", "Feature C"],
                col_labels=["Sample 1", "Sample 2", "Sample 3"],
                name="Synthetic abundance", unit="unitless", study=kit.study,
            )),
            ("diverging_heatmap", kit.matrix_heatmap(
                [[-1.2, 0, 1.5], [0.8, None, -1.6], [2, -0.5, 0]],
                row_labels=["Feature A", "Feature B", "Feature C"],
                col_labels=["Sample 1", "Sample 2", "Sample 3"],
                name="Synthetic signed deviation", unit="unitless",
                mode="diverging", center=0, study=kit.study,
            )),
        ]
        for stem, fig in plots_to_export:
            artifacts.extend(kit.save(fig, out / stem))
            plt.close(fig)
    if ml:
        from .ml import run_classification

        artifacts.append(save_json(out / "ml_demo_metrics.json", run_classification(rows, seed=seed)))
    manifest = create_manifest(out, artifacts, seed=seed, purpose="Synthetic research-template smoke run")
    save_json(out / "run_manifest.json", manifest)
    print(json.dumps({"quality": summary, "manifest": str(out / "run_manifest.json"),
                      "artifacts": len(artifacts)}, indent=2))


def audit(root: Path, *, require_release: bool = False) -> int:
    required = [
        "README.md", "pyproject.toml", "docs/PROTOCOL.md", "docs/DATA_DICTIONARY.md",
        "docs/SOURCE_REGISTER.md", "docs/RELEASE_GATES.md", "references/LITERATURE_MATRIX.csv",
        ".github/workflows/ci.yml", "docs/FUNCTION_CALL_SHEET.md",
        "docs/FIGURE_STANDARD.md", "src/research_template/biomed.py",
        "src/research_template/summary.py",
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
    create = commands.add_parser(
        "init-study", help="Create an empty study workspace from researcher input"
    )
    create.add_argument("--out", type=Path, required=True)
    create.add_argument("--title", required=True)
    create.add_argument(
        "--objective", choices=("descriptive", "inferential", "predictive"), required=True
    )
    create.add_argument("--analysis-unit", required=True)
    verify = commands.add_parser(
        "check-study", help="Check a study scaffold, not its scientific validity"
    )
    verify.add_argument("--root", type=Path, required=True)
    check = commands.add_parser("audit", help="Check scaffold; scientific release is blocked by default")
    check.add_argument("--root", type=Path, default=Path("."))
    check.add_argument("--require-release", action="store_true", help="Exit nonzero without approved science")
    args = parser.parse_args(argv)
    if args.command == "init-study":
        try:
            project = create_study(
                args.out, title=args.title, objective=args.objective,
                analysis_unit=args.analysis_unit,
            )
        except (StudyScaffoldError, OSError) as error:
            print(f"Study initialization blocked: {error}", file=sys.stderr)
            return 2
        print(json.dumps({"project_dir": str(project), **validate_study(project)}, indent=2))
        return 0
    if args.command == "check-study":
        report = validate_study(args.root)
        print(json.dumps(report, indent=2))
        return 0 if report["scaffold_status"] == "PASS" else 1
    if args.command == "demo":
        demo(args.out, n=args.n, seed=args.seed, plots=args.plots, ml=args.ml)
        return 0
    return audit(args.root, require_release=args.require_release)


if __name__ == "__main__":
    raise SystemExit(main())
