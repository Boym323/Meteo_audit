#!/usr/bin/env python3
"""Build the source catalog and dependency graph from the dated live inventory and audit evidence."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]

LINEAGE = {
    "pocasi-loucka.eu": {
        "role": "Current production archive and GW3000 sync source",
        "physical_origin": "Loučka station; owner reports this database was created in early 2026, assembled with historical rows from remaining archives, and receives current GW3000 gateway records.",
        "lineage_confidence": "OWNER_ATTESTED for broad origin; TECHNICALLY_OBSERVED for current rows and values",
        "dependency_ids": ["archive:pocasi-loucka.eu_old", "archive:old_weewx", "archive:weewx_WH1080", "archive:pocasi-loucka.eu_GW1000"],
        "caveats": ["Historical merge algorithm and per-field selection are unknown.", "Modern rows may be identical or near-identical copies of parallel gateway/station data; database identity does not prove independent sensors."],
    },
    "pocasi-loucka.eu_old": {
        "role": "Historical merged archive copy",
        "physical_origin": "Loučka historical archive; owner explicitly does not know the exact origin, migration date, or merge procedure.",
        "lineage_confidence": "UNKNOWN_ORIGIN; TECHNICALLY_OBSERVED snapshot",
        "dependency_ids": ["archive:old_weewx", "archive:weewx_WH1080"],
        "caveats": ["Likely contains merged/copied legacy data; source-selection rules and row-specific removal history are not reconstructable from this copy alone."],
    },
    "pocasi-loucka.eu_GW1000": {
        "role": "Archive snapshot from the production database operating with the GW1000 gateway",
        "physical_origin": "Loučka station/GW1000 path per owner; historical base expected to be shared with pocasi-loucka.eu.",
        "lineage_confidence": "OWNER_ATTESTED broad identity; TECHNICALLY_OBSERVED archived values",
        "dependency_ids": ["archive:pocasi-loucka.eu", "archive:pocasi-loucka.eu_old", "archive:old_weewx", "archive:weewx_WH1080"],
        "caveats": ["Snapshot is stale at its captured maximum; absence after that point is not an observed station outage.", "Parallel GW1000/GW3000 output is not assumed independent or interchangeable."],
    },
    "old_weewx": {
        "role": "Legacy WeeWX archive copy",
        "physical_origin": "Exact origin and role unknown to owner; historical station software/device lineage is not recorded.",
        "lineage_confidence": "UNKNOWN_ORIGIN; TECHNICALLY_OBSERVED snapshot",
        "dependency_ids": ["archive:pocasi-loucka.eu_old", "archive:pocasi-loucka.eu", "archive:pocasi-loucka.eu_GW1000", "archive:weewx_WH1080"],
        "caveats": ["Unit code 17; field-level values diverge from WH1080 and merged copies.", "Timestamp equality between legacy copies does not establish independent instruments."],
    },
    "weewx_WH1080": {
        "role": "Legacy archive named for WH1080/WeeWX",
        "physical_origin": "Name suggests a WH1080/WeeWX path, but owner does not know the exact source origin, device history, or merge path.",
        "lineage_confidence": "NAME_INFERRED plus UNKNOWN_ORIGIN; TECHNICALLY_OBSERVED snapshot",
        "dependency_ids": ["archive:pocasi-loucka.eu_old", "archive:pocasi-loucka.eu", "archive:pocasi-loucka.eu_GW1000", "archive:old_weewx"],
        "caveats": ["Unit code 17; source-copy field divergences are documented.", "Do not treat as an independent confirmation of old_weewx without a separate sensor lineage record."],
    },
    "loucka_reconstruction": {
        "role": "Reconstructed and currently synchronized target archive",
        "physical_origin": "Derived Loučka archive combining a common historical archive base with applied reconstructions/estimates and verified current-source inserts.",
        "lineage_confidence": "MIXED; row/field-level audit varies by period",
        "dependency_ids": ["archive:pocasi-loucka.eu", "archive:pocasi-loucka.eu_old", "archive:pocasi-loucka.eu_GW1000", "archive:old_weewx", "archive:weewx_WH1080", "evidence:reconstruction_changes", "evidence:applied_estimates", "evidence:archive_sync_audit", "evidence:archive_sync_verification"],
        "caveats": ["Target is not an independent measurement source.", "Applied restoration or estimate audit proves the submitted operation and current payload state, not ultimate original sensor provenance."],
    },
}


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> None:
    snapshot = load_json("data/HISTORICAL_SOURCE_INVENTORY_LIVE.json")
    old_inventory = load_json("source_inventory.json")
    reference_assets = load_json("data/reference-inventory/reference_source_catalog.json")
    evidence_tables = {r["table"]: r["row_count"] for r in snapshot["reconstruction_evidence_tables"]}
    sources = []
    for entry in snapshot["archives"]:
        db = entry["database"]
        lineage = LINEAGE[db]
        live = entry["archive"]
        old = next((x for x in old_inventory["archives"] if x["database"] == db), {})
        sources.append({
            "source_id": f"archive:{db}", "database": db, "table": "archive", "role": lineage["role"],
            "accessible_at_snapshot": entry["accessible"], "coverage_unix_utc": {"min": live["min_timestamp"], "max": live["max_timestamp"]},
            "coverage_utc": {"min": datetime.fromtimestamp(live["min_timestamp"], timezone.utc).isoformat().replace("+00:00", "Z"), "max": datetime.fromtimestamp(live["max_timestamp"], timezone.utc).isoformat().replace("+00:00", "Z")},
            "coverage_local_europe_prague": {"min": datetime.fromtimestamp(live["min_timestamp"], timezone.utc).astimezone(ZoneInfo("Europe/Prague")).isoformat(), "max": datetime.fromtimestamp(live["max_timestamp"], timezone.utc).astimezone(ZoneInfo("Europe/Prague")).isoformat()},
            "row_count": live["row_count"], "distinct_timestamps": live["distinct_timestamps"],
            "duplicate_timestamp_count": live["duplicate_timestamp_count"], "usUnits_distribution": live["usUnits_distribution"],
            "interval_minutes_distribution": live["interval_minutes_distribution"], "schema_sha256": live["schema_sha256"],
            "related_tables": [t for t in entry["tables"] if t.startswith("archive_day_")],
            "related_tables_interpretation": "WeeWX-derived daily rollups in the same database; not independent raw observations." if any(t.startswith("archive_day_") for t in entry["tables"]) else None,
            "physical_origin": lineage["physical_origin"], "lineage_confidence": lineage["lineage_confidence"],
            "dependency_ids": lineage["dependency_ids"], "caveats": lineage["caveats"],
            "prior_inventory_snapshot": {"rows": old.get("rows"), "min_timestamp": old.get("min_timestamp"), "max_timestamp": old.get("max_timestamp")},
        })

    references = []
    for row in snapshot.get("reference_stations", []):
        sid = row.get("station_id")
        refs = {
            "source_id": f"reference:{sid}", "provider": row.get("provider"), "station_id": sid,
            "station_name": row.get("station_name"), "source_url": row.get("source_url"),
            "access_status": row.get("access_status"), "location_description": row.get("location_description"),
            "elevation_m": row.get("elevation_m"), "timezone": row.get("timezone_name"),
            "notes": row.get("notes"), "origin_class": "external comparison station; not a Loučka sensor archive",
        }
        if sid == "luhamet_sehradice":
            refs["physical_independence"] = "Separate named station; suitable as an external regional comparator after variable/time/unit checks, not as a duplicate sensor observation."
        elif sid == "wu_ilouka4":
            refs["physical_independence"] = "Coordinates and exact station identity are unverified in local evidence; independence from Loučka is unresolved. Do not count it as an independent station until resolved."
        references.append(refs)

    chmi = []
    for dataset in reference_assets.get("datasets", []):
        for file in dataset.get("files", []):
            chmi.append({"path": file.get("path"), "provider": dataset.get("provider"), "dataset_id": dataset.get("dataset_id"),
                         "station_id": file.get("station_id"), "element": file.get("element"), "month": file.get("month"),
                         "url": file.get("url"), "status": file.get("status"), "sha256": file.get("sha256_manifest"),
                         "bytes": file.get("bytes_actual")})

    estimates = load_json("data/applied_estimated_operations.json")
    applied_estimate_fields = {}
    for row in estimates:
        var = row["variable"]
        applied_estimate_fields[var] = applied_estimate_fields.get(var, 0) + 1

    catalog = {
        "schema": "loucka-historical-source-catalog-v1",
        "captured_utc": snapshot["captured_utc"], "database_server_version": snapshot["server_version"],
        "read_only_capture": True,
        "inventory_snapshot": "data/HISTORICAL_SOURCE_INVENTORY_LIVE.json",
        "inventory_snapshot_sha256": __import__("hashlib").sha256((ROOT / "data/HISTORICAL_SOURCE_INVENTORY_LIVE.json").read_bytes()).hexdigest(),
        "source_archive_count": len(sources), "sources": sources,
        "external_reference_sources": references, "chmi_reference_assets": chmi,
        "reconstruction_and_sync_evidence": {
            "database_tables": snapshot["reconstruction_evidence_tables"],
            "applied_estimate_field_operations": applied_estimate_fields,
            "applied_estimate_operation_count": len(estimates),
            "interpretation": "These are transformation/audit records, not sensor measurements. Archive audit absence is not original-measurement proof.",
        },
        "lineage_and_transformation_findings": [
            {"finding": "Owner reports Cumulus-to-WeeWX transition, historical wind recalculation, stuck-value repair, extreme removal, and merged copies; exact transition dates/rules and row-level affected values are unknown.", "evidence_class": "OWNER_ATTESTED", "references": ["SOURCE_LINEAGE_OWNER_STATEMENT.md", "HISTORICAL_MIGRATION_AND_CLEANING_REPORT.md"]},
            {"finding": "GW3000 and GW1000 database archives share 1,489,468 exact historical timestamp pairs outside 2021 with no one-sided row and identical unit/interval codes; this supports shared database lineage, not independent measurement or full field equality.", "evidence_class": "TECHNICALLY_OBSERVED plus owner context", "references": ["GW1000_GW3000_CONCORDANCE_REPORT.md"]},
            {"finding": "Legacy source copies share many exact timestamp keys but diverge by field, NULL availability, unit code, and epoch. A shared key is a shared archive record time, not independent sensor corroboration.", "evidence_class": "TECHNICALLY_OBSERVED", "references": ["HISTORICAL_MIGRATION_AND_CLEANING_REPORT.md", "SOURCE_TIMESTAMP_ALIGNMENT_REPORT.md"]},
            {"finding": "Observed old archive windSpeed/windGust ratios are consistent with unit transformation in some epochs, mixed in 2013 and anomalous in 2020; this is not a global row-level correction rule.", "evidence_class": "TECHNICALLY_OBSERVED / interpretation remains limited", "references": ["HISTORICAL_WIND_TRANSFORMATION_REPORT.md"]},
            {"finding": "Rain and rainRate semantics vary or conflict across copies; raw rainRate is not safe to aggregate as interval rainfall for all epochs.", "evidence_class": "TECHNICALLY_OBSERVED", "references": ["GW1000_GW3000_CONCORDANCE_REPORT.md", "UNIFIED_ARCHIVE_BLOCKERS.md"]},
            {"finding": "Known estimates currently applied are 30,537 field operations (10,113 outTemp and 20,424 outHumidity); they remain ESTIMATED and are not measurements.", "evidence_class": "LOCAL_APPLIED_ESTIMATE_REGISTRY", "references": ["data/applied_estimated_operations.json"]},
            {"finding": "Q1 2018 remains protected and 2021 diagnostic-only; no automatic provenance or production inference is made for these scopes.", "evidence_class": "USER_PROTECTED_SCOPE", "references": ["MASTER_GOAL_HISTORICAL_REVIEW_2026-11-15.md"]},
        ],
        "historical_invalidations": {
            "owner_attested_classes": ["stuck measurement repairs", "extreme/bad-data removals", "historical edits", "archive merging"],
            "row_level_invalidations_identified_from_available lineage": False,
            "decision": "Do not infer intentional deletion from a source-only key or infer original measurement from a matching copy. Keep specific suspect cohorts unresolved unless a row-specific record proves cause.",
        },
        "limitations": [
            "The physical sensor serial numbers, station siting history, gateway-to-sensor wiring, driver versions/configuration, exact migration dates, exact archive merge choices, and original unedited backups are not present in the reviewed evidence.",
            "Archive values may be copies or transformed descendants of the same original measurement; duplicate databases are not independent votes.",
            "Reference station data has different siting and cadence. External agreement supports plausibility only after temporal/unit alignment; it does not prove Loučka sensor provenance.",
            "The production snapshot was captured at the stated UTC time while sync continued; the snapshot is not an immutable synchronization lock on any database.",
        ],
        "source_evidence": ["SOURCE_LINEAGE_OWNER_STATEMENT.md", "SOURCE_ARCHIVE_PROVENANCE_CONSOLIDATION.md", "HISTORICAL_MIGRATION_AND_CLEANING_REPORT.md", "HISTORICAL_WIND_TRANSFORMATION_REPORT.md", "GW1000_GW3000_CONCORDANCE_REPORT.md", "MASTER_GOAL_ARCHIVE_COMPLETION_EVIDENCE.json", "data/reference-inventory/reference_source_catalog.json"],
    }

    nodes = [{"id": s["source_id"], "kind": "meteorological_archive", "independent_measurement": False if s["database"] == "loucka_reconstruction" else "unproven", "database": s["database"], "table": "archive"} for s in sources]
    nodes += [{"id": r["source_id"], "kind": "external_reference_station", "independent_measurement": r.get("physical_independence", "unknown")} for r in references]
    nodes += [
        {"id": "evidence:reconstruction_changes", "kind": "row-field change audit", "measurement_source": False},
        {"id": "evidence:applied_estimates", "kind": "local estimated operation registry", "measurement_source": False},
        {"id": "evidence:archive_sync_audit", "kind": "immutable source row audit", "measurement_source": False},
        {"id": "evidence:archive_sync_verification", "kind": "postimage verification", "measurement_source": False},
        {"id": "derived:archive_day_rollups", "kind": "WeeWX daily derived aggregates", "measurement_source": False},
        {"id": "reference:chmi_11777_11778", "kind": "official external station assets", "measurement_source": True, "same_station_as_loucka": False},
    ]
    edges = []
    for child in ("archive:pocasi-loucka.eu", "archive:pocasi-loucka.eu_old", "archive:pocasi-loucka.eu_GW1000"):
        for parent in ("archive:old_weewx", "archive:weewx_WH1080"):
            edges.append({"from": parent, "to": child, "relation": "owner_attested_historical_merge_or_shared_lineage", "confidence": "broad lineage only; exact per-row selection unknown"})
    edges.append({"from": "archive:pocasi-loucka.eu_GW1000", "to": "archive:pocasi-loucka.eu", "direction": "undirected", "relation": "shared_historical_database_basis", "confidence": "owner-attested and exact timestamp concordance; not proof of independent sensors"})
    for db in ("pocasi-loucka.eu", "pocasi-loucka.eu_old", "pocasi-loucka.eu_GW1000", "old_weewx", "weewx_WH1080"):
        edges.append({"from": f"archive:{db}", "to": "archive:loucka_reconstruction", "relation": "historical archive input or concordance source", "confidence": "varies by timestamp/field; target is derived and not independent"})
    edges += [
        {"from": "archive:pocasi-loucka.eu", "to": "archive:loucka_reconstruction", "relation": "approved post-fence GW3000 insert-only sync", "evidence": "verified source row payload, audit events and postimage batches; current runtime"},
        {"from": "evidence:reconstruction_changes", "to": "archive:loucka_reconstruction", "relation": "records applied/restored/corrected field changes", "evidence": "field event audit; not raw source"},
        {"from": "evidence:applied_estimates", "to": "archive:loucka_reconstruction", "relation": "records applied estimated values", "evidence": "30,537 applied entries remain ESTIMATED"},
        {"from": "evidence:archive_sync_audit", "to": "archive:loucka_reconstruction", "relation": "records source payload for approved synced rows"},
        {"from": "evidence:archive_sync_verification", "to": "archive:loucka_reconstruction", "relation": "verifies target postimage by sync batch"},
        {"from": "archive:pocasi-loucka.eu", "to": "derived:archive_day_rollups", "relation": "same-database derived WeeWX daily aggregates"},
        {"from": "archive:pocasi-loucka.eu_GW1000", "to": "derived:archive_day_rollups", "relation": "same-database derived WeeWX daily aggregates"},
        {"from": "reference:luhamet_sehradice", "to": "archive:loucka_reconstruction", "relation": "external regional comparison/reference observations; never a Loučka sensor value"},
        {"from": "reference:wu_ilouka4", "to": "archive:loucka_reconstruction", "relation": "external reference candidate; station location identity unresolved"},
        {"from": "reference:chmi_11777_11778", "to": "archive:loucka_reconstruction", "relation": "official external station comparison context; different stations"},
    ]
    graph = {"schema": "loucka-historical-source-dependency-graph-v1", "captured_utc": snapshot["captured_utc"], "nodes": nodes, "edges": edges,
             "weighting_rule": "Records sharing a parent archive, copied timestamp rowset, merge, or target derivation are one lineage family; never count copies as independent sensor evidence."}

    (ROOT / "HISTORICAL_SOURCE_CATALOG.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "HISTORICAL_SOURCE_DEPENDENCY_GRAPH.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Historical source catalog", "", f"Live metadata snapshot: {snapshot['captured_utc']} ({snapshot['server_version']}). All database inventory queries used read-only transactions. Full row counts, timestamp ranges, unit/cadence distributions, schema hashes, references, and dependency graph are in the adjacent JSON files.", "", "## Loučka archive databases", "", "| Database | Rows | UTC coverage | usUnits | interval (minutes) | Source interpretation |", "|---|---:|---|---|---|---|"]
    for s in sources:
        units = ", ".join(f"{k}: {v:,}" for k, v in s["usUnits_distribution"].items())
        ints = ", ".join(f"{k}: {v:,}" for k, v in s["interval_minutes_distribution"].items())
        lines.append(f"| `{s['database']}.archive` | {s['row_count']:,} | {s['coverage_utc']['min']} – {s['coverage_utc']['max']} | {units} | {ints} | {s['role']} |")
    lines += ["", "All six archive tables have unique `dateTime` keys in this snapshot. Metric `usUnits=16` appears in the newer archives and reconstruction; legacy `old_weewx` and `weewx_WH1080` use code 17. Five-minute cadence dominates, while code 6 is a documented legacy cadence and uncommon 10/30/40/55/75 intervals require row/epoch review. Do not pool copies as independent evidence.", "", "## Physical lineage and known changes", "", "The owner attests to a Cumulus-to-WeeWX transition, historical wind recalculation, repairs of stuck values, removal of extremes, and merging of historical databases. Exact dates, driver versions/configuration, source selection, affected timestamps/fields, and original backups are unavailable. The physical origin of `old_weewx`, `weewx_WH1080`, and `pocasi-loucka.eu_old` is specifically unknown. Current source and reconstruction copies share substantial exact rowsets; exact equality proves stored-copy concordance only.", "", "Stored wind ratios show a field/epoch pattern consistent with unit conversion from 2014–2019 and mixed regimes around 2013, but there are 2020 exceptions. This supports no global conversion rule. Historical `rainRate` and pressure/altimeter copy differences remain unresolved. No row-specific historic invalidation list was found; owner-attested cleanup is not enough to label individual values invalidated.", "", "## External reference sources", ""]
    for r in references:
        lines += [f"### {r['provider']} — {r['station_name']}", "", f"Station ID: `{r['station_id']}`; location: {r['location_description']}; elevation: {r.get('elevation_m')} m; access: `{r['access_status']}`.", "", r.get("notes", ""), "", r.get("physical_independence", ""), ""]
    lines += ["### CHMI local reference files", "", f"The local manifest catalog records {reference_assets['distinct_existing_file_count']} existing files across {len(reference_assets['datasets'])} datasets; unavailable/missing manifest references are retained rather than recreated. Station IDs, measured elements, month, URL, local path, retrieval state, byte length, and SHA-256 are in `HISTORICAL_SOURCE_CATALOG.json`.", "", "## Reconstruction and sync evidence", "", "`loucka_reconstruction` is a derived archive. Its live tables include the field change ledger, reconstruction candidates/batches, backups/QC tables, reference observations, and GW3000 audit/cursor/verification records. The live table counts are in JSON. The local estimate registry contains 30,537 applied field operations (10,113 `outTemp`; 20,424 `outHumidity`); these stay classified as estimates. Sync audit and verification prove only the bounded synchronized source rows and their present postimages.", "", "Q1 2018 remains protected, 2021 diagnostic-only, and rain/rainRate semantics remain unresolved for historical interpretation. The dependency graph prevents treating archives derived from a shared database base as independent sensors.", "", "## Evidence and limitations", "", "This catalog distinguishes owner statements from technical snapshot facts. It does not claim original sensor provenance where the record lacks it. Detailed prior evidence: `SOURCE_LINEAGE_OWNER_STATEMENT.md`, `SOURCE_ARCHIVE_PROVENANCE_CONSOLIDATION.md`, `HISTORICAL_MIGRATION_AND_CLEANING_REPORT.md`, `HISTORICAL_WIND_TRANSFORMATION_REPORT.md`, `GW1000_GW3000_CONCORDANCE_REPORT.md`, `MASTER_GOAL_ARCHIVE_COMPLETION_EVIDENCE.json`, and the reference manifests."]
    (ROOT / "HISTORICAL_SOURCE_CATALOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
