#!/usr/bin/env python3
"""Compare priority Loucka monthly RH candidates to exact-UTC CHMI 10-minute data."""
from __future__ import annotations
import csv, hashlib, json, math, statistics, sqlite3, zlib
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'data/historical_value_concordance.sqlite'
TZ=ZoneInfo('Europe/Prague')
STEP=600
STATIONS=('0-203-0-11777','0-203-0-11778')

def bounds(period):
    y,m=map(int,period.split('-')); lo=int(datetime(y,m,1,tzinfo=TZ).timestamp())
    y,m=(y+1,1) if m==12 else (y,m+1)
    return lo,int(datetime(y,m,1,tzinfo=TZ).timestamp())

def qtile(values,q):
    if not values:return None
    xs=sorted(values);p=(len(xs)-1)*q;i=int(p);j=min(i+1,len(xs)-1)
    return xs[i]+(xs[j]-xs[i])*(p-i)

def reference_paths(station):
    paths=[]
    for folder in ('data/chmi-priority-temperature/raw','data/chmi-2026-recent/raw','data/chmi-2018/raw'):
        paths.extend(sorted((ROOT/folder).glob(f'10m-{station}-*.json')))
    paths.extend(sorted((ROOT/'data/chmi-rh-winter-validation/raw').glob(f'10m-{station}-H-*.csv')))
    # Separate pilot copy is included only if it is not already represented by
    # the canonical 2026 cache path.
    pilot=ROOT/'data/publication-pilot-reference/chmi_11777_2026-01_10min.json'
    if station=='0-203-0-11777' and pilot.is_file(): paths.append(pilot)
    return list(dict.fromkeys(paths))

def parse_reference(path,station):
    rows={}
    if path.suffix.lower()=='.csv':
        with path.open(encoding='utf-8-sig',newline='') as f:
            for x in csv.DictReader(f):
                if x.get('STATION')!=station or x.get('ELEMENT')!='H':continue
                try:ts=int(datetime.fromisoformat(x['DT'].replace('Z','+00:00')).timestamp());value=float(x.get('VALUE') or x.get('VAL'))
                except (ValueError,TypeError,KeyError):continue
                rows[ts]={'value':value,'quality':str(x.get('QUALITY','')),'flag':str(x.get('FLAG','') or ''),'source':path}
    else:
        raw=json.loads(path.read_text(encoding='utf-8'))
        for sid,element,stamp,value,flag,qc in raw['data']['data']['values']:
            if sid!=station or element!='H':continue
            try:ts=int(datetime.fromisoformat(stamp.replace('Z','+00:00')).timestamp());value=float(value)
            except (ValueError,TypeError):continue
            rows[ts]={'value':value,'quality':str(qc),'flag':str(flag or ''),'source':path}
    return rows

def plateau_runs(series):
    runs=[];start=prev=None;values=[]
    for ts,value in sorted(series.items()):
        if value<99:
            if start is not None and prev-start>=300:runs.append({'start_utc':start,'end_utc':prev,'duration_minutes':(prev-start+300)/60,'slots':len(values)})
            start=prev=None;values=[];continue
        if start is None or ts!=prev+300:
            if start is not None and prev-start>=300:runs.append({'start_utc':start,'end_utc':prev,'duration_minutes':(prev-start+300)/60,'slots':len(values)})
            start=ts;values=[value]
        else:values.append(value)
        prev=ts
    if start is not None and prev-start>=300:runs.append({'start_utc':start,'end_utc':prev,'duration_minutes':(prev-start+300)/60,'slots':len(values)})
    return runs

def main():
    candidates={r['period']:r for r in json.loads((ROOT/'MONTHLY_PUBLICATION_CANDIDATES.json').read_text())['candidates'] if r['variable']=='outHumidity'}
    db=sqlite3.connect(f'file:{DB.resolve()}?mode=ro',uri=True)
    local_by_period={}; all_plateaus={}
    for period in sorted(candidates):
        lo,hi=bounds(period);local={}
        for ts,blob in db.execute('SELECT dateTime,comparison_zlib FROM timestamp_evidence WHERE dateTime>? AND dateTime<=? ORDER BY dateTime',(lo,hi)):
            item=json.loads(zlib.decompress(blob));h=item.get('outHumidity',{}).get('target_value');t=item.get('outTemp',{}).get('target_value');w=item.get('windSpeed',{}).get('target_value')
            if h is not None:local[int(ts)]={'humidity_pct':float(h),'temperature_c':float(t) if t is not None else None,'wind_speed_kmh':float(w) if w is not None else None}
        local_by_period[period]=local;all_plateaus[period]=plateau_runs({ts:r['humidity_pct'] for ts,r in local.items()})
    db.close()
    results=[];source_sha={}
    refs_by_station={}
    for station in STATIONS:
        merged={}
        for path in reference_paths(station):
            parsed=parse_reference(path,station)
            if parsed:
                source_sha[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
                for ts,row in parsed.items():merged.setdefault(ts,row)
        refs_by_station[station]=merged
    for period,candidate in sorted(candidates.items()):
        lo,hi=bounds(period);expected=set(range(((lo//STEP)+1)*STEP,hi+1,STEP));local=local_by_period[period]
        for station in STATIONS:
            merged=refs_by_station[station]
            in_month={ts:r for ts,r in merged.items() if ts in expected}
            valid={ts:r for ts,r in in_month.items() if r['quality'] in ('0','0.0') and math.isfinite(r['value'])}
            if not valid:continue
            pairs=[(ts,local[ts]['humidity_pct'],r['value']) for ts,r in sorted(valid.items()) if ts in local]
            n=len(pairs);diff=[rv-lv for _,lv,rv in pairs];lx=[lv for _,lv,_ in pairs];rx=[rv for _,_,rv in pairs]
            if n:
                bias=statistics.mean(diff);mae=statistics.mean(abs(x) for x in diff);rmse=math.sqrt(statistics.mean(x*x for x in diff))
                mx,my=statistics.mean(lx),statistics.mean(rx);den=math.sqrt(sum((x-mx)**2 for x in lx)*sum((y-my)**2 for y in rx));corr=sum((x-mx)*(y-my) for x,y in zip(lx,rx))/den if den else None
            else:bias=mae=rmse=corr=None
            by_hour=defaultdict(list);daily=defaultdict(lambda:[[],[]])
            for ts,lv,rv in pairs:
                dt=datetime.fromtimestamp(ts,TZ);by_hour[f'{dt.hour//6*6:02d}-{dt.hour//6*6+5:02d}'].append(rv-lv)
                daily[dt.date().isoformat()][0].append(lv);daily[dt.date().isoformat()][1].append(rv)
            daily_delta=[statistics.mean(b)-statistics.mean(a) for a,b in daily.values()]
            plateau_context=[]
            for run in all_plateaus[period]:
                plateau_pairs=[(ts,r['value']) for ts,r in valid.items() if run['start_utc']<=ts<=run['end_utc']]
                if plateau_pairs:
                    ref_values=[v for _,v in plateau_pairs]
                    local_values=[local[ts] for ts,_ in plateau_pairs if ts in local]
                    plateau_context.append({**run,'reference_matched_slots':len(ref_values),
                      'reference_mean_rh_pct':statistics.mean(ref_values),'reference_min_rh_pct':min(ref_values),'reference_max_rh_pct':max(ref_values),
                      'reference_slots_ge_95_pct':sum(v>=95 for v in ref_values),'reference_slots_ge_99_pct':sum(v>=99 for v in ref_values),
                      'reference_fraction_ge_95_pct':sum(v>=95 for v in ref_values)/len(ref_values),
                      'reference_fraction_ge_99_pct':sum(v>=99 for v in ref_values)/len(ref_values),
                      'local_temperature_mean_c':statistics.mean(x['temperature_c'] for x in local_values if x['temperature_c'] is not None) if any(x['temperature_c'] is not None for x in local_values) else None,
                      'local_temperature_min_c':min(x['temperature_c'] for x in local_values if x['temperature_c'] is not None) if any(x['temperature_c'] is not None for x in local_values) else None,
                      'local_temperature_max_c':max(x['temperature_c'] for x in local_values if x['temperature_c'] is not None) if any(x['temperature_c'] is not None for x in local_values) else None,
                      'local_wind_mean_kmh':statistics.mean(x['wind_speed_kmh'] for x in local_values if x['wind_speed_kmh'] is not None) if any(x['wind_speed_kmh'] is not None for x in local_values) else None})
            used={r['source'] for ts,r in merged.items() if ts in expected}
            files=[{'path':p.relative_to(ROOT).as_posix(),'sha256':source_sha[p.relative_to(ROOT).as_posix()]} for p in sorted(used,key=lambda p:p.as_posix())]
            quality=Counter(r['quality'] for r in in_month.values())
            results.append({'period':period,'station_id':station,'reference_files_used':files,
                'expected_10_minute_slots_in_local_civil_month':len(expected),'valid_reference_slots_in_month':len(valid),'matched_pairs':n,'unmatched_valid_reference_slots':len(valid)-n,
                'matched_coverage_of_valid_reference':n/len(valid) if valid else 0.0,'reference_slot_coverage_of_expected':len(valid)/len(expected) if expected else 0.0,
                'loucka_slots_without_valid_reference':sum(ts in local for ts in expected)-n,'quality_counts':dict(quality),
                'loucka_candidate_monthly_mean_pct':candidate['value'],'loucka_paired_mean_pct':statistics.mean(lx) if n else None,'reference_paired_mean_pct':statistics.mean(rx) if n else None,
                'bias_reference_minus_loucka_percentage_points':bias,'mae_percentage_points':mae,'rmse_percentage_points':rmse,'correlation':corr,
                'difference_quantiles_percentage_points':{'p05':qtile(diff,.05),'p50':qtile(diff,.5),'p95':qtile(diff,.95)},
                'daily_means':{'days_with_pairs':len(daily_delta),'mean_daily_bias_percentage_points':statistics.mean(daily_delta) if daily_delta else None,'mae_daily_mean_difference_percentage_points':statistics.mean(abs(x) for x in daily_delta) if daily_delta else None},
                'six_hour_local_time_bias_percentage_points':{k:statistics.mean(v) for k,v in sorted(by_hour.items())},'local_ge99_plateau_runs_with_reference_context':plateau_context,
                'cadence':'Exact 10-minute UTC timestamps only; no interpolation. Loucka source cadence is 5-minute archive records.','quality_rule':'Only CHMI quality code 0 is included in paired statistics; nonzero and missing quality are excluded.',
                'interpretation':'Regional plausibility and plateau context only; not sensor calibration, identity, siting equivalence, or direct physical validation.'})
    plateau_weather={}
    for period,runs in all_plateaus.items():
        rows=local_by_period[period]
        active=[r for r in rows.values() if r['humidity_pct']>=99]
        inactive=[r for r in rows.values() if r['humidity_pct']<99]
        def summary(group,key):
            values=[r[key] for r in group if r.get(key) is not None]
            return {'n':len(values),'mean':statistics.mean(values) if values else None,'median':statistics.median(values) if values else None,'minimum':min(values) if values else None,'maximum':max(values) if values else None}
        station_context={}
        for station in STATIONS:
            contexts=[x for x in results if x['period']==period and x['station_id']==station]
            events=[e for x in contexts for e in x['local_ge99_plateau_runs_with_reference_context']]
            n=sum(e['reference_matched_slots'] for e in events)
            station_context[station]={'plateau_runs_with_reference_pairs':len(events),'reference_matched_slots_during_plateaus':n,
              'reference_slots_ge_95_pct':sum(e['reference_slots_ge_95_pct'] for e in events),
              'reference_slots_ge_99_pct':sum(e['reference_slots_ge_99_pct'] for e in events),
              'reference_fraction_ge_95_pct':sum(e['reference_slots_ge_95_pct'] for e in events)/n if n else None,
              'reference_fraction_ge_99_pct':sum(e['reference_slots_ge_99_pct'] for e in events)/n if n else None}
        plateau_weather[period]={'candidate_rows':len(rows),'local_ge_99_rows':len(active),'local_ge_99_fraction':len(active)/len(rows) if rows else None,
          'plateau_run_count':len(runs),'plateau_temperature_c':summary(active,'temperature_c'),'non_plateau_temperature_c':summary(inactive,'temperature_c'),
          'plateau_wind_speed_kmh':summary(active,'wind_speed_kmh'),'non_plateau_wind_speed_kmh':summary(inactive,'wind_speed_kmh'),
          'exact_utc_reference_context_during_plateaus':station_context}
    years=defaultdict(lambda:{'candidate_periods':0,'periods_with_ge_99_plateaus':0,'plateau_run_count':0,'local_ge_99_rows':0})
    for period,ctx in plateau_weather.items():
        y=period[:4];years[y]['candidate_periods']+=1;years[y]['periods_with_ge_99_plateaus']+=bool(all_plateaus[period])
        years[y]['plateau_run_count']+=len(all_plateaus[period]);years[y]['local_ge_99_rows']+=ctx['local_ge_99_rows']
    weather_summary={'candidate_periods':len(plateau_weather),'periods_with_ge_99_plateaus':sum(bool(all_plateaus[p]) for p in plateau_weather),
      'local_ge_99_plateau_runs':sum(map(len,all_plateaus.values())),'by_year':dict(sorted(years.items())),
      'interpretation_limit':'Temperature and wind are descriptive co-measures from the Loucka archive; CHMI RH is regional exact-UTC context where available. Neither identifies cause, physical sensor epoch, or accuracy. Rainfall and dew-point inputs are not present in this concordance snapshot.'}
    out={'schema':'loucka-monthly-humidity-reference-validation-v2','snapshot_id':hashlib.sha256(DB.read_bytes()).hexdigest(),
        'reference_manifest_sha256':hashlib.sha256((ROOT/'data/chmi-priority-temperature/manifest.json').read_bytes()).hexdigest(),
        'candidate_period_count':len(candidates),'candidate_periods':sorted({r['period'] for r in results}),
        'candidate_periods_without_compatible_subdaily_reference':sorted(set(candidates)-{r['period'] for r in results}),
        'station_month_results':results,'local_ge99_plateau_runs':all_plateaus,'plateau_weather_context_by_period':plateau_weather,'plateau_weather_summary':weather_summary,'reference_file_sha256':source_sha,
        'method_limits':['All 45 humidity candidates are screened; exact-UTC CHMI comparisons are produced only where a same-month 10-minute H series exists.',
          'No interpolation; adjacent cached months are included where available for Europe/Prague civil-month UTC edges.',
          'CHMI sample time-function semantics for relative humidity have not been confirmed from metadata.',
          'Regional station differences and archive copies do not prove Loucka sensor truth or justify correction.']}
    (ROOT/'MONTHLY_HUMIDITY_REFERENCE_VALIDATION.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'candidate_periods':len(candidates),'periods_with_reference':len(out['candidate_periods']),'station_month_results':len(results),'matched_pairs_total':sum(r['matched_pairs'] for r in results),'local_ge99_plateau_runs':sum(map(len,all_plateaus.values()))},indent=2))

if __name__=='__main__':main()
