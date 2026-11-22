#!/usr/bin/env python3
"""Render a complete candidate/coverage report from current validation records."""
import hashlib, json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    availability = json.loads((ROOT / "TEMPERATURE_REFERENCE_AVAILABILITY.json").read_text())
    validation = json.loads((ROOT / "MONTHLY_TEMPERATURE_REFERENCE_VALIDATION.json").read_text())
    files = ["MONTHLY_PUBLICATION_CANDIDATES.json", "TEMPERATURE_REFERENCE_AVAILABILITY.json",
             "MONTHLY_TEMPERATURE_REFERENCE_VALIDATION.json", "data/chmi-2026-recent/manifest.json",
             "data/chmi-priority-temperature/manifest.json"]
    hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
    stats = defaultdict(Counter)
    for c in availability["candidates"]:
        stats[c["period"][:4]][c["reference_status"]] += 1
    lines = [
        "# Monthly temperature validation review", "",
        "Scope: all 54 selected monthly outTemp means. Candidate selection is not validation.", "",
        "## Evidence coverage", "",
        f"- {availability['summary'].get('SAME_MONTH_SUBDAILY_AVAILABLE', 0)} candidate months have same-month subdaily CHMI references; {len(validation['station_month_results'])} station-month comparisons were processed.",
        f"- {availability['summary'].get('DAILY_CONTEXT_ONLY', 0)} months have CHMI daily context only; daily extrema are not paired directly to a monthly mean.",
        f"- {availability['summary'].get('NO_LOCAL_SAME_MONTH_REFERENCE', 0)} months have no cached same-month local reference.",
        f"- {sum(r['matched_pairs'] for r in validation['station_month_results']):,} exact UTC pairs were analyzed across {len(validation['station_month_results'])} unique station-month comparisons.",
        "- References use exact UTC timestamps, CHMI quality code zero, and no interpolation. Available adjacent UTC-month files are loaded to cover the Europe/Prague civil-month edges.",
        "- CHMI data is regional plausibility evidence, not Loučka sensor calibration or proof of measurement identity. CHMI 10-minute temperature time-function semantics were not established from the inspected metadata; interval-average versus instantaneous differences remain a limitation.",
        "- January 2026 remains the independent regression case. The separate pilot uses one station; where both CHMI stations are cached, the candidate comparison evaluates each station once per month. Duplicate cached copies are excluded.",
        "",
        "## Candidate counts by year", "",
        "| Year | Candidates | Same-month subdaily | Daily context | No local reference |", "|---|---:|---:|---:|---:|"
    ]
    for year, counts in sorted(stats.items()):
        lines.append(f"| {year} | {sum(counts.values())} | {counts['SAME_MONTH_SUBDAILY_AVAILABLE']} | {counts['DAILY_CONTEXT_ONLY']} | {counts['NO_LOCAL_SAME_MONTH_REFERENCE']} |")
    lines += ["", "## Exact-UTC station-month results", "",
              "| Period | Station | Expected slots | Valid reference | Matched | Ref coverage | Bias °C | MAE °C | RMSE °C | Corr. | Daily bias °C |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in sorted(validation["station_month_results"], key=lambda x:(x["period"],x["station_id"])):
        def f(v, digits=3): return "—" if v is None else f"{v:.{digits}f}"
        lines.append(f"| {r['period']} | {r['station_id']} | {r['expected_10_minute_slots_in_local_civil_month']} | {r['valid_reference_slots_in_month']} | {r['matched_pairs']} | {r['reference_slot_coverage_of_expected']:.2%} | {f(r['bias_reference_minus_loucka_C'])} | {f(r['mae_C'])} | {f(r['rmse_C'])} | {f(r['correlation'])} | {f(r['daily_mean_comparison']['mean_daily_bias_reference_minus_loucka_C'])} |")
    lines += ["", "## Difference distribution and timing", "",
              "Machine-readable station-month rows include difference p05/p50/p95, six-hour local-time bias, daily mean comparisons, expected and valid slots, unmatched slots, exact source paths, and file hashes. See `MONTHLY_TEMPERATURE_REFERENCE_VALIDATION.json`.", "",
              "A regional difference or high correlation does not establish Loučka sensor accuracy. No reference value is substituted, no calibration correction is made, and months without compatible references remain explicitly unvalidated.", "",
              "### Input hashes", ""]
    for path, digest in hashes.items(): lines.append(f"- `{path}`: `{digest}`")
    (ROOT / "TEMPERATURE_MONTHLY_VALIDATION_REPORT.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(json.dumps({"candidate_months": availability["candidate_count"],
                      "station_month_comparisons": len(validation["station_month_results"]),
                      "same_month_reference_candidates": availability["summary"].get("SAME_MONTH_SUBDAILY_AVAILABLE",0)}, indent=2))

if __name__ == "__main__": main()
