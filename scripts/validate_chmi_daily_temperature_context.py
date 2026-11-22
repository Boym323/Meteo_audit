#!/usr/bin/env python3
"""Compare selected Loučka monthly temperature means with CHMI daily context."""
from __future__ import annotations
import csv, hashlib, json, calendar
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/chmi-historical-daily-temperature"
OUT_JSON = ROOT / "CHMI_DAILY_TEMPERATURE_CONTEXT_REVIEW.json"
OUT_MD = ROOT / "CHMI_DAILY_TEMPERATURE_CONTEXT_REVIEW.md"

def main() -> None:
    candidates = json.loads((ROOT / "MONTHLY_PUBLICATION_CANDIDATES.json").read_text())["candidates"]
    temps = {x["period"]: x for x in candidates if x["variable"] == "outTemp"}
    manifest = json.loads((DATA / "manifest.json").read_text())
    manifest_files = {x["station_id"]: x for x in manifest["files"]}
    station_values = {}
    for path in sorted((DATA / "raw").glob("*.csv")):
        station = path.name.removeprefix("dly-").removesuffix("-T.csv")
        if station not in manifest_files or hashlib.sha256(path.read_bytes()).hexdigest() != manifest_files[station]["sha256"]:
            raise SystemExit(f"CHMI daily evidence is missing from manifest or hash-mismatched: {path}")
        values = defaultdict(dict)
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("ELEMENT") != "T" or row.get("TIMEFUNC") != "AVG" or row.get("QUALITY") != "0.0":
                    continue
                dt = row.get("DT", "")[:10]
                raw = row.get("VALUE", "").strip()
                if len(dt) == 10 and raw:
                    try:
                        date.fromisoformat(dt)
                        values[dt[:7]][dt] = float(raw)
                    except ValueError:
                        pass
        station_values[station] = values

    local_avail = json.loads((ROOT / "TEMPERATURE_REFERENCE_AVAILABILITY.json").read_text())
    by_period = {x["period"]: x for x in local_avail["candidates"] if x["variable"] == "outTemp"}
    results=[]
    for period, candidate in sorted(temps.items()):
        availability=by_period[period]["reference_status"]
        if availability == "SAME_MONTH_SUBDAILY_AVAILABLE":
            continue
        year, month = map(int, period.split("-"))
        expected = calendar.monthrange(year, month)[1]
        for station, months in sorted(station_values.items()):
            daily=months.get(period,{})
            vals=list(daily.values())
            mean=sum(vals)/len(vals) if vals else None
            results.append({"period":period,"station_id":station,"candidate_monthly_mean_C":candidate["value"],
              "candidate_coverage":candidate["coverage"],"local_subdaily_reference_status":availability,
              "expected_daily_slots":expected,"valid_daily_mean_slots_quality_zero":len(vals),
              "daily_coverage":len(vals)/expected,"chmi_mean_of_daily_means_C":mean,
              "difference_chmi_daily_mean_minus_loucka_monthly_mean_C":None if mean is None else mean-candidate["value"],
              "daily_mean_min_C":min(vals) if vals else None,"daily_mean_max_C":max(vals) if vals else None,
              "reference_path":f"data/chmi-historical-daily-temperature/raw/dly-{station}-T.csv",
              "reference_sha256":next(x["sha256"] for x in manifest["files"] if x["station_id"]==station),
              "interpretation":"Regional context only; daily observation window and day weighting do not establish equivalence with Loučka civil-month archive mean."})
    doc={"schema":"loucka-chmi-daily-temperature-context-review-v1","snapshot_id":json.loads((ROOT/"AUTOMATED_VALIDATION_RUN.json").read_text())["snapshot_id"],
      "scope":"outTemp monthly candidates without same-month local 10-minute CHMI reference; daily T,AVG context for two nearby CHMI stations",
      "method":"Quality code 0.0 and TIMEFUNC AVG only; mean of available daily means within the named YYYY-MM; no imputation; compare aggregates for regional context only.",
      "limitations":["CHMI daily-day boundaries/time-function semantics were not mapped to Loučka archive-end civil-month boundaries.","Mean of daily means is not guaranteed to equal a time-weighted monthly mean.","Regional differences do not establish sensor calibration or prove a Loučka value is erroneous.","This evidence does not alter the shared classifier or publication decisions."],
      "inputs":{"candidate_sha256":hashlib.sha256((ROOT/"MONTHLY_PUBLICATION_CANDIDATES.json").read_bytes()).hexdigest(),
        "availability_sha256":hashlib.sha256((ROOT/"TEMPERATURE_REFERENCE_AVAILABILITY.json").read_bytes()).hexdigest(),
        "manifest_sha256":hashlib.sha256((DATA/"manifest.json").read_bytes()).hexdigest()},"result_count":len(results),"results":results}
    OUT_JSON.write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    lines=["# ČHMÚ daily temperature context for monthly Loučka candidates","",
      "This review adds official daily mean temperature context for outTemp candidate months without same-month local subdaily references. The values are not treated as a direct monthly validation because daily observation windows, civil-month alignment, and daily weighting have not been shown equivalent to the Loučka archive method.","",
      f"Scope: {len({r['period'] for r in results})} candidate months × two stations ({len(results)} rows). Only CHMI `T`, `TIMEFUNC=AVG`, `QUALITY=0.0` values were used. No imputation, calibration, correction, or classifier override was applied.","",
      "| Month | Local subdaily status | Station | Days / expected | CHMI mean of daily means °C | Loučka monthly mean °C | Difference °C |","|---|---|---|---:|---:|---:|---:|"]
    for r in results:
        def fmt(x): return "—" if x is None else f"{x:.2f}"
        lines.append(f"| {r['period']} | {r['local_subdaily_reference_status']} | {r['station_id']} | {r['valid_daily_mean_slots_quality_zero']}/{r['expected_daily_slots']} | {fmt(r['chmi_mean_of_daily_means_C'])} | {r['candidate_monthly_mean_C']:.2f} | {fmt(r['difference_chmi_daily_mean_minus_loucka_monthly_mean_C'])} |")
    lines += ["","## Limits","",*([f"- {x}" for x in doc["limitations"]]),"","Input hashes are in the JSON artifact. Source files and retrieval metadata are in `data/chmi-historical-daily-temperature/manifest.json`."]
    OUT_MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"result_count":len(results),"candidate_months":len({r['period'] for r in results}),
      "months_with_both_stations":sum(all(any(x['period']==p and x['station_id']==s and x['valid_daily_mean_slots_quality_zero']>0 for x in results) for s in station_values) for p in temps if by_period[p]['reference_status']!='SAME_MONTH_SUBDAILY_AVAILABLE')},indent=2))

if __name__ == "__main__": main()
