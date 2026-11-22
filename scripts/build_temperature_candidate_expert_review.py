#!/usr/bin/env python3
"""Build candidate-specific, non-calibrating temperature review dispositions."""
from __future__ import annotations
import hashlib, json, math, statistics, sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from validate_temperature_monthly_references import parse_reference, period_bounds

OUT_JSON=ROOT/"TEMPERATURE_CANDIDATE_EXPERT_REVIEW.json"
OUT_MD=ROOT/"TEMPERATURE_CANDIDATE_EXPERT_REVIEW.md"
STATIONS=("0-203-0-11777","0-203-0-11778")

def metrics(pairs):
    if not pairs:
        return {"paired_slots":0,"bias_11777_minus_11778_C":None,"mae_C":None,"rmse_C":None,"correlation":None,"difference_quantiles_C":{"p05":None,"p50":None,"p95":None}}
    diffs=[a-b for _,a,b in pairs]
    mx=statistics.mean(a for _,a,_ in pairs);my=statistics.mean(b for _,_,b in pairs)
    den=math.sqrt(sum((a-mx)**2 for _,a,_ in pairs)*sum((b-my)**2 for _,_,b in pairs))
    ordered=sorted(diffs)
    def q(frac):
        pos=(len(ordered)-1)*frac;lo=int(pos);hi=min(lo+1,len(ordered)-1)
        return ordered[lo]+(ordered[hi]-ordered[lo])*(pos-lo)
    return {"paired_slots":len(pairs),"bias_11777_minus_11778_C":statistics.mean(diffs),
      "mae_C":statistics.mean(abs(x) for x in diffs),"rmse_C":math.sqrt(statistics.mean(x*x for x in diffs)),
      "correlation":sum((a-mx)*(b-my) for _,a,b in pairs)/den if den else None,
      "difference_quantiles_C":{"p05":q(.05),"p50":q(.5),"p95":q(.95)}}

def sign_relation(a,b):
    if a is None or b is None:return "NOT_COMPUTABLE"
    if a>0 and b>0:return "BOTH_REFERENCES_WARMER_THAN_LOUCKA"
    if a<0 and b<0:return "BOTH_REFERENCES_COOLER_THAN_LOUCKA"
    if a==0 and b==0:return "BOTH_REFERENCE_BIASES_ZERO"
    if a==0 or b==0:return "ONE_REFERENCE_BIAS_ZERO"
    return "REFERENCE_BIAS_SIGNS_SPLIT"

def main():
    candidates=json.loads((ROOT/"MONTHLY_PUBLICATION_CANDIDATES.json").read_text())["candidates"]
    temps={x["period"]:x for x in candidates if x["variable"]=="outTemp"}
    availability=json.loads((ROOT/"TEMPERATURE_REFERENCE_AVAILABILITY.json").read_text())
    availability_by_period={x["period"]:x for x in availability["candidates"] if x["variable"]=="outTemp"}
    validation=json.loads((ROOT/"MONTHLY_TEMPERATURE_REFERENCE_VALIDATION.json").read_text())
    station_rows={}
    for r in validation["station_month_results"]:
        station_rows.setdefault(r["period"],{})[r["station_id"]]=r
    daily=json.loads((ROOT/"CHMI_DAILY_TEMPERATURE_CONTEXT_REVIEW.json").read_text())
    daily_rows={}
    for r in daily["results"]:daily_rows.setdefault(r["period"],{})[r["station_id"]]=r
    rows=[]
    for period,candidate in sorted(temps.items()):
        status=availability_by_period[period]["reference_status"]
        refs=station_rows.get(period,{})
        interstation=None
        if all(s in refs for s in STATIONS):
            merged={}
            for station in STATIONS:
                result=refs[station]
                for source in result["reference_files_used"]:
                    values,_,_=parse_reference(ROOT/source["path"],station)
                    merged.setdefault(station,{}).update(values)
            lo,hi=period_bounds(period)
            common=[]
            for ts in sorted(set(merged[STATIONS[0]])&set(merged[STATIONS[1]])):
                if not lo<ts<=hi:continue
                a,b=merged[STATIONS[0]][ts],merged[STATIONS[1]][ts]
                if a["quality"] in ("0","0.0") and b["quality"] in ("0","0.0"):
                    common.append((ts,a["value"],b["value"]))
            expected=refs[STATIONS[0]]["expected_10_minute_slots_in_local_civil_month"]
            interstation={**metrics(common),"expected_local_civil_month_slots":expected,
              "coverage_of_expected_slots":len(common)/expected if expected else 0,
              "cadence":"exact UTC timestamps; both station quality codes zero; no interpolation"}
        daily_pair=daily_rows.get(period,{})
        station_bias={s:refs[s].get("bias_reference_minus_loucka_C") for s in STATIONS if s in refs}
        if len(station_bias)==2:
            bias_relation=sign_relation(station_bias[STATIONS[0]],station_bias[STATIONS[1]])
            spread=abs(station_bias[STATIONS[0]]-station_bias[STATIONS[1]])
        elif len(daily_pair)==2 and all(daily_pair[s].get("difference_chmi_daily_mean_minus_loucka_monthly_mean_C") is not None for s in STATIONS):
            b0=daily_pair[STATIONS[0]]["difference_chmi_daily_mean_minus_loucka_monthly_mean_C"]
            b1=daily_pair[STATIONS[1]]["difference_chmi_daily_mean_minus_loucka_monthly_mean_C"]
            bias_relation=sign_relation(b0,b1);spread=abs(b0-b1)
        else:
            bias_relation="INSUFFICIENT_TWO_STATION_EVIDENCE";spread=None
        daily_summary=[{"station_id":s,"expected_days":daily_pair[s]["expected_daily_slots"],
          "valid_days":daily_pair[s]["valid_daily_mean_slots_quality_zero"],
          "coverage":daily_pair[s]["daily_coverage"],
          "chmi_mean_of_daily_means_C":daily_pair[s]["chmi_mean_of_daily_means_C"],
          "daily_context_minus_loucka_monthly_mean_C":daily_pair[s]["difference_chmi_daily_mean_minus_loucka_monthly_mean_C"],
          "reference_sha256":daily_pair[s]["reference_sha256"]}
          for s in STATIONS if s in daily_pair and daily_pair[s]["valid_daily_mean_slots_quality_zero"]>0]
        if status=="SAME_MONTH_SUBDAILY_AVAILABLE":
            disposition="NO_NUMERIC_CORRECTION_SUPPORTED_BY_REGIONAL_COMPARISON"
            basis="Two-station exact-time metrics describe regional temporal tracking and station spread, but do not identify a Loučka sensor error or a unique replacement monthly mean."
            next_step="Resolve dated Loučka sensor/driver/configuration and siting; establish CHMI T timestamp time-function; assess the measured inter-station spread against local microclimate before any accuracy judgment."
        elif daily_summary:
            disposition="NO_NUMERIC_CORRECTION_SUPPORTED_BY_DAILY_CONTEXT"
            basis="Daily regional means provide aggregate context only; unknown daily window and weighting prevent direct equivalence to the Loučka civil-month archive mean."
            next_step="Map CHMI daily DT/TIMEFUNC AVG windows and daily weighting to Europe/Prague archive intervals, or obtain same-month subdaily observations."
        else:
            disposition="NO_REFERENCE_EVIDENCE; REVIEW_REQUIRED"
            basis="No usable local same-month reference was available in the frozen reference set."
            next_step="Acquire an authorized independent reference with compatible cadence and period."
        if period=="2026-01":
            disposition="EXISTING_JANUARY_PILOT_RETAINED; NO_OVERRIDE"
            basis="This review does not supersede the existing January specialist pilot; the second station is retained as regional corroboration, not calibration."
            next_step="Keep the pilot's disclosed limitations; resolve physical sensor epoch and configuration before expanding any readiness status."
        rows.append({"period":period,"variable":"outTemp","candidate_monthly_mean_C":candidate["value"],
          "candidate_coverage":candidate["coverage"],"local_reference_status":status,
          "station_month_metrics":{s:{"matched_pairs":refs[s]["matched_pairs"],"matched_coverage":refs[s]["matched_coverage_of_valid_reference"],
            "bias_reference_minus_loucka_C":refs[s]["bias_reference_minus_loucka_C"],"mae_C":refs[s]["mae_C"],"rmse_C":refs[s]["rmse_C"],
            "correlation":refs[s]["correlation"],"daily_mean_comparison":refs[s]["daily_mean_comparison"],
            "six_hour_local_time_bias_C":refs[s]["six_hour_local_time_bias_C"],"reference_sha256":refs[s]["reference_sha256"]} for s in STATIONS if s in refs},
          "interstation_exact_pair_metrics":interstation,"daily_context_station_metrics":daily_summary or None,
          "two_reference_bias_relation":bias_relation,"absolute_bias_difference_between_references_C":spread,
          "expert_disposition":disposition,"decision_basis":basis,"next_evidence_step":next_step,
          "existing_specialist_pilot_recorded":period=="2026-01",
          "correction_authorized":False,"publication_authorized":False})
    catalog=json.loads((ROOT/"REFERENCE_STATION_CATALOG.json").read_text())
    station_meta={x["station_id"]:{k:x.get(k) for k in ("name","latitude","longitude","elevation_m")}
      for x in catalog["stations"] if x.get("station_id") in STATIONS}
    a=station_meta[STATIONS[0]];b=station_meta[STATIONS[1]]
    if None not in (a["latitude"],a["longitude"],b["latitude"],b["longitude"]):
        phi1,phi2=math.radians(a["latitude"]),math.radians(b["latitude"])
        dphi=phi2-phi1;dlambda=math.radians(b["longitude"]-a["longitude"])
        hav=math.sin(dphi/2)**2+math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        station_distance_km=6371.0088*2*math.asin(math.sqrt(hav))
    else:station_distance_km=None
    paired=[r["interstation_exact_pair_metrics"] for r in rows if r["interstation_exact_pair_metrics"]]
    pair_summary={key:{"median":statistics.median(x[key] for x in paired if x.get(key) is not None),
      "minimum":min(x[key] for x in paired if x.get(key) is not None),"maximum":max(x[key] for x in paired if x.get(key) is not None)}
      for key in ("bias_11777_minus_11778_C","mae_C","rmse_C","correlation")}
    subdaily_direction_counts=dict(Counter(r["two_reference_bias_relation"] for r in rows if r["interstation_exact_pair_metrics"]))
    daily_direction_counts=dict(Counter(r["two_reference_bias_relation"] for r in rows if r["daily_context_station_metrics"]))
    doc={"schema":"loucka-temperature-candidate-expert-review-v1","snapshot_id":validation["snapshot_id"],
      "candidate_count":len(rows),"subdaily_two_station_months":sum(bool(r["interstation_exact_pair_metrics"]) for r in rows),
      "daily_context_only_months":sum(bool(r["daily_context_station_metrics"]) and not r["station_month_metrics"] for r in rows),
      "reference_station_metadata":station_meta,"reference_station_distance_km":station_distance_km,
      "loucka_coordinates_available":False,"subdaily_interstation_summary":pair_summary,
      "subdaily_loucka_bias_relation_counts":subdaily_direction_counts,"daily_context_bias_relation_counts":daily_direction_counts,
      "decision_policy":"Candidate-specific regional evidence is assessed without a universal bias/correlation threshold. No regional reference is treated as Loučka calibration; numeric corrections and publication are not authorized.",
      "source_sha256":{"candidates":hashlib.sha256((ROOT/"MONTHLY_PUBLICATION_CANDIDATES.json").read_bytes()).hexdigest(),
       "reference_availability":hashlib.sha256((ROOT/"TEMPERATURE_REFERENCE_AVAILABILITY.json").read_bytes()).hexdigest(),
       "subdaily_validation":hashlib.sha256((ROOT/"MONTHLY_TEMPERATURE_REFERENCE_VALIDATION.json").read_bytes()).hexdigest(),
       "reference_station_catalog":hashlib.sha256((ROOT/"REFERENCE_STATION_CATALOG.json").read_bytes()).hexdigest(),
       "daily_context":hashlib.sha256((ROOT/"CHMI_DAILY_TEMPERATURE_CONTEXT_REVIEW.json").read_bytes()).hexdigest()},"results":rows}
    OUT_JSON.write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    pair_summary_line=(f"Across the {len(paired)} exact-paired subdaily months, station-to-station median bias (Vizovice minus Luhačovice) is {pair_summary['bias_11777_minus_11778_C']['median']:.3f} °C (range {pair_summary['bias_11777_minus_11778_C']['minimum']:.3f} to {pair_summary['bias_11777_minus_11778_C']['maximum']:.3f}); median MAE is {pair_summary['mae_C']['median']:.3f} °C (range {pair_summary['mae_C']['minimum']:.3f} to {pair_summary['mae_C']['maximum']:.3f}); median correlation is {pair_summary['correlation']['median']:.3f} (range {pair_summary['correlation']['minimum']:.3f} to {pair_summary['correlation']['maximum']:.3f}). For Loučka versus the two references, sign patterns were: " + ", ".join(f"{k}: {v}" for k,v in sorted(subdaily_direction_counts.items())) + ". These are observed patterns, not thresholds or calibration results.")
    lines=["# Candidate-specific monthly temperature expert review","",
      f"Scope: {len(rows)} of 54 selected monthly `outTemp` means. {doc['subdaily_two_station_months']} months have exact-UTC subdaily comparisons at both CHMI stations; {doc['daily_context_only_months']} months have daily regional context only.","",
      "This review makes a separate disposition for every candidate but applies no universal bias or correlation threshold. Regional agreement supports temporal context only. It does not establish Loučka sensor identity, calibration, siting equivalence, or a numeric replacement. No correction or publication is authorized.","",
      f"Reference metadata: {STATIONS[0]} ({a['name']}, elevation {a['elevation_m']} m) and {STATIONS[1]} ({b['name']}, elevation {b['elevation_m'] if b['elevation_m'] is not None else 'unknown'} m) are approximately {station_distance_km:.1f} km apart. Loučka sensor coordinates are unavailable, so its distances to either station cannot be stated.","",
      pair_summary_line,"",
      "## Candidate dispositions and evidence", "",
      "| Month | Loučka mean °C | Reference mode | Two-station bias relation | Ref bias spread °C | Station 11777 bias °C | Station 11778 bias °C | Decision |", "|---|---:|---|---|---:|---:|---:|---|"]
    for r in rows:
        s=r["station_month_metrics"]
        b0=s.get(STATIONS[0],{}).get("bias_reference_minus_loucka_C")
        b1=s.get(STATIONS[1],{}).get("bias_reference_minus_loucka_C")
        if b0 is None and r["daily_context_station_metrics"]:
            dr={x["station_id"]:x for x in r["daily_context_station_metrics"]}
            b0=dr.get(STATIONS[0],{}).get("daily_context_minus_loucka_monthly_mean_C")
            b1=dr.get(STATIONS[1],{}).get("daily_context_minus_loucka_monthly_mean_C")
        def f(x):return "—" if x is None else f"{x:.3f}"
        lines.append(f"| {r['period']} | {r['candidate_monthly_mean_C']:.3f} | {r['local_reference_status']} | {r['two_reference_bias_relation']} | {f(r['absolute_bias_difference_between_references_C'])} | {f(b0)} | {f(b1)} | {r['expert_disposition']} |")
    lines += ["", "## Inter-station metrics", "",
      "Where both subdaily station files exist, JSON includes exact paired UTC slot count, coverage, inter-station bias, MAE, RMSE, correlation, and difference quantiles after both station quality codes are zero-filtered. These are descriptive station-to-station measurements, not decision thresholds.",
      "", "## Evidence limits and next steps", "",
      "Each JSON record includes its metric-level evidence and a period-specific next evidence step. The common blockers are unresolved Loučka physical sensor epoch, driver/configuration and siting, and unverified CHMI temperature time-function semantics. Daily-only candidates additionally require mapping of CHMI `DT`/`TIMEFUNC` day windows and weighting to the local archive period.",
      "", f"Snapshot SHA-256: `{doc['snapshot_id']}`. Input hashes are recorded in `TEMPERATURE_CANDIDATE_EXPERT_REVIEW.json`."]
    OUT_MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"candidate_months":len(rows),"subdaily_two_station_months":doc["subdaily_two_station_months"],"daily_context_only_months":doc["daily_context_only_months"],"report":str(OUT_MD)},indent=2))

if __name__=="__main__":main()
