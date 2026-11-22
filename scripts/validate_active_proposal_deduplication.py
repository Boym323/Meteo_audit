#!/usr/bin/env python3
"""Validate active proposal registry, operation uniqueness and insert dependencies. Local files only."""
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / "config/active_proposal_registry.json").read_text())
assert registry["database_mode"] == "READ_ONLY" and not registry["staging"] and not registry["application_performed"]
active = [x for x in registry["packages"] if x["status"] == "ACTIVE"]
keys, inserts = defaultdict(list), defaultdict(list)
observed_ops = 0
package_results = []
for package in active:
    base = ROOT / package["path"]
    ops = json.loads((base / "corrections.json").read_text())
    assert len(ops) == package["field_operations"], package["package_id"]
    for i, row in enumerate(ops):
        ts, variable, operation = int(row["timestamp"]), row["variable"], row["operation"]
        year = datetime.fromtimestamp(ts, timezone.utc).year
        reason = row.get('reason','')
        assert ('RESTORED' in reason or 'ESTIMATED' in reason), (package['package_id'], row)
        assert ('provenance' in reason.lower() or 'uncertainty' in reason.lower()), (package['package_id'], reason)
        assert year != 2021 and not (year == 2018 and datetime.fromtimestamp(ts, timezone.utc).month <= 3), row
        keys[(ts, variable)].append((package["package_id"], i, operation))
        if operation == "insert": inserts[ts].append((package["package_id"], i))
        observed_ops += 1
    package_results.append({"package_id": package["package_id"], "operations": len(ops), "expected": package["field_operations"]})

duplicate_field_targets = {str(k): v for k, v in keys.items() if len(v) > 1}
duplicate_row_inserts = {str(k): v for k, v in inserts.items() if len(v) > 1}
assert not duplicate_field_targets, duplicate_field_targets
assert not duplicate_row_inserts, duplicate_row_inserts

# The 2013 pilot inserts a row and then applies later variables to that same row;
# preserve its declared order and distinguish the physical insert from updates.
pilot = next(x for x in active if x["package_id"] == "restored-source-only-2013-july-pilot")
ops = json.loads((ROOT / pilot["path"] / "corrections.json").read_text())
by_ts = defaultdict(list)
for i, row in enumerate(ops): by_ts[int(row["timestamp"])].append((i, row["operation"], row["variable"]))
for ts, sequence in by_ts.items():
    types = [x[1] for x in sequence]
    if "update" in types:
        # Three timestamps create a new row then fill outHumidity; the 22:00
        # boundary timestamp updates a row present in the validated snapshot.
        if ts == 1373320800:
            assert types == ["update"] and sequence[0][2] == "outTemp", (ts, sequence)
        else:
            assert "insert" in types and types.index("insert") < types.index("update"), (ts, sequence)

assert observed_ops == registry["active_operation_count"]
assert len(inserts) == registry["active_physical_new_database_rows_if_applied"]
assert sum(1 for v in keys.values() for x in v if x[2] == "update") == registry["active_update_operations"]
assert registry["active_unique_timestamps"] == len({int(x["timestamp"]) for pkg in active for x in json.loads((ROOT / pkg["path"] / "corrections.json").read_text())})
for package in active:
    assert package["user_approval"] == "NOT_APPROVED"
    assert package["actual_weather_mcp_dry_run"] == "NOT_RUN"
    assert package["actual_application"] == "NOT_APPLIED"
assert sum(x["field_operations"] for x in active if x["classification"] == "RESTORED") == registry["active_restored_operations"]
assert sum(x["field_operations"] for x in active if x["classification"] == "ESTIMATED") == registry["active_estimated_operations"]
result = {"status":"PASS", "active_packages":len(active), "operations":observed_ops,
          "unique_timestamp_variable_targets":len(keys), "duplicate_field_targets":0,
          "duplicate_physical_inserts":0, "q1_2018_proposals":0, "year_2021_proposals":0,
          "2013_insert_before_dependent_updates":"PASS", "packages":package_results,
          "database_access":"NONE", "database_writes":0, "staging":False}
(ROOT / "data/active_proposal_deduplication_v3.json").write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps(result))
