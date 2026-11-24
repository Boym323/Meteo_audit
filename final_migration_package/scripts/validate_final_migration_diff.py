#!/usr/bin/env python3
"""Independent integrity check for the captured live migration manifest."""
from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
EXPECTED_FIELDS = {
    "outTemp": 47, "outHumidity": 20422, "rain": 2201, "rainRate": 59595,
    "extraTemp1": 2, "extraTemp2": 14, "soilTemp1": 13, "soilTemp5": 10,
    "soilTemp6": 21,
}
CLEAR_BATCHES = {"qc-extra-temp-outliers-20261123-v1", "qc-soil-negative-outliers-20261123-v1"}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    summary = json.loads((ROOT / "FINAL_MIGRATION_DIFF_SUMMARY.json").read_text())
    manifest = json.loads((REPO / "FINAL_MIGRATION_MANIFEST.json").read_text())
    payload = ROOT / summary["operations_file"]
    errors = []
    if sha(payload) != summary["operations_sha256"]:
        errors.append("compressed operation diff SHA-256 mismatch")
    types, fields, units, seen = Counter(), Counter(), Counter(), set()
    clear_rows, audit_mismatches, missing_source = [], 0, 0
    inserts_with_events = 0
    with gzip.open(payload, "rt", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            row = json.loads(line)
            key = (int(row["dateTime"]), row["variable"])
            if key in seen:
                errors.append(f"duplicate operation {key}")
            seen.add(key)
            units[str(row.get("usUnits"))] += 1
            if row.get("usUnits") != 16:
                errors.append(f"unexpected usUnits for migration row {key}: {row.get('usUnits')}")
            if row.get("production_approval_status") != "NOT_APPROVED":
                errors.append(f"production approval not fail-closed at {key}")
            types[row["operation_type"]] += 1
            if row["operation_type"] == "INSERT":
                full = row.get("full_row")
                if not isinstance(full, dict) or len(full) != 80 or int(full["dateTime"]) != key[0]:
                    errors.append(f"invalid complete row payload at {key}")
                if row.get("usUnits") != full.get("usUnits"):
                    errors.append(f"insert usUnits mismatch at {key}")
                inserts_with_events += bool(row.get("related_audit_events"))
            else:
                fields[row["variable"]] += 1
                if row.get("audit_event_id") is None:
                    errors.append(f"missing audit event at {key}")
                if row.get("audit_state_matches_reconstruction") is False:
                    audit_mismatches += 1
                if not row.get("source_database"):
                    missing_source += 1
                if row.get("operation_type") == "NULL_CLEAR" and (row.get("audit_event") or {}).get("batch_key") in CLEAR_BATCHES:
                    clear_rows.append(row)
                    event = row["audit_event"]
                    if not (event["state"] == "applied" and event["old_value"] == row["production_value"] and event["new_value"] is None and row["reconstruction_value"] is None):
                        errors.append(f"new NULL_CLEAR audit mismatch at {key}")
    if types != Counter({"INSERT": 10399, "NULL_FILL": 12671, "VALUE_REPLACE": 68759, "NULL_CLEAR": 895}):
        errors.append(f"operation type counts mismatch: {dict(types)}")
    if dict(fields) != EXPECTED_FIELDS:
        errors.append(f"field counts mismatch: {dict(fields)}")
    if len(seen) != 92724:
        errors.append(f"operation key count mismatch: {len(seen)}")
    if len(clear_rows) != 60:
        errors.append(f"new temperature NULL_CLEAR count mismatch: {len(clear_rows)}")
    clear_fields = Counter(row["variable"] for row in clear_rows)
    if clear_fields != Counter({"extraTemp1": 2, "extraTemp2": 14, "soilTemp1": 13, "soilTemp5": 10, "soilTemp6": 21}):
        errors.append(f"new temperature NULL_CLEAR field counts mismatch: {dict(clear_fields)}")
    if missing_source != 0:
        errors.append(f"field operations without source claim: {missing_source}")
    if inserts_with_events != 10399:
        errors.append(f"INSERT rows without related audit events: {10399-inserts_with_events}")
    if audit_mismatches != summary["field_operations_latest_audit_state_mismatch"]:
        errors.append("latest audit reconciliation mismatch count differs from summary")
    if summary["validation"] != "PASS" or manifest["hashes"]["operations_sha256"] != summary["operations_sha256"]:
        errors.append("manifest/summary validation status or hash mismatch")
    result = {
        "result": "PASS" if not errors else "FAIL", "operations": len(seen),
        "operation_types": dict(types), "field_counts": dict(fields),
        "usUnits_counts": dict(units),
        "verified_new_temperature_null_clears": len(clear_rows),
        "related_audit_events_for_inserts": inserts_with_events,
        "latest_audit_state_mismatches_review_required": audit_mismatches,
        "errors": errors,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
