#!/usr/bin/env python3
"""Aggregate exact-hour CHMI temperature comparisons on existing 2019-2020 holdout rows."""
import csv, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/'data/chmi-rh-winter-validation/loucka_hourly_complete_cases.json'
MANIFEST=ROOT/'data/chmi-rh-winter-validation/manifest.json'
STATIONS={'11777':'Vizovice','11778':'Kladná-Žilín'}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def score(errors):
    n=len(errors)
    return {'n':n,'bias_c':sum(errors)/n,'mae_c':sum(abs(e) for e in errors)/n,'rmse_c':math.sqrt(sum(e*e for e in errors)/n)}

local_rows=json.loads(LOCAL.read_text(encoding='utf-8'))
local={int(x['dateTime']):x for x in local_rows}
assert len(local)==len(local_rows)==5608
refs={}
source_files=[]
for year in (2019,2020):
    for code in STATIONS:
        for month in ('01','02'):
            path=ROOT/f'data/chmi-rh-winter-validation/raw/10m-0-203-0-{code}-T-{year}{month}.csv'
            assert path.is_file(),path
            source_files.append({'path':str(path.relative_to(ROOT)),'sha256':sha(path)})
            with path.open(newline='',encoding='utf-8') as stream:
                for row in csv.DictReader(stream):
                    if row['QUALITY']!='0.0' or not row['VALUE']: continue
                    dt=datetime.fromisoformat(row['DT'].replace('Z','+00:00')).astimezone(timezone.utc)
                    ts=int(dt.timestamp())
                    if ts%3600: continue
                    key=(ts,code)
                    assert key not in refs,key
                    refs[key]=float(row['VALUE'])

out=[]
for year in (2019,2020):
    common=[]
    for ts,row in local.items():
        if datetime.fromtimestamp(ts,timezone.utc).year!=year: continue
        if row.get('outTemp') is None or row.get('luhamet_temp') is None: continue
        if any((ts,code) not in refs for code in STATIONS): continue
        common.append((ts,float(row['outTemp']),float(row['luhamet_temp']),refs[(ts,'11777')],refs[(ts,'11778')]))
    assert common,year
    summary={'year':year,'n_unique_utc_targets':len(common)}
    for label,idx in [('luhamet_sehradice',2),('chmi_vizovice',3),('chmi_kladna_zilin',4)]:
        summary[label]=score([r[1]-r[idx] for r in common])
    out.append(summary)

manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
record={
 'schema':'h5-same-holdout-multistation-comparison-v1',
 'scope':'Exact UTC hourly subset of the existing 2019-2020 temporal holdout, only January and February, where Loucka target outTemp, LuhaMet outTemp, and QC=0 CHMI T from both stations are all present.',
 'target_rows_unique':sum(x['n_unique_utc_targets'] for x in out),
 'years':out,
 'comparison_definition':'Errors are contemporary archive Loucka outTemp minus each reference. This is a spatial transfer/consistency comparison, not verification against independent Loucka truth and not a missing-window model validation.',
 'source_metadata':{'local_hourly_snapshot_path':str(LOCAL.relative_to(ROOT)),'local_hourly_snapshot_sha256':sha(LOCAL),'chmi_manifest_path':str(MANIFEST.relative_to(ROOT)),'chmi_manifest_sha256':sha(MANIFEST),'chmi_source_files':source_files,'station_ids':STATIONS,'quality_filter':'QUALITY=0.0 only','time_match':'exact UTC timestamp; retain hourly UTC timestamps only'},
 'limitations':['The 2019-2020 transfer holdout is temporal but not fully blind: prior model exploration included this period.','CHMI stations are regional context, not local truth.','This exact common subset covers January-February only.','ERA5/ERA5-Land were not downloaded; authoritative Loucka sensor coordinates/elevation are unavailable, so no grid cell was selected.','No model was fitted, no correction was proposed, and no gap truth was inferred.'],
 'database_access':'NONE','database_writes':0,'mcp_dry_run':'NOT_RUN','staging':False,'application':'NOT_APPLIED'
}
(ROOT/'data/h5_same_holdout_multistation_comparison.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (ROOT/'data/h5_same_holdout_multistation_comparison.csv').open('w',newline='',encoding='utf-8') as f:
    fields=['year','n_unique_utc_targets','reference','n_pairs','bias_c','mae_c','rmse_c']
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for year in out:
        for key,label in [('luhamet_sehradice','LuhaMet Sehradice'),('chmi_vizovice','ČHMÚ Vizovice'),('chmi_kladna_zilin','ČHMÚ Kladná-Žilín')]:
            sc=year[key];w.writerow({'year':year['year'],'n_unique_utc_targets':year['n_unique_utc_targets'],'reference':label,'n_pairs':sc['n'],'bias_c':f"{sc['bias_c']:.6f}",'mae_c':f"{sc['mae_c']:.6f}",'rmse_c':f"{sc['rmse_c']:.6f}"})
print(json.dumps({'status':'BUILT','unique_targets':record['target_rows_unique'],'years':[{x['year']:x['n_unique_utc_targets']} for x in out]},ensure_ascii=False))
