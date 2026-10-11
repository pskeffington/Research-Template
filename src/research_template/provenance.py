"""Deterministic record of inputs, outputs, parameters and software provenance."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def current_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def version_of(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def create_manifest(
    root: Path, files: list[Path], *, seed: int, purpose: str, classification: str = "synthetic"
) -> dict:
    """Generate an evidence manifest; callers must keep private paths out of public exports."""
    if classification != "synthetic":
        raise ValueError("Default public manifest is restricted to synthetic demo artifacts")
    root = root.resolve()
    artifacts = []
    for file in files:
        path = file.resolve()
        if not path.is_file() or not path.is_relative_to(root):
            raise ValueError("Artifacts must exist and lie within the selected output directory")
        artifacts.append({"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)})
    return {
        "schema_version": "1.0",
        "status": "DEMONSTRATION_ONLY",
        "scientific_release": "BLOCKED_UNTIL_REVIEWED",
        "purpose": purpose,
        "classification": classification,
        "seed": seed,
        "code_commit": current_commit(),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "packages": {p: version_of(p) for p in ("research-template-kit", "matplotlib", "scikit-learn", "torch")},
        },
        "artifacts": artifacts,
        "nondeterminism_note": "A seed alone does not guarantee cross-platform deterministic results.",
    }


def save_json(path: Path, data: dict | list) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return path
