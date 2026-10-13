"""Executable research starter CLI. No external datasets or secrets required."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .provenance import create_manifest, save_json
from .quality import REQUIRED_COLUMNS, validate_cohort
from .study_packs import PackError, list_packs, load_pack, plan_pack, validate_csv
from .synthetic import make_cohort


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
    study_packs = commands.add_parser(
        "pack", help="Browse source-qualified study dictionaries and validate user CSVs"
    )
    pack_commands = study_packs.add_subparsers(dest="pack_command", required=True)
    pack_commands.add_parser("list", help="Show implemented opt-in dictionary packs")
    details = pack_commands.add_parser("describe", help="View a pack and its source references")
    details.add_argument("--id", required=True)
    plan = pack_commands.add_parser("plan", help="Review needed files, joins and weights")
    plan.add_argument("--id", required=True)
    verify = pack_commands.add_parser("validate", help="Inspect local CSV schema without copying data")
    verify.add_argument("--id", required=True)
    verify.add_argument("--table", required=True)
    verify.add_argument("--csv", type=Path, required=True)
    check = commands.add_parser("audit", help="Check scaffold; scientific release is blocked by default")
    check.add_argument("--root", type=Path, default=Path("."))
    check.add_argument("--require-release", action="store_true", help="Exit nonzero without approved science")
    args = parser.parse_args(argv)
    if args.command == "pack":
        try:
            if args.pack_command == "list":
                result = list_packs()
            elif args.pack_command == "describe":
                result = load_pack(args.id)
            elif args.pack_command == "plan":
                result = plan_pack(args.id)
            else:
                result = validate_csv(args.id, args.table, args.csv)
        except (PackError, OSError, UnicodeError, ValueError) as error:
            print(json.dumps({"status": "BLOCKED", "reason": str(error)}, indent=2))
            return 2
        print(json.dumps(result, indent=2))
        if args.pack_command == "validate":
            return 0 if result["status"] == "STRUCTURE_PASS_ANALYSIS_REVIEW_REQUIRED" else 1
        return 0
    if args.command == "demo":
        demo(args.out, n=args.n, seed=args.seed, plots=args.plots, ml=args.ml)
        return 0
    return audit(args.root, require_release=args.require_release)


if __name__ == "__main__":
    raise SystemExit(main())
