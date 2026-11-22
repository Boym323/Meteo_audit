#!/usr/bin/env python3
"""Create one conservative, evidence-specific RH disposition per candidate month."""
from __future__ import annotations
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'HUMIDITY_CANDIDATE_VALIDATION_REVIEW.json'
OUT_MD=ROOT/'HUMIDITY_CANDIDATE_VALIDATION_REVIEW.md'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    candidates=json.loads((ROOT/'MONTHLY_PUBLICATION_CANDIDATES.json').read_text())['candidates']
    diagnostics=json.loads((ROOT/'MONTHLY_CANDIDATE_SERIES_DIAGNOSTICS.json').read_text())
    refs=json.loads((ROOT/'MONTHLY_HUMIDITY_REFERENCE_VALIDATION.json').read_text())
    daily=json.loads((ROOT/'HUMIDITY_DAILY_REFERENCE_CONTEXT.json').read_text())
    d_by={r['period']:r for r in diagnostics['records'] if r['variable']=='outHumidity'}
    paired={}
    for r in refs['station_month_results']: paired.setdefault(r['period'],[]).append(r)
    daily_by={}
    for r in daily['results']:
        if r['valid_quality_zero_days']>0: daily_by.setdefault(r['period'],[]).append(r)
    out=[]
    for c in sorted((x for x in candidates if x['variable']=='outHumidity'),key=lambda x:x['period']):
        p=c['period'];d=d_by[p];r=paired.get(p,[]);dr=daily_by.get(p,[])
        weather=refs.get('plateau_weather_context_by_period',{}).get(p,{})
        saturation=int(d.get('saturated_humidity_rows_ge_99_pct') or 0)
        total=int(d.get('target_nonnull_rows') or 0)
        plateau_seconds=int(d.get('longest_humidity_ge_99_run_seconds') or 0)
        exact_seconds=int(d.get('longest_consecutive_exact_value_run_seconds') or 0)
        regional=[]
        for x in r:
            regional.append({'evidence_type':'EXACT_UTC_SUBDAILY_REGIONAL_COMPARISON','station_id':x['station_id'],
              'matched_pairs':x['matched_pairs'],'matched_coverage':x['matched_coverage_of_valid_reference'],
              'bias_reference_minus_loucka_percentage_points':x['bias_reference_minus_loucka_percentage_points'],
              'mae_percentage_points':x['mae_percentage_points'],'rmse_percentage_points':x['rmse_percentage_points'],
              'correlation':x['correlation'],'reference_file_hashes':x.get('reference_files_used',[])})
        for x in dr:
            regional.append({'evidence_type':'DAILY_AGGREGATE_REGIONAL_CONTEXT_ONLY','station_id':x['station_id'],
              'station_name':x['station_name'],'valid_days':x['valid_quality_zero_days'],'expected_days':x['expected_days'],
              'mean_of_daily_means_pct':x['mean_of_daily_means_pct'],
              'difference_daily_context_minus_loucka_pp':x['difference_daily_context_minus_loucka_pp'],
              'quality_counts':x['quality_counts'],'flag_counts':x['flag_counts'],'source_sha256':x['source_sha256']})
        evidence_level=('MATCHED_SUBDAILY_REGIONAL_EVIDENCE' if r else 'DAILY_REGIONAL_CONTEXT_ONLY' if dr else 'NO_COMPATIBLE_CACHED_REFERENCE')
        if r:
            biases=[x['bias_reference_minus_loucka_percentage_points'] for x in r]
            station_spread=max(biases)-min(biases) if len(biases)>1 else 0.0
            interpretation=(f"Exact-UTC comparison exists at {len(r)} regional station(s); observed station bias range is "
              f"{min(biases):.2f} to {max(biases):.2f} pp (between-station spread {station_spread:.2f} pp). "
              "Temporal agreement and regional differences do not validate the Loucka sensor or identify a correction.")
        elif dr:
            summaries=', '.join(f"{x['station_name']} {x['mean_of_daily_means_pct']:.1f}% (Δ {x['difference_daily_context_minus_loucka_pp']:+.1f} pp; {x['valid_quality_zero_days']}/{x['expected_days']} days)" for x in dr)
            interpretation=(f"Daily regional aggregates are available: {summaries}. CHMI daily-window semantics are not matched "
              "to Loucka monthly archive intervals; these values are context only, with no daywise pairing or interpolation.")
        else:
            interpretation='No compatible cached regional reference exists for this candidate month.'
        blockers=[
          'Loucka RH sensor model, identity, accuracy specification, and physical siting are not established for this month.',
          'Dated sensor/gateway/driver/configuration epochs and historical RH mapping are unresolved.',
          'A regional difference or ≥99% plateau run cannot distinguish saturation, quantization, condensation, microclimate, or archive behavior without instrument and event evidence.'
        ]
        out.append({'period':p,'variable':'outHumidity','candidate_monthly_mean_pct':c['value'],
          'candidate_coverage':c['coverage'],'archive_series_screen':{'target_nonnull_rows':total,
            'rows_ge_99_pct':saturation,'fraction_ge_99_pct':saturation/total if total else None,
            'longest_ge_99_run_seconds':plateau_seconds,'longest_exact_value_run_seconds':exact_seconds,
            'minimum_pct':d.get('minimum'),'maximum_pct':d.get('maximum')},
          'regional_evidence_level':evidence_level,'regional_comparisons':regional,'plateau_meteorological_context':weather,
          'candidate_specific_interpretation':interpretation,'unresolved_blockers':blockers,
          'disposition':'REVIEW_REQUIRED_SENSOR_VALIDATION','correction_authorized':False,
          'publication_authorized':False,'physical_validation':False,'matched_regional_comparison_available':bool(r),
          'evidence_references':['MONTHLY_CANDIDATE_SERIES_DIAGNOSTICS.json','MONTHLY_HUMIDITY_REFERENCE_VALIDATION.json' if r else 'HUMIDITY_DAILY_REFERENCE_CONTEXT.json']})
    doc={'schema':'loucka-humidity-candidate-validation-review-v1','snapshot_id':diagnostics['snapshot_id'],
      'candidate_count':len(out),'matched_subdaily_candidates':sum(x['regional_evidence_level']=='MATCHED_SUBDAILY_REGIONAL_EVIDENCE' for x in out),
      'daily_context_only_candidates':sum(x['regional_evidence_level']=='DAILY_REGIONAL_CONTEXT_ONLY' for x in out),
      'without_cached_reference_candidates':sum(x['regional_evidence_level']=='NO_COMPATIBLE_CACHED_REFERENCE' for x in out),
      'sensor_accuracy_validated':0,'correction_authorized':False,'publication_authorized':False,
      'plateau_weather_summary':refs.get('plateau_weather_summary',{}),
      'source_sha256':{'candidates':sha(ROOT/'MONTHLY_PUBLICATION_CANDIDATES.json'),
        'diagnostics':sha(ROOT/'MONTHLY_CANDIDATE_SERIES_DIAGNOSTICS.json'),
        'subdaily_reference_validation':sha(ROOT/'MONTHLY_HUMIDITY_REFERENCE_VALIDATION.json'),
        'daily_reference_context':sha(ROOT/'HUMIDITY_DAILY_REFERENCE_CONTEXT.json')},
      'method_limits':['CHMI stations are regional comparisons, not co-located instrument standards.',
        'Daily H,AVG has no demonstrated equivalence to the Loucka monthly archive statistic.',
        refs.get('plateau_weather_summary',{}).get('interpretation_limit','Local temperature and wind co-measures do not establish humidity sensor cause or epoch.'),
        'Candidate-specific dispositions describe available evidence and blockers; they do not claim human calibration or physical sensor validation.'],
      'records':out}
    OUT.write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    lines=['# Candidate-specific humidity validation review','',
      f"Snapshot SHA-256: `{doc['snapshot_id']}`. This is an automated evidence disposition, not physical calibration.",'',
      f"Candidates: {len(out)}; exact-UTC regional comparisons: {doc['matched_subdaily_candidates']}; daily-context-only: {doc['daily_context_only_candidates']}; without cached reference: {doc['without_cached_reference_candidates']}. Sensor accuracy validated: 0.",'',
      '| Period | Mean RH | ≥99% rows | Longest ≥99% run | Reference evidence | Disposition |','|---|---:|---:|---:|---|---|']
    for x in out:
        s=x['archive_series_screen'];evidence=x['regional_evidence_level'].replace('_',' ').lower()
        lines.append(f"| {x['period']} | {x['candidate_monthly_mean_pct']:.2f}% | {s['rows_ge_99_pct']:,}/{s['target_nonnull_rows']:,} ({s['fraction_ge_99_pct']:.1%}) | {s['longest_ge_99_run_seconds']/3600:.2f} h | {evidence} | {x['disposition']} |")
    lines+=['','## Candidate-specific regional interpretation','']
    for x in out:
        lines.append(f"### {x['period']}")
        lines.append('')
        lines.append(x['candidate_specific_interpretation'])
        w=x.get('plateau_meteorological_context',{});pt=w.get('plateau_temperature_c',{});pw=w.get('plateau_wind_speed_kmh',{})
        lines.append(f"Local ≥99% episodes: {w.get('plateau_run_count',0)}; local RH≥99 rows {w.get('local_ge_99_rows',0)}/{w.get('candidate_rows',0)}. During plateau rows with available data, archived outTemp mean/range was {pt.get('mean')} °C ({pt.get('minimum')} to {pt.get('maximum')}); archived windSpeed mean was {pw.get('mean')} km/h. These co-measures do not identify cause.")
        for station,ctx in w.get('exact_utc_reference_context_during_plateaus',{}).items():
            if ctx.get('reference_matched_slots_during_plateaus'):
                lines.append(f"  - {station}: {ctx['reference_matched_slots_during_plateaus']} exact-UTC CHMI H pairs during local plateaus; {ctx['reference_slots_ge_95_pct']} ({ctx['reference_fraction_ge_95_pct']:.1%}) were ≥95%, {ctx['reference_slots_ge_99_pct']} ({ctx['reference_fraction_ge_99_pct']:.1%}) were ≥99%.")
        lines.append('')
        lines.append('Unresolved for this candidate: '+ ' '.join(x['unresolved_blockers']))
        lines.append('')
    lines+=['Daily context retains CHMI quality and flag counts. Exact-UTC comparisons retain matched pair counts, coverage, bias, MAE, RMSE, correlation, and source file hashes. No value correction is authorized.','']
    OUT_MD.write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'output':str(OUT),'candidate_count':len(out),'matched_subdaily':doc['matched_subdaily_candidates'],
      'daily_context_only':doc['daily_context_only_candidates'],'without_reference':doc['without_cached_reference_candidates']},indent=2))
if __name__=='__main__':main()
