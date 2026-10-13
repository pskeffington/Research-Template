"""The public starter may not embed a single project's analysis or private schema."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCANNED = ("README.md", "R", "src", "scripts", "docs", "references", ".github")
TEXT_EXTENSIONS = {".py", ".R", ".md", ".csv", ".yml", ".yaml", ".toml"}

# Deliberately assemble tokens so this test does not itself contain study names.
STUDY_MARKERS = (
    "pam" + "50",
    "tc" + "ga",
    "br" + "ca",
    "st" + "06",
    "st" + "07",
    "st" + "09",
    "dart" + "mouth.hse",
)


def test_public_source_and_docs_remain_study_agnostic():
    for name in SCANNED:
        location = ROOT / name
        paths = [location] if location.is_file() else location.rglob("*")
        for path in paths:
            if not path.is_file() or path.suffix not in TEXT_EXTENSIONS:
                continue
            text = path.read_text(encoding="utf-8").lower()
            for marker in STUDY_MARKERS:
                assert marker not in text, (
                    f"Public starter contains a study-specific reference in {path}: {marker}"
                )


def test_generic_user_onboarding_is_documented():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for term in (
        "Use this template",
        "research-template demo",
        "docs/PROJECT_SETUP.md",
        "docs/FUNCTION_CALL_SHEET.md",
        "docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md",
        "references/JOURNAL_FIGURE_REQUIREMENTS_MATRIX_2026-10-12.csv",
    ):
        assert term in readme


def test_reusable_r_and_python_modules_remain_available():
    for name in (
        "R/research_plots.R",
        "R/research_tidy.R",
        "R/research_complex_heatmap.R",
        "R/research_inference_plots.R",
        "R/research_interactive.R",
        "R/manuscript_delivery.R",
        "src/research_template/plots.py",
        "src/research_template/ml.py",
    ):
        assert (ROOT / name).is_file()
