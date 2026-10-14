"""Pre-cooked *reference-only* oncology study workspaces.

Inspired by public Dartmouth Cancer Center research programs, without
institutional endorsement. No source data, analyses, inference or exports.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from importlib import resources
from pathlib import Path

from .sector_catalog import read_sector_catalog
from .study import StudyScaffoldError, create_study, validate_study

RECIPE_IDS = frozenset({"CPS-02", "SGN-02", "ICI-02", "TEC-01"})
ROLE_COLUMNS = (
    "role", "source_column", "type", "purpose", "required_for_analysis",
    "source_column_hint",
)
RECIPE_STATUS = "PRECOOKED_REFERENCE_WORKSPACE_ONLY"
RECIPE_FILES = (
    "SECTOR_RECIPE.json", "RECIPE_STATE.json", "VARIABLE_MAPPING.csv",
    "ANALYSIS_PLAN.md", "FIGURE_PLAN.md", "SECURITY_AND_APPROVALS.md",
)


class RecipeError(ValueError):
    """A reference recipe, workspace or proposed approval is invalid."""


def _load_catalog() -> tuple[dict, bytes]:
    raw = resources.files("research_template").joinpath("sector_recipes.json").read_bytes()
    manifest = json.loads(raw)
    sector = read_sector_catalog()
    if (
        manifest.get("schema_version") != 1
        or manifest.get("institutional_endorsement") != "NOT_CLAIMED"
        or manifest.get("data_download") != "DISABLED"
        or manifest.get("researcher_data_ingestion") != "DISABLED"
        or manifest.get("public_release") != "BLOCKED"
        or not isinstance(manifest.get("recipes"), list)
        or {r.get("id") for r in manifest["recipes"]} != RECIPE_IDS
    ):
        raise RecipeError("Sector recipe collection is incomplete or overauthorized")
    known = {x["id"]: x for x in sector["deployables"]}
    for recipe in manifest["recipes"]:
        ident = recipe["id"]
        if (
            known[ident]["program_id"] != recipe.get("program_id")
            or recipe.get("source_documentation_url") != known[ident]["dictionary_url"]
            or recipe.get("source_access_url") != known[ident]["data_access_url"]
            or recipe.get("schema_status") != RECIPE_STATUS
            or any(recipe.get(key) != expected for key, expected in (
                ("access_review", "PENDING"), ("scientific_review", "PENDING"),
                ("data_import", "DISABLED"), ("auto_statistics", "DISABLED"),
                ("public_release", "BLOCKED"),
            ))
            or not recipe.get("variable_roles")
            or not recipe.get("figure_recipes")
            or not recipe.get("method_choices")
            or not recipe.get("review_gates")
        ):
            raise RecipeError(f"{ident}: invalid source or execution gate")
        roles = [entry["role"] for entry in recipe["variable_roles"]]
        if len(roles) != len(set(roles)):
            raise RecipeError(f"{ident}: duplicated variable role")
        for entry in recipe["variable_roles"]:
            if (
                not re.fullmatch(r"[a-z][a-z0-9_]*", entry["role"])
                or entry["type"] not in {"text", "number", "category"}
                or type(entry["required_for_analysis"]) is not bool
                or not entry.get("purpose")
            ):
                raise RecipeError(f"{ident}: invalid variable dictionary")
        for method in recipe["method_choices"]:
            if (
                method.get("execution") != "DISABLED_PENDING_DESIGN_REVIEW"
                or not method.get("reference_url", "").startswith("https://")
            ):
                raise RecipeError(f"{ident}: unapproved method")
        for figure in recipe["figure_recipes"]:
            if figure.get("render_status") != "PLAN_ONLY" or not figure.get("restriction"):
                raise RecipeError(f"{ident}: unapproved figure")
    return manifest, raw


def list_recipes() -> dict:
    manifest, raw = _load_catalog()
    return {
        "status": "REFERENCE_WORKSPACE_TEMPLATES_ONLY",
        "recipes_sha256": hashlib.sha256(raw).hexdigest(),
        "recipes": [
            {
                "id": r["id"], "program_id": r["program_id"],
                "label": r["label"], "analysis_unit": r["analysis_unit"],
                "status": r["schema_status"],
            }
            for r in manifest["recipes"]
        ],
        "actual_data_loaded": False,
        "analyses_executed": False,
        "public_release": "BLOCKED",
    }


def get_recipe(recipe_id: str) -> tuple[dict, str]:
    manifest, raw = _load_catalog()
    if recipe_id not in RECIPE_IDS:
        raise RecipeError("Unknown or not-yet-pre-cooked sector recipe ID")
    result = next(r for r in manifest["recipes"] if r["id"] == recipe_id)
    return result, hashlib.sha256(raw).hexdigest()


def _safe_destination(path: Path) -> None:
    if path.exists() or path.is_symlink():
        raise RecipeError("Study destination exists; never overwrite user files")
    if any(p.is_symlink() for p in path.parents):
        raise RecipeError("A parent folder redirects through a symlink")


def _md_plan(recipe: dict, *, figure: bool) -> str:
    if figure:
        sections = [
            f"# Candidate figure plan — {recipe['id']}",
            "",
            "**PLANNING ONLY.** Do not display real datasets, maps, subject data or results here.",
            "",
        ]
        for f in recipe["figure_recipes"]:
            sections.extend([
                f"## {f['figure']}", "",
                f"**Uncertainty/display:** {f['uncertainty']}", "",
                f"**Do not:** {f['restriction']}", "",
            ])
    else:
        sections = [
            f"# Analysis and study design — {recipe['id']}", "",
            "**DRAFT:** Methods below are *candidates*, not automatically selected tests.",
            f"**Unit of analysis:** {recipe['analysis_unit']}", "",
            "## Candidate methods", "",
        ]
        for method in recipe["method_choices"]:
            sections.extend([
                f"### {method['method']}", "",
                f"{method['preconditions']}", "",
                f"Reference: {method['reference_url']}", "",
                "**Execution:** BLOCKED until study-specific design review.", "",
            ])
        sections.extend(["## Required review gates", ""])
        for gate in recipe["review_gates"]:
            sections.append(f"- [ ] {gate}")
        sections.extend(["", "## Scientific and privacy sign-off", "",
            "- [ ] Independent data rights and storage approved",
            "- [ ] Actual source dictionary and sample/unit schema verified",
            "- [ ] Estimand, analytic cohort, uncertainty and testing independently reviewed",
            "- [ ] Figure/caption/disclosure and publication rights separately approved", ""])
    return "\n".join(sections) + "\n"


def create_recipe_workspace(recipe_id: str, destination: Path, title: str | None = None) -> Path:
    """Create a NEW, no-input project with a recipe snapshot and blank mapping."""
    recipe, digest = get_recipe(recipe_id)
    destination = Path(destination)
    _safe_destination(destination)
    try:
        path = create_study(
            destination, title=title or recipe["label"],
            objective=recipe["default_objective"],
            analysis_unit=recipe["analysis_unit"],
        )
    except StudyScaffoldError as exc:
        raise RecipeError(str(exc)) from exc
    try:
        with (path / "SECTOR_RECIPE.json").open("x", encoding="utf-8") as output:
            json.dump(recipe, output, indent=2)
            output.write("\n")
        state = {
            "schema_version": 1,
            "recipe_id": recipe_id,
            "recipe_collection_sha256": digest,
            "source_catalog_url": recipe["source_documentation_url"],
            "access_application_url": recipe["source_access_url"],
            "recipe_status": RECIPE_STATUS,
            "institutional_endorsement": "NOT_CLAIMED",
            "data_access": "NOT_ASSESSED",
            "sample_alignment": "NOT_ASSESSED",
            "analysis_execution": "DISABLED",
            "figure_rendering": "DISABLED",
            "scientific_review": "PENDING",
            "public_release": "BLOCKED",
        }
        with (path / "RECIPE_STATE.json").open("x", encoding="utf-8") as output:
            json.dump(state, output, indent=2)
            output.write("\n")
        with (path / "VARIABLE_MAPPING.csv").open(
            "x", encoding="utf-8", newline=""
        ) as stream:
            writer = csv.DictWriter(stream, fieldnames=ROLE_COLUMNS)
            writer.writeheader()
            for entry in recipe["variable_roles"]:
                writer.writerow({
                    **entry,
                    "source_column": "",
                })
        (path / "ANALYSIS_PLAN.md").write_text(_md_plan(recipe, figure=False),
                                               encoding="utf-8")
        (path / "FIGURE_PLAN.md").write_text(_md_plan(recipe, figure=True),
                                             encoding="utf-8")
        (path / "SECURITY_AND_APPROVALS.md").write_text(
            "# Dataset rights and secure execution — pending\n\n"
            "This is an independently written, publicly sourced planning template, "
            "not institutional approval or a research dataset.\n\n"
            f"Source dictionary: {recipe['source_documentation_url']}\n\n"
            f"Official data access instructions: {recipe['source_access_url']}\n\n"
            "Fill VARIABLE_MAPPING.csv only after selecting a source version and "
            "separately verifying every actual source column, unit, coding rule and "
            "subject/sampling structure. Blank source_column fields are intentional.\n\n"
            "No data have been downloaded or loaded, no inference has been fitted, "
            "and no medical figure has been rendered.\n\n"
            "Read the public template docs/DATA_ACCESS_AND_SECURITY.md before "
            "importing data. Local ignore rules are not secure storage.\n\n"
            "- [ ] Source access/data use agreement checked\n"
            "- [ ] Institutional review and approved computing location checked\n"
            "- [ ] Design, joins, missingness and source version documented\n"
            "- [ ] Protected outputs/disclosure review completed before sharing\n",
            encoding="utf-8",
        )
        report = validate_recipe_workspace(path)
        if report["status"] != "REFERENCE_WORKSPACE_PASS_NO_ANALYSIS":
            raise RecipeError("Created recipe workspace failed structural self-check")
    except Exception:
        # create_study exclusively created this new output directory.
        shutil.rmtree(path)
        raise
    return path


def validate_recipe_workspace(path: Path) -> dict:
    """Structural integrity only: never open raw subject data or authorize analysis."""
    path = Path(path)
    errors = list(validate_study(path)["errors"])
    if not path.is_dir() or path.is_symlink():
        errors.append("Missing recipe workspace")
    else:
        for name in RECIPE_FILES:
            file = path / name
            if file.is_symlink() or not file.is_file():
                errors.append(f"Missing or redirected reference file: {name}")
        if not errors:
            try:
                state = json.loads((path / "RECIPE_STATE.json").read_text(encoding="utf-8"))
                recipe = json.loads((path / "SECTOR_RECIPE.json").read_text(encoding="utf-8"))
                approved, digest = get_recipe(state["recipe_id"])
                if state != {
                    "schema_version": 1,
                    "recipe_id": approved["id"],
                    "recipe_collection_sha256": digest,
                    "source_catalog_url": approved["source_documentation_url"],
                    "access_application_url": approved["source_access_url"],
                    "recipe_status": RECIPE_STATUS,
                    "institutional_endorsement": "NOT_CLAIMED",
                    "data_access": "NOT_ASSESSED",
                    "sample_alignment": "NOT_ASSESSED",
                    "analysis_execution": "DISABLED",
                    "figure_rendering": "DISABLED",
                    "scientific_review": "PENDING",
                    "public_release": "BLOCKED",
                } or recipe != approved:
                    errors.append("Source provenance or review status altered")
                with (path / "VARIABLE_MAPPING.csv").open(
                    encoding="utf-8-sig", newline=""
                ) as stream:
                    reader = csv.DictReader(stream)
                    if tuple(reader.fieldnames or ()) != ROLE_COLUMNS:
                        errors.append("Variable mapping CSV columns changed")
                    else:
                        rows = list(reader)
                        if [r["role"] for r in rows] != [
                            r["role"] for r in approved["variable_roles"]
                        ]:
                            errors.append("Required role order or count changed")
                        for row, ref in zip(rows, approved["variable_roles"], strict=False):
                            for key in ROLE_COLUMNS:
                                if key != "source_column" and str(row[key]) != str(ref[key]):
                                    errors.append(f"Fixed reference metadata changed for {row['role']}")
                            if row["source_column"] and (
                                "\n" in row["source_column"]
                                or len(row["source_column"]) > 160
                            ):
                                errors.append("Invalid user-provided source column")
            except (OSError, KeyError, TypeError, ValueError, csv.Error) as exc:
                errors.append(f"Invalid recipe reference metadata: {type(exc).__name__}")
    return {
        "status": ("REFERENCE_WORKSPACE_PASS_NO_ANALYSIS"
                   if not errors else "REFERENCE_WORKSPACE_BLOCKED"),
        "errors": errors,
        "scientific_validation": "NOT_ASSESSED",
        "data_access": "NOT_ASSESSED",
        "input_rows_read": 0,
        "analyses_executed": False,
        "public_release": "BLOCKED",
    }
