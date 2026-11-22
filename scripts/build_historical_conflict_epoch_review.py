#!/usr/bin/env python3
"""Build an epoch-level conflict review from frozen value concordance summaries."""
import hashlib,json,sqlite3,zlib,math,heapq
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def sha256_file(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def directional_source_review():
 """Summarize target-matching-primary vs each named legacy copy, by field/year.

 Quantiles use a deterministic bottom-k sample keyed by timestamp. Exact signs,
 extrema, moments, and candidate 3.6-factor counts are streamed over all pairs.
 """
 source=ROOT/'data/historical_value_concordance.sqlite';source_sha=sha256_file(source)
 existing=ROOT/'HISTORICAL_CONFLICT_EPOCH_REVIEW.json'
 if existing.exists():
  try:
   cached=json.loads(existing.read_text())
   if cached.get('schema')=='loucka-historical-conflict-epoch-review-v2' and cached.get('source_concordance_sqlite_sha256')==source_sha:
    return cached['directional_source_distribution_rows']
  except (ValueError,KeyError):pass
 db=sqlite3.connect(f"file:{source}?mode=ro",uri=True)
 state={};limit=512
 for year,ts,blob in db.execute('SELECT local_year,dateTime,comparison_zlib FROM timestamp_evidence ORDER BY dateTime'):
  fields=json.loads(zlib.decompress(blob))
  for var,v in fields.items():
   obs={x['archive']:x for x in v['source_observations'] if x.get('normalized_value') is not None}
   primary=obs.get('pocasi-loucka.eu')
   if not primary or v.get('target_value') is None or Decimal(v['target_value'])!=Decimal(primary['normalized_value']): continue
   p=Decimal(primary['normalized_value'])
   for archive,o in obs.items():
    if archive=='pocasi-loucka.eu':continue
    legacy=Decimal(o['normalized_value'])
    if legacy==p:continue
    key=(var,year,archive);a=state.get(key)
    if a is None:a=state[key]={'n':0,'positive':0,'negative':0,'zero':0,'sum':0.0,'sum2':0.0,'min':None,'max':None,'factor36':0,'sample':[]}
    d=legacy-p;f=float(d);a['n']+=1;a['positive']+=d>0;a['negative']+=d<0;a['zero']+=d==0;a['sum']+=f;a['sum2']+=f*f
    a['min']=f if a['min'] is None else min(a['min'],f);a['max']=f if a['max'] is None else max(a['max'],f)
    if p!=0 and abs(legacy-p*Decimal('3.6'))<=max(Decimal('1e-9'),abs(legacy)*Decimal('1e-9')):a['factor36']+=1
    sample_digest=hashlib.sha256(f'{ts}|{var}|{archive}'.encode()).hexdigest();item=(-int(sample_digest[:16],16),f)
    if len(a['sample'])<limit:heapq.heappush(a['sample'],item)
    elif item>a['sample'][0]:heapq.heapreplace(a['sample'],item)
 db.close();out=[]
 for (var,year,archive),a in sorted(state.items()):
  vals=sorted(x[1] for x in a['sample'])
  def q(p):return vals[round((len(vals)-1)*p)] if vals else None
  mean=a['sum']/a['n'];sd=math.sqrt(max(0,a['sum2']/a['n']-mean*mean))
  out.append({'variable':var,'year':year,'primary_archive':'pocasi-loucka.eu','comparison_archive':archive,'pairs_target_matches_primary_and_archives_differ':a['n'],'legacy_minus_primary_sign_counts':{'positive':a['positive'],'negative':a['negative'],'zero':a['zero']},'delta_normalized_units':{'minimum':a['min'],'p10_deterministic_sample':q(.1),'median_deterministic_sample':q(.5),'p90_deterministic_sample':q(.9),'maximum':a['max'],'mean':mean,'population_sd':sd,'quantile_method':f'deterministic bottom-{limit} SHA256(dateTime|variable|archive) sample; exact sign, extrema and moments over all pairs'},'legacy_equals_3_6_times_primary_within_1e-9':a['factor36'],'factor36_screen_denominator':a['n'],'sensor_or_driver_epoch_proven':False,'interpretation':'Pairwise archive divergence only; source copies may share lineage. Direction/distribution do not establish which archive is correct or identify a hardware/driver epoch.'})
 return out

def main():
 src=ROOT/'HISTORICAL_CONFLICT_SUBTYPES_SUMMARY.json';summary=json.loads(src.read_text());rows=summary['by_variable_year_and_source_epoch'];out=[]
 for r in rows:
  n=int(r.get('CONFLICTING_SOURCE_TOTAL',0));dis=int(r.get('TARGET_MATCHES_PRIMARY_WITH_LEGACY_DISAGREEMENT',0));rounding=int(r.get('LEGACY_NUMERIC_ROUNDING_ONLY',0));known=int(r.get('KNOWN_TRANSFORMATION_PATTERN_SUPPORTED_BY_EXISTING_AUDIT',0));no_match=int(r.get('TARGET_NO_COMPATIBLE_SOURCE_MATCH',0));legacy=int(r.get('TARGET_MATCHES_LEGACY_ONLY',0))
  if not n:continue
  var=r['variable'];wind=var in {'windSpeed','windGust'}
  out.append({'variable':var,'year':int(r['year']),'source_availability_signature':r['source_epoch_evidence_signature'],'conflicting_values':n,'target_matches_primary_with_legacy_difference':dis,'numeric_rounding_only':rounding,'transformation_supported_at_value_level':known,'target_no_source_match':no_match,'target_matches_legacy_only':legacy,'unresolved_primary_legacy_difference':max(0,dis-rounding-known),'unit_semantics_unresolved':int(r.get('UNRESOLVED_UNIT_OR_DRIVER_SEMANTICS',0)),'epoch_context':('Historical wind report documents changes in archive ratios and a standard METRICWX-to-METRIC factor 3.6 for speed/gust, but value-level summary support is zero here; retain as unresolved unless exact row-level factor evidence is joined.' if wind else ('Pressure field semantics remain driver/altitude dependent.' if var in {'pressure','barometer','altimeter'} else 'Archive copies are dependent lineage; disagreement does not identify the correct measurement.')),'evidence_status':'UNRESOLVED' if max(0,dis-rounding-known)>0 or no_match or legacy else 'NO_MATERIAL_DIFFERENCE_CLASSIFIED'})
 totals=summary['totals'];directional=directional_source_review();doc={'schema':'loucka-historical-conflict-epoch-review-v2','generated_utc':summary['snapshot_id'],'snapshot_id':summary['snapshot_id'],'source_summary_sha256':sha256_file(src),'source_concordance_sqlite_sha256':sha256_file(ROOT/'data/historical_value_concordance.sqlite'),'source_rows':len(out),'conflicting_values':totals['CONFLICTING_SOURCE_TOTAL'],'legacy_disagreement_values':totals.get('LEGACY_NUMERICALLY_MATERIAL_DIFFERENCE',0),'rounding_only_values':totals.get('LEGACY_NUMERIC_ROUNDING_ONLY',0),'value_level_transformation_supported':totals.get('KNOWN_TRANSFORMATION_PATTERN_SUPPORTED_BY_EXISTING_AUDIT',0),'unmatched_target_values':totals.get('TARGET_NO_COMPATIBLE_SOURCE_MATCH',0),'epoch_review_rows':out,'directional_source_distribution_rows':directional,'directional_source_distribution_method':'For each year, variable, and named non-primary archive, compare normalized source values only where the target exactly equals the primary archive and the archive pair differs. Deltas are comparison archive minus primary archive. This is a pairwise diagnostic and is not substituted into original concordance counts.','interpretation_limits':['Grouping by year and archive availability is not proof of sensor epoch or instrument identity.','Dependent archives are not independent measurements.','Known unit/driver history explains only cases with reproducible exact row-level support; otherwise epoch remains open.','Yearly named-source divergence is not evidence of hardware replacement or driver change; dated local configuration evidence is required.','No target values or source archives were changed.']}
 (ROOT/'HISTORICAL_CONFLICT_EPOCH_REVIEW.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+'\n');print(json.dumps({k:doc[k] for k in ('source_rows','conflicting_values','legacy_disagreement_values','rounding_only_values','value_level_transformation_supported','unmatched_target_values')},indent=2))
 byvar=defaultdict(lambda:defaultdict(int))
 for r in directional:
  a=byvar[r['variable']];a['pairs']+=r['pairs_target_matches_primary_and_archives_differ'];a['positive']+=r['legacy_minus_primary_sign_counts']['positive'];a['negative']+=r['legacy_minus_primary_sign_counts']['negative'];a['factor36']+=r['legacy_equals_3_6_times_primary_within_1e-9']
 md=['# Historical conflict epoch and directional archive review','',f"Snapshot `{summary['snapshot_id']}`; source value-concordance SHA-256 `{doc['source_concordance_sqlite_sha256']}`.",'',f"The canonical value-level totals are preserved: {doc['conflicting_values']:,} source conflicts, including {doc['legacy_disagreement_values']:,} materially different legacy values and {doc['rounding_only_values']:,} rounding-only values. The value-level transformation-supported count remains {doc['value_level_transformation_supported']:,}; unmatched target/source cases remain {doc['unmatched_target_values']}.",'','## Pairwise direction and distribution','', 'For each local calendar year, field, and named non-primary archive, the companion JSON compares source values only when the target exactly equals `pocasi-loucka.eu` and the named archive differs. Delta is normalized comparison archive minus primary archive. These are pairwise diagnostic counts, can count a timestamp once per source archive, and are not additions to the canonical conflict count. Exact direction, extrema and moments use all eligible pairs; p10/median/p90 use the deterministic SHA256 bottom-512 sample per group.','', '| Field | Pairwise differing values | Legacy above primary | Legacy below primary | Exact 3.6-factor screen |','|---|---:|---:|---:|---:|']
 for var,a in sorted(byvar.items()):md.append(f"| `{var}` | {a['pairs']:,} | {a['positive']:,} | {a['negative']:,} | {a['factor36']:,} |")
 md += ['', 'The exact 3.6 screen is `legacy = 3.6 × primary` within relative/absolute 1e-9 after the existing unit normalization. It identifies a candidate scaling signature, not proven cause or a correction rule. In wind, the signature also appears in 2009–2013. This is consistent with the existing wind review finding that early `usUnits=16/17` copies can contain identical raw speed/gust values: applying the stored unit codes yields a 3.6 normalized difference, while the raw archive pair itself does not identify which copy is already converted. The new pairwise result therefore extends the named archive comparison, not the proven transformation window. These cohorts remain open without dated configuration/driver evidence. Archive aliases share lineage, so apparent replication across copies is not independent confirmation.','', 'The source availability cohorts are not physical sensor epochs. This review adds no hardware replacement or driver change dates because local dated evidence has not established them. The canonical provenance categories, exact comparisons, historical values, and publication decisions are unchanged; no target values or archives were modified.','', '## Reproduction','', 'Run `python3 scripts/build_historical_conflict_epoch_review.py`. It reads `data/historical_value_concordance.sqlite` via SQLite `mode=ro`, streams timestamp records, and writes the JSON evidence plus this report.']
 (ROOT/'HISTORICAL_CONFLICT_EPOCH_REVIEW.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
if __name__=='__main__':main()
