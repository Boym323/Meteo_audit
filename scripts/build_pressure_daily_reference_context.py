#!/usr/bin/env python3
"""Summarize CHMI daily P,AVG as non-calibration context for barometer candidates."""
from __future__ import annotations
import calendar,csv,hashlib,json,math
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'PRESSURE_DAILY_REFERENCE_CONTEXT.json'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    manifest=json.loads((ROOT/'data/chmi-daily-pressure/manifest.json').read_text())
    chmi=next(x for x in manifest['files'] if x['station_id']=='0-20000-0-11774')
    candidates=json.loads((ROOT/'MONTHLY_PUBLICATION_CANDIDATES.json').read_text())['candidates']
    periods=sorted({r['period'] for r in candidates if r['variable']=='barometer'})
    vals=defaultdict(list);quality=defaultdict(lambda:defaultdict(int));flags=defaultdict(lambda:defaultdict(int))
    path=ROOT/chmi['path']
    if sha(path)!=chmi['sha256']: raise ValueError('CHMI daily pressure cache hash mismatch')
    with path.open(encoding='utf-8-sig',newline='') as stream:
        for row in csv.DictReader(stream):
            if row['STATION']!=chmi['station_id'] or row['ELEMENT']!='P': continue
            period=row['DT'][:7]
            if period not in periods: continue
            key=period;quality[key][row['QUALITY']]+=1;flags[key][row['FLAG'] or '(blank)']+=1
            if row['TIMEFUNC']!='AVG' or row['QUALITY']!='0.0' or not row['VALUE']: continue
            try:value=float(row['VALUE'])
            except ValueError:continue
            if math.isfinite(value) and 0<value<1200:vals[key].append(value)
    local={}
    with (ROOT/'data/STATISTICAL_VARIANTS_MONTHLY.csv').open(encoding='utf-8',newline='') as stream:
        for row in csv.DictReader(stream):
            if row['variant']=='B_DOCUMENTED_SOURCE_AND_RECOVERY' and row['period'] in periods and row['variable'] in {'pressure','barometer','altimeter'}:
                local[(row['period'],row['variable'])]=float(row['mean_time_weighted']) if row['mean_time_weighted'] else None
    results=[]
    for period in periods:
        expected=calendar.monthrange(*map(int,period.split('-')))[1];ordered=sorted(vals.get(period,[]));mean=sum(ordered)/len(ordered) if ordered else None
        def quantile(q):return ordered[round(q*(len(ordered)-1))] if ordered else None
        local_means={v:local.get((period,v)) for v in ('pressure','barometer','altimeter')}
        results.append({'period':period,'reference_station_id':chmi['station_id'],'reference_station_name':chmi['station_name'],
          'reference_latitude':chmi.get('latitude'),'reference_longitude':chmi.get('longitude'),'reference_elevation_m':chmi.get('elevation_m'),
          'chmi_element':'P','timefunc':'AVG','time_basis':'CHMI UTC calendar month from daily rows timestamped 00Z',
          'expected_days':expected,'valid_quality_zero_avg_days':len(ordered),'coverage':len(ordered)/expected,
          'mean_of_daily_means_hpa':mean,'median_daily_mean_hpa':quantile(.5),'p10_daily_mean_hpa':quantile(.1),'p90_daily_mean_hpa':quantile(.9),
          'quality_counts':dict(sorted(quality[period].items())),'flag_counts':dict(sorted(flags[period].items())),
          'local_variant_b_month_means_hpa':local_means,
          'descriptive_context_differences_hpa':{v:mean-value if mean is not None and value is not None else None for v,value in local_means.items()},
          'comparison_status':'DAILY_STATION_PRESSURE_CONTEXT_ONLY' if ordered else 'NO_QUALITY_ZERO_DAILY_AVERAGE',
          'source_sha256':chmi['sha256']})
    doc={'schema':'loucka-chmi-daily-pressure-context-v1','snapshot_id':json.loads((ROOT/'data/STATISTICAL_VARIANTS_MANIFEST.json').read_text())['concordance_sqlite_sha256'],
      'candidate_period_count':len(periods),'candidate_periods_with_quality_zero_daily_avg':sum(r['valid_quality_zero_avg_days']>0 for r in results),
      'candidate_periods_without_daily_avg':[r['period'] for r in results if not r['valid_quality_zero_avg_days']],
      'station':{k:chmi.get(k) for k in ('station_id','station_name','latitude','longitude','elevation_m','valid_from_utc','metadata_source','metadata_source_sha256','url','path','sha256')},
      'source_sha256':{'candidate_list':sha(ROOT/'MONTHLY_PUBLICATION_CANDIDATES.json'),'variant_table':sha(ROOT/'data/STATISTICAL_VARIANTS_MONTHLY.csv'),'cache_manifest':sha(ROOT/'data/chmi-daily-pressure/manifest.json')},
      'method_limits':['CHMI element P is kept separate from CHMI P_hm and Loucka pressure, barometer, and altimeter; no conversion or field relabeling is applied.',
        'This is a month-level mean of quality-0 CHMI daily AVG values, not matched external validation. CHMI UTC daily windows are not mapped to Loucka Europe/Prague monthly archive intervals.',
        'Differences are descriptive regional context only; the Loucka sensor elevation, WeeWX pressure reduction, sensor identity, and field mapping remain unresolved.',
        'Daily context does not set physical_validation or external_validation and does not authorize publication or correction.'],
      'results':results}
    OUT.write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT),'candidate_periods':len(periods),'with_quality_zero_daily_avg':doc['candidate_periods_with_quality_zero_daily_avg'],'without_daily_avg':len(doc['candidate_periods_without_daily_avg'])},indent=2))
if __name__=='__main__':main()
