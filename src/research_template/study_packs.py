"""Versioned, opt-in data-dictionary packs with read-only CSV structure checks.

A Study Pack describes source schemas and safe analysis prerequisites.
It never downloads, joins, transforms, uploads, or publishes a research dataset.
"""

from __future__ import annotations

import csv
import json
import math
import re
from importlib import resources
from pathlib import Path

PACK_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SUPPORTED_TYPES = {"integer", "number", "category", "text"}
MISSING = {"", ".", "NA", "N/A"}
MAX_BYTES = 100 * 1024 * 1024
MAX_ERRORS = 20


class PackError(ValueError):
    """Invalid, unsupported or unsafe study-pack request."""


def load_pack(pack_id: str) -> dict:
    if not isinstance(pack_id, str) or not PACK_ID.fullmatch(pack_id):
        raise PackError("Invalid study-pack identifier")
    item = resources.files("research_template").joinpath("packs", f"{pack_id}.json")
    if not item.is_file():
        raise PackError(f"Unknown or not-yet-implemented Study Pack: {pack_id}")
    definition = json.loads(item.read_text(encoding="utf-8"))
    if (definition.get("pack_id") != pack_id
            or definition.get("schema_version") != 1
            or definition.get("status") != "SCHEMA_VALIDATION_PILOT"
            or not isinstance(definition.get("tables"), dict)
            or not definition["tables"]):
        raise PackError("Invalid or unsupported Study Pack schema")
    for name, table in definition["tables"].items():
        if (not re.fullmatch(r"[A-Za-z0-9_]+", name)
                or not table.get("source_url", "").startswith("https://")
                or not isinstance(table.get("columns"), dict)
                or table.get("join_key") not in table["columns"]):
            raise PackError(f"Missing reference authority or join key in {name}")
        for field, spec in table["columns"].items():
            if (not re.fullmatch(r"[A-Za-z0-9_]+", field)
                    or spec.get("type") not in SUPPORTED_TYPES
                    or type(spec.get("required")) is not bool
                    or type(spec.get("nullable")) is not bool):
                raise PackError(f"Unsupported dictionary field: {field}")
            if spec["type"] == "category" and (
                not isinstance(spec.get("values"), list)
                or not all(isinstance(v, str) for v in spec["values"])
            ):
                raise PackError(f"Missing categorical level dictionary: {field}")
    return definition


def list_packs() -> list[dict]:
    """Only show actually implemented packs; never imply other studies are ready."""
    folder = resources.files("research_template").joinpath("packs")
    packs = []
    for item in folder.iterdir():
        if item.name.endswith(".json"):
            key = item.name[:-5]
            pack = load_pack(key)
            packs.append({
                "pack_id": pack["pack_id"],
                "name": pack["display_name"],
                "version": pack["version"],
                "status": pack["status"],
                "table_count": len(pack["tables"]),
                "data_download": "DISABLED",
                "analysis_approval": "NOT_GRANTED",
            })
    return sorted(packs, key=lambda x: x["pack_id"])


def plan_pack(pack_id: str) -> dict:
    pack = load_pack(pack_id)
    return {
        "pack_id": pack_id,
        "version": pack["version"],
        "status": "REFERENCE_PLAN_ONLY",
        "files": {
            name: {
                "expected_csv": table["expected_csv"],
                "source_dictionary": table["source_url"],
                "required_columns": [
                    column for column, spec in table["columns"].items()
                    if spec["required"]
                ],
                "join_key": table["join_key"],
            }
            for name, table in pack["tables"].items()
        },
        "join_plan": pack.get("join_plan"),
        "survey_design": pack.get("survey_design"),
        "data_ingestion": "USER_CONTROLLED_NOT_EXECUTED",
        "weighted_inference": "NOT_AUTHORIZED",
        "public_release": "BLOCKED",
    }


def _value_ok(raw: str, spec: dict) -> bool:
    kind = spec["type"]
    if kind == "text":
        return True
    if kind == "category":
        return raw in spec["values"]
    try:
        value = float(raw)
    except (ValueError, OverflowError):
        return False
    if not math.isfinite(value):
        return False
    return kind == "number" or value.is_integer()


def validate_csv(pack_id: str, table_name: str, path: Path) -> dict:
    """Read-only structural validation: never log or export original cell values."""
    pack = load_pack(pack_id)
    if table_name not in pack["tables"]:
        raise PackError(f"Table not included in Study Pack: {table_name}")
    table = pack["tables"][table_name]
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise PackError("Input must be a regular existing CSV, not a symlink")
    if path.name != table["expected_csv"]:
        raise PackError(
            f"Wrong filename/cycle: expected {table['expected_csv']}; "
            "no automatic study-cycle matching"
        )
    if path.stat().st_size > MAX_BYTES:
        raise PackError("CSV exceeds the 100 MiB pilot safety limit")
    errors: list[str] = []
    missing: dict[str, int] = {}
    special: dict[str, int] = {}
    total = 0
    seen: set[str] = set()
    fields = table["columns"]
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        if not headers or len(headers) != len(set(headers)) or any(not h for h in headers):
            raise PackError("Missing, empty or duplicated CSV column headings")
        absent = [name for name, spec in fields.items()
                  if spec["required"] and name not in headers]
        if absent:
            return {
                "pack_id": pack_id, "table": table_name,
                "status": "STRUCTURE_BLOCKED",
                "missing_columns": absent,
                "row_count": 0, "errors": ["Required source columns absent"],
                "analysis_approved": False, "public_release": "BLOCKED",
            }
        inspected = {name: spec for name, spec in fields.items() if name in headers}
        missing = {name: 0 for name in inspected}
        special = {name: 0 for name, spec in inspected.items()
                   if "special_codes" in spec}
        for row in reader:
            total += 1
            if total > 100_000:
                raise PackError("Pilot row limit exceeded; use a reviewed streaming adapter")
            if None in row:
                if len(errors) < MAX_ERRORS:
                    errors.append(f"CSV field-count mismatch at row {total}")
                continue
            key = (row.get(table["join_key"]) or "").strip()
            if not key or key in seen:
                if len(errors) < MAX_ERRORS:
                    errors.append(f"Missing or duplicate join key at row {total}")
            seen.add(key)
            for field, spec in inspected.items():
                value = row[field]
                if value is None:
                    value = ""
                value = value.strip()
                if value in MISSING:
                    missing[field] += 1
                    if not spec["nullable"] and len(errors) < MAX_ERRORS:
                        errors.append(f"Required non-null field missing: {field} at row {total}")
                elif not _value_ok(value, spec):
                    if len(errors) < MAX_ERRORS:
                        errors.append(f"Invalid coded/type value in {field} at row {total}")
                elif field in special and value in spec["special_codes"]:
                    special[field] += 1
    if total == 0 and len(errors) < MAX_ERRORS:
        errors.append("Source CSV is empty")
    return {
        "pack_id": pack_id,
        "table": table_name,
        "source_dictionary": table["source_url"],
        "status": "STRUCTURE_PASS_ANALYSIS_REVIEW_REQUIRED" if not errors
                  else "STRUCTURE_BLOCKED",
        "row_count": total,
        "present_required_columns": [x for x in fields if x in inspected],
        "missing_counts": missing,
        "special_code_counts": special,
        "errors": errors,
        "raw_rows_exported": False,
        "original_file_modified": False,
        "survey_design": "RESEARCHER_REVIEW_REQUIRED",
        "analysis_approved": False,
        "public_release": "BLOCKED",
    }
