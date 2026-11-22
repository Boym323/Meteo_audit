#!/usr/bin/env python3
"""Deterministic validation for the bounded 2019 short-gap source disposition."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
x=json.loads((R/'data/b5_2019_short_gap_exact_slot_source_disposition.json').read_text())
raw=json.loads((R/'data/b5_2019_short_gap_exact_slot_source_review.json').read_text())
registry=json.loads((R/'config/active_proposal_registry.json').read_text())
assert x['unique_timestamps']==22 and x['gaps_with_source']==14 and x['returned_archive_rows']==44
assert x['cross_archive_availability']['target_presence_by_archive']=={
 'loucka_reconstruction':'0 exact target rows','pocasi-loucka.eu':'0 exact target rows',
 'pocasi-loucka.eu_GW1000':'0 exact target rows','pocasi-loucka.eu_old':'0 exact target rows',
 'old_weewx':'22 exact target rows','weewx_WH1080':'22 exact target rows'}
assert x['dispositions']=={
 'PREVIOUSLY_REVIEWED_P3_SOURCE_PRESENT':12,
 'COVERED_BY_ACTIVE_RESTORED_PROPOSAL':1,
 'REVIEW_REQUIRED_SOURCE_RH_CONFLICT_AND_LOCAL_TEMP_OFFSET':8,
 'REVIEW_REQUIRED_POSSIBLE_HISTORICAL_OUTTEMP_NULLING':1}
assert x['field_concordance']['outTemp']=={'paired':22,'equal':22,'conflict':0,'one_sided':0,'both_null':0}
assert x['field_concordance']['outHumidity']=={'paired':10,'equal':2,'conflict':8,'one_sided':12,'both_null':0}
assert all(q['units']==[17,17] and q['intervals']==[5,5] for q in x['targets'])
assert len(x['targets'])==len(raw['targets'])
for t in [1561406100,1561406400,1561406700,1561407000,1561407300,1561407600,1561407900,1561408200,1564776000]:
 q=next(y for y in x['targets'] if y['target_time']==t)
 assert q['disposition'].startswith('REVIEW_REQUIRED')
 assert not q['active_operations_at_timestamp']
ops=[(p['package_id'],int(o['timestamp']),o['variable']) for p in registry['packages'] for o in p.get('operation_keys',[])]
assert any(t==1559239800 and v=='outTemp' for _,t,v in ops)
assert not any(t in {1561406100,1561406400,1561406700,1561407000,1561407300,1561407600,1561407900,1561408200,1564776000} for _,t,_ in ops)
q=(R/'sql/readonly/b5_2019_short_gap_exact_slot_source_review.sql').read_text().lower()
assert q.lstrip().startswith('-- read-only') and 'where gap_band=\'lt_1h\'' in q and 'protection_scope=\'normal\'' in q
assert not any(k in q for k in ['insert into','update ','delete from','drop table','alter table','create table'])
report=(R/'reports/2026-11-14-B5-2019-short-gap-source-disposition.md').read_text()
for term in ['22 unique interior','14 gap episodes','2019-06-24','2019-08-02','REVIEW_REQUIRED','No new active operation']:
 assert term.lower() in report.lower(),term
print(json.dumps({'status':'PASS','source_rows':44,'unique_timestamps':22,'gap_episodes':14,'p3_overlap_not_repeated':12,'active_existing':1,'new_review_required':9,'new_operations':0,'database_access':'NONE','writes':0},ensure_ascii=False))
