#!/usr/bin/env python3
"""Build explicit station-epoch uncertainty and candidate result registries."""
import csv, hashlib, json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    catalog_path = ROOT / "REFERENCE_STATION_CATALOG.json"
    catalog = read_json(catalog_path)
    snapshot = read_json(ROOT / "data/STATISTICAL_READINESS_CURRENT.json")["snapshot"]
    snapshot_id = read_json(ROOT / "data/STATISTICAL_VARIANTS_MANIFEST.json")["concordance_sqlite_sha256"]
    source_catalog_path = ROOT / "HISTORICAL_SOURCE_CATALOG.json"
    conflict_path = ROOT / "HISTORICAL_CONFLICT_EPOCH_REVIEW.json"
    conflicts = read_json(conflict_path)
    live_capture_path = ROOT / "data/gw3000-current-readonly/capture-20261116T010749Z.json"
    live_capture = read_json(live_capture_path) if live_capture_path.is_file() else None
    public_history_path = ROOT / "data/source-lineage/public_station_history_20261113.json"
    public_history = read_json(public_history_path) if public_history_path.is_file() else {"evidence": []}
    local_metadata_path = ROOT / "LOCAL_STATION_METADATA_SEARCH.json"
    local_metadata_search = read_json(local_metadata_path) if local_metadata_path.is_file() else None

    # Preserve operator-reported station history as a separate evidence layer.
    # These statements identify station/system changes, not sensor-specific
    # deployments or the provenance of any SQL archive copy.
    reported_history = [
        {
            "record_id": "loucka-watson-w8681-reported",
            "record_type": "operator_reported_station_configuration_period",
            "valid_from": "2009-03-29",
            "valid_to": "2022-08-20",
            "boundary_precision": "date_only; replacement time on 2022-08-20 is unknown",
            "reported_station_model": "Watson W-8681",
            "reported_software": "Cumulus v1.8.7 (contemporaneous page captured 2009-08-30 only)",
            "gateway_model": None,
            "sensor_model_or_identity": None,
            "location_report": {"latitude": "49.165278", "longitude": "17.877500", "elevation_m": 420,
                                "source_precision": "coordinates transcribed from archived station page; sensor mast placement not documented"},
            "evidence_sources": ["https://pocasi-loucka.eu/about/", "https://web.archive.org/web/20090830152549/http://www.pomykal.eu/pocasi/"],
            "evidence_sha256": sha(public_history_path) if public_history_path.is_file() else None,
            "claims": ["Station operator reports measurement start on 2009-03-29 with Watson W-8681.",
                       "Archived station page captured 2009-08-30 identifies Watson-8681 and Cumulus v1.8.7.",
                       "Archived page reports coordinates 49°09'55\"N, 17°52'39\"E and elevation 420 m."],
            "limitations": ["The contemporaneous location is a station-page location, not independently verified sensor coordinates.",
                            "No sensor serial, mast/siting description, WeeWX configuration, archive export lineage, or unit transformation is established.",
                            "The change date is reported at date precision; exact transition time is unknown."]
        },
        {
            "record_id": "loucka-gw1000-replacement-reported",
            "record_type": "operator_reported_station_replacement_not_sensor_specific_epoch",
            "valid_from": "2022-08-20",
            "valid_to": None,
            "boundary_precision": "date_only; end date and replacement time for later GW3000 observation unknown",
            "reported_station_model": None,
            "reported_software": None,
            "gateway_model": "GW1000 (reported replacement device; does not identify the outdoor sensor suite)",
            "sensor_model_or_identity": None,
            "location_report": None,
            "evidence_sources": ["https://pocasi-loucka.eu/about/"],
            "evidence_sha256": sha(public_history_path) if public_history_path.is_file() else None,
            "claims": ["Station operator reports the weather station was replaced with GW1000 on 2022-08-20."],
            "limitations": ["This does not prove a physical sensor was replaced, identify the sensors connected to the gateway, or date a later GW3000 installation.",
                            "No historical driver/configuration mapping or archive-copy lineage is established."]
        }
    ] if public_history.get("evidence") else []

    location_reports = [
        {"source": "archived 2009 station page", "latitude": 49.165278, "longitude": 17.877500, "elevation_m": 420,
         "evidence_source": "https://web.archive.org/web/20090830152549/http://www.pomykal.eu/pocasi/",
         "evidence_sha256": sha(public_history_path) if public_history_path.is_file() else None,
         "limitation": "Published station location; exact sensor position and elevation method are not documented."},
        {"source": "current Weather Underground station profile", "latitude": 49.166, "longitude": 17.878, "elevation_m": 431,
         "evidence_source": "https://www.wunderground.com/dashboard/pws/IZLNSKLO2",
         "evidence_sha256": sha(public_history_path) if public_history_path.is_file() else None,
         "limitation": "Current profile only; sensor location and historical continuity are not established."}
    ] if public_history.get("evidence") else []

    # The archive coverage window is not evidence of a physical sensor epoch.
    registry = {
        "schema": "loucka-station-sensor-epoch-registry-v1",
        "snapshot_id": snapshot_id,
        "source_snapshot_sha256": sha(ROOT / "data/STATISTICAL_READINESS_CURRENT.json"),
        "station": "Počasí Loučka",
        "reported_station_configuration_periods": reported_history,
        "reported_station_location_metadata": {
            "reports": location_reports,
            "agreement_status": "NEARBY_BUT_NOT_IDENTICAL; elevation differs by 11 m",
            "canonical_sensor_location_or_elevation": None,
            "interpretation": "Public station-page locations improve locality context but do not prove exact sensor coordinates/elevation or sensor siting."
        },
        "sensor_epochs": [{
            "station_epoch_id": "loucka-physical-epoch-unresolved",
            "valid_from": "2009-03-29T00:00:00Z",
            "valid_to": "2026-11-15T23:59:59Z",
            "epoch_type": "archive_coverage_envelope_not_sensor_epoch",
            "sensor_model": None,
            "sensor_identity_evidence": "No dated physical sensor identity record found. A read-only search found no standard-named WeeWX configuration/backup files in the inspected host roots; local app fixtures have null/unverified location and unknown sensor status.",
            "gateway_model": None,
            "driver": None,
            "driver_version": None,
            "units": {"archive_usUnits": 16, "scope": "current readiness snapshot only; historical source archives contain other unit codes"},
            "cadence": "Variable; field/month cadence evidence is in the readiness snapshot and archive diagnostics.",
            "location": {"latitude": None, "longitude": None, "evidence": None},
            "elevation_m": None,
            "configuration_hash": None,
            "evidence_sources": [
                "data/STATISTICAL_READINESS_CURRENT.json",
                "REFERENCE_STATION_CATALOG.json",
                "HISTORICAL_SOURCE_CATALOG.json",
                "HISTORICAL_CONFLICT_EPOCH_REVIEW.json",
                "LOCAL_STATION_METADATA_SEARCH.json"
            ],
            "unresolved_questions": [
                "Exact station coordinates and sensor elevation",
                "Dated sensor/gateway models, firmware, driver and configuration",
                "Sensor-specific valid-from/valid-to dates and deployment changes",
                "Exposure, shielding, ventilation and precipitation gauge siting",
                "Whether archive source-availability transitions correspond to any physical change"
            ]
        }],
        "archive_source_availability_cohorts": sorted({
            r["source_availability_signature"] for r in conflicts["epoch_review_rows"]
        }),
        "current_gateway_observation": ({
            "observation_type": "point_in_time_current_gateway_configuration_not_a_sensor_epoch",
            "observed_from_utc": live_capture["capture_started_utc"],
            "observed_to_utc": live_capture["capture_completed_utc"],
            "gateway_model_and_firmware": live_capture["gateway"]["version"].get("version"),
            "gateway_units": live_capture["gateway"]["units"],
            "rain_priority_code": live_capture["rain_configuration"]["get_rain_totals"].get("rainFallPriority"),
            "rain_priority_label": next((x.get("gauge") for x in live_capture["rain_configuration"]["get_rain_totals"].get("list", [])
                                          if x.get("value") == live_capture["rain_configuration"]["get_rain_totals"].get("rainFallPriority")), None),
            "rain_gain": live_capture["rain_configuration"]["get_rain_totals"].get("rainGain"),
            "rain_capable_sensor_inventory": live_capture["rain_configuration"]["rain_capable_sensor_catalog"],
            "evidence_path": str(live_capture_path.relative_to(ROOT)),
            "evidence_sha256": sha(live_capture_path),
            "physical_sensor_epoch_proven": False,
            "interpretation_limit": "Current gateway settings and reported sensor catalog do not prove dated historical deployment, actual sensor measurement assignment, or WeeWX archive mapping.",
        } if live_capture else None),
        "local_application_metadata_search": local_metadata_search,
        "interpretation": "Source-availability cohorts document which copies were available for comparison. Operator-reported station configuration periods are recorded separately; they do not establish sensor-specific deployment, SQL archive lineage, driver transformations, or physical sensor epochs.",
        "reference_stations": catalog["stations"],
        "metadata_limits": [
            "No village centroid has been substituted for sensor coordinates.",
            "Reference-station metadata does not establish Loučka sensor metadata.",
            "Null fields mean evidence was not found; they are not estimates.",
            "The local configuration search was filename-based and does not rule out unmounted backups or files with unrelated names."
        ]
    }
    (ROOT / "STATION_SENSOR_EPOCH_REGISTRY.json").write_text(
        json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    evidence_path = ROOT / "MONTHLY_VALIDATION_EVIDENCE.json"
    evidence = read_json(evidence_path)
    diagnostics = read_json(ROOT / "MONTHLY_CANDIDATE_SERIES_DIAGNOSTICS.json")
    series_by_key = {(x["period"], x["variable"]): x for x in diagnostics["records"]}
    temp_validation = read_json(ROOT / "MONTHLY_TEMPERATURE_REFERENCE_VALIDATION.json")
    temp_by_period = {}
    for r in temp_validation.get("station_month_results", []):
        temp_by_period.setdefault(r["period"], []).append(r)
    records = []
    for e in evidence["records"]:
        refs = temp_by_period.get(e["period"], []) if e["variable"] == "outTemp" else []
        if e["period"] == "2026-01" and e["variable"] in {"outTemp", "outHumidity"}:
            detail = read_json(ROOT / "PILOT_2026_01_VALIDATED_STATISTICS.json")
            stat = next((x for x in detail["statistics"] if x["variable"] == e["variable"]), None)
            review = "PILOT_SPECIALIST_REVIEW_AVAILABLE"
        elif e.get("temperature_expert_review"):
            stat = None
            review = "CANDIDATE_SPECIFIC_EXPERT_REVIEW_COMPLETE_PHYSICAL_VALIDATION_MISSING"
        elif refs:
            stat = None
            review = "REGIONAL_TEMPERATURE_REFERENCE_AVAILABLE"
        elif e.get("daily_regional_context_summary"):
            stat = None
            review = "DAILY_TEMPERATURE_CONTEXT_ONLY_REVIEW_REQUIRED"
        elif e.get("daily_humidity_regional_context_summary"):
            stat = None
            review = "DAILY_HUMIDITY_CONTEXT_ONLY_REVIEW_REQUIRED"
        elif e.get("pressure_daily_regional_context_summary"):
            stat = None
            review = "DAILY_PRESSURE_CONTEXT_ONLY_REVIEW_REQUIRED"
        elif e.get("candidate_status") == "BLOCKED_NO_SAME_VARIANT_POSITIVE_WIND_SPEED":
            stat = None
            review = "BLOCKED_NO_SAME_VARIANT_POSITIVE_WIND_SPEED"
        else:
            stat = None
            review = "CANDIDATE_EVIDENCE_ONLY_REVIEW_REQUIRED"
        series_diagnostic = series_by_key.get((e["period"], e["variable"]))
        if series_diagnostic is None:
            # Preserve an explicit candidate-level trace when the specialist
            # series calculator has no numeric statistic (e.g. wind direction
            # gated by same-variant speed). This is availability evidence,
            # not a fabricated numeric series or a substitute for validation.
            series_diagnostic = {
                "diagnostic_status": e.get("candidate_status", "NO_SPECIALIST_SERIES_STATISTIC"),
                "target_nonnull_rows": sum(int(n) for n in e.get("provenance_breakdown", {}).values()),
                "candidate_value": e.get("value"),
                "observed_slots": e.get("observed_slots"),
                "expected_slots": e.get("expected_slots"),
                "coverage": e.get("coverage"),
                "interval_weighted_diagnostic": e.get("interval_weighted_diagnostic"),
            }
        records.append({
            **e,
            "within_month_archive_series_diagnostics": series_diagnostic,
            "candidate_review_status": review,
            "specialist_pilot_statistic": stat,
            "temperature_reference_station_months": refs,
            "sensor_epoch_id": "loucka-physical-epoch-unresolved",
            "decision_scope": "Evidence record describes available evidence; it does not itself authorize publication."
        })
    counts = Counter((r["candidate_review_status"], r["variable"]) for r in records)
    results = {
        "schema": "loucka-monthly-validation-results-v1",
        "snapshot_id": snapshot_id,
        "candidate_count": len(records),
        "candidate_source_sha256": evidence["candidate_source_sha256"],
        "evidence_registry_sha256": sha(evidence_path),
        "temperature_reference_validation_sha256": sha(ROOT / "MONTHLY_TEMPERATURE_REFERENCE_VALIDATION.json"),
        "daily_temperature_context_sha256": evidence.get("daily_temperature_context_sha256"),
        "daily_humidity_context_sha256": evidence.get("daily_humidity_context_sha256"),
        "daily_pressure_context_sha256": evidence.get("daily_pressure_context_sha256"),
        "records": records,
        "review_status_counts_by_variable": {
            variable: dict(Counter({status: n for (status, var), n in counts.items() if var == variable}))
            for variable in sorted({r["variable"] for r in records})
        },
        "summary": {
            "candidate_records_materialized": len(records),
            "daily_temperature_context_records": sum(bool(r.get("daily_regional_context_summary")) for r in records),
            "daily_humidity_context_records": sum(bool(r.get("daily_humidity_regional_context_summary")) for r in records),
            "daily_pressure_context_records": sum(bool(r.get("pressure_daily_regional_context_summary")) for r in records),
            "temperature_expert_review_records": sum(bool(r.get("temperature_expert_review")) for r in records),
            "physical_sensor_epochs_proven": 0,
            "caveat": "Candidate evidence has been joined to available reference and pilot records. Missing specialist evidence remains an explicit review state; this does not claim all 248 candidates have full expert validation."
        }
    }
    (ROOT / "MONTHLY_VALIDATION_RESULTS.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"epoch_registry_records": len(registry["sensor_epochs"]), "source_availability_cohorts": len(registry["archive_source_availability_cohorts"]), "monthly_candidate_results": len(records), "physical_sensor_epochs_proven": 0}, indent=2))

if __name__ == "__main__":
    main()
