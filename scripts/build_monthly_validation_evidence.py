#!/usr/bin/env python3
"""Materialize one conservative evidence record for each selected monthly mean."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
OUT=ROOT/"MONTHLY_VALIDATION_EVIDENCE.json"

def load(path): return json.loads(path.read_text(encoding="utf-8"))

def main():
    candidates=load(ROOT/"MONTHLY_PUBLICATION_CANDIDATES.json")["candidates"]
    stats=load(DATA/"STATISTICAL_READINESS_CURRENT.json")
    variants={}
    import csv
    with (DATA/"STATISTICAL_VARIANTS_MONTHLY.csv").open(encoding="utf-8",newline="") as f:
        for row in csv.DictReader(f):
            if row["variant"]=="B_DOCUMENTED_SOURCE_AND_RECOVERY": variants[(row["period"],row["variable"])]=row
    interval_variants={}
    with (DATA/"INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_MONTHLY.csv").open(encoding="utf-8",newline="") as f:
        for row in csv.DictReader(f):
            if row["variant"]=="B_DOCUMENTED_SOURCE_AND_RECOVERY": interval_variants[(row["period"],row["variable"])]=row
    ext_path=ROOT/"PILOT_2026_01_EXTERNAL_VALIDATION.json"
    ext=load(ext_path) if ext_path.exists() else {}
    temp_validation_path=ROOT/"MONTHLY_TEMPERATURE_REFERENCE_VALIDATION.json"
    temp_validation=load(temp_validation_path) if temp_validation_path.exists() else {"station_month_results":[]}
    daily_context_path=ROOT/"CHMI_DAILY_TEMPERATURE_CONTEXT_REVIEW.json"
    daily_context=load(daily_context_path) if daily_context_path.exists() else {"results":[]}
    temp_expert_path=ROOT/"TEMPERATURE_CANDIDATE_EXPERT_REVIEW.json"
    temp_expert=load(temp_expert_path) if temp_expert_path.exists() else {"results":[]}
    humidity_validation_path=ROOT/"MONTHLY_HUMIDITY_REFERENCE_VALIDATION.json"
    humidity_validation=load(humidity_validation_path) if humidity_validation_path.exists() else {"station_month_results":[]}
    humidity_daily_path=ROOT/"HUMIDITY_DAILY_REFERENCE_CONTEXT.json"
    humidity_daily=load(humidity_daily_path) if humidity_daily_path.exists() else {"results":[]}
    humidity_review_path=ROOT/"HUMIDITY_CANDIDATE_VALIDATION_REVIEW.json"
    humidity_review=load(humidity_review_path) if humidity_review_path.exists() else {"records":[]}
    pressure_daily_path=ROOT/"PRESSURE_DAILY_REFERENCE_CONTEXT.json"
    pressure_daily=load(pressure_daily_path) if pressure_daily_path.exists() else {"results":[]}
    pressure_validation_path=ROOT/"MONTHLY_PRESSURE_REFERENCE_VALIDATION.json"
    pressure_validation=load(pressure_validation_path) if pressure_validation_path.exists() else {"station_month_results":[]}
    wind_validation_path=ROOT/"MONTHLY_WIND_REFERENCE_VALIDATION.json"
    wind_validation=load(wind_validation_path) if wind_validation_path.exists() else {"station_month_results":[]}
    temp_by_period={}
    for result in temp_validation["station_month_results"]:
        temp_by_period.setdefault(result["period"],[]).append(result)
    daily_by_period={}
    for result in daily_context.get("results",[]):
        daily_by_period.setdefault(result["period"],[]).append(result)
    temp_expert_by_period={r["period"]:r for r in temp_expert.get("results",[])}
    humidity_by_period={}
    for result in humidity_validation["station_month_results"]:
        humidity_by_period.setdefault(result["period"],[]).append(result)
    humidity_daily_by_period={}
    for result in humidity_daily.get("results",[]):
        if result.get("valid_quality_zero_days",0)>0: humidity_daily_by_period.setdefault(result["period"],[]).append(result)
    humidity_review_by_period={r["period"]:r for r in humidity_review.get("records",[])}
    pressure_daily_by_period={r["period"]:r for r in pressure_daily.get("results",[]) if r.get("valid_quality_zero_avg_days",0)>0}
    pressure_by_period={}
    for result in pressure_validation["station_month_results"]:
        pressure_by_period.setdefault(result["period"],[]).append(result)
    wind_by_candidate={}
    for result in wind_validation["station_month_results"]:
        wind_by_candidate.setdefault((result["period"],result["variable"]),[]).append(result)
    pilot_path=ROOT/"PILOT_2026_01_VALIDATED_STATISTICS.json"
    pilot={r["variable"]:r for r in load(pilot_path).get("statistics",[])} if pilot_path.exists() else {}
    records=[]
    for c in candidates:
        p,v=c["period"],c["variable"]
        raw=variants[(p,v)]
        interval=interval_variants[(p,v)]
        prov=ast.literal_eval(raw["provenance_counts"])
        matches=[r for r in stats["monthly"] if r["period"]==p and r["variable"]==v]
        stat=matches[0] if matches else {}
        is_pilot=p=="2026-01" and v in pilot
        ref=ext.get("variables",{}).get(v) if is_pilot else None
        regional_refs=(temp_by_period.get(p,[]) if v=="outTemp" else humidity_by_period.get(p,[]) if v=="outHumidity" else pressure_by_period.get(p,[]) if v=="barometer" else wind_by_candidate.get((p,v),[]) if v in ("windSpeed","windGust","windDir") else [])
        daily_refs=([r for r in daily_by_period.get(p,[]) if r["valid_daily_mean_slots_quality_zero"]>0] if v=="outTemp" else [])
        humidity_daily_refs=humidity_daily_by_period.get(p,[]) if v=="outHumidity" else []
        pressure_daily_ref=pressure_daily_by_period.get(p) if v=="barometer" else None
        temperature_expert_review=temp_expert_by_period.get(p) if v=="outTemp" else None
        candidate_statistic_available=c.get("value") is not None
        regional_ok=bool(candidate_statistic_available and regional_refs and all(x["matched_coverage_of_valid_reference"]>=.98 and x["matched_pairs"]>0 for x in regional_refs))
        evidence_status=("PILOT_EVIDENCE_AVAILABLE" if is_pilot and ref else
                         "REGIONAL_REFERENCE_COMPARISON_AVAILABLE_PHYSICAL_VALIDATION_MISSING" if regional_ok else
                         "B_VARIANT_STATISTIC_UNAVAILABLE_SAME_VARIANT_SPEED_MISSING" if not candidate_statistic_available and v=="windDir" else
                         "DAILY_REGIONAL_CONTEXT_ONLY_PHYSICAL_VALIDATION_MISSING" if daily_refs or humidity_daily_refs or pressure_daily_ref else
                         "PILOT_STATISTIC_REVIEW_INCOMPLETE" if is_pilot else
                         "PERIOD_SPECIFIC_PHYSICAL_AND_EXTERNAL_EVIDENCE_MISSING")
        ref_summary=({k:ref.get(k) for k in ("matched_coverage","correlation","bias_chmi_minus_loucka","matched_10_min_pairs")} if ref else None)
        regional_summary=([{"station_id":x["station_id"],"matched_pairs":x["matched_pairs"],"matched_coverage":x["matched_coverage_of_valid_reference"],"bias_reference_minus_loucka":x.get("bias_reference_minus_loucka_C",x.get("bias_reference_minus_loucka_percentage_points",x.get("bias_reference_minus_loucka_hPa",x.get("bias_reference_minus_loucka")))),"mae":x.get("mae_C",x.get("mae_percentage_points",x.get("mae_hPa",x.get("mae")))),"rmse":x.get("rmse_C",x.get("rmse_percentage_points",x.get("rmse_hPa",x.get("rmse")))),"correlation":x.get("correlation"),"circular_direction_statistics":x.get("circular_direction_statistics"),"unit":("degC" if v=="outTemp" else "hPa" if v=="barometer" else "percentage_points" if v=="outHumidity" else "degrees" if v=="windDir" else "m/s")} for x in regional_refs] if regional_refs else None)
        if ref_summary is None and regional_summary is not None:ref_summary=regional_summary
        # A separate immutable record supports technical availability, never truth.
        limitations=["Coverage and archive-copy agreement do not independently validate sensor accuracy."]
        if is_pilot:limitations.append(pilot[v]["decision_reason"])
        if regional_ok and v=="barometer":limitations.append("CHMI Holešov P_hm is a regional sea-level pressure comparator; Loučka pressure-field semantics, sensor elevation and reduction configuration remain unverified.")
        elif regional_ok and v in ("windSpeed","windGust","windDir"):limitations.append("CHMI wind data are regional context; local sensor exposure and equal time support are unverified, and CHMI Fmax is not assumed to share the local gust window.")
        elif regional_ok:limitations.append("Nearby CHMI stations provide regional plausibility evidence; this does not establish Loučka sensor identity, calibration, or physical accuracy.")
        elif daily_refs:limitations.append("Official daily T,AVG data provide regional aggregate context only. CHMI day boundaries and daily weighting are not mapped to Loučka civil-month archive intervals; this is not matched external validation.")
        elif humidity_daily_refs:limitations.append("Official daily H,AVG data provide regional aggregate context only. CHMI day boundaries and daily weighting are not mapped to Loučka civil-month archive intervals; this is not matched external validation and does not establish sensor accuracy.")
        elif pressure_daily_ref:limitations.append("Official CHMI daily P,AVG provides regional station-pressure context only. It is not equated to Loučka pressure, barometer, or altimeter; daily windows are not mapped to Loučka civil-month archive intervals, and this is not matched external or physical validation.")
        elif not is_pilot:limitations.append("No qualifying period-specific external or physical validation record is available.")
        if not candidate_statistic_available and v=="windDir":limitations.append("Regional wind-direction pairs describe target archive direction values, but cannot validate a B-variant monthly mean because same-variant positive windSpeed is unavailable.")
        daily_summary=([{"station_id":x["station_id"],"expected_daily_slots":x["expected_daily_slots"],"valid_daily_mean_slots_quality_zero":x["valid_daily_mean_slots_quality_zero"],"daily_coverage":x["daily_coverage"],"chmi_mean_of_daily_means_C":x["chmi_mean_of_daily_means_C"],"difference_chmi_daily_mean_minus_loucka_monthly_mean_C":x["difference_chmi_daily_mean_minus_loucka_monthly_mean_C"],"reference_sha256":x["reference_sha256"],"unit":"degC"} for x in daily_refs] if daily_refs else None)
        humidity_daily_summary=([{"station_id":x["station_id"],"station_name":x["station_name"],"expected_days":x["expected_days"],"valid_quality_zero_days":x["valid_quality_zero_days"],"coverage":x["coverage"],"mean_of_daily_means_pct":x["mean_of_daily_means_pct"],"difference_daily_context_minus_loucka_pp":x["difference_daily_context_minus_loucka_pp"],"days_ge_99_pct":x["days_ge_99_pct"],"quality_counts":x["quality_counts"],"flag_counts":x["flag_counts"],"source_sha256":x["source_sha256"],"comparison_status":x["comparison_status"],"unit":"percent_RH"} for x in humidity_daily_refs] if humidity_daily_refs else None)
        pressure_daily_summary=({"station_id":pressure_daily_ref["reference_station_id"],"station_name":pressure_daily_ref["reference_station_name"],"element":pressure_daily_ref["chmi_element"],"timefunc":pressure_daily_ref["timefunc"],"time_basis":pressure_daily_ref["time_basis"],"expected_days":pressure_daily_ref["expected_days"],"valid_quality_zero_avg_days":pressure_daily_ref["valid_quality_zero_avg_days"],"coverage":pressure_daily_ref["coverage"],"mean_of_daily_means_hpa":pressure_daily_ref["mean_of_daily_means_hpa"],"quality_counts":pressure_daily_ref["quality_counts"],"flag_counts":pressure_daily_ref["flag_counts"],"local_variant_b_month_means_hpa":pressure_daily_ref["local_variant_b_month_means_hpa"],"descriptive_context_differences_hpa":pressure_daily_ref["descriptive_context_differences_hpa"],"reference_sha256":pressure_daily_ref["source_sha256"],"comparison_status":pressure_daily_ref["comparison_status"],"unit":"hPa"} if pressure_daily_ref else None)
        records.append({
            "period":p,"variable":v,"statistic":"time_weighted_mean","value":c["value"],"unit":c["unit"],
            "candidate_status":"BLOCKED_NO_SAME_VARIANT_POSITIVE_WIND_SPEED" if v=="windDir" and c.get("value") is None and c.get("wind_direction_without_variant_speed_excluded",0)>0 else "CANDIDATE_EVIDENCE_RECORDED",
            "interval_weighted_diagnostic":{"value":float(interval["interval_mean"]) if interval["interval_mean"] else None,"time_coverage":float(interval["time_coverage"]),"longest_uncovered_gap_seconds":int(interval["longest_uncovered_gap_seconds"]),"retained_intervals":int(interval["retained_intervals"]),"overlap_excluded_intervals":int(interval["overlap_excluded_intervals"]),"unknown_or_unavailable_speed_excluded":int(interval["unknown_or_unavailable_speed_excluded"]),"calm_direction_excluded":int(interval["calm_direction_excluded"]),"methodology":interval["methodology"]},
            "physical_validation":bool(is_pilot and v=="outTemp"),
            "external_validation":bool(candidate_statistic_available and ((ref and ref.get("matched_coverage",0)>=.98 and ref.get("correlation",0)>=.90) or regional_ok)),
            "independent_sensor_lineage":False,
            "documented_archive_continuity":bool(prov.get("SOURCE_MATCHED",0)+prov.get("RECOVERED_SOURCE",0)>0 and prov.get("CONFLICTING_SOURCE",0)==0),
            "explicit_limitations":bool(is_pilot),
            "sensor_error":bool(is_pilot and v=="outHumidity"),
            "evidence_status":evidence_status,
            "evidence_reference":{
                "candidate":"MONTHLY_PUBLICATION_CANDIDATES.json",
                "variant":"data/STATISTICAL_VARIANTS_MONTHLY.csv",
                "readiness":"data/STATISTICAL_READINESS_CURRENT.json" if stat else None,
                "external":"PILOT_2026_01_EXTERNAL_VALIDATION.json" if ref else ("MONTHLY_TEMPERATURE_REFERENCE_VALIDATION.json" if v=="outTemp" and regional_refs else "MONTHLY_HUMIDITY_REFERENCE_VALIDATION.json" if v=="outHumidity" and regional_refs else "MONTHLY_PRESSURE_REFERENCE_VALIDATION.json" if v=="barometer" and regional_refs else "MONTHLY_WIND_REFERENCE_VALIDATION.json" if v in ("windSpeed","windGust","windDir") and regional_refs else "CHMI_DAILY_TEMPERATURE_CONTEXT_REVIEW.json" if daily_refs else "HUMIDITY_DAILY_REFERENCE_CONTEXT.json" if humidity_daily_refs else "PRESSURE_DAILY_REFERENCE_CONTEXT.json" if pressure_daily_ref else None),
                "pilot":"PILOT_2026_01_VALIDATED_STATISTICS.json" if is_pilot else None},
            "provenance_breakdown":prov,
            "coverage":float(c["coverage"]),"observed_slots":int(c["observed_slots"]),"expected_slots":int(c["expected_slots"]),
            "reference_summary":ref_summary,
            "regional_reference_summary":regional_summary,
                "daily_regional_context_summary":daily_summary,"daily_humidity_regional_context_summary":humidity_daily_summary,
            "humidity_candidate_validation_review":humidity_review_by_period.get(p) if v=="outHumidity" else None,
            "pressure_daily_regional_context_summary":pressure_daily_summary,
            "temperature_expert_review":temperature_expert_review,
            "limitations":limitations
        })
    doc={"schema":"loucka-monthly-validation-evidence-v2","candidate_count":len(candidates),"candidate_source_sha256":hashlib.sha256((ROOT/"MONTHLY_PUBLICATION_CANDIDATES.json").read_bytes()).hexdigest(),"variant_source_sha256":hashlib.sha256((DATA/"STATISTICAL_VARIANTS_MONTHLY.csv").read_bytes()).hexdigest(),"interval_variant_source_sha256":hashlib.sha256((DATA/"INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_MONTHLY.csv").read_bytes()).hexdigest(),"temperature_reference_validation_sha256":hashlib.sha256(temp_validation_path.read_bytes()).hexdigest() if temp_validation_path.exists() else None,"daily_temperature_context_sha256":hashlib.sha256(daily_context_path.read_bytes()).hexdigest() if daily_context_path.exists() else None,"temperature_candidate_expert_review_sha256":hashlib.sha256(temp_expert_path.read_bytes()).hexdigest() if temp_expert_path.exists() else None,"humidity_reference_validation_sha256":hashlib.sha256(humidity_validation_path.read_bytes()).hexdigest() if humidity_validation_path.exists() else None,"daily_humidity_context_sha256":hashlib.sha256(humidity_daily_path.read_bytes()).hexdigest() if humidity_daily_path.exists() else None,"humidity_candidate_validation_review_sha256":hashlib.sha256(humidity_review_path.read_bytes()).hexdigest() if humidity_review_path.exists() else None,"pressure_reference_validation_sha256":hashlib.sha256(pressure_validation_path.read_bytes()).hexdigest() if pressure_validation_path.exists() else None,"daily_pressure_context_sha256":hashlib.sha256(pressure_daily_path.read_bytes()).hexdigest() if pressure_daily_path.exists() else None,"wind_reference_validation_sha256":hashlib.sha256(wind_validation_path.read_bytes()).hexdigest() if wind_validation_path.exists() else None,"pilot_external_validation_sha256":hashlib.sha256(ext_path.read_bytes()).hexdigest() if ext_path.exists() else None,"pilot_statistics_sha256":hashlib.sha256(pilot_path.read_bytes()).hexdigest() if pilot_path.exists() else None,"records":records}
    OUT.write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"output":str(OUT),"records":len(records),"pilot_evidence_records":sum(r["evidence_status"]=="PILOT_EVIDENCE_AVAILABLE" for r in records),"external_validation_records":sum(r["external_validation"] for r in records),"temperature_expert_review_records":sum(bool(r.get("temperature_expert_review")) for r in records)},indent=2))

if __name__=="__main__": main()
