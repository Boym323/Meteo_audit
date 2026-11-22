#!/usr/bin/env python3
"""Deterministic source-copy and episode-flatness review for the 100 exact-grid 2009 B5 rows."""
import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=json.loads((ROOT/'data/b5_2009_on_grid_candidate_source_rows.json').read_text())['rows']
ctx=json.loads((ROOT/'data/b5_2009_on_grid_candidate_target_context.json').read_text())['rows']
episodes=[{'id':'2009-04-04-gap-2','start':1238841000,'end':1238851500,'expected_source_rows':14},{'id':'2009-08-12-gap-15','start':1250055900,'end':1250082000,'expected_source_rows':86}]
out=[]
for e in episodes:
 rows=[r for r in src if e['start']<r['dateTime']<e['end']]
 assert len(rows)==e['expected_source_rows']
 bounds={t:next(r for r in ctx if r['dateTime']==t) for t in (e['start'],e['end'])}
 fields=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','barometer']
 concordance={f:{'old_equals_wh1080':sum(r['old_'+f]==r['wh_'+f] for r in rows),'old_equals_eu_old':sum(r['old_'+f]==r['euold_'+f] for r in rows)} for f in fields}
 temps=[r['old_outTemp'] for r in rows if r['old_outTemp'] is not None]
 out.append({'episode_id':e['id'],'source_row_count':len(rows),'first_source_utc':rows[0]['dateTime'],'last_source_utc':rows[-1]['dateTime'],'source_usUnits':sorted({r['old_usUnits'] for r in rows}),'source_interval':sorted({r['old_interval'] for r in rows}),'outTemp':{'nonnull':len(temps),'distinct_values':len(set(temps)),'min':min(temps),'max':max(temps),'all_three_archives_equal':all(r['old_outTemp']==r['wh_outTemp']==r['euold_outTemp'] for r in rows),'adjacent_source_step_max_C':max(abs(float(b['old_outTemp'])-float(a['old_outTemp'])) for a,b in zip(rows,rows[1:]))},'source_context_fields':concordance,'reconstruction_bounds':{'before':{k:bounds[e['start']][k] for k in ['dateTime','outTemp','outHumidity','rain','windSpeed','windGust']},'after':{k:bounds[e['end']][k] for k in ['dateTime','outTemp','outHumidity','rain','windSpeed','windGust']}},'exact_reconstruction_source_keys':sum(r['exact_reconstruction_key'] is not None for r in rows),'nearest_projection_existing':sum(r['nearest_projection_key'] is not None for r in rows),'disposition':'SOURCE_SENSOR_STUCK_SUSPECTED_REVIEW_REQUIRED','restored_proposal_created':False})
result={'schema':'b5-2009-on-grid-outtemp-episode-review-v1','episodes':out,'total_source_rows':len(src),'all_target_keys_absent_from_reconstruction':all(r['exact_reconstruction_key'] is None for r in src),'all_source_keys_exactly_present_in_old_wh_euold':all(r['old_outTemp']==r['wh_outTemp']==r['euold_outTemp'] for r in src),'reason':'Two source episodes have exact-copy but perfectly constant outTemp over 14 samples/65 minutes and 86 samples/7h05m. The April source 4.8 C conflicts strongly with reconstruction boundary values 14.28 C and 22.0 C. The August source 22.2 C lies near its boundary values 20.92 C and 22.08 C but is flat through a long interval while surrounding reconstruction temperatures vary. Owner-attested historical stuck-sensor corrections and cleaning make exact copies insufficient; source rows remain suspect and are not restored.','safety':{'database_access':'READ_ONLY source and target SELECTs only','writes':0,'staging':False,'application':False,'q1_2018_queried':False,'year_2021_queried':False}}
(ROOT/'data/b5_2009_on_grid_candidate_temperature_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'episodes':[{'id':e['episode_id'],'rows':e['source_row_count'],'temp':e['outTemp'],'bounds':[e['reconstruction_bounds']['before']['outTemp'],e['reconstruction_bounds']['after']['outTemp']],'disposition':e['disposition']} for e in out]},indent=2))
