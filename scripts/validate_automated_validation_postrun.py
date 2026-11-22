#!/usr/bin/env python3
"""Reproducible read-only audit of the final automated validation outputs."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_MODULES = [
    "tests.test_atlas_statistics_contract", "tests.test_time_bounds",
    "tests.test_interval_period_stats", "tests.test_publication_pilot_v2",
    "tests.test_provenance_counts", "tests.test_statistical_variants",
    "tests.test_readiness_snapshot_adapter", "tests.test_temperature_reference_validation",
    "tests.test_publication_v3_exports", "tests.test_historical_conflict_epoch_review",
    "tests.test_current_gw3000_e4", "tests.test_epoch_registry_and_monthly_results",
    "tests.test_three_unmatched_temperature_review", "tests.test_humidity_reference_validation",
    "tests.test_pressure_reference_validation", "tests.test_wind_reference_validation",
    "tests.test_automated_candidate_outcomes", "tests.test_atlas_preview_http",
    "tests.test_interval_weighted_variants",
]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def systemd_properties(unit: str) -> dict[str, str]:
    raw = subprocess.run(["systemctl", "show", unit, "--no-pager"], check=True,
                         text=True, stdout=subprocess.PIPE).stdout
    result = {}
    for line in raw.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def main() -> int:
    run = load("AUTOMATED_VALIDATION_RUN.json")
    candidate_doc = load("MONTHLY_PUBLICATION_CANDIDATES.json")
    evidence = load("MONTHLY_VALIDATION_EVIDENCE.json")
    manifest = load("data/STATISTICAL_VARIANTS_MANIFEST.json")
    interval_manifest = load("data/INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_MANIFEST.json")
    matrix = load("data/PUBLICATION_READINESS_DECISIONS.json")
    v3 = load("STATISTICAL_PUBLICATION_DECISIONS_V3.json")

    with (ROOT / "data/PUBLICATION_READINESS_DECISIONS.csv").open(newline="", encoding="utf-8") as f:
        decisions = list(csv.DictReader(f))
    with (ROOT / "data/INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_MONTHLY.csv").open(newline="", encoding="utf-8") as f:
        monthly_intervals = {(r["period"], r["variable"], r["variant"]): r for r in csv.DictReader(f)}
    with (ROOT / "data/INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_ANNUAL.csv").open(newline="", encoding="utf-8") as f:
        annual_intervals = {(r["period"], r["variable"], r["variant"]): r for r in csv.DictReader(f)}
    candidates = {(r["period"], r["variable"]) for r in candidate_doc["candidates"]}

    interval_rows_checked = 0
    for row in decisions:
        if row["statistic"] not in {"MEAN", "EXTREMA"}:
            continue
        variant = "B_DOCUMENTED_SOURCE_AND_RECOVERY" if (
            row["scope"] == "MONTHLY" and row["statistic"] == "MEAN"
            and (row["period"], row["variable"]) in candidates
        ) else "E_FULL_CURRENT_ARCHIVE"
        source = monthly_intervals if row["scope"] == "MONTHLY" else annual_intervals
        interval = source[(row["period"], row["variable"], variant)]
        temporal = json.loads(row["interval_coverage"])
        if temporal["variant"] != variant:
            raise AssertionError(f"wrong interval variant for {row['period']} {row['variable']} {row['statistic']}")
        if abs(float(temporal["safe_time_coverage"]) - float(interval["time_coverage"])) > 1e-12:
            raise AssertionError(f"interval coverage mismatch for {row['period']} {row['variable']} {row['statistic']}")
        if float(temporal["safe_time_coverage"]) > 1.0:
            raise AssertionError("interval coverage exceeds one")
        interval_rows_checked += 1

    e4 = [r for r in decisions if r["publication_readiness"] == "BLOCKED_E4"]
    if not e4 or any(r["variable"] not in {"rain", "rainRate"} for r in e4):
        raise AssertionError("E4 blocker escaped rain/rainRate")
    protected = [r for r in decisions if r["scope"] == "MONTHLY" and r["period"] in {"2018-01", "2018-02", "2018-03"}]
    if not protected or any(r["publication_readiness"] != "PROTECTED" for r in protected if r["variable"] not in {"rain", "rainRate"}):
        raise AssertionError("Q1 2018 protection invariant failed")
    diagnostic = [r for r in decisions if r["period"].startswith("2021") and r["variable"] not in {"rain", "rainRate"}]
    if not diagnostic or any(r["publication_readiness"] != "DIAGNOSTIC_ONLY" for r in diagnostic):
        raise AssertionError("2021 diagnostic-only invariant failed")
    if len(candidate_doc["candidates"]) != 248 or len(evidence["records"]) != 248:
        raise AssertionError("priority candidate/evidence record count mismatch")
    if len(decisions) != matrix["matrix_rows"] or len(v3["decisions"]) != len(decisions):
        raise AssertionError("readiness/V3 decision row count mismatch")
    if matrix["publication_authorized"] or v3["publication_authorized"] or run["publication_authorized"]:
        raise AssertionError("publication authorization must remain false")
    if manifest["readiness_snapshot_alignment"]["status"] != "MATCH":
        raise AssertionError("daily readiness and statistical variants do not share a snapshot")

    sync_timer = systemd_properties("loucka-archive-sync.timer")
    sync_service = systemd_properties("loucka-archive-sync.service")
    sync_health_path = Path("/var/lib/loucka-archive-sync/health.json")
    sync_health = json.loads(sync_health_path.read_text()) if sync_health_path.exists() else None
    if sync_timer.get("ActiveState") != "active" or sync_timer.get("UnitFileState") != "enabled":
        raise AssertionError("continuous archive sync timer is not active and enabled")
    if sync_service.get("Result") != "success" or sync_service.get("ExecMainStatus") != "0":
        raise AssertionError("most recent continuous archive sync service run did not succeed")
    if not sync_health or sync_health.get("status") != "HEALTHY":
        raise AssertionError("latest continuous archive sync health file is absent or unhealthy")

    command = [sys.executable, "-m", "unittest", *TEST_MODULES, "-q"]
    proc = subprocess.run(command, cwd=ROOT, env={**__import__("os").environ, "PYTHONPATH": "src"},
                          text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.returncode:
        raise RuntimeError(proc.stdout)
    test_line = next((line.strip() for line in proc.stdout.splitlines() if line.startswith("Ran ")), "")
    test_count = int(test_line.split()[1]) if test_line else None
    if test_count is None:
        raise RuntimeError("unittest output did not contain a test count")

    doc = {
        "schema": "loucka-automated-validation-postrun-audit-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "snapshot_id": run["snapshot_id"],
        "pipeline_stages_passed": sum(s["status"] == "PASS" for s in run["stages"]),
        "priority_candidates": len(candidate_doc["candidates"]),
        "candidate_evidence_records": len(evidence["records"]),
        "readiness_rows": len(decisions),
        "interval_mean_extrema_rows_checked": interval_rows_checked,
        "interval_source_hashes": {
            "monthly": sha(ROOT / "data/INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_MONTHLY.csv"),
            "annual": sha(ROOT / "data/INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_ANNUAL.csv"),
        },
        "interval_manifest_snapshot_id": interval_manifest["snapshot_sha256"],
        "e4_blocked_rows": len(e4),
        "e4_blocked_variables": sorted({r["variable"] for r in e4}),
        "non_rain_e4_blocked_rows": 0,
        "q1_2018_non_rain_rows_protected": sum(r["publication_readiness"] == "PROTECTED" for r in protected if r["variable"] not in {"rain", "rainRate"}),
        "2021_non_rain_rows_diagnostic_only": len(diagnostic),
        "live_sync": {
            "timer_active": sync_timer.get("ActiveState"),
            "timer_enabled": sync_timer.get("UnitFileState"),
            "last_trigger_local": sync_timer.get("LastTriggerUSec"),
            "service_result": sync_service.get("Result"),
            "service_exit_status": sync_service.get("ExecMainStatus"),
            "health_checked_utc": sync_health["checked_utc"],
            "health_status": sync_health["status"],
            "sync_lag_seconds": sync_health["sync_lag_seconds"],
            "missing_current_source_rows": sync_health["missing_current_source_rows"],
            "conflict_count": sync_health["conflict_count"],
            "source_max_timestamp": sync_health["source_max_timestamp"],
            "target_max_timestamp": sync_health["target_max_timestamp"],
        },
        "tests": {"command": command, "count": test_count, "status": "PASS", "output": proc.stdout.strip()},
        "publication_authorized": False,
        "historical_database_writes": run["database_write_performed"],
        "deployment_performed": run["deployment_performed"],
        "checks": {
            "candidate_evidence_complete": True,
            "readiness_variant_interval_coverage_matches_sidecars": True,
            "interval_coverage_never_exceeds_one": True,
            "e4_isolated_to_rain_fields": True,
            "q1_2018_protected": True,
            "2021_diagnostic_only": True,
            "publication_disabled": True,
            "snapshot_alignment": "MATCH",
            "continuous_archive_sync_healthy": True,
        },
    }
    (ROOT / "POST_PIPELINE_VALIDATION_AUDIT.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "snapshot_id": doc["snapshot_id"], "tests": test_count,
                      "interval_rows_checked": interval_rows_checked, "e4_rows": len(e4),
                      "non_rain_e4_rows": 0, "publication_authorized": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
