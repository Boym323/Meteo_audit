#!/usr/bin/env python3
"""Build explicit monthly/annual publication decisions with evidence and reasons."""
import ast,csv,json
from collections import defaultdict,Counter
from pathlib import Path
import sys
import hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from meteo_audit.publication_classifier import classify_evidence

DATA=ROOT/"data"
FIELDS=("outTemp","outHumidity","pressure","barometer","altimeter","windSpeed","windGust","windDir")
NONDIR=tuple(x for x in FIELDS if x!="windDir")

def readcsv(name):
    with (DATA/name).open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))

def evidence_registry():
    """Load individual evidence, keyed to the exact period and variable."""
    path=ROOT/"MONTHLY_VALIDATION_EVIDENCE.json"
    if not path.exists(): return {}
    doc=json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema") not in {"loucka-monthly-validation-evidence-v1","loucka-monthly-validation-evidence-v2"} or not isinstance(doc.get("records"),list):
        raise ValueError("Invalid MONTHLY_VALIDATION_EVIDENCE.json schema")
    candidates=ROOT/"MONTHLY_PUBLICATION_CANDIDATES.json"
    variants=DATA/"STATISTICAL_VARIANTS_MONTHLY.csv"
    if doc.get("candidate_source_sha256")!=hashlib.sha256(candidates.read_bytes()).hexdigest():
        raise ValueError("Evidence registry is stale against monthly candidates")
    if doc.get("variant_source_sha256")!=hashlib.sha256(variants.read_bytes()).hexdigest():
        raise ValueError("Evidence registry is stale against statistical variants")
    if doc.get("schema")=="loucka-monthly-validation-evidence-v2":
        interval_variants=DATA/"INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_MONTHLY.csv"
        if doc.get("interval_variant_source_sha256")!=hashlib.sha256(interval_variants.read_bytes()).hexdigest():
            raise ValueError("Evidence registry is stale against interval-weighted variants")
    for key,rel in (("temperature_reference_validation_sha256","MONTHLY_TEMPERATURE_REFERENCE_VALIDATION.json"),("pilot_external_validation_sha256","PILOT_2026_01_EXTERNAL_VALIDATION.json"),("pilot_statistics_sha256","PILOT_2026_01_VALIDATED_STATISTICS.json")):
        source=ROOT/rel
        current=hashlib.sha256(source.read_bytes()).hexdigest() if source.exists() else None
        if doc.get(key)!=current: raise ValueError(f"Evidence registry is stale against {rel}")
    expected={(r["period"],r["variable"]) for r in json.loads(candidates.read_text())["candidates"]}
    result={}
    for record in doc["records"]:
        key=(record["period"],record["variable"])
        if key in result: raise ValueError(f"Duplicate evidence record: {key}")
        result[key]=record
    if set(result)!=expected:
        raise ValueError(f"Evidence registry key coverage mismatch: missing={len(expected-set(result))}, extra={len(set(result)-expected)}")
    return result

def main():
    stats=json.loads((DATA/"STATISTICAL_READINESS_CURRENT.json").read_text());monthly=stats["monthly"];annual=stats["annual"]
    evidence=evidence_registry()
    candidate_doc=json.loads((ROOT/"MONTHLY_PUBLICATION_CANDIDATES.json").read_text())
    candidates={(r["period"],r["variable"]):r for r in candidate_doc["candidates"]}
    variant={(r["period"],r["variable"]):r for r in readcsv("STATISTICAL_VARIANTS_MONTHLY.csv") if r["variant"]=="E_FULL_CURRENT_ARCHIVE"}
    b_variant={(r["period"],r["variable"]):r for r in readcsv("STATISTICAL_VARIANTS_MONTHLY.csv") if r["variant"]=="B_DOCUMENTED_SOURCE_AND_RECOVERY"}
    interval_monthly={(r["period"],r["variable"],r["variant"]):r for r in readcsv("INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_MONTHLY.csv")}
    interval_annual={(r["period"],r["variable"],r["variant"]):r for r in readcsv("INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_ANNUAL.csv")}
    variant_year={(r["period"],r["variable"]):r for r in readcsv("STATISTICAL_VARIANTS_ANNUAL.csv") if r["variant"]=="E_FULL_CURRENT_ARCHIVE"}
    by_year=defaultdict(list)
    for row in monthly:by_year[(row["period"][:4],row["variable"])].append(row)
    decisions=[]
    def append(row,scope,statistic,sample_pass,metric):
        period=row["period"];var=row["variable"];key=(period,var)
        is_candidate=scope=="MONTHLY" and statistic=="MEAN" and key in candidates
        vc=(b_variant.get(key,{}) if is_candidate else variant.get(key,{})) if scope=="MONTHLY" else variant_year.get((period,var),{})
        counts=ast.literal_eval(vc["provenance_counts"]) if isinstance(vc.get("provenance_counts"),str) and vc.get("provenance_counts") else (vc.get("provenance_counts",{}) if isinstance(vc.get("provenance_counts"),dict) else {})
        coverage=float(vc.get("coverage") or 0);expected=int(vc.get("expected_unique_slots") or 0)
        est=int(counts.get("ESTIMATED",0)) if is_candidate else int(row.get("estimated_values",0) or 0)
        unclassified=int(counts.get("UNCLASSIFIED",0)) if is_candidate else int(row.get("unclassified_values",0) or 0)
        conflict=int(counts.get("CONFLICTING_SOURCE",0));unknown_sources=int(counts.get("UNCLASSIFIED",0));original=int(counts.get("ORIGINAL_VERIFIED",0))
        protected=(period.startswith("2018-") and period[5:7] in {"01","02","03"}) or (scope=="ANNUAL" and period=="2018")
        diagnostic=period.startswith("2021") or (scope=="ANNUAL" and period=="2021")
        selected_variant="B_DOCUMENTED_SOURCE_AND_RECOVERY" if is_candidate else "E_FULL_CURRENT_ARCHIVE"
        interval_source=interval_monthly if scope=="MONTHLY" else interval_annual
        interval_row=interval_source.get((period,var,selected_variant))
        if interval_row is None:
            raise ValueError(f"Missing interval-weighted {scope.lower()} row for {(period,var,selected_variant)}")
        safe_cov=float(interval_row["time_coverage"] or 0)
        candidate_gap=int(interval_row["longest_uncovered_gap_seconds"] or 0)
        temporal={"variant":selected_variant,"safe_time_coverage":safe_cov,
                  "longest_uncovered_gap_seconds":candidate_gap,
                  "overlap_detected":int(interval_row.get("overlap_excluded_intervals") or 0)>0,
                  "overlap_excluded_intervals":int(interval_row.get("overlap_excluded_intervals") or 0),
                  "retained_intervals":int(interval_row.get("retained_intervals") or 0),
                  "weight_seconds":int(interval_row.get("weight_seconds") or 0),
                  "period_seconds":int(interval_row.get("period_seconds") or 0),
                  "interval_weighted_mean":float(interval_row["interval_mean"]) if interval_row.get("interval_mean") else None,
                  "interval_weighted_resultant":float(interval_row["interval_resultant"]) if interval_row.get("interval_resultant") else None,
                  "methodology":interval_row.get("methodology")}
        # Slot screens remain necessary, but cannot override unsafe or missing
        # interval-union coverage for the exact statistical variant used.
        coverage_threshold=.99 if statistic=="EXTREMA" else .95
        gap_threshold=1800 if statistic=="EXTREMA" else 21600
        sample_pass=bool(sample_pass and safe_cov>=coverage_threshold and candidate_gap<=gap_threshold)
        if is_candidate:
            sample_pass=bool(sample_pass and coverage>=.95)
        ev=evidence.get((period,var),{})
        status,reason=classify_evidence({"protected":protected,"diagnostic":diagnostic,"e4":var in {"rain","rainRate"},"integrity_ok":bool(stats.get("snapshot",{}).get("snapshot_utc")),"estimates":est,"representative":sample_pass,"sensor_error":bool(ev.get("sensor_error",False)),"unresolved_conflicts":conflict+unknown_sources,"physical_validation":bool(ev.get("physical_validation",False)),"provenance_sufficient":bool(counts.get("SOURCE_MATCHED",0) or counts.get("RECOVERED_SOURCE",0) or counts.get("RESTORED",0)),"external_validation":bool(ev.get("external_validation",False)),"independent_sensor_lineage":bool(ev.get("independent_sensor_lineage",False)),"documented_archive_continuity":bool(ev.get("documented_archive_continuity",False)),"explicit_limitations":bool(ev.get("explicit_limitations",False))})
        if unclassified or conflict or unknown_sources:reason += f" Provenance also contains {unclassified} unclassified builder values, {unknown_sources} source-unclassified values, and {conflict} conflicting source fields."
        if is_candidate and ev.get("candidate_status")=="BLOCKED_NO_SAME_VARIANT_POSITIVE_WIND_SPEED":reason += " Candidate mean is unavailable because B has no same-variant positive windSpeed."
        permitted={"PROTECTED":"Parallel review only.","DIAGNOSTIC_ONLY":"Diagnostics only.","BLOCKED_E4":"Raw archive-as-recorded display only with E4 disclosure; no totals or rates.","REVIEW_REQUIRED_ESTIMATES":"Research review only; no definitive statistic until estimates are separately assessed.","NOT_REPRESENTATIVE_COVERAGE":"Exploratory analysis only; period not representative under the declared screen.","REVIEW_REQUIRED_PROVENANCE":"Research/pilot review only; disclose source dependencies and unresolved lineage.","REVIEW_REQUIRED_CONFLICTS":"Research review only until conflict evidence is resolved.","REVIEW_REQUIRED_SENSOR_VALIDATION":"Research/pilot review only pending physical and sensor validation.","READY_FOR_PUBLICATION":"Publication recommendation under verified evidence; publication still requires separate authorization.","READY_WITH_DISCLOSED_LIMITATIONS":"Recommendation with disclosed private-station lineage limitations; publication still requires separate authorization."}[status]
        rep="PASS_MEAN_SCREEN" if sample_pass and statistic=="MEAN" else ("PASS_EXTREMA_SCREEN" if sample_pass and statistic=="EXTREMA" else "FAIL_OR_NOT_SCREENED")
        decisions.append({"period":period,"scope":scope,"variable":var,"statistic":statistic,"publication_readiness":status,"evidence_state":"Per-statistic evidence record supplied." if ev else "No individual physical/reference evidence record; explicit review required.","evidence_record":ev or None,"interval_coverage":temporal,"permitted_use":permitted,"representativeness":rep,"coverage_used":coverage,"candidate_selection_coverage":candidates[key].get("selection_coverage") if is_candidate else None,"expected_unique_slots":expected,"variant_on_grid_values":int(vc.get("variant_on_grid_values",0) or 0),"recovered_source_values":int(counts.get("RECOVERED_SOURCE",0)),"source_matched_values":int(counts.get("SOURCE_MATCHED",0)),"restored_values":int(counts.get("RESTORED",0)),"corrected_values":int(counts.get("CORRECTED",0)),"estimated_values":est,"conflicting_source_values":conflict,"unclassified_values":unclassified,"unclassified_source_fields":unknown_sources,"missing_measured_slots":int(vc.get("missing_measured_slots",0) or 0),"original_verified_values":original,"uncertainty":reason,"rejection_reason":reason,"statistics_used":("B_DOCUMENTED_SOURCE_AND_RECOVERY monthly candidate; B slot and clipped-interval coverage both gate representativeness." if is_candidate else f"E_FULL_CURRENT_ARCHIVE values; {selected_variant} clipped-interval coverage also gates representativeness." )})
    for r in monthly:
        cov=float(r["coverage_measured"] or 0);days=int(r["days_passing_mean_rule"]);days_req=int(r["days_required_mean_rule"]);gap=int(r["max_observed_or_edge_gap_seconds"]);cad=float(r["modal_cadence_share"] or 0)
        mean_pass=bool(int(r["expected_unique_slots"]) and cov>=.95 and days>=days_req and gap<=21600 and cad>=.90)
        append(r,"MONTHLY","MEAN",mean_pass,{})
        if r["variable"]!="windDir":
            ext_pass=bool(int(r["expected_unique_slots"]) and cov>=.99 and int(r["days_passing_extrema_rule"])>=int(r["days_required_extrema_rule"]) and gap<=1800 and cad>=.90 and not int(r["estimated_values"]))
            append(r,"MONTHLY","EXTREMA",ext_pass,{})
    for r in annual:
        months=by_year[(r["period"],r["variable"])]
        cov=float(r["coverage_measured"] or 0);gap=int(r["max_observed_or_edge_gap_seconds"]);cad=float(r["modal_cadence_share"] or 0)
        mean_months=sum(bool(int(x["expected_unique_slots"]) and float(x["coverage_measured"] or 0)>=.95 and int(x["days_passing_mean_rule"])>=int(x["days_required_mean_rule"]) and int(x["max_observed_or_edge_gap_seconds"])<=21600 and float(x["modal_cadence_share"] or 0)>=.90) for x in months)
        mean_pass=bool(int(r["expected_unique_slots"]) and cov>=.95 and int(r["days_passing_mean_rule"])>=int(r["days_required_mean_rule"]) and gap<=21600 and cad>=.90 and mean_months>=11)
        append(r,"ANNUAL","MEAN",mean_pass,{})
        if r["variable"]!="windDir":
            ext_months=sum(bool(int(x["expected_unique_slots"]) and float(x["coverage_measured"] or 0)>=.99 and int(x["days_passing_extrema_rule"])>=int(x["days_required_extrema_rule"]) and int(x["max_observed_or_edge_gap_seconds"])<=1800 and float(x["modal_cadence_share"] or 0)>=.90 and not int(x["estimated_values"])) for x in months)
            ext_pass=bool(int(r["expected_unique_slots"]) and cov>=.99 and int(r["days_passing_extrema_rule"])>=int(r["days_required_extrema_rule"]) and gap<=1800 and cad>=.90 and ext_months>=11 and not int(r["estimated_values"]))
            append(r,"ANNUAL","EXTREMA",ext_pass,{})
    # Explicit E4 rows cover all archive periods even though those fields have
    # deliberately been omitted from the computed statistical tables.
    periods=sorted({r["period"] for r in monthly});years=sorted({r["period"] for r in annual})
    for scope,values in (("MONTHLY",periods),("ANNUAL",years)):
        for period in values:
            for var in ("rain","rainRate"):
                decisions.append({"period":period,"scope":scope,"variable":var,"statistic":"TOTAL_OR_RATE","publication_readiness":"BLOCKED_E4","evidence_state":"E4 counter/driver semantics unresolved","permitted_use":"Raw archive-as-recorded display only with E4 disclosure; no totals or rates.","representativeness":"NOT_SCREENED","coverage_used":"","expected_unique_slots":"","variant_on_grid_values":"","recovered_source_values":0,"source_matched_values":0,"restored_values":0,"corrected_values":0,"estimated_values":0,"conflicting_source_values":0,"unclassified_values":"","unclassified_source_fields":"","missing_measured_slots":"","original_verified_values":0,"uncertainty":"No unit/driver/reset/interval semantics established for this epoch.","rejection_reason":"BLOCKED_E4","statistics_used":"None."})
    counts=Counter(r["publication_readiness"] for r in decisions)
    path=DATA/"PUBLICATION_READINESS_DECISIONS.csv"
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(decisions[0]));w.writeheader()
        for row in decisions:
            w.writerow({k:(json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(dict,list)) else v) for k,v in row.items()})
    manifest={"schema":"loucka-publication-readiness-decisions-v2","source_stats_snapshot_utc":stats["snapshot"]["snapshot_utc"],"source_variant_snapshot":"data/STATISTICAL_VARIANTS_MANIFEST.json","source_interval_monthly_sha256":hashlib.sha256((DATA/"INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_MONTHLY.csv").read_bytes()).hexdigest(),"source_interval_annual_sha256":hashlib.sha256((DATA/"INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_ANNUAL.csv").read_bytes()).hexdigest(),"matrix_rows":len(decisions),"publication_readiness_counts":dict(counts),"ready_for_publication_rows":counts["READY_FOR_PUBLICATION"],"ready_with_disclosed_limitations_rows":counts["READY_WITH_DISCLOSED_LIMITATIONS"],"publication_authorized":False,"rules":"Positive outcomes are implemented but require integrity, value provenance, physical validation, representative coverage, no estimates, no known faults or unresolved conflicts, and either independent validation or documented continuity plus limitations. Slot screens and exact-variant clipped interval-union coverage/gap screens both constrain representativeness. No positive outcome is inferred from coverage alone."}
    (DATA/"PUBLICATION_READINESS_DECISIONS.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
