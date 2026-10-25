#!/usr/bin/env python3
"""Re-run non-network local validation and fail-closed behavior checks.

No Git mutations, upstream requests or downloads; this never runs a real CLI.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def run(args, expectation, path):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    process = subprocess.run([sys.executable, *args], cwd=HERE, env=env,
                             capture_output=True, text=True, timeout=120, check=False)
    passed = process.returncode == expectation
    return {"status": "PASS" if passed else "FAIL", "return_code": process.returncode,
            "expected_return_code": expectation,
            "last_stdout": process.stdout.strip().splitlines()[-3:],
            "last_stderr": process.stderr.strip().splitlines()[-3:],
            "description": path}


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    checks = {}
    checks["unittest"] = run(["-m", "unittest", "discover", "-s", "tests", "-q"], 0, "independent unit tests")
    checks["unittest_optimized"] = run(["-O", "-m", "unittest", "discover", "-s", "tests", "-q"],
                                         0, "optimized-Python unit tests")
    offline = RESULTS / "local_qa_reference"
    checks["offline_reference"] = run(["run_validation.py", "--offline", "--out", str(offline)],
                                       0, "independent oracle; engine must be SKIPPED")
    strict_offline = RESULTS / "local_qa_required"
    checks["strict_offline"] = run(["run_validation.py", "--offline", "--require-cli",
                                    "--out", str(strict_offline)], 2, "required engine not run")

    plan_dir = RESULTS / "local_qa_plan"
    checks["cli_plan_offline"] = run(["run_validation.py", "--plan-only", "--out", str(plan_dir)],
                                      0, "16-case CLI command contract audit; no engine execution")

    fake_dir = RESULTS / "local_qa_fake_bin"
    fake_dir.mkdir(parents=True, exist_ok=True)
    fake = fake_dir / "rustgis-cli"
    fake.write_text("#!/bin/sh\nexit 0\n", encoding="ascii")
    fake.chmod(0o700)
    fake_out = RESULTS / "local_qa_fake_run"
    checks["false_success_rejection"] = run(["run_validation.py", "--require-cli", "--cli",
                                               str(fake), "--out", str(fake_out)], 1,
                                              "zero-exit dummy CLI must fail when artifacts missing")

    reports = {}
    for name, path in [("offline", offline), ("strict", strict_offline), ("fake", fake_out)]:
        report_path = path / "validation_report.json"
        if report_path.is_file():
            entry = json.loads(report_path.read_text(encoding="utf-8"))
            reports[name] = {"reference": entry["reference"]["status"],
                             "engine": entry["engine_status"],
                             "check_outcomes": {x: sum(y["status"] == x for y in entry["engine_checks"].values())
                                                for x in ("PASS", "FAIL", "BLOCKED")}}
    plan_path = plan_dir / "validation_report.json"
    planned = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path.is_file() else {}
    plan = planned.get("engine_plan", {})
    checks["cli_plan_integrity"] = {
        "status": "PASS" if (plan.get("status") == "PASS" and plan.get("case_count") == 16
                           and planned.get("engine_status") == "SKIPPED"
                           and len(plan.get("argv", {})) == 16) else "FAIL",
        "description": "plan audit is complete, fully specified, and not counted as engine execution",
    }

    conditions = (reports.get("offline", {}).get("engine") == "SKIPPED"
                  and reports.get("offline", {}).get("reference") == "PASS"
                  and reports.get("strict", {}).get("engine") == "SKIPPED"
                  and reports.get("fake", {}).get("engine") == "FAIL")
    checks["report_status_integrity"] = {"status": "PASS" if conditions else "FAIL",
                                          "description": "explicit engine status never confused with oracle"}

    outcome = "PASS" if all(value["status"] == "PASS" for value in checks.values()) else "FAIL"
    output = {"kind": "local_non_network_qa", "version": "1.2.0",
              "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "overall": outcome, "rustgis_engine_executed": False,
              "git_commits_or_pushes": False, "checks": checks, "reports": reports}
    out = RESULTS / "local_qa_gate.json"
    out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Local QA: {outcome}, {sum(x['status']=='PASS' for x in checks.values())}/{len(checks)} gates")
    print(f"Engine execution: NOT PERFORMED; report: {out}")
    return 0 if outcome == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
