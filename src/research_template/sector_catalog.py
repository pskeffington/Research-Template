"""Read-only cancer-research sector catalog: scientific planning, never execution.

Catalog items are inspired by *public* institutional research themes but are
independent; they do not imply institutional partnership or authorization.
"""

from __future__ import annotations

import json
import re
from importlib import resources

ID = re.compile(r"(CPS|SGN|ICI|TEC)-[0-9]{2}\Z")
PROGRAMS = frozenset({"CPS", "SGN", "ICI", "TEC"})
STATUS = "PRESTAGED_METADATA_ONLY"


class CatalogError(ValueError):
    """Invalid or unsupported reference catalog contract."""


def read_sector_catalog() -> dict:
    item = resources.files("research_template").joinpath("sector_catalog.json")
    catalog = json.loads(item.read_text(encoding="utf-8"))
    programs = catalog.get("programs", [])
    items = catalog.get("deployables", [])
    if (catalog.get("schema_version") != 1
            or catalog.get("institutional_approval") != "NOT_CLAIMED"
            or catalog.get("scientific_release") != "BLOCKED"
            or catalog.get("data_download") != "DISABLED"
            or not isinstance(programs, list)
            or not isinstance(items, list)
            or {v.get("id") for v in programs} != PROGRAMS
            or len({x.get("id") for x in items}) != len(items)):
        raise CatalogError("Invalid or unsafe research-sector catalog")
    for sector in programs:
        if not sector.get("url", "").startswith("https://"):
            raise CatalogError("Missing official program reference")
    for candidate in items:
        if (not ID.fullmatch(candidate.get("id", ""))
                or candidate.get("program_id") not in PROGRAMS
                or not candidate["id"].startswith(candidate["program_id"] + "-")
                or candidate.get("state") != STATUS
                or candidate.get("automatic_analysis") != "DISABLED"
                or candidate.get("user_data_access") != "NOT_GRANTED"
                or candidate.get("publication") != "BLOCKED"
                or candidate.get("priority") not in ("P1", "P2", "P3")
                or not all(candidate.get(key, "").startswith("https://")
                           for key in ("dictionary_url", "method_source_url",
                                       "data_access_url"))):
            raise CatalogError("Unverified or implicitly authorized sector deployment")
    return catalog


def list_sectors(program_id: str | None = None) -> dict:
    catalog = read_sector_catalog()
    if program_id is not None and program_id not in PROGRAMS:
        raise CatalogError("Unknown cancer research program")
    deployables = [
        {
            "id": item["id"],
            "program_id": item["program_id"],
            "title": item["title"],
            "source_name": item["source_name"],
            "priority": item["priority"],
            "state": item["state"],
        }
        for item in catalog["deployables"]
        if program_id is None or item["program_id"] == program_id
    ]
    return {
        "status": "DISCOVERY_ONLY",
        "research_programs": [
            p for p in catalog["programs"]
            if program_id is None or p["id"] == program_id
        ],
        "count": len(deployables),
        "deployables": deployables,
        "data_download": "DISABLED",
        "analysis_execution": "DISABLED",
        "public_release": "BLOCKED",
    }


def plan_sector(deployable_id: str) -> dict:
    catalog = read_sector_catalog()
    matches = [v for v in catalog["deployables"] if v["id"] == deployable_id]
    if len(matches) != 1:
        raise CatalogError("Unknown or unimplemented deployable identifier")
    item = matches[0]
    program = next(v for v in catalog["programs"] if v["id"] == item["program_id"])
    return {
        "status": "PRESTAGED_REFERENCE_PLAN_ONLY",
        "deployable": item,
        "program_reference": program,
        "mandatory_review": [
            "Confirm source dictionary version and user access rights",
            "Confirm observation unit, eligibility and allowed joins",
            "Validate input types, variables, units and missingness",
            "Choose scientific design and justify statistical assumptions",
            "Assess confounding, dependence, leakage and uncertainty",
            "Approve candidate figures, provenance and privacy",
            "Independently authorize publication and any clinical claims",
        ],
        "input_data_loaded": False,
        "analysis_execution": "DISABLED",
        "public_release": "BLOCKED",
    }
