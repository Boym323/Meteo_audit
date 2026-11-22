#!/usr/bin/env python3
"""Refresh the humidity review with all available exact-UTC regional comparisons."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    base=(ROOT/'HUMIDITY_MONTHLY_SERIES_REVIEW.md').read_text(encoding='utf-8').rstrip()
    validation=json.loads((ROOT/'MONTHLY_HUMIDITY_REFERENCE_VALIDATION.json').read_text())
    daily=json.loads((ROOT/'HUMIDITY_DAILY_REFERENCE_CONTEXT.json').read_text())
    rows=validation['station_month_results']
    diagnostic=json.loads((ROOT/'MONTHLY_CANDIDATE_SERIES_DIAGNOSTICS.json').read_text())
    humidity=sorted((r for r in diagnostic['records'] if r['variable']=='outHumidity'),key=lambda r:r['period'])
    by_period={}
    for row in rows:by_period.setdefault(row['period'],[]).append(row)
    daily_by_period={}
    for row in daily['results']:
        if row['valid_quality_zero_days']>0:daily_by_period.setdefault(row['period'],[]).append(row)
    text=base+f"\n\n## Regional comparison extension: {validation['candidate_period_count']} humidity months screened\n\n"
    text+=(f"Exact UTC 10-minute CHMI data were compared for {len(set(r['period'] for r in rows))} of {validation['candidate_period_count']} priority humidity candidate months, with {len(rows)} station-month results. References include Vizovice (0-203-0-11777) and Kladná-Žilín (0-203-0-11778) where available. The comparator is regional evidence only. "
           'CHMI quality code 0 is required; no interpolation is used. The candidate value is the existing monthly Loučka mean.\n\n')
    text+=f"Candidates without compatible same-month 10-minute humidity references: {len(validation['candidate_periods_without_compatible_subdaily_reference'])} ({', '.join(validation['candidate_periods_without_compatible_subdaily_reference'])}). Plateau runs are separately screened across all {validation['candidate_period_count']} candidate months.\n\n"
    text+='| Period | CHMI station | Matched pairs | Reference coverage | Loučka paired RH | CHMI paired RH | CHMI−Loučka bias | MAE | RMSE | Correlation |\n|---|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'
    for r in rows:
        text+=f"| {r['period']} | {r['station_id']} | {r['matched_pairs']} | {r['matched_coverage_of_valid_reference']:.3%} | {r['loucka_paired_mean_pct']:.2f}% | {r['reference_paired_mean_pct']:.2f}% | {r['bias_reference_minus_loucka_percentage_points']:.2f} pp | {r['mae_percentage_points']:.2f} pp | {r['rmse_percentage_points']:.2f} pp | {r['correlation']:.3f} |\n"
    text+='\n## Individual archive-series outcome for every priority candidate\n\n'
    text+=('Each candidate below has a separate archive-series screen. “≥99% rows” and the longest continuous run are flags, not fault diagnoses. Subdaily bias ranges summarize exact-UTC comparisons; daily values are aggregate regional context only. CHMI daily aggregation window and weighting are not documented as equivalent to the Loučka civil-month archive mean.\n\n')
    text+='| Period | Loučka mean RH | Rows ≥99% | Longest ≥99% run | Longest exact-value run | 10m CHMI station-months | 10m bias range | Daily context (station: mean; Δ pp) |\n|---|---:|---:|---:|---:|---:|---:|---|\n'
    for candidate in humidity:
        period=candidate['period']; refs=by_period.get(period,[])
        count=int(candidate['saturated_humidity_rows_ge_99_pct'] or 0)
        run_seconds=int(candidate['longest_humidity_ge_99_run_seconds'] or 0)
        exact_seconds=int(candidate['longest_consecutive_exact_value_run_seconds'] or 0)
        exact_value=candidate['longest_run_value']
        bias=(f"{min(r['bias_reference_minus_loucka_percentage_points'] for r in refs):.2f} to {max(r['bias_reference_minus_loucka_percentage_points'] for r in refs):.2f} pp"
              if refs else 'no reference')
        daily_parts=[f"{r['station_name']}: {r['mean_of_daily_means_pct']:.1f}% ({r['difference_daily_context_minus_loucka_pp']:+.1f} pp)" for r in daily_by_period.get(period,[]) if r['mean_of_daily_means_pct'] is not None]
        daily_text='; '.join(daily_parts) if daily_parts else 'no quality-0 data'
        text+=(f"| {period} | {candidate['arithmetic_sample_mean']:.2f}% | {count:,} ({count/candidate['target_nonnull_rows']:.1%}) | "
               f"{run_seconds/3600:.2f} h | {exact_value} for {exact_seconds/3600:.2f} h | {len(refs)} | {bias} | {daily_text} |\n")
    for period in ('2026-01','2026-02'):
        month_rows=[r for r in rows if r['period']==period]
        runs=month_rows[0]['local_ge99_plateau_runs_with_reference_context'] if month_rows else []
        longest=max(runs,key=lambda x:x['duration_minutes'],default=None)
        if longest:
            means=[]
            for station_row in month_rows:
                matching=next((r for r in station_row['local_ge99_plateau_runs_with_reference_context'] if r['start_utc']==longest['start_utc']),None)
                if matching:means.append(matching['reference_mean_rh_pct'])
            if means:
                text+=f"\n- {period}: {len(validation['local_ge99_plateau_runs'][period])} local ≥99% runs of at least 10 minutes; longest was {longest['duration_minutes']/60:.2f} hours. That episode's mean RH at matched CHMI stations ranged from {min(means):.1f}% to {max(means):.1f}%.\n"
    text+='\nAcross periods, results support only regional consistency and plateau context. Daily comparisons are not matched external validation and do not set the candidate evidence external-validation flag. They do not establish physical sensor accuracy, distinguish sensor saturation from quantization or condensation, or authorize a correction. Sensor model, siting, configuration, and epoch-specific driver semantics remain unresolved. The January pilot remains sensor-review-required; no month is cleared solely by regional comparison.\n\n'
    text+=f"Subdaily reference validation JSON SHA-256: `{__import__('hashlib').sha256((ROOT/'MONTHLY_HUMIDITY_REFERENCE_VALIDATION.json').read_bytes()).hexdigest()}`. Daily context JSON SHA-256: `{__import__('hashlib').sha256((ROOT/'HUMIDITY_DAILY_REFERENCE_CONTEXT.json').read_bytes()).hexdigest()}`. Snapshot SHA-256: `{validation['snapshot_id']}`.\n"
    (ROOT/'HUMIDITY_SENSOR_VALIDATION_REPORT.md').write_text(text,encoding='utf-8')
    print(json.dumps({'station_month_rows':len(rows),'report':'HUMIDITY_SENSOR_VALIDATION_REPORT.md'},indent=2))

if __name__=='__main__':main()
