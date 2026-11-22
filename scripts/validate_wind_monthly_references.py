#!/usr/bin/env python3
"""Regional wind comparison for monthly candidates using CHMI 10-minute data."""
from __future__ import annotations
import hashlib,json,math,sqlite3,statistics,zlib
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]; DB=ROOT/'data/historical_value_concordance.sqlite'
TZ=ZoneInfo('Europe/Prague'); STEP=600
STATIONS=('0-203-0-11777','0-203-0-11778')
ELEMENTS={'windSpeed':'Fprum','windGust':'Fmax','windDir':'Dprum'}
DOCS=['https://opendata.chmi.cz/meteorology/climate/Klimatologicka_data_popis.pdf',
      'https://www.chmi.cz/documents/42501/55105/Meteo-2011-04.pdf/4a70d57c-c430-d581-f8de-c07731f0531d?t=1755527817402']

def bounds(period):
    y,m=map(int,period.split('-'));lo=int(datetime(y,m,1,tzinfo=TZ).timestamp())
    y,m=(y+1,1) if m==12 else (y,m+1)
    return lo,int(datetime(y,m,1,tzinfo=TZ).timestamp())

def paths(station):
    out=[]
    for folder in ('data/chmi-priority-temperature/raw','data/chmi-2026-recent/raw','data/chmi-2018/raw'):
        out.extend(sorted((ROOT/folder).glob(f'10m-{station}-*.json')))
    return list(dict.fromkeys(out))

def circ_delta(a,b): return (a-b+180.0)%360.0-180.0
def circ_stats(local,ref):
    if not local:return {'local_circular_mean_deg':None,'reference_circular_mean_deg':None,'circular_bias_reference_minus_loucka_deg':None,'circular_mae_deg':None,'local_resultant_length':None,'reference_resultant_length':None}
    def vector(xs):
        s=sum(math.sin(math.radians(v)) for v in xs)/len(xs);c=sum(math.cos(math.radians(v)) for v in xs)/len(xs)
        return math.degrees(math.atan2(s,c))%360,math.hypot(s,c)
    lm,lr=vector(local);rm,rr=vector(ref);ds=[abs(circ_delta(y,x)) for x,y in zip(local,ref)]
    return {'local_circular_mean_deg':lm,'reference_circular_mean_deg':rm,'circular_bias_reference_minus_loucka_deg':circ_delta(rm,lm),'circular_mae_deg':statistics.mean(ds),'local_resultant_length':lr,'reference_resultant_length':rr}

def main():
    candidates=json.loads((ROOT/'MONTHLY_PUBLICATION_CANDIDATES.json').read_text())['candidates']
    target=[r for r in candidates if r['variable'] in ELEMENTS]
    periods=sorted({r['period'] for r in target})
    db=sqlite3.connect(f'file:{DB.resolve()}?mode=ro',uri=True)
    local={}
    for period in periods:
        lo,hi=bounds(period);values=defaultdict(dict)
        for ts,blob in db.execute('SELECT dateTime,comparison_zlib FROM timestamp_evidence WHERE dateTime>? AND dateTime<=? ORDER BY dateTime',(lo,hi)):
            v=json.loads(zlib.decompress(blob))
            for variable in ELEMENTS:
                x=v.get(variable,{}).get('target_value')
                if x is not None:
                    try:values[variable][int(ts)]=float(x)
                    except (ValueError,TypeError):pass
        local[period]=values
    db.close()
    refs={};hashes={}
    for station in STATIONS:
        merged={}
        for path in paths(station):
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            raw=json.loads(path.read_text(encoding='utf-8'))
            for sid,el,stamp,value,flag,qc in raw['data']['data']['values']:
                if sid!=station or el not in {'Fprum','Fmax','Dprum'}:continue
                try:ts=int(datetime.fromisoformat(stamp.replace('Z','+00:00')).timestamp());val=float(value)
                except (ValueError,TypeError):continue
                # Priority cache paths precede older duplicate cache copies.
                merged.setdefault((el,ts),{'value':val,'quality':str(qc),'flag':str(flag or ''),'path':path,'sha256':digest})
            hashes[path.relative_to(ROOT).as_posix()]=digest
        refs[station]=merged
    results=[]
    for candidate in target:
        period=candidate['period'];variable=candidate['variable'];element=ELEMENTS[variable]
        lo,hi=bounds(period);expected=set(range(((lo//STEP)+1)*STEP,hi+1,STEP))
        for station in STATIONS:
            series={ts:r for (el,ts),r in refs[station].items() if el==element and ts in expected and r['quality'] in ('0','0.0') and math.isfinite(r['value'])}
            if not series:continue
            local_series=local[period][variable]
            pairs=[]
            for ts,row in sorted(series.items()):
                if ts not in local_series:continue
                lv=local_series[ts];rv=row['value']
                if variable in ('windSpeed','windGust'):
                    lv=lv/3.6 # candidate contract is km/h; CHMI F/Fmax use m/s
                elif not (0<=lv<=360 and 0<=rv<=360):continue
                pairs.append((ts,lv,rv,row))
            n=len(pairs);lx=[p[1] for p in pairs];rx=[p[2] for p in pairs]
            if variable=='windDir':
                directional=circ_stats(lx,rx);bias=directional['circular_bias_reference_minus_loucka_deg'];mae=directional['circular_mae_deg'];rmse=math.sqrt(statistics.mean(circ_delta(y,x)**2 for x,y in zip(lx,rx))) if n else None
                corr=None
            else:
                diffs=[y-x for x,y in zip(lx,rx)]
                bias=statistics.mean(diffs) if n else None;mae=statistics.mean(abs(x) for x in diffs) if n else None;rmse=math.sqrt(statistics.mean(x*x for x in diffs)) if n else None
                mx=statistics.mean(lx) if n else 0;my=statistics.mean(rx) if n else 0;den=math.sqrt(sum((x-mx)**2 for x in lx)*sum((y-my)**2 for y in rx)) if n else 0
                corr=sum((x-mx)*(y-my) for x,y in zip(lx,rx))/den if den else None;directional=None
            daily=defaultdict(lambda:[[],[]]);by_hour=defaultdict(list)
            for ts,lv,rv,_ in pairs:
                dt=datetime.fromtimestamp(ts,TZ);daily[dt.date().isoformat()][0].append(lv);daily[dt.date().isoformat()][1].append(rv)
                by_hour[f'{dt.hour//6*6:02d}-{dt.hour//6*6+5:02d}'].append(circ_delta(rv,lv) if variable=='windDir' else rv-lv)
            daily_diff=[]
            for a,b in daily.values():
                if variable=='windDir': daily_diff.append(circ_delta(circ_stats(b,a)['reference_circular_mean_deg'],circ_stats(b,a)['local_circular_mean_deg']))
                else:daily_diff.append(statistics.mean(b)-statistics.mean(a))
            used={p[3]['path'] for p in pairs}
            qcounts=defaultdict(int)
            for (el,ts),r in refs[station].items():
                if el==element and ts in expected:qcounts[r['quality']]+=1
            rec={'period':period,'variable':variable,'statistic':candidate['statistic'],'station_id':station,'reference_element':element,
              'reference_files_used':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashes[p.relative_to(ROOT).as_posix()]} for p in sorted(used,key=lambda x:x.as_posix())],
              'unit_normalization':'Loucka km/h divided by 3.6 to m/s; CHMI speed in m/s.' if variable in ('windSpeed','windGust') else 'No unit conversion; degrees clockwise from north.',
              'expected_10_minute_slots_in_local_civil_month':len(expected),'valid_reference_slots_in_month':len(series),'matched_pairs':n,
              'matched_coverage_of_valid_reference':n/len(series) if series else 0,'reference_slot_coverage_of_expected':len(series)/len(expected) if expected else 0,
              'quality_counts':dict(qcounts),'loucka_candidate_monthly_mean':candidate['value'],'loucka_paired_mean':statistics.mean(lx) if n and variable!='windDir' else None,
              'reference_paired_mean':statistics.mean(rx) if n and variable!='windDir' else None,'bias_reference_minus_loucka':bias,'mae':mae,'rmse':rmse,'correlation':corr,
              'daily_mean_bias_reference_minus_loucka':statistics.mean(daily_diff) if daily_diff else None,
              'six_hour_local_time_bias':{k:statistics.mean(v) for k,v in sorted(by_hour.items())},
              'circular_direction_statistics':directional,
              'interpretation':'Regional context only. CHMI and Loucka samples have different documented or unresolved averaging/gust windows; timestamp equality does not prove equal time support, exposure, sensor identity, or calibration.'}
            results.append(rec)
    out={'schema':'loucka-monthly-wind-reference-validation-v1','snapshot_id':hashlib.sha256(DB.read_bytes()).hexdigest(),
      'reference_manifest_sha256':hashlib.sha256((ROOT/'data/chmi-priority-temperature/manifest.json').read_bytes()).hexdigest(),
      'source_documentation_urls':DOCS,'reference_file_sha256':hashes,'candidate_counts':{v:sum(r['variable']==v for r in target) for v in ELEMENTS},
      'candidate_count':len(target),'candidate_period_count':len(periods),'station_month_results':results,
      'method_limits':['Exact UTC timestamp joins only; no interpolation.',
       'CHMI Fprum represents a 10-minute mean wind-speed element; CHMI Fmax is a maximum-speed element. The exact instrument gust window is not inferred from element name alone.',
       'Local windSpeed and windGust candidate values are normalized from km/h to m/s; CHMI wind values are reported in m/s.',
       'Local wind archive records and CHMI 10-minute samples do not have proven identical time functions; comparisons are regional context, not direct validation or calibration.',
       'These results are regional consistency context, not calibration; no wind corrections or publication clearances are produced.']}
    (ROOT/'MONTHLY_WIND_REFERENCE_VALIDATION.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'candidate_count':len(target),'candidate_period_count':len(periods),'station_month_results':len(results),'matched_pairs':sum(r['matched_pairs'] for r in results),'by_variable':{v:sum(r['variable']==v for r in results) for v in ELEMENTS}},indent=2))

if __name__=='__main__':main()
