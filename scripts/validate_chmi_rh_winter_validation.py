#!/usr/bin/env python3
"""Validate immutable CHMI source cache and aggregate P4 context output."""
import csv,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
m=json.loads((R/'data/chmi-rh-winter-validation/manifest.json').read_text())
assert len(m['files'])==32 and len({x['path'] for x in m['files']})==32
rows=0
for x in m['files']:
 p=R/x['path']; b=p.read_bytes(); assert len(b)==x['bytes']; assert hashlib.sha256(b).hexdigest()==x['sha256']
 with p.open(newline='',encoding='utf-8') as f:
  rr=list(csv.DictReader(f))
 assert len(rr)==x['rows'] and rr
 assert all(v['STATION']==x['station'] and v['ELEMENT']==x['element'] for v in rr)
 rows+=len(rr)
assert rows==m['records_total']==136512
for x in m['metadata_files']:
 p=R/x['path']; assert p.stat().st_size==x['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']
for x in m.get('additional_local_evidence',[]):
 p=R/x['path']; assert p.stat().st_size==x['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']
hist=json.loads((R/'data/chmi-rh-winter-validation/source_history_summary.json').read_text())
assert sum(x['rows_n'] for x in hist['rows'])==5608
assert sum(x['outtemp_history_rows'] for x in hist['rows'])==0
assert sum(x['humidity_history_rows'] for x in hist['rows'])==55
assert hashlib.sha256((R/hist['query']).read_bytes()).hexdigest()==next(x['sha256'] for x in m['additional_local_evidence'] if x['path']==hist['query'])
s=m['local_join_snapshot']; p=R/s['path']; q=R/s['query_path']
assert p.stat().st_size==s['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==s['sha256']
assert hashlib.sha256(q.read_bytes()).hexdigest()==s['query_sha256']
local=json.loads(p.read_text()); assert len(local)==s['rows']==5608
assert all((r['dateTime']%3600)==0 for r in local)
assert not any(1609459200<=r['dateTime']<1614556800 for r in local if r['outHumidity'] is not None and r.get('proposal'))
agg=json.loads((R/'reports/2026-11-13-chmi-winter-rh-reference-validation.json').read_text())
assert agg['retrieved_files']==32 and agg['chmi_10min_rows']==68256
assert agg['2022_outage_coverage']['local_rh_nonnull']==0
assert agg['2022_outage_coverage']['luhamet_rh_valid']==693
assert len(agg['2022_outage_reference_context'])==8 and len(agg['exact_hour_station_pair_agreement'])==16
assert sum(x['outtemp_history_rows'] for x in agg['local_change_history_by_year'])==0
assert sum(x['humidity_history_rows'] for x in agg['local_change_history_by_year'])==55
assert 'ESTIMATED' not in json.dumps(agg) and 'RESTORED' not in json.dumps(agg)
result={'status':'PASS','source_files':32,'source_records':rows,'metadata_files':len(m['metadata_files']),'local_outtemp_history_events':0,'local_RH_history_events':55,'local_exact_hour_rows':len(local),'aggregate_station_timestamps':agg['chmi_10min_rows'],'outage_loucka_rh_nonnull':agg['2022_outage_coverage']['local_rh_nonnull'],'outage_luhamet_rh_valid':agg['2022_outage_coverage']['luhamet_rh_valid'],'candidates_created':0,'db_writes':0,'protected_2021':'diagnostic only','protected_q1_2018':'not queried'}
(R/'data/chmi-rh-winter-validation/validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
