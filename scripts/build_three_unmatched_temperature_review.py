#!/usr/bin/env python3
"""Build contextual review for every outTemp conflict matching no source."""
import hashlib,json,sqlite3,zlib
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1];DB=ROOT/'data/historical_value_concordance.sqlite';TZ=ZoneInfo('Europe/Prague')

def chmi_context(ts: int, target: Decimal, source_values: list[dict]) -> dict:
 """Attach exact-grid CHMI context when an immutable monthly cache exists.

 Never interpolate or treat a regional station as a calibration observation.
 """
 period=datetime.fromtimestamp(ts,timezone.utc).strftime('%Y%m')
 stations=[]
 for station_id,name in [('0-203-0-11777','Vizovice'),('0-203-0-11778','Kladna-Zilin')]:
  rel=Path('data/chmi-priority-temperature/raw')/f'10m-{station_id}-{period}.json'
  path=ROOT/rel
  if not path.exists():
   stations.append({'station_id':station_id,'station_name':name,'status':'REFERENCE_FILE_UNAVAILABLE','file':str(rel)})
   continue
  payload=json.loads(path.read_text())
  rows=[]
  for station,element,stamp,value,flag,quality in payload['data']['data']['values']:
   if station!=station_id or element!='T' or value is None: continue
   epoch=int(datetime.fromisoformat(stamp.replace('Z','+00:00')).timestamp())
   if abs(epoch-ts)<=1800:
    rows.append({'timestamp_utc':stamp,'offset_seconds_from_target':epoch-ts,'value':value,'unit':'degC','flag':flag,'quality':quality})
  exact=[r for r in rows if r['offset_seconds_from_target']==0]
  before=[r for r in rows if r['offset_seconds_from_target']<0]
  after=[r for r in rows if r['offset_seconds_from_target']>0]
  nearest_before=max(before,key=lambda r:r['offset_seconds_from_target']) if before else None
  nearest_after=min(after,key=lambda r:r['offset_seconds_from_target']) if after else None
  source_map={s['archive']:s.get('normalized_value') for s in source_values}
  context=[]
  for r in rows:
   item=dict(r)
   item['difference_from_target_C']=float(Decimal(str(r['value']))-target)
   legacy=source_map.get('pocasi-loucka.eu_old')
   item['difference_from_legacy_C']=float(Decimal(str(r['value']))-Decimal(str(legacy))) if legacy is not None else None
   context.append(item)
  stations.append({'station_id':station_id,'station_name':name,'status':'AVAILABLE','file':str(rel),
   'file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
   'source_url':f'https://opendata.chmi.cz/meteorology/climate/historical/data/10min/{datetime.fromtimestamp(ts,timezone.utc).year}/{rel.name}',
   'dataset':'CHMI Open.Data.10M element T; values retained on source UTC grid, flags and quality preserved.',
   'exact_timestamp_match_count':len(exact),'nearest_before':nearest_before,'nearest_after':nearest_after,
   'observations_within_30_minutes':context})
 return {'method':'Exact UTC timestamps only; no interpolation or cadence conversion. This is regional plausibility context and not calibration or proof of Loucka sensor truth.',
  'target_timestamp_utc':datetime.fromtimestamp(ts,timezone.utc).isoformat().replace('+00:00','Z'),
  'stations':stations}
def main():
 c=sqlite3.connect(f'file:{DB.resolve()}?mode=ro',uri=True); targets=[]
 for ts,blob in c.execute("SELECT dateTime,comparison_zlib FROM timestamp_evidence WHERE local_year IN (2015,2022) ORDER BY dateTime"):
  x=json.loads(zlib.decompress(blob))['outTemp']
  if x.get('provenance_category')!='CONFLICTING_SOURCE' or x.get('target_value') is None:continue
  obs=x.get('source_observations') or []
  if not any(o.get('normalized_value')==x['target_value'] for o in obs):targets.append((int(ts),x))
 results=[]
 for ts,x in targets:
  window=[]
  for t,ival,b in c.execute('SELECT dateTime,target_interval,comparison_zlib FROM timestamp_evidence WHERE dateTime BETWEEN ? AND ? ORDER BY dateTime',(ts-1800,ts+1800)):
   f=json.loads(zlib.decompress(b))['outTemp']; window.append({'timestamp_utc':datetime.fromtimestamp(t,timezone.utc).isoformat().replace('+00:00','Z'),'timestamp_local':datetime.fromtimestamp(t,TZ).isoformat(),'interval_minutes':ival,'target_value':f.get('target_value'),'provenance_category':f.get('provenance_category')})
  target=Decimal(str(x['target_value'])); vals=[]
  for o in x.get('source_observations') or []:
   v=Decimal(str(o['normalized_value'])) if o.get('normalized_value') is not None else None
   vals.append({'archive':o.get('archive'),'raw_value':o.get('raw_value'),'normalized_value':o.get('normalized_value'),'usUnits':o.get('usUnits'),'interval_minutes':o.get('interval_minutes'),'difference_from_target':str(v-target) if v is not None else None})
  epsilon_case=max(abs(target),max((abs(Decimal(v['difference_from_target'])) for v in vals if v['difference_from_target'] is not None),default=Decimal(0)))<Decimal('1e-15')
  local_dt=datetime.fromtimestamp(ts,TZ); period=local_dt.strftime('%Y-%m')
  month_rows=c.execute('SELECT COUNT(*) FROM timestamp_evidence WHERE local_month=?',(period,)).fetchone()[0]
  alternatives=[Decimal(v['normalized_value']) for v in vals if v['normalized_value'] is not None]
  material_alternatives=[v for v in alternatives if abs(v-target)>=Decimal('0.01')]
  assessment=('Near-zero numerical disagreement among archive copies; exact source match fails only at floating-point epsilon scale. Neighboring temperatures cross 0 C smoothly. This is a provenance equality artifact, not evidence of a meteorological error.' if epsilon_case else 'Current primary archive and GW1000 copy contain a near-zero value while the older archive contains 0.525 C. Neighboring target values describe a plausible cooling transition, but the surrounding rows also have source conflicts, so continuity cannot identify which reading is true.')
  case_id='outTemp:'+datetime.fromtimestamp(ts,timezone.utc).strftime('%Y%m%dT%H%M%SZ')
  reference=chmi_context(ts,target,vals)
  regional_assessment={'status':'NO_CACHED_SAME_MONTH_REFERENCE','interpretation':'No matching immutable ten-minute CHMI file was available for this case.'}
  if period=='2022-12':
   legacy=next((Decimal(v['normalized_value']) for v in vals if v['archive']=='pocasi-loucka.eu_old' and v['normalized_value'] is not None),None)
   comparisons=[]
   for station in reference['stations']:
    for obs in (station.get('nearest_before'),station.get('nearest_after')):
     if obs is None:continue
     value=Decimal(str(obs['value']))
     comparisons.append({'station_id':station['station_id'],'timestamp_utc':obs['timestamp_utc'],'reference_value_C':float(value),
      'absolute_difference_from_target_C':float(abs(value-target)),
      'absolute_difference_from_legacy_C':float(abs(value-legacy)) if legacy is not None else None})
   regional_assessment={'status':'ADJACENT_REGIONAL_CONTEXT_ONLY','nearest_slot_comparisons':comparisons,
    'interpretation':'The cached CHMI 10-minute values on either side are numerically closer to the legacy 0.525 C reading than to the near-zero target at these nearby stations. They are not exact-time observations of the Loucka sensor, so this does not establish the historical value or authorize correction.'}
  results.append({'case_id':case_id,'timestamp_epoch':ts,'timestamp_utc':datetime.fromtimestamp(ts,timezone.utc).isoformat().replace('+00:00','Z'),'timestamp_local':local_dt.isoformat(),'period':period,'target_value':x['target_value'],'target_unit':x.get('target_unit'),'source_observations':vals,'surrounding_target_series_plus_minus_30min':window,'assessment':assessment,
   'expert_disposition':('NO_METEOROLOGICAL_CORRECTION; retain the stored value and classify the exact-match failure as floating-point epsilon noise.' if epsilon_case else 'UNRESOLVED_SOURCE_CONFLICT; preserve the current archive value unchanged and do not substitute the legacy value.'),
   'evidence_strength':'HIGH for non-material numerical disagreement; NONE for sensor truth' if epsilon_case else 'MODERATE for archive-copy provenance; INSUFFICIENT for sensor truth',
   'correction_authorized':False,'replacement_value':None,
   'quantitative_context':{'largest_absolute_archive_copy_difference_C':str(max((abs(Decimal(v['difference_from_target'])) for v in vals if v['difference_from_target'] is not None),default=Decimal(0))),'material_alternative_values_C':[str(v) for v in material_alternatives],'timestamp_evidence_rows_in_month':month_rows,'illustrative_single_slot_month_mean_shift_C':(str((material_alternatives[0]-target)/Decimal(month_rows)) if material_alternatives and month_rows else None)},
   'regional_reference_context':reference,'regional_reference_assessment':regional_assessment,
   'remaining_evidence_needed':(['Original sensor payload or acquisition/driver trace to establish the physical reading. Regional context is available only on adjacent ten-minute UTC slots and cannot resolve this exact five-minute observation.' if period=='2022-12' else 'Original sensor payload or acquisition/driver trace to establish physical reading; exact-time independent station record if available.'] if not epsilon_case else ['No further evidence is needed to conclude that the disagreement is numerically negligible; sensor truth is not established.'])})
 c.close();out={'schema':'loucka-three-unmatched-temperature-review-v1','snapshot_id':hashlib.sha256(DB.read_bytes()).hexdigest(),'count':len(results),'selection':'outTemp CONFLICTING_SOURCE target value does not exactly match any normalized source observation','results':results}
 (ROOT/'THREE_UNMATCHED_TEMPERATURE_VALUES_REVIEW.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'count':len(results),'timestamps':[r['timestamp_utc'] for r in results]},indent=2))
if __name__=='__main__':main()
