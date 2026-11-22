#!/usr/bin/env python3
"""Clean-extract validation of v3 and all active package validators/simulators."""
import hashlib, json, subprocess, sys, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "loucka_historical_audit_and_priority_corrections_v3.zip"
with zipfile.ZipFile(ZIP) as z:
    names = set(z.namelist())
    manifest = json.loads(z.read("MANIFEST.json"))
    assert manifest["main_report_count"] == 18
    assert len(manifest["contents"]) == manifest["file_count_excluding_manifest"]
    inventory = json.loads(z.read("reports/required-report-inventory.json"))
    assert inventory["required_report_count"] == 18
    assert all("reports/" + x["report"] in names for x in inventory["reports"])
    assert all(x in names for x in ["MANIFEST.json", "PRE_APPLICATION_CHECKLIST.md", "config/active_proposal_registry.json"])
    for item in manifest["contents"]:
        raw = z.read(item["path"])
        assert len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"], item["path"]
    registry = json.loads(z.read("config/active_proposal_registry.json"))
    for item in registry["packages"]:
        if item["status"] == "ACTIVE":
            for suffix in ("corrections.json", "manifest.json", "weather_mcp_batches.json"):
                assert f"{item['path']}/{suffix}" in names, (item["package_id"], suffix)
            assert (f"{item['path']}/simulation.json" in names or
                    f"{item['path']}/offline_simulation.json" in names), item["package_id"]

with tempfile.TemporaryDirectory(prefix="loucka-v3-clean-") as td:
    with zipfile.ZipFile(ZIP) as z: z.extractall(td)
    base = Path(td)
    commands = [
        [sys.executable, "scripts/validate_active_proposal_deduplication.py"],
        [sys.executable, "scripts/validate_source_first_active_proposals.py"],
        [sys.executable, "proposals/estimated_short_temperature_gaps_v2/validate.py"],
        [sys.executable, "proposals/restored_source_only_2013_july_pilot/validate.py"],
        [sys.executable, "scripts/validate_2018_dec31_restored_update_pilot.py"],
        [sys.executable, "proposals/restored_source_only_2019_may30_outtemp/validate.py"],
        [sys.executable, "proposals/restored_source_only_2020_isolated_outtemp/validate.py"],
        [sys.executable, "proposals/restored_source_only_rows_v2/validate.py"],
        [sys.executable, "scripts/validate_final_report_bundle.py"],
        [sys.executable, "proposals/restored_source_only_2013_july_pilot/simulate.py"],
        [sys.executable, "proposals/restored_source_only_2019_may30_outtemp/simulate.py"],
        [sys.executable, "proposals/restored_source_only_2020_isolated_outtemp/simulate.py"],
    ]
    results = []
    for command in commands:
        proc = subprocess.run(command, cwd=base, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        results.append({"command": " ".join(command), "returncode": proc.returncode, "output": proc.stdout[-4000:]})
        if proc.returncode:
            print(json.dumps({"status":"FAIL", "file_count":len(names), "failed":results[-1]}, indent=2))
            raise SystemExit(proc.returncode)
    # Re-run package integrity checks after simulators regenerated local results.
    post_simulation_checks = [
        [sys.executable, "proposals/restored_source_only_2013_july_pilot/validate.py"],
        [sys.executable, "proposals/restored_source_only_2019_may30_outtemp/validate.py"],
        [sys.executable, "proposals/restored_source_only_2020_isolated_outtemp/validate.py"],
    ]
    for command in post_simulation_checks:
        proc = subprocess.run(command, cwd=base, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        results.append({"command": " ".join(command) + " (post-simulation)", "returncode": proc.returncode, "output": proc.stdout[-4000:]})
        if proc.returncode:
            print(json.dumps({"status":"FAIL", "file_count":len(names), "failed":results[-1]}, indent=2))
            raise SystemExit(proc.returncode)
    # The P3 package validator checks the preserved v2.1 simulation result, its
    # 21-operation manifest and uncertainty contract. It deliberately avoids the
    # older v2 simulator, which expects 24 now-superseded operations.
    result = {"status":"PASS", "archive":ZIP.name, "members":len(names), "manifest_files_verified":len(manifest["contents"]),
              "clean_extraction":True, "active_package_count":len([x for x in registry["packages"] if x["status"]=="ACTIVE"]),
              "active_operations":registry["active_operation_count"], "commands":results,
              "local_simulation_scope":"offline only; no DB connection, MCP dry-run, staging or application"}
    out = ROOT / "reports/2026-11-13-v3-clean-extract-validation.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="commands"}, indent=2))
