#!/usr/bin/env python3
"""Build a per-gap source-state disposition for the 44 >=24h gaps."""
import csv
import json
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AVAIL = ROOT / "data/long_gap_ge24h_per_archive_availability.json"
COPY = ROOT / "data/long_gap_source_copy_field_hashes.json"
EDGE = ROOT / "data/long_gap_eu_old_boundary_source_review.json"
JSON_OUT = ROOT / "data/long_gap_44_source_state_disposition.json"
CSV_OUT = ROOT / "reports/2026-11-13-long-gap-44-source-state-disposition.csv"
MD_OUT = ROOT / "reports/2026-11-13-long-gap-44-source-state-disposition.md"
ARCHIVES = ["loucka_reconstruction", "pocasi-loucka.eu", "pocasi-loucka.eu_GW1000", "pocasi-loucka.eu_old", "old_weewx", "weewx_WH1080"]
FIELDS = ["usUnits", "interval", "outTemp", "outHumidity", "rain", "rainRate", "windSpeed", "windDir", "windGust", "barometer"]
REGIONAL_BY_START = {
    "2016-01-18": {"station": "LuhaMet", "exact_pairs": 0, "interpretation": "No exact-time reference coverage; off-grid source phase remains unresolved."},
    "2017-05-12": {"station": "LuhaMet", "exact_pairs": 4601, "interpretation": "Regional references 5.5–25.5 C while source outTemp is zero-heavy; not local truth."},
    "2017-01-09": {"station": "LuhaMet", "exact_pairs": 2254, "interpretation": "Regional frost context; source outTemp plateau not a local truth series."},
}

def main():
    a = json.loads(AVAIL.read_text())
    copies = {int(x["gap_id"]): x["copy_comparison"] for x in json.loads(COPY.read_text())["gaps"]}
    edge = {int(x["gap_id"]): x for x in json.loads(EDGE.read_text())["cases"]}
    assert len(a["gaps"]) == 44
    out = []
    for g in a["gaps"]:
        gid = int(g["gap_id"])
        src = {x["source_database"]: x for x in g["source_availability"]}
        assert set(src) == set(ARCHIVES)
        n_old = int(src["old_weewx"]["source_rows"])
        n_wh = int(src["weewx_WH1080"]["source_rows"])
        assert n_old == n_wh
        c = copies.get(gid, {"rows": 0, "exact_timestamp_sequence": None, "fields": {}})
        field_exact = {f: bool(c["fields"][f]["exact_sequence_equal"]) for f in FIELDS} if c["rows"] else {}
        source_rows = {db: int(src[db]["source_rows"]) for db in ARCHIVES}
        total_sources = sum(source_rows.values())
        euold_case = edge.get(gid)
        if not total_sources:
            source_state = "NO_SOURCE_ROWS_IN_ANY_OF_SIX_ARCHIVES"
            candidate_disposition = "MISSING_CAUSE_UNRESOLVED"
        elif euold_case:
            source_state = "LEGACY_ROWS_PLUS_OFFGRID_BOUNDARY_KEYS"
            candidate_disposition = euold_case["classification"]
        elif c["rows"] and all(field_exact.values()):
            source_state = "LEGACY_ROW_KEYS_AND_CHECKED_FIELDS_AGREE"
            candidate_disposition = "REVIEW_REQUIRED_PROVENANCE_NOT_INDEPENDENT"
        else:
            source_state = "LEGACY_ROWS_FIELD_SPECIFIC_CONFLICT_OR_NULL_DIFFERENCE"
            candidate_disposition = "REVIEW_REQUIRED_FIELD_SPECIFIC_SOURCE_CONFLICT"
        wh_zero = int(src["weewx_WH1080"].get("outTemp_zero", 0) or 0)
        start_utc = datetime.datetime.fromtimestamp(g["start"], datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        end_utc = datetime.datetime.fromtimestamp(g["end"], datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        regional = REGIONAL_BY_START.get(start_utc[:10])
        row = {
            "gap_id": gid, "year": g["year"], "start_utc": start_utc, "end_utc": end_utc,
            "delta_seconds": g["delta"], "conditional_300s_slots_not_expected_count": max(0, g["delta"] // 300 - 1),
            **{f"{db}_rows": source_rows[db] for db in ARCHIVES},
            "source_row_total_across_archives_nonunique": total_sources,
            "legacy_row_counts_equal": n_old == n_wh,
            "legacy_exact_timestamp_sequence_equal": c["exact_timestamp_sequence"],
            "legacy_all_10_fields_equal": bool(c["rows"] and all(field_exact.values())) if c["rows"] else None,
            "legacy_fields_equal": json.dumps(field_exact, sort_keys=True) if field_exact else "{}",
            "weewx_WH1080_outTemp_zero_rows": wh_zero,
            "weewx_WH1080_outTemp_zero_share": round(wh_zero / n_wh, 6) if n_wh else None,
            "eu_old_boundary_offgrid_rows": 1 if euold_case else 0,
            "eu_old_nearest_endpoint_offset_seconds": euold_case["source_minus_endpoint_seconds"] if euold_case else None,
            "eu_old_endpoint_equal_fields": sum(euold_case["eu_old_endpoint_equal_fields"].values()) if euold_case else None,
            "eu_old_endpoint_conflicting_fields": ";".join(f for f,v in euold_case["eu_old_endpoint_equal_fields"].items() if not v) if euold_case else "",
            "regional_context": regional["station"] if regional else "not_queried_for_this_gap",
            "regional_exact_pairs": regional["exact_pairs"] if regional else None,
            "source_state": source_state,
            "cause": "UNRESOLVED: row presence/absence and source-copy differences do not distinguish downtime, historical cleaning, merge omission, transformation, or sensor fault",
            "candidate_disposition": candidate_disposition,
            "correction_proposal": "NONE",
            "protected_scope": "2021_DIAGNOSTIC_ONLY" if g["year"] == 2021 else ("2018_Q1_INTERIM_PROTECTED" if start_utc.startswith("2018-01") else "NORMAL"),
        }
        out.append(row)
    assert sum(x["source_state"] == "NO_SOURCE_ROWS_IN_ANY_OF_SIX_ARCHIVES" for x in out) == 9
    assert sum(x["eu_old_boundary_offgrid_rows"] for x in out) == 9
    assert sum(x["legacy_all_10_fields_equal"] is True for x in out) == 5
    assert all(x["correction_proposal"] == "NONE" for x in out)
    with CSV_OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    summary = {
        "schema": "long-gap-44-source-state-disposition-v1",
        "created_utc": "2026-11-13T19:17:15Z",
        "interval_count": 44,
        "source_rows_per_archive": {db: sum(x[f"{db}_rows"] for x in out) for db in ARCHIVES},
        "source_state_counts": {state: sum(x["source_state"] == state for x in out) for state in sorted({x["source_state"] for x in out})},
        "legacy_copy_exact_timestamps": sum(x["legacy_exact_timestamp_sequence_equal"] is True for x in out),
        "legacy_copy_all_10_fields_equal": sum(x["legacy_all_10_fields_equal"] is True for x in out),
        "eu_old_boundary_suspects": 9,
        "local_cause_resolved": 0,
        "correction_proposals": 0,
        "records": out,
        "interpretation": "This is an evidence/status partition, not a cause-of-gap determination or restoration approval. Conditional five-minute slots are arithmetic only, never expected/missing counts.",
    }
    JSON_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# Per-gap source-state disposition: 44 gaps >=24 hours",
        "",
        "All 44 exact reconstruction open intervals have per-archive READ-ONLY source coverage from all six archives. The CSV/JSON record source availability, old-copy field concordance, WH1080 zero share, known LuhaMet context and the nine eu_old boundary-near keys. `conditional_300s_slots_not_expected_count` is hypothetical cadence arithmetic only.",
        "",
        "## Current evidence partition",
        "",
        "- 9 gaps have no source rows in any of the six archives. Cause remains unknown; do not infer station downtime or historical deletion.",
        "- 35 gaps have source rows in both legacy archives, with identical timestamp sequences; only 5/35 match all ten checked field sequences. The copies are not independent votes.",
        "- 9 of those source-present gaps also contain one eu_old off-grid row only 59–120 seconds from a reconstruction endpoint. Eight exactly match that endpoint across ten fields; one differs in outTemp and remains review-only.",
        "- Zero-heavy historical temperature episodes are visible in the per-gap zero share and separately reviewed exact-time/regional context exists only for selected 2016/2017 cases. Regional weather is not local truth.",
        "- No cause is resolved for any gap and no correction proposal is created by this registry.",
        "",
        "This closes the per-gap source availability and evidence partition for the 44 longest gaps, not the broader B5 task over all gap events. Historical intentional removal, sensor faults, operational downtime and merge rules remain unresolved; other source-only and short-gap episodes remain under B5/C3. See `reports/2026-11-13-long-gap-per-archive-availability.md`, `reports/2026-11-13-long-gap-source-copy-field-concordance.md`, and `reports/2026-11-13-long-gap-eu_old-boundary-rows.md`.",
        "",
        "Reproduction: `python3 scripts/build_long_gap_44_disposition.py`.",
        "",
    ]
    MD_OUT.write_text("\n".join(lines))
    print(f"PASS: {len(out)} gap dispositions; no local cause resolved; source state counts={summary['source_state_counts']}")

if __name__ == "__main__":
    main()
