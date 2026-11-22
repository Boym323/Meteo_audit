#!/usr/bin/env python3
"""Render an auditable report for civil-period interval coverage and means."""
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    coverage=json.loads((ROOT/"INTERVAL_COVERAGE_REVIEW.json").read_text())
    adjusted=json.loads((ROOT/"INTERVAL_ADJUSTED_MONTHLY_MEANS.json").read_text())
    by_key={(r["period"],r["variable"]):r for r in adjusted["rows"]}
    overlaps=[r for r in coverage["results"] if r["overlap_detected"]]
    deltas=[r for r in adjusted["rows"] if r["mean_delta"] is not None]
    min_coverage=min(r["time_coverage"] for r in coverage["results"])
    max_coverage=max(r["time_coverage"] for r in coverage["results"])
    total_uncovered=sum(r["uncovered_seconds"] for r in coverage["results"])
    total_gap_events=sum(len(r["internal_gap_spans_utc"]) for r in coverage["results"])
    max_delta=max(abs(r["mean_delta"]) for r in deltas)
    db_sha=coverage["snapshot_id"]
    lines=[
      "# Civil-period archive interval review", "",
      "## Scope and source", "",
      f"- Candidate set: {coverage['candidate_count']} monthly statistics; {coverage['period_variable_count']} period-variable coverage rows and {adjusted['candidate_count']} interval-adjusted diagnostic means.",
      f"- Read-only source snapshot: `data/historical_value_concordance.sqlite`, SHA-256 `{db_sha}`.",
      "- Calendar: `Europe/Prague` local civil months, including CET/CEST boundary durations. SQLite `timestamp_evidence` was read with `mode=ro`; no database or archive value was changed.",
      "- Timestamp method: WeeWX archive timestamp is the interval end; support is `(end − target_interval, end]`. Every supported interval is clipped to its actual intersection with the civil month. Intervals ending just after month end are considered when they still overlap the month.",
      "",
      "## Coverage method", "",
      "Coverage is measured from the union of valid clipped intervals, not from row count or the sum of interval durations. This prevents repeated or overlapping records from creating artificial coverage over 100%. The review separately records invalid intervals, duplicated overlap duration, internal uncovered spans, period-edge uncovered time, and exact UTC epoch bounds for each gap or overlap.",
      f"Across {coverage['period_variable_count']} candidate-variable periods, union coverage ranges from {min_coverage:.4%} to {max_coverage:.4%}. No row exceeds 100%. There are {sum(r['overlap_rows'] for r in coverage['results']):,} overlapping interval rows in {len(overlaps)} period-variable groups, {total_gap_events:,} internal gap spans, and {total_uncovered:,} uncovered seconds summed across the period-variable groups. This sum counts time separately for each variable; it is not station-wide unique downtime.",
      "",
      "## Interval-weighted diagnostic means", "",
      "Only candidate B values with `SOURCE_MATCHED`, `RECOVERED_SOURCE`, or `RESTORED` provenance are used. Scalar values are weighted by retained overlap seconds. A record whose interval overlaps a previously included interval is excluded as a whole to avoid assigning duplicated time twice. Wind direction uses duration-weighted circular vectors and excludes calm or unknown-speed observations. Missing support is not imputed. These means are diagnostic; canonical candidates and publication decisions are not replaced.",
      f"Interval-weighted coverage ranges from {min(r['interval_time_coverage'] for r in adjusted['rows']):.4%} to {max(r['interval_time_coverage'] for r in adjusted['rows']):.4%}; {sum(r['overlap_excluded_rows'] for r in adjusted['rows']):,} candidate-variable interval rows were excluded for overlap. Across {len(deltas)} defined scalar/circular deltas, the largest absolute difference from the canonical timestamp mean is {max_delta:.6f} in the variable's native unit.",
      "",
      "### January 2026 regression values", "",
      "| Variable | Timestamp mean | Interval-weighted mean | Difference | Interval coverage |", "|---|---:|---:|---:|---:|"
    ]
    for variable in ("outTemp","outHumidity","barometer"):
        r=by_key[("2026-01",variable)]
        lines.append(f"| {variable} | {r['canonical_mean']:.12f} | {r['interval_adjusted_mean']:.12f} | {r['mean_delta']:+.12f} | {r['interval_time_coverage']:.4%} |")
    lines += ["", "### Periods with overlaps", "",
      "| Month | Variable | Overlap rows | Overlap seconds | Union coverage | Excluded in adjusted mean | Mean difference |", "|---|---|---:|---:|---:|---:|---:|"]
    for r in sorted(overlaps,key=lambda x:(x["period"],x["variable"])):
        a=by_key[(r["period"],r["variable"])]
        lines.append(f"| {r['period']} | {r['variable']} | {r['overlap_rows']} | {r['overlap_seconds']} | {r['time_coverage']:.4%} | {a['overlap_excluded_rows']} | {a['mean_delta'] if a['mean_delta'] is not None else '—'} |")
    lines += ["", "## Regression coverage", "",
      "`tests/test_time_bounds.py` exercises: first and last partial intervals at period boundaries; end-exclusive/start-exclusive timestamp predicates; leap-year February; spring and autumn DST month durations; long and irregular intervals; an off-grid timestamp; intervals crossing a period boundary; internal missing support; overlap union; rejection of invalid spans; and the invariant that union coverage cannot exceed 100%.",
      "", "## Reproduction", "",
      "```sh\npython3 scripts/build_interval_coverage_review.py\npython3 scripts/build_interval_adjusted_candidate_means.py\npython3 scripts/build_interval_time_method_report.py\nPYTHONPATH=src python3 -m unittest discover -s tests -p 'test_time_bounds.py' -v\n```", "",
      "## Input hashes", "",
      f"- `INTERVAL_COVERAGE_REVIEW.json`: `{hashlib.sha256((ROOT/'INTERVAL_COVERAGE_REVIEW.json').read_bytes()).hexdigest()}`",
      f"- `INTERVAL_ADJUSTED_MONTHLY_MEANS.json`: `{hashlib.sha256((ROOT/'INTERVAL_ADJUSTED_MONTHLY_MEANS.json').read_bytes()).hexdigest()}`",
      f"- `src/meteo_audit/time_bounds.py`: `{hashlib.sha256((ROOT/'src/meteo_audit/time_bounds.py').read_bytes()).hexdigest()}`"]
    (ROOT/"INTERVAL_TIME_METHOD_REVIEW.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"candidate_variable_periods":len(coverage["results"]),"overlap_groups":len(overlaps),"gap_spans":total_gap_events,"max_abs_mean_delta":max_delta,"report":"INTERVAL_TIME_METHOD_REVIEW.md"},indent=2))

if __name__=="__main__":main()
