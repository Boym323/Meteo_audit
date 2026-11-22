#!/usr/bin/env python3
"""Summarize official CHMI daily humidity as regional context for Loucka months."""
from __future__ import annotations
import csv, hashlib, json, math
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'HUMIDITY_DAILY_REFERENCE_CONTEXT.json'

def main():
    manifest=json.loads((ROOT/'data/chmi-daily-humidity/manifest.json').read_text())
    candidates=json.loads((ROOT/'MONTHLY_PUBLICATION_CANDIDATES.json').read_text())['candidates']
    humidity={r['period']:r for r in candidates if r['variable']=='outHumidity'}
    aggregate=defaultdict(list); counts=defaultdict(lambda:defaultdict(int)); flags=defaultdict(lambda:defaultdict(int)); source_hash={}
    for f in manifest['files']:
        path=ROOT/f['path']; digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=f['sha256']: raise ValueError(f"CHMI cache hash mismatch: {f['path']}")
        source_hash[f['station_id']]=digest
        with path.open(encoding='utf-8-sig',newline='') as stream:
            for row in csv.DictReader(stream):
                if row['STATION']!=f['station_id'] or row['ELEMENT']!='H' or row['TIMEFUNC']!='AVG': continue
                period=row['DT'][:7]; key=(period,f['station_id']); counts[key][row['QUALITY']]+=1; flags[key][row['FLAG'] or '(blank)']+=1
                if row['QUALITY']!='0.0' or not row['VALUE']: continue
                try: value=float(row['VALUE'])
                except ValueError: continue
                if not math.isfinite(value) or not 0<=value<=100: continue
                aggregate[key].append(value)
    results=[]
    for period,candidate in sorted(humidity.items()):
        lo=candidate.get('value')
        for f in manifest['files']:
            key=(period,f['station_id']); values=aggregate.get(key,[])
            import calendar
            expected=calendar.monthrange(int(period[:4]),int(period[5:7]))[1]
            ordered=sorted(values)
            def quantile(q):
                if not ordered:return None
                return ordered[round(q*(len(ordered)-1))]
            mean=sum(values)/len(values) if values else None
            results.append({'period':period,'station_id':f['station_id'],'station_name':f['station_name'],
                'timefunc':'AVG','expected_days':expected,'valid_quality_zero_days':len(values),
                'coverage':len(values)/expected,'mean_of_daily_means_pct':mean,'p10_pct':quantile(.1),
                'median_pct':quantile(.5),'p90_pct':quantile(.9),'days_ge_99_pct':sum(v>=99 for v in values),
                'loucka_monthly_mean_pct':lo,'difference_daily_context_minus_loucka_pp':mean-lo if mean is not None and lo is not None else None,
                'comparison_status':'DAILY_CONTEXT_ONLY' if values else 'NO_QUALITY_ZERO_DAILY_DATA',
                'quality_counts':dict(sorted(counts[key].items())),'flag_counts':dict(sorted(flags[key].items())),'source_sha256':source_hash[f['station_id']]})
    doc={'schema':'loucka-chmi-daily-humidity-context-v1','candidate_period_count':len(humidity),
      'candidate_periods_without_subdaily_reference':json.loads((ROOT/'MONTHLY_HUMIDITY_REFERENCE_VALIDATION.json').read_text())['candidate_periods_without_compatible_subdaily_reference'],
      'result_count':len(results),'stations':[{k:f[k] for k in ('station_id','station_name','url','path','sha256')} for f in manifest['files']],
      'methodology':['CHMI H,TIMEFUNC=AVG,QUALITY=0.0 only; flags and quality counts are retained.',
       'Daily values are summarized by calendar month; no daywise pairing, interpolation, or synthetic subdaily values.',
       'CHMI daily aggregation window/weighting is not documented as equivalent to the Loucka archive mean; differences are descriptive regional context only.',
       'This context does not set external_validation or physical_validation and cannot authorize correction or publication.'],
      'results':results}
    OUT.write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(OUT),'candidate_periods':len(humidity),'station_month_rows':len(results),'with_daily_data':sum(r['valid_quality_zero_days']>0 for r in results)},indent=2))
if __name__=='__main__':main()
