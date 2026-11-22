#!/usr/bin/env python3
"""Compare January 2026 Loucka pilot values with official CHMI Vizovice T/H."""
import csv,hashlib,json,math,sqlite3,statistics
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data';REF=DATA/'publication-pilot-reference'
DB=DATA/'historical_value_concordance.sqlite';RAW=REF/'chmi_11777_2026-01_10min.json';META=REF/'chmi_station_metadata_meta1.csv'
SNAP='1e34859d05bb0ec20d3810c4fbb376d231a6ee0bfca0c4c636dcfb2d1114e4ba'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if sha(DB)!=SNAP:raise SystemExit('Loucka snapshot SHA-256 mismatch')
    data=json.loads(RAW.read_text());rows=data['data']['data']['values']
    station=next((x for x in csv.DictReader(META.open(encoding='utf-8-sig')) if x['WSI']=='0-203-0-11777' and x['BEGIN_DATE']<='2026-01-01T00:00Z'<=x['END_DATE']),None)
    if not station:raise SystemExit('No active CHMI station metadata row')
    chmi=defaultdict(dict);quality=Counter()
    for station_id,element,stamp,value,flag,qc in rows:
        if element not in {'T','H'}:continue
        quality[f'{element}:{qc}']+=1
        if value not in ('',None) and float(qc)==0:chmi[stamp][element]=float(value)
    db=sqlite3.connect(f'file:{DB.resolve()}?mode=ro',uri=True)
    target={}
    for ts,blob in db.execute("SELECT dateTime,comparison_zlib FROM timestamp_evidence WHERE local_month='2026-01'"):
        fields=json.loads(__import__('zlib').decompress(blob));stamp=datetime.fromtimestamp(ts,__import__('datetime').timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        target[stamp]={k:(float(fields[k]['target_value']) if fields[k]['target_value'] is not None else None) for k in ('outTemp','outHumidity')}
    db.close()
    result={}
    for element,var in (('T','outTemp'),('H','outHumidity')):
        pairs=[(target[t][var],chmi[t][element]) for t in sorted(set(chmi)&set(target)) if element in chmi[t] and target[t][var] is not None]
        local=[x for x,y in pairs];ref=[y for x,y in pairs]
        errors=[y-x for x,y in pairs]
        cov=len(pairs)/len(chmi) if chmi else 0
        mean_ref=sum(ref)/len(ref);mean_local=sum(local)/len(local)
        corr=statistics.correlation(local,ref) if len(pairs)>1 else None
        result[var]={'chmi_element':element,'unit':'degC' if element=='T' else 'percent','matched_10_min_pairs':len(pairs),'chmi_valid_slots':len(chmi),'matched_coverage':cov,'chmi_arithmetic_mean':mean_ref,'loucka_same_time_sample_mean':mean_local,'bias_chmi_minus_loucka':statistics.mean(errors),'mae':statistics.mean(abs(x) for x in errors),'rmse':math.sqrt(statistics.mean(x*x for x in errors)),'correlation':corr,'difference_p05':sorted(errors)[int(.05*(len(errors)-1))],'difference_p50':statistics.median(errors),'difference_p95':sorted(errors)[int(.95*(len(errors)-1))],'daily_mean_pairs':None,'interpretation':'Regional plausibility / temporal behavior check only; neither equality nor identity of original measurements is implied.'}
        byday=defaultdict(list)
        for t in sorted(set(chmi)&set(target)):
            if element in chmi[t] and target[t][var] is not None:byday[t[:10]].append((target[t][var],chmi[t][element]))
        daily=[(sum(a for a,b in v)/len(v),sum(b for a,b in v)/len(v)) for v in byday.values() if v]
        result[var]['daily_mean_pairs']=len(daily)
        result[var]['daily_mean_bias_chmi_minus_loucka']=statistics.mean(b-a for a,b in daily)
    out={'schema':'loucka-pilot-chmi-reference-validation-v1','loucka_snapshot_id':SNAP,'reference':{'provider':'Czech Hydrometeorological Institute','station_id':'0-203-0-11777','station_name':station['FULL_NAME'],'station_code':station['GH_ID'],'latitude':float(station['GEOGR1']),'longitude':float(station['GEOGR2']),'elevation_m':float(station['ELEVATION']),'metadata_operational_from':station['BEGIN_DATE'],'timezone':'UTC','file':'data/publication-pilot-reference/chmi_11777_2026-01_10min.json','file_sha256':sha(RAW),'metadata_file':'data/publication-pilot-reference/chmi_station_metadata_meta1.csv','metadata_sha256':sha(META),'source_url':'https://opendata.chmi.cz/meteorology/climate/recent/data/10min/01/10m-0-203-0-11777-202601.json','station_metadata_url':'https://opendata.chmi.cz/meteorology/climate/historical_csv/metadata/meta1.csv','creation_utc':data.get('datumVytvoreni'),'quality_code_counts':dict(sorted(quality.items()))},'geographic_and_method_limits':{'loucka_sensor_coordinates':'not recorded in the local evidence; exact distance cannot be computed','elevation_difference':'unknown because Loucka sensor elevation is not tied to a verified coordinate','exposure':'different official regional station; microclimate and siting differ','alignment':'same exact UTC 10-minute timestamp only; no interpolation; CHMI quality 0 only','cadence':'both compared at the exact CHMI 10-minute cadence, 4464 nominal monthly slots','role':'external regional plausibility and temporal-behavior check; cannot validate identity or prove the Loucka sensor value'},'variables':result}
    (ROOT/'PILOT_2026_01_EXTERNAL_VALIDATION.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
