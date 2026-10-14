"""Create and validate an empty, study-neutral research workspace.

Only study metadata and blank documentation are generated. No data ingestion,
network access, scientific approval or publication authorization occurs.
"""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

OBJECTIVES = ("descriptive", "inferential", "predictive")
DATA_DICTIONARY_COLUMNS = (
    "variable_name", "description", "data_type", "unit", "analysis_role",
    "missingness_rule", "source_id", "privacy_classification",
)
SOURCE_REGISTER_COLUMNS = (
    "source_id", "description", "owner_or_custodian", "license_or_use_terms",
    "storage_reference", "privacy_classification", "access_approved",
    "source_version", "sha256",
)
REQUIRED_FILES = (
    "study.json", "README.md", "PROTOCOL.md", "data_dictionary.csv",
    "source_register.csv", ".gitignore",
)
PRIVATE_FOLDERS = ("data", "outputs", "private")


class StudyScaffoldError(ValueError):
    """Invalid or unsafe input to the study workspace scaffold."""


def _field(value: str, label: str, *, limit: int = 120) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StudyScaffoldError(f"{label} must be nonempty")
    result = value.strip()
    if len(result) > limit or any(ord(char) < 32 or ord(char) == 127 for char in result):
        raise StudyScaffoldError(f"{label} contains control characters or exceeds {limit} chars")
    return result


def _write_header(path: Path, fields: tuple[str, ...]) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerow(fields)


def create_study(out: Path, *, title: str, objective: str, analysis_unit: str) -> Path:
    """Generate a blank workspace in a NEW directory; never overwrite existing files."""
    title = _field(title, "Study title")
    analysis_unit = _field(analysis_unit, "Analysis unit", limit=80)
    if objective not in OBJECTIVES:
        raise StudyScaffoldError(f"Objective must be one of {', '.join(OBJECTIVES)}")
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise StudyScaffoldError(f"Destination already exists: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir(exist_ok=False)
    try:
        metadata = {
            "schema_version": 1,
            "title": title,
            "objective": objective,
            "analysis_unit": analysis_unit,
            "project_state": "DRAFT_UNREVIEWED",
            "data_access": "NOT_ASSESSED",
            "scientific_validation": "NOT_ASSESSED",
            "public_release": "BLOCKED",
        }
        (out / "study.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (out / "README.md").write_text(
            f"# {title}\n\n"
            "**Status:** Draft research workspace; no source data or findings included.\n\n"
            f"**Study objective:** {objective}\n\n"
            f"**Analysis unit:** {analysis_unit}\n\n"
            "Complete the protocol, variable dictionary and data-source register "
            "before substituting real inputs. Record scientific, ethics, privacy and "
            "licensing approval outside this generated scaffold.\n\n"
            "The data, private and outputs folders are ignored by Git. Ignore rules "
            "are not access-control mechanisms; use approved protected storage.\n",
            encoding="utf-8",
        )
        (out / "PROTOCOL.md").write_text(
            "# Study protocol — draft\n\n"
            f"**Working title:** {title}\n\n"
            f"**Purpose:** {objective}\n\n"
            f"**Unit of analysis:** {analysis_unit}\n\n"
            "## Research question and hypotheses\n\n"
            "[Describe the question, estimand and hypotheses, if applicable.]\n\n"
            "## Design, population and sampling\n\n"
            "[Specify inclusion/exclusion rules, time structure and dependence.]\n\n"
            "## Approved data sources and rights\n\n"
            "[Complete source register, access/privacy review and licensing conditions.]\n\n"
            "## Variables, units, joins and missingness\n\n"
            "[Complete dictionary, transformations, denominator and missingness plan.]\n\n"
            "## Statistical and computational analysis\n\n"
            "[Prespecify assumptions, tests, uncertainty, validation and splits.]\n\n"
            "## Bias, limitations and ethics\n\n"
            "[Record confounding, measurement error, fairness and review obligations.]\n\n"
            "## Figure preparation and publication\n\n"
            "[Document legends, print size, accessibility and release approvals.]\n\n"
            "## Review checklist\n\n"
            "- [ ] Data-source permissions independently reviewed\n"
            "- [ ] Analysis protocol reviewed\n"
            "- [ ] Scientific interpretation independently reviewed\n"
            "- [ ] Privacy and publication approvals recorded\n",
            encoding="utf-8",
        )
        _write_header(out / "data_dictionary.csv", DATA_DICTIONARY_COLUMNS)
        _write_header(out / "source_register.csv", SOURCE_REGISTER_COLUMNS)
        (out / ".gitignore").write_text(
            "# Local study files and derived outputs; NOT access control\n"
            "/data/\n/private/\n/outputs/\n.env\n.env.*\n*.key\n*.pem\n",
            encoding="utf-8",
        )
        for name in PRIVATE_FOLDERS:
            (out / name).mkdir()
    except Exception:
        shutil.rmtree(out)
        raise
    return out


def validate_study(root: Path) -> dict[str, object]:
    """Validate scaffold structure only; never certify data or scientific results."""
    root = Path(root)
    errors: list[str] = []
    if root.is_symlink() or not root.is_dir():
        errors.append("Study workspace missing or redirected")
    else:
        for name in REQUIRED_FILES:
            file = root / name
            if file.is_symlink() or not file.is_file():
                errors.append(f"Missing or redirected scaffold file: {name}")
        for name in PRIVATE_FOLDERS:
            directory = root / name
            if directory.is_symlink() or not directory.is_dir():
                errors.append(f"Missing or redirected protected-output directory: {name}")
        manifest = root / "study.json"
        if manifest.is_file() and not manifest.is_symlink():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("Expected JSON object")
                if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
                    errors.append("Unsupported study metadata schema")
                _field(data.get("title"), "Study title")
                _field(data.get("analysis_unit"), "Analysis unit", limit=80)
                if data.get("objective") not in OBJECTIVES:
                    errors.append("Invalid study objective")
                if data.get("project_state") != "DRAFT_UNREVIEWED":
                    errors.append("Generated project state cannot assert formal approval")
                if data.get("data_access") != "NOT_ASSESSED":
                    errors.append("Data access cannot be approved by the scaffold")
                if data.get("scientific_validation") != "NOT_ASSESSED":
                    errors.append("Scientific validation cannot be approved by the scaffold")
                if data.get("public_release") != "BLOCKED":
                    errors.append("Public release must remain blocked")
            except (OSError, ValueError, TypeError) as exc:
                errors.append(f"Invalid study metadata: {exc}")
        for name, columns in (
            ("data_dictionary.csv", DATA_DICTIONARY_COLUMNS),
            ("source_register.csv", SOURCE_REGISTER_COLUMNS),
        ):
            path = root / name
            if path.is_file() and not path.is_symlink():
                try:
                    with path.open(encoding="utf-8-sig", newline="") as handle:
                        actual = next(csv.reader(handle), ())
                    if tuple(actual) != columns:
                        errors.append(f"Required metadata columns differ: {name}")
                except (OSError, UnicodeError, csv.Error) as exc:
                    errors.append(f"Cannot read {name}: {exc}")
        ignore = root / ".gitignore"
        if ignore.is_file() and not ignore.is_symlink():
            content = ignore.read_text(encoding="utf-8")
            for marker in ("/data/", "/private/", "/outputs/", ".env", "*.key"):
                if marker not in content.splitlines():
                    errors.append(f"Study ignore rule missing: {marker}")
    return {
        "scaffold_status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "scientific_validation": "NOT_ASSESSED",
        "data_access": "NOT_ASSESSED",
        "public_release": "BLOCKED",
    }
