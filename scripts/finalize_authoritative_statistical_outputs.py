#!/usr/bin/env python3
"""Apply deterministic calendar/status finalization and validate saved stats."""
from __future__ import annotations
import csv,hashlib,json,math,os
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];DATA=Path(os.environ.get("METEO_AUDIT_READINESS_OUTPUT_DIR",ROOT/"data"))
COLLECTIONS={"daily":"daily","monthly":"monthly","annual":"annual","provenance":"provenance","missing":"missing_data","blockers":"publication_blockers","recommendations":"reconstruction_recommendations"}
FILES={"daily":"DAILY_STATISTICAL_READINESS_CURRENT.csv","monthly":"MONTHLY_STATISTICAL_READINESS_CURRENT.csv","annual":"ANNUAL_STATISTICAL_READINESS_CURRENT.csv","provenance":"STATISTICAL_PROVENANCE_CURRENT.csv","missing":"STATISTICAL_MISSING_DATA_CURRENT.csv","blockers":"STATISTICAL_PUBLICATION_BLOCKERS_CURRENT.csv","recommendations":"STATISTICAL_RECONSTRUCTION_RECOMMENDATIONS_CURRENT.csv"}

def write_csv(path,rows):
    if not rows:path.write_text("\n",encoding="utf-8");return
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    path=DATA/"STATISTICAL_READINESS_CURRENT.json";doc=json.loads(path.read_text(encoding="utf-8"));snap=doc["snapshot"]
    last=snap["local_coverage_through"]
    for r in doc["daily"]:
        day=r["local_day"];yr=day[:4];mm=day[5:7];exp=int(r["expected_unique_slots"])
        if yr=="2018" and mm in {"01","02","03"}:status="PROTECTED_Q1_2018_REVIEW_REQUIRED"
        elif yr=="2021":status="DIAGNOSTIC_2021_NO_PRODUCTION_DECISION"
        elif day==last:status="PARTIAL_CURRENT_LOCAL_DAY"
        elif not exp:status="NOT_AVAILABLE_BEFORE_FIRST_OBSERVED_EPOCH"
        elif int(r["raw_nonnull_including_offgrid"])==0:status="NO_ARCHIVE_ROW_SENSOR_EPOCH_VS_UNRESOLVED_GAP"
        elif int(r["estimated_values"]):status="REVIEW_REQUIRED_ESTIMATED_VALUES"
        elif int(r["unclassified_values"]):status="REVIEW_REQUIRED_PROVENANCE_UNKNOWN"
        elif r["daily_mean_sampling_pass"] in (True,"True"):status="READY_WITH_LIMITATIONS"
        else:status="NOT_REPRESENTATIVE_COVERAGE_OR_GAP"
        r["readiness"]=status

    for r in doc["monthly"]:
        period=r["period"];var=r["variable"]
        if var=="windDir":r["extrema_readiness"]="NOT_APPLICABLE_CIRCULAR_VARIABLE"
        elif period in {"2018-01","2018-02","2018-03"}:r["extrema_readiness"]="PROTECTED_Q1_2018_REVIEW_REQUIRED"
        elif period.startswith("2021-"):r["extrema_readiness"]="DIAGNOSTIC_2021_NO_PRODUCTION_DECISION"
        elif period==last[:7]:r["extrema_readiness"]="PARTIAL_CURRENT_MONTH_NOT_CERTIFIABLE"
        elif int(r["estimated_values"]):r["extrema_readiness"]="REVIEW_REQUIRED_ESTIMATED_VALUES_INCLUDED"
        elif int(r["unclassified_values"]):r["extrema_readiness"]="REVIEW_REQUIRED_PROVENANCE_UNKNOWN"

    month_groups=defaultdict(list)
    for r in doc["monthly"]:month_groups[(r["period"][:4],r["variable"])].append(r)
    for r in doc["annual"]:
        period=r["period"];var=r["variable"];months=month_groups[(period,var)]
        r["months_passing_mean_rule"]=sum(x["readiness"]=="READY_WITH_LIMITATIONS" for x in months)
        r["months_passing_extrema_rule"]=sum(x["extrema_readiness"]=="READY_WITH_LIMITATIONS" for x in months)
        if var=="windDir":r["extrema_readiness"]="NOT_APPLICABLE_CIRCULAR_VARIABLE"
        elif period=="2018":r["extrema_readiness"]="REVIEW_REQUIRED_Q1_2018_PROTECTED_SUBPERIOD"
        elif period=="2021":r["extrema_readiness"]="DIAGNOSTIC_2021_NO_PRODUCTION_DECISION"
        elif period=="2009":r["extrema_readiness"]="PARTIAL_FIRST_OBSERVED_YEAR_NOT_CERTIFIABLE"
        elif period==last[:4]:r["extrema_readiness"]="PARTIAL_YEAR_NOT_CERTIFIABLE"
        elif int(r["estimated_values"]):r["extrema_readiness"]="REVIEW_REQUIRED_ESTIMATED_VALUES_INCLUDED"
        elif int(r["unclassified_values"]):r["extrema_readiness"]="REVIEW_REQUIRED_PROVENANCE_UNKNOWN"
        elif r["extrema_readiness"]=="READY_WITH_LIMITATIONS" and r["months_passing_extrema_rule"]<11:r["extrema_readiness"]="NOT_READY_FEWER_THAN_11_MONTHS"
        if r["readiness"]=="READY_WITH_LIMITATIONS" and r["months_passing_mean_rule"]<11:r["readiness"]="NOT_READY_FEWER_THAN_11_MONTHS"

    doc["provenance"]=[{k:r[k] for k in ("period","variable","recovered_source_values","restored_values","corrected_values","estimated_values","unclassified_values","original_verified_values","readiness")} for r in doc["monthly"]]
    blockers=[]
    for r in doc["monthly"]:
        if r["readiness"]!="READY_WITH_LIMITATIONS":
            blockers.append({"period":r["period"],"variable":r["variable"],"readiness":r["readiness"],"estimated_values":r["estimated_values"],"unclassified_values":r["unclassified_values"],"missing_measured_slots":r["missing_measured_slots"],"publication_blocker":"Yes; current readiness is not sufficient for definitive climate publication."})
    doc["publication_blockers"]=blockers
    snap["methods"]["calm_wind"]="Count exact on-grid windDir rows with windSpeed=0 and positive recorded interval."
    snap["snapshot_semantics"]=("snapshot_utc and source_snapshot_sha256 identify the immutable read-only value-concordance snapshot used as the only archive input; archive_max_timestamp is its data edge." if snap.get("source_snapshot_sha256") else "snapshot_utc is the completion time of this report build. Archive rows came from one read-only consistent transaction whose snapshot began at the first archive-table query before the streaming passes; archive_max_timestamp is the data edge inside that transaction.")
    snap["methods"]["mean_screen_thresholds"]="Monthly: coverage >=0.95, >=90% of days pass day/night coverage, modal cadence share >=0.90, longest gap <=6h. Annual: at least 11 constituent monthly mean screens pass."
    snap["methods"]["extrema_screen_thresholds"]="Monthly: coverage >=0.99, >=95% of days pass, modal cadence share >=0.90, longest gap <=30m. Annual: at least 11 constituent monthly extrema screens pass. Unknown provenance and estimates remain review-only."
    snap["script_sha256"]=hashlib.sha256((ROOT/"scripts/build_authoritative_statistical_readiness.py").read_bytes()).hexdigest()

    checks={"daily_rows":len(doc["daily"]),"monthly_rows":len(doc["monthly"]),"annual_rows":len(doc["annual"]),"coverage_ratio_mismatches":0,"negative_missing_slots":0,"nonzero_original_verified_values":0,"wind_direction_extrema_rows":0,"rain_fields_included":False,"partial_current_day_rows":0,"protected_q1_rows":0,"diagnostic_2021_rows":0,"weighted_period_mean_mismatches":0,"calm_count_period_mismatches":0,"periods_status_ready_mean":0,"periods_status_ready_extrema":0}
    daily_groups=defaultdict(list)
    for d in doc["daily"]:
        if d["variable"] in {"outTemp","outHumidity","windSpeed","windGust","windDir","barometer","pressure","altimeter"}:daily_groups[(d["local_day"][:7],d["variable"])].append(d)
        exp=int(d["expected_unique_slots"]);meas=int(d["non_estimated_on_grid_slots"])
        if exp and abs(float(d["coverage_measured"] or 0)-meas/exp)>1.1e-8:checks["coverage_ratio_mismatches"]+=1
        if int(d["missing_measured_slots"])<0:checks["negative_missing_slots"]+=1
        if int(d["original_verified_values"]):checks["nonzero_original_verified_values"]+=1
        if d["local_day"]==last and d["readiness"]=="PARTIAL_CURRENT_LOCAL_DAY":checks["partial_current_day_rows"]+=1
        if d["local_day"].startswith("2018-") and d["local_day"][5:7] in {"01","02","03"} and d["readiness"]!="PROTECTED_Q1_2018_REVIEW_REQUIRED":checks["protected_q1_rows"]+=1
        if d["local_day"].startswith("2021-") and d["readiness"]!="DIAGNOSTIC_2021_NO_PRODUCTION_DECISION":checks["diagnostic_2021_rows"]+=1
        if d["variable"]=="windDir" and d["daily_extrema_sampling_pass"]:checks["wind_direction_extrema_rows"]+=1
    for m in doc["monthly"]:
        days=daily_groups[(m["period"],m["variable"])]
        if m["variable"]=="windDir":
            s=sum(float(x["circular_sin_current"]) for x in days);c=sum(float(x["circular_cos_current"]) for x in days)
            mean=math.degrees(math.atan2(s,c))%360 if s or c else ""
        else:
            ss=sum(float(x["sum_weighted_current"]) for x in days);ww=sum(float(x["weight_seconds_current"]) for x in days);mean=ss/ww if ww else ""
        got=m["mean_current_archive_time_weighted"]
        if (got=="") != (mean=="") or (got!="" and abs(float(got)-float(mean))>1e-7):checks["weighted_period_mean_mismatches"]+=1
        if m["variable"]=="windDir":
            calm=sum(int(x.get("calm_wind_samples_exact_zero_speed_with_direction") or 0) for x in days)
            if calm!=int(m.get("calm_wind_samples_exact_zero_speed_with_direction") or 0):checks["calm_count_period_mismatches"]+=1
        if m["readiness"]=="READY_WITH_LIMITATIONS":checks["periods_status_ready_mean"]+=1
        if m["extrema_readiness"]=="READY_WITH_LIMITATIONS":checks["periods_status_ready_extrema"]+=1
    checks["rain_fields_included"]=any(r["variable"].lower() in {"rain","rainrate"} for r in doc["monthly"])
    passed=all(v==0 or k in {"daily_rows","monthly_rows","annual_rows","partial_current_day_rows","periods_status_ready_mean","periods_status_ready_extrema"} for k,v in checks.items()) and checks["partial_current_day_rows"]==8
    checks.update({"status":"PASS" if passed else "FAIL","snapshot_utc":snap["snapshot_utc"],"script_sha256":snap["script_sha256"]})
    (DATA/"STATISTICAL_READINESS_VALIDATION.json").write_text(json.dumps(checks,indent=2)+"\n",encoding="utf-8")
    for key,collection in COLLECTIONS.items():write_csv(DATA/FILES[key],doc[collection])
    path.write_text(json.dumps(doc,ensure_ascii=False,separators=(",",":"),default=str)+"\n",encoding="utf-8")
    print(json.dumps(checks,indent=2))

if __name__=="__main__":main()
