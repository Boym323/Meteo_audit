#!/usr/bin/env python3
"""Build an availability-based, non-certifying 77-field x year readiness matrix."""
import csv, json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/2026-11-13-annual-archive-field-availability-2009-2026.json"
REGISTRY = ROOT / "config/active_proposal_registry.json"
OUT_CSV = ROOT / "reports/2026-11-13-readiness-77-fields-expanded.csv"
OUT_JSON = ROOT / "reports/2026-11-13-readiness-77-fields-expanded.json"
OUT_MD = ROOT / "reports/2026-11-13-readiness-77-fields-expanded.md"

src = json.loads(SOURCE.read_text())
reg = json.loads(REGISTRY.read_text())
years = [int(y) for y in src["years"]]
records = {(int(x["year"]), x["variable"]): x for x in src["records"]}
variables = sorted({x["variable"] for x in src["records"]})
assert len(variables) == src["fields_count"] == 77
assert len(records) == len(years) * len(variables)

proposals = defaultdict(Counter)
for pkg in reg["packages"]:
    if pkg["status"] != "ACTIVE":
        continue
    for op in pkg.get("operation_keys", []):
        year = datetime.fromtimestamp(int(op["timestamp"]), timezone.utc).year
        key = (year, op["variable"])
        proposals[key]["operations"] += 1
        proposals[key][pkg["classification"]] += 1

out = []
for year in years:
    for variable in variables:
        r = records[(year, variable)]
        n = int(r["archive_rows"]); nonnull = int(r["nonnull_rows"]); null = int(r["null_rows"])
        counts = proposals[(year, variable)]
        issue = ""
        if year == 2014 and variable == "outTemp":
            issue = "SOURCE_SENSOR_STUCK_SUSPECTED; 1071 source-only zero values; one current target conflict"
        if year == 2020 and variable == "outTemp":
            issue = f"{counts['operations']} active unapproved operations; four source-only outTemp values in current v2 proposal; 2020-02-22 source/local conflict held REVIEW_REQUIRED; RH-conflict values excluded"
        if year == 2018:
            protection = "CONTAINS_Q1_2018_INTERIM"
        elif year == 2021:
            protection = "DIAGNOSTIC_ONLY"
        else:
            protection = "NONE"
        readiness = "NOT_AVAILABLE" if nonnull == 0 else "REVIEW_REQUIRED"
        out.append({
            "utc_year": year,
            "variable": variable,
            "readiness": readiness,
            "archive_rows": n,
            "nonnull_rows": nonnull,
            "null_rows": null,
            "null_share": round(null / n, 8) if n else None,
            "archive_value_state": "NO_NONNULL_ARCHIVE_VALUES" if nonnull == 0 else ("ALL_ROWS_NONNULL" if null == 0 else "PARTIAL_NULL"),
            "active_unapproved_proposal_operations": counts["operations"],
            "active_restored_operations": counts["RESTORED"],
            "active_estimated_operations": counts["ESTIMATED"],
            "conditional_candidate_count": None,
            "unresolvable_gap_count": None,
            "chart_impact": "REVIEW_REQUIRED" if nonnull else "NOT_AVAILABLE",
            "daily_annual_statistics_impact": "REVIEW_REQUIRED" if nonnull else "NOT_AVAILABLE",
            "records_impact": "REVIEW_REQUIRED" if nonnull else "NOT_AVAILABLE",
            "atlas_suitability": "REVIEW_REQUIRED" if nonnull else "NOT_AVAILABLE",
            "protection_status": protection,
            "known_issue_tag": issue,
            "reason": "Availability snapshot only; no annual physical/source-quality certification. NOT_AVAILABLE denotes no non-NULL value in this archive-year, not proof that a sensor was absent.",
            "evidence_refs": "reports/2026-11-13-annual-archive-field-availability-2009-2026.csv; reports/2026-11-13-monthly-archive-field-availability-2009-2026.csv",
            "temporal_denominator": "archive rows only; expected measurement slots and sensor operational time are not established",
            "snapshot_period": src["period"],
        })

fields = list(out[0])
with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(out)

readiness_counts = Counter(x["readiness"] for x in out)
summary = {
    "schema": "provisional-availability-readiness-77-fields-v1",
    "as_of_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    "database": src["database"],
    "years": years,
    "variables": variables,
    "variable_count": len(variables),
    "matrix_cells": len(out),
    "annual_archive_row_counts": src["year_row_counts"],
    "readiness_counts": dict(readiness_counts),
    "active_proposal_operations_in_matrix": sum(x["active_unapproved_proposal_operations"] for x in out),
    "proposal_status": "ACTIVE_LOCAL_VALIDATION_ONLY; none approved, staged, MCP dry-run or applied",
    "conditional_candidate_count": None,
    "unresolvable_gap_count": None,
    "limitations": [
        "This is an availability-based screen, not complete per-record quality review or readiness sign-off.",
        "No cell is READY or READY_WITH_LIMITATIONS because physical, source and temporal-denominator evidence is not complete for all 77 fields and years.",
        "NOT_AVAILABLE means no non-NULL value in the archive-year; it does not prove the sensor was absent.",
        "Year 2021 remains diagnostic-only; Q1 2018 remains interim and protected."
    ],
    "source_file": str(SOURCE.relative_to(ROOT)),
    "records": out,
}
OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
summary_lines = [
    "# Expanded archive readiness baseline — 77 numeric fields",
    "",
    "**Provisional availability screen only; not publication sign-off.**",
    "",
    f"Matrix: {len(years)} UTC years × {len(variables)} fields = {len(out)} cells.",
    f"Readiness states: {dict(readiness_counts)}.",
    f"Active unapproved proposal operations represented: {summary['active_proposal_operations_in_matrix']}.",
    "",
    "All populated cells remain REVIEW_REQUIRED because per-year sensor lineage, physical QC and operational-slot denominators are not certified for all channels. NOT_AVAILABLE means no non-NULL archive value for that field-year, not proof that the physical sensor was absent. Conditional-candidate and unresolved-gap counts are null because those cannot be derived from availability alone.",
    "",
    "2021 is diagnostic-only. Q1 2018 remains interim/protected. Active proposal counts are unapproved local proposals, not recommendations for immediate application.",
    "",
    "Machine-readable row-level matrix: 2026-11-13-readiness-77-fields-expanded.csv and .json.",
]
OUT_MD.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
print(json.dumps({"cells":len(out),"fields":len(variables),"years":len(years),"readiness_counts":dict(readiness_counts),"active_proposal_operations":summary["active_proposal_operations_in_matrix"]}))
