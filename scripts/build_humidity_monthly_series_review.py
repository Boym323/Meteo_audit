#!/usr/bin/env python3
"""Summarize saturation/plateau diagnostics across all humidity candidates."""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    path = ROOT / "MONTHLY_CANDIDATE_SERIES_DIAGNOSTICS.json"
    doc = json.loads(path.read_text())
    rows = sorted((r for r in doc["records"] if r["variable"] == "outHumidity"), key=lambda r: r["period"])
    saturated = [r for r in rows if r["saturated_humidity_rows_ge_99_pct"]]
    ranked = sorted(saturated, key=lambda r: r["longest_humidity_ge_99_run_seconds"] or 0, reverse=True)
    total_high = sum(r["saturated_humidity_rows_ge_99_pct"] or 0 for r in rows)
    md = [
        "# Humidity candidate series screening",
        "",
        f"Frozen concordance SHA-256: `{doc['snapshot_id']}`. Series diagnostic SHA-256: `{hashlib.sha256(path.read_bytes()).hexdigest()}`.",
        "",
        f"The archive-series scan covers {len(rows)} of 45 priority monthly outHumidity candidates. {len(saturated)} candidates contain at least one value at or above 99%; across those candidates there are {total_high:,} such rows.",
        "",
        "## Longest runs at or above 99%",
        "",
        "Run continuity uses adjacent archived rows and breaks when the timestamp gap exceeds 1.5 times the larger adjacent interval. A run may contain both 99% and 100% values.",
        "",
        "| Period | Rows ≥99% | Longest run | Value at longest exact run | Candidate rows |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in ranked[:15]:
        duration = r["longest_humidity_ge_99_run_seconds"] or 0
        exact = r["longest_run_value"]
        exact_duration = r["longest_consecutive_exact_value_run_seconds"]
        md.append(f"| {r['period']} | {r['saturated_humidity_rows_ge_99_pct']:,} | {duration/3600:.2f} h | {exact} ({exact_duration/3600:.2f} h exact) | {r['target_nonnull_rows']:,} |")
    md += [
        "",
        "January 2026 remains sensor-review-required: the detailed pilot review identifies two 99% plateaus, the longest lasting 15 h 40 min. That differs from the aggregate period scan's definition of any consecutive ≥99% run, so the values are not directly interchangeable.",
        "",
        "These runs are flags for targeted context review. High humidity and long repeated values can arise from weather, quantization, saturation, condensation, or sensor behavior; the archive series alone cannot distinguish these explanations. The station's humidity sensor model, upper measurement limit, siting, ventilation, and dated configuration remain undocumented. No correction is applied and no candidate receives positive readiness from this screen.",
        "",
        "Source: `MONTHLY_CANDIDATE_SERIES_DIAGNOSTICS.json`; target values from the frozen value concordance. The scan does not treat archive-copy matches as independent sensor validation."
    ]
    (ROOT / "HUMIDITY_MONTHLY_SERIES_REVIEW.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"humidity_candidates": len(rows), "months_with_ge99": len(saturated), "ge99_rows": total_high,
                      "longest_ge99_hours": (ranked[0]["longest_humidity_ge_99_run_seconds"] / 3600) if ranked else 0}, indent=2))

if __name__ == "__main__":
    main()
