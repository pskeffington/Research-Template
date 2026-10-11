"""Whole-repository naming rules and executable R call-sheet consistency."""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_SOURCE_DIRS = ("src", "scripts", "tests")
DOCUMENTATION = (
    "README.md",
    "R/README.md",
    "R/STYLE_GUIDE.md",
    "docs/FUNCTION_CALL_SHEET.md",
)


def test_every_python_source_parses_with_pep8_names():
    paths = sorted(
        path for directory in PYTHON_SOURCE_DIRS
        for path in (ROOT / directory).rglob("*.py")
    )
    assert len(paths) >= 10
    snake_case = re.compile(r"^_{0,2}[a-z][a-z0-9]*(?:_[a-z0-9]+)*_{0,2}$")
    pascal_case = re.compile(r"^_?[A-Z][a-zA-Z0-9]*$")
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assert snake_case.fullmatch(node.name), f"{path}: {node.name}"
            elif isinstance(node, ast.ClassDef):
                assert pascal_case.fullmatch(node.name), f"{path}: {node.name}"


def _r_code_blocks(markdown_text: str) -> list[str]:
    pattern = r"(?:^|\n)(?:\x60{3}|~{3})r\s*\n(.*?)(?:\n\x60{3}|\n~{3})"
    return re.findall(pattern, markdown_text, flags=re.DOTALL)


def test_all_documented_r_graph_calls_load_tidy_first_exactly_once():
    for relative_path in DOCUMENTATION:
        content = (ROOT / relative_path).read_text(encoding="utf-8")
        for block in _r_code_blocks(content):
            tidy_source = 'source("R/research_tidy.R")'
            plot_source = 'source("R/research_plots.R")'
            if plot_source in block:
                assert tidy_source in block, f"{relative_path}: tidy source missing"
                assert block.index(tidy_source) < block.index(plot_source), (
                    f"{relative_path}: tidy contract must load before plotting"
                )
                assert block.count(tidy_source) == 1, (
                    f"{relative_path}: redundant tidy source"
                )


def test_primary_docs_link_the_style_contract():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    style = (ROOT / "R/STYLE_GUIDE.md").read_text(encoding="utf-8")
    sheet = (ROOT / "docs/FUNCTION_CALL_SHEET.md").read_text(encoding="utf-8")
    assert "R/STYLE_GUIDE.md" in readme
    assert "dplyr::" in sheet and "tidyr::" in sheet and "ggplot2::" in sheet
    assert "snake_case" in style
    assert (ROOT / "R/tests/test_style_contract.R").is_file()
    assert (ROOT / "R/tests/test_tidy_workflow.R").is_file()
