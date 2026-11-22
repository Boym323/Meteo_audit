#!/usr/bin/env python3
"""Build a sourced pressure-semantics decision review from candidate and reference evidence."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=json.loads((ROOT/'MONTHLY_PRESSURE_REFERENCE_VALIDATION.json').read_text())
    series=json.loads((ROOT/'MONTHLY_CANDIDATE_SERIES_DIAGNOSTICS.json').read_text())
    rows=[r for r in series['records'] if r['variable']=='barometer']
    lines=['# Pressure semantics validation review','',f"Frozen target concordance: `{p['snapshot_id']}`. Pressure reference manifest SHA-256: `{p['reference_manifest_sha256']}`.",'',
      '## Scope and disposition','',
      'The evidence covers all 68 priority monthly `barometer` candidates as concurrent field-offset diagnostics, plus exact-UTC-hour regional CHMI pressure context for January and February 2026. This evidence does not identify which Loučka field is raw, station pressure, sea-level pressure or a driver/WeeWX derivation. Keep pressure candidates in review; no field substitution or recalculation is authorized.','',
      '## Candidate-wide field relationships','',
      f"`barometer − pressure` and `altimeter − barometer` distributions are available for {len(rows)} of 68 monthly barometer candidates in `PRESSURE_CANDIDATE_SEMANTICS_REVIEW.md`. January 2026 reproduces medians of +52.620 hPa and −2.399 hPa across 8,888 paired archive rows. The relationship changes seasonally: the 68 candidates show a range of monthly medians rather than one constant offset.",'',
      '## Official CHMI regional context','',
      'CHMI Holešov hourly SYNOP `P_hm` is sea-level-reduced pressure. Comparisons below use exact UTC hourly timestamps, quality code 0, and no interpolation. CHMI metadata gives Holešov elevation 222.25 m; verified Loučka sensor coordinates and elevation are still absent. Hourly timestamp equality does not establish equal time functions for CHMI and WeeWX samples.','',
      '| Period | Expected hours | Valid CHMI hours | Matched hours | Coverage | Local barometer mean | CHMI P_hm mean | CHMI−barometer bias | MAE | RMSE | Correlation |',
      '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in p['station_month_results']:
        m=r['timestamp_coincident_field_metrics_vs_chmi_p_hm']['barometer']
        lines.append(f"| {r['period']} | {r['expected_hourly_utc_slots_in_local_civil_month']} | {r['valid_p_hm_slots']} | {m['paired_timestamp_count']} | {m['matched_coverage_of_valid_reference']:.3%} | {m['loucka_hourly_archive_sample_mean_hpa']:.2f} hPa | {m['chmi_p_hm_paired_mean_hpa']:.2f} hPa | {m['chmi_minus_loucka_bias_hpa']:.2f} hPa | {m['mae_hpa']:.2f} hPa | {m['rmse_hpa']:.2f} hPa | {m['correlation']:.3f} |")
    lines += ['', '### Other stored fields at the same timestamps','',
      '| Period | Local `pressure` mean | CHMI−pressure bias | Local `altimeter` mean | CHMI−altimeter bias | Median barometer−pressure | Median altimeter−barometer |',
      '|---|---:|---:|---:|---:|---:|---:|']
    for r in p['station_month_results']:
        m=r['timestamp_coincident_field_metrics_vs_chmi_p_hm'];o=r['coincident_archive_field_offsets_hpa']
        lines.append(f"| {r['period']} | {m['pressure']['loucka_hourly_archive_sample_mean_hpa']:.2f} hPa | {m['pressure']['chmi_minus_loucka_bias_hpa']:.2f} hPa | {m['altimeter']['loucka_hourly_archive_sample_mean_hpa']:.2f} hPa | {m['altimeter']['chmi_minus_loucka_bias_hpa']:.2f} hPa | {o['barometer_minus_pressure_median']:.2f} hPa | {o['altimeter_minus_barometer_median']:.2f} hPa |")
    lines += ['',
      'These observations support only a limited regional consistency check: local `barometer` is within a few hPa of CHMI P_hm in these months, while local `pressure` is roughly 50–52 hPa lower. That pattern is consistent with distinct station-level and reduced pressure quantities, but it does not prove that is what the Loučka fields mean. The offset is not used to infer Loučka elevation, and no pressure value is corrected. The 2026 results do not resolve the other 66 barometer candidates or historical sensor epochs.','',
      '## Remaining evidence required','',
      'To decide the fields’ physical meaning, obtain the dated Loučka station elevation and coordinates, model/identity of the pressure sensor, gateway and firmware, WeeWX driver/version, complete configuration snapshots and the specific reduction formula/parameters. Row-wise reproduction should start from a verified raw station-pressure input and temperature. CHMI Holešov is regional context, not a substitute for those deployment records.','',
      f"Reference source manifest: `data/chmi-2026-synop-pressure/manifest.json`. Validation JSON SHA-256: `{hashlib.sha256((ROOT/'MONTHLY_PRESSURE_REFERENCE_VALIDATION.json').read_bytes()).hexdigest()}`."]
    (ROOT/'PRESSURE_SEMANTICS_VALIDATION_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'barometer_candidates_screened':len(rows),'pressure_reference_months':len(p['station_month_results']),'report':'PRESSURE_SEMANTICS_VALIDATION_REPORT.md'},indent=2))

if __name__=='__main__':main()
