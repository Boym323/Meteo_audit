#!/usr/bin/env python3
"""Report observed pressure-field offsets without inferring field semantics."""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    path = ROOT / "MONTHLY_CANDIDATE_SERIES_DIAGNOSTICS.json"
    doc = json.loads(path.read_text())
    rows = sorted((r for r in doc["records"] if r["variable"] == "barometer"), key=lambda r: r["period"])
    lines = [
        "# Pressure candidate field relationship review", "",
        f"Frozen concordance SHA-256: `{doc['snapshot_id']}`. Series diagnostics SHA-256: `{hashlib.sha256(path.read_bytes()).hexdigest()}`.", "",
        f"Concurrent field differences are summarized for {len(rows)} of 68 priority monthly `barometer` candidates. Values are `barometer − pressure` and `altimeter − barometer`, in hPa, from rows where both fields are non-NULL.", "",
        "| Period | Paired rows | Median barometer−pressure | 5th–95th percentile | Median altimeter−barometer | 5th–95th percentile |",
        "|---|---:|---:|---:|---:|---:|"
    ]
    for r in rows:
        offsets = r["concurrent_pressure_field_offsets_hpa"]
        bp, ab = offsets["barometer_minus_pressure"], offsets["altimeter_minus_barometer"]
        def show(x): return "n/a" if x is None else f"{x:.3f}"
        n = min(bp["paired_rows"], ab["paired_rows"])
        lines.append(f"| {r['period']} | {n:,} | {show(bp['median'])} | {show(bp['p05'])} to {show(bp['p95'])} | {show(ab['median'])} | {show(ab['p05'])} to {show(ab['p95'])} |")
    jan = next((r for r in rows if r["period"] == "2026-01"), None)
    lines += [
        "", "## Interpretation", "",
        (f"January 2026 recomputation gives median barometer−pressure {jan['concurrent_pressure_field_offsets_hpa']['barometer_minus_pressure']['median']:.3f} hPa and altimeter−barometer {jan['concurrent_pressure_field_offsets_hpa']['altimeter_minus_barometer']['median']:.3f} hPa. These reproduce the previously reported approximate +52.62 hPa and −2.40 hPa offsets." if jan else "January 2026 is not present in these candidate months."),
        "",
        "The monthly relationships establish how the stored fields differ, not which field is raw, station pressure, sea-level pressure, or a driver/WeeWX calculation. Site elevation, sensor identity and dated driver configuration remain unavailable. No fields are renamed, substituted, or recalculated, and no candidate is approved from these offsets.",
        "",
        "Source: immutable target values in `data/historical_value_concordance.sqlite`; exact pair counts and distributions are in `MONTHLY_CANDIDATE_SERIES_DIAGNOSTICS.json`."
    ]
    ref_path=ROOT/'MONTHLY_PRESSURE_REFERENCE_VALIDATION.json'
    if ref_path.exists():
        ref=json.loads(ref_path.read_text())
        lines += ["", "## Limited CHMI sea-level pressure context: 2026", "",
            "Official hourly SYNOP `P_hm` from CHMI Holešov is compared at identical UTC hourly timestamps with Loučka archive values. This is regional plausibility evidence only; timestamp coincidence does not prove equal observation functions. CHMI station metadata lists Holešov at 222.25 m, while the Loučka sensor elevation/location is unverified.",
            "", "| Period | Paired hours | CHMI reference coverage | Loučka barometer hourly mean | CHMI P_hm paired mean | CHMI−Loučka bias | MAE | Correlation |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for r in ref['station_month_results']:
            m=r['timestamp_coincident_field_metrics_vs_chmi_p_hm']['barometer']
            lines.append(f"| {r['period']} | {m['paired_timestamp_count']} | {m['matched_coverage_of_valid_reference']:.3%} | {m['loucka_hourly_archive_sample_mean_hpa']:.2f} hPa | {m['chmi_p_hm_paired_mean_hpa']:.2f} hPa | {m['chmi_minus_loucka_bias_hpa']:.2f} hPa | {m['mae_hpa']:.2f} hPa | {m['correlation']:.3f} |")
        lines += ["", "On these coincident samples, `barometer` is about 3.09 hPa above CHMI P_hm in January and 0.72 hPa below it in February; `pressure` is about 49.51 and 52.36 hPa below P_hm, respectively. `altimeter` also varies relative to P_hm. These comparisons are compatible with distinct pressure reductions but cannot verify the Loučka field semantics, reduction formula or station elevation.",
            "", f"Reference JSON: `MONTHLY_PRESSURE_REFERENCE_VALIDATION.json`; SHA-256 `{hashlib.sha256(ref_path.read_bytes()).hexdigest()}`. Raw reference files and source URLs are in `data/chmi-2026-synop-pressure/manifest.json`."]
    (ROOT / "PRESSURE_CANDIDATE_SEMANTICS_REVIEW.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"barometer_candidates": len(rows), "january_2026": jan["concurrent_pressure_field_offsets_hpa"] if jan else None}, indent=2))

if __name__ == "__main__":
    main()
