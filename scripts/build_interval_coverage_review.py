#!/usr/bin/env python3
"""Measure actual interval union for selected local-civil monthly candidates."""
from __future__ import annotations
import bisect, hashlib, json, sqlite3, zlib
from collections import defaultdict
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from meteo_audit.time_bounds import local_period_bounds, interval_overlap_seconds, interval_union_metrics

def main():
    candidates=json.loads((ROOT/"MONTHLY_PUBLICATION_CANDIDATES.json").read_text())["candidates"]
    variables={}
    for row in candidates:
        variables.setdefault(row["period"],set()).add(row["variable"])
    periods=sorted(variables)
    bounds={p:local_period_bounds(p) for p in periods}
    starts=[bounds[p][0] for p in periods]
    ends=[bounds[p][1] for p in periods]
    spans=defaultdict(list)
    counts=defaultdict(lambda:{"rows":0,"invalid_interval":0,"clipped_rows":0,"unclipped_seconds":0})
    dbp=ROOT/"data/historical_value_concordance.sqlite"
    db=sqlite3.connect(f"file:{dbp.resolve()}?mode=ro",uri=True)
    for i,(ts,raw_interval,blob) in enumerate(db.execute("SELECT dateTime,target_interval,comparison_zlib FROM timestamp_evidence ORDER BY dateTime")):
        ts=int(ts); interval=int(raw_interval or 0)
        if interval<=0 or interval>1440:
            idx=bisect.bisect_left(starts,ts)-1
            if idx>=0 and starts[idx]<ts<=ends[idx]:
                fields=json.loads(zlib.decompress(blob))
                period=periods[idx]
                for var in variables[period]:
                    if fields.get(var,{}).get("target_value") is not None:
                        counts[(period,var)]["rows"]+=1
                        counts[(period,var)]["invalid_interval"]+=1
            continue
        interval_start=ts-interval*60
        first=bisect.bisect_right(ends,interval_start)
        last=bisect.bisect_left(starts,ts)-1
        if first>last:
            continue
        overlaps=[]
        for j in range(first,last+1):
            period=periods[j]
            overlap=interval_overlap_seconds(ts,interval*60,*bounds[period])
            if overlap:
                overlaps.append((period,overlap))
        if not overlaps:
            continue
        fields=json.loads(zlib.decompress(blob))
        for period,overlap in overlaps:
            lo,hi=bounds[period]
            for var in variables[period]:
                if fields.get(var,{}).get("target_value") is None:
                    continue
                key=(period,var);a=counts[key];a["rows"]+=1
                a["unclipped_seconds"]+=interval*60
                if overlap<interval*60:a["clipped_rows"]+=1
                spans[key].append((max(interval_start,lo),min(ts,hi)))
        if i and i%250000==0: print(f"processed_rows={i}",flush=True)
    db.close()
    results=[]
    for period in periods:
        duration=bounds[period][1]-bounds[period][0]
        for variable in sorted(variables[period]):
            key=(period,variable);m=interval_union_metrics(spans[key]);a=counts[key]
            coverage=m["covered_seconds"]/duration
            if coverage>1:
                raise AssertionError(f"Interval union coverage exceeded 100% for {period} {variable}")
            results.append({"period":period,"variable":variable,"rows":a["rows"],
              "valid":len(spans[key]),"invalid_interval":a["invalid_interval"],
              "clipped_rows":a["clipped_rows"],"unclipped_seconds":a["unclipped_seconds"],
              "period_seconds":duration,"covered_seconds":m["covered_seconds"],
              "uncovered_seconds":duration-m["covered_seconds"],
              "time_coverage":coverage,"safe_time_coverage":coverage,
              "overlap_detected":m["overlap_rows"]>0,"overlap_rows":m["overlap_rows"],
              "overlap_seconds":m["overlap_seconds"],
              "internal_gap_seconds":m["internal_gap_seconds"],
              "gap_seconds_between_intervals":m["internal_gap_seconds"],
              "internal_gap_spans_utc":[{"start_epoch":a,"end_epoch":b,"seconds":b-a} for a,b in m["gap_spans"]],
              "overlap_spans_utc":[{"start_epoch":a,"end_epoch":b,"seconds":b-a} for a,b in m["overlap_spans"]],
              "interval_semantics":"timestamp is interval end; extent is (end-interval,end]; all valid target intervals intersecting the Europe/Prague civil month are clipped to the period and union-measured, including ends just beyond its boundary"})
    out={"schema":"loucka-interval-coverage-review-v3","snapshot_id":hashlib.sha256(dbp.read_bytes()).hexdigest(),
      "candidate_count":len(candidates),"period_variable_count":len(results),"results":results,
      "transition_anomalies":[],"transition_anomaly_note":"Per-period union metrics report actual internal uncovered and overlapping seconds; the prior global transition list was omitted because it attributed cross-month transitions to only one period."}
    (ROOT/"INTERVAL_COVERAGE_REVIEW.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"period_variable_count":len(results),
      "clipped_rows":sum(r["clipped_rows"] for r in results),
      "overlap_period_variables":sum(r["overlap_detected"] for r in results),
      "invalid_interval_rows":sum(r["invalid_interval"] for r in results),
      "max_coverage":max((r["time_coverage"] for r in results),default=0),
      "period_variable_rows_with_uncovered_time":sum(r["uncovered_seconds"]>0 for r in results)},indent=2))

if __name__=="__main__":main()
