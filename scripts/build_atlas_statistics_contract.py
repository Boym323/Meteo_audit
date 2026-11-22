#!/usr/bin/env python3
"""Build a deterministic atlas contract for all 248 candidate evidence rows."""
import ast,csv,json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
TZ=ZoneInfo('Europe/Prague')
FIELDS={
 "statistic_id":"string", "period":"string", "period_start":"string", "period_end":"string", "timezone":"string",
 "variable":"string", "statistic":"string", "value":["number","null"], "unit":"string",
 "expected_slots":"integer", "observed_slots":"integer", "coverage":"number", "time_coverage":["number","null"],
 "longest_gap":["integer","null"], "provenance_breakdown":"object", "estimated_count":"integer",
 "conflict_count":"integer", "unresolved_conflict_count":"integer", "sensor_epoch_id":["string","null"],
 "reference_validation":["object","null"], "methodology_version":"string", "publication_readiness":"string",
 "publication_authorized":"boolean", "limitations":"array", "uncertainty":"string", "evidence_reference":"string",
 "snapshot_id":"string", "generated_utc":"string",
 "interval_weighted_value":["number","null"], "interval_time_coverage":"number", "longest_uncovered_gap_seconds":"integer"
}

def iso_boundary(period,next_month=False):
    y,m=map(int,period.split('-'))
    if next_month:y,m=(y+1,1) if m==12 else (y,m+1)
    return datetime(y,m,1,tzinfo=TZ).isoformat()

def main():
    candidates=json.loads((ROOT/'MONTHLY_PUBLICATION_CANDIDATES.json').read_text())['candidates']
    evidence=json.loads((ROOT/'MONTHLY_VALIDATION_RESULTS.json').read_text())
    evidence_by={(r['period'],r['variable']):r for r in evidence['records']}
    interval=json.loads((ROOT/'INTERVAL_COVERAGE_REVIEW.json').read_text())
    interval_by={(r['period'],r['variable']):r for r in interval['results']}
    with (ROOT/'data/INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_MONTHLY.csv').open(encoding='utf-8',newline='') as stream:
        interval_variant_rows={(r['period'],r['variable'],r['variant']):r for r in csv.DictReader(stream)}
    registry=json.loads((ROOT/'STATION_SENSOR_EPOCH_REGISTRY.json').read_text())
    epoch=(registry.get('sensor_epochs') or [{}])[0].get('station_epoch_id')
    decisions={}
    with (ROOT/'STATISTICAL_PUBLICATION_DECISIONS_V3.csv').open(encoding='utf-8',newline='') as f:
        for row in csv.DictReader(f):
            if row['scope']=='MONTHLY' and row['statistic']=='MEAN':decisions[(row['period'],row['variable'])]=row
    generated=json.loads((ROOT/'data/PUBLICATION_READINESS_DECISIONS.json').read_text())['source_stats_snapshot_utc']
    snapshot=evidence['snapshot_id']; records=[]
    for c in sorted(candidates,key=lambda x:(x['period'],x['variable'])):
        key=(c['period'],c['variable']);ev=evidence_by[key];iv=interval_by.get(key,{});dec=decisions.get(key,{})
        ir=interval_variant_rows.get((c['period'],c['variable'],'B_DOCUMENTED_SOURCE_AND_RECOVERY'),{})
        prov=ev['provenance_breakdown'];conf=int(prov.get('CONFLICTING_SOURCE',0));unresolved=int(prov.get('UNRESOLVED',0))
        limitations=list(ev['limitations'])
        if iv.get('overlap_detected'):limitations.append('Archive intervals overlap; safe time coverage is withheld for this period-variable.')
        limitations.extend([
          'This is a candidate monthly mean from the documented B source/recovery variant; it is not an interval-adjusted canonical statistic.',
          'This local preview is not publication authorization and does not claim full climatological representativeness.'
        ])
        ref=None
        if ev.get('regional_reference_summary') or ev.get('reference_summary'):
            ref={'evidence_status':ev.get('evidence_status'),'external_comparison_available':bool(ev.get('external_validation')),
                 'physical_validation':bool(ev.get('physical_validation')),'summary':ev.get('regional_reference_summary') or ev.get('reference_summary')}
        record={
          'statistic_id':dec.get('statistic_id',f"{c['period']}:MONTHLY:{c['variable']}:MEAN"),'period':c['period'],
          'period_start':dec.get('period_start',iso_boundary(c['period'])),'period_end':dec.get('period_end',iso_boundary(c['period'],True)),'timezone':'Europe/Prague',
          'variable':c['variable'],'statistic':ev['statistic'],'value':c['value'],'unit':c['unit'],
          'expected_slots':int(c['expected_slots']),'observed_slots':int(c['observed_slots']),'coverage':float(c['coverage']),
          'time_coverage':iv.get('safe_time_coverage'),'longest_gap':int(iv['gap_seconds_between_intervals']) if iv.get('gap_seconds_between_intervals') is not None else None,
          'provenance_breakdown':prov,'estimated_count':int(prov.get('ESTIMATED',0)),
          'conflict_count':conf,'unresolved_conflict_count':conf+unresolved,
          'sensor_epoch_id':ev.get('sensor_epoch_id') or epoch,'reference_validation':ref,
          'methodology_version':dec.get('methodology_version','statistical-publication-policy-v3.0'),
          'publication_readiness':dec.get('publication_readiness','REVIEW_REQUIRED_EVIDENCE'),
          'publication_authorized':False,'limitations':limitations,
          'uncertainty':dec.get('uncertainty') or 'Candidate statistic has unresolved physical, provenance, or representativeness uncertainty.',
          'evidence_reference':f"MONTHLY_VALIDATION_RESULTS.json#period={c['period']}&variable={c['variable']}",
          'snapshot_id':snapshot,'generated_utc':generated,
          'interval_weighted_value':float(ir['interval_mean']) if ir.get('interval_mean') else None,
          'interval_time_coverage':float(ir.get('time_coverage') or 0),
          'longest_uncovered_gap_seconds':int(ir.get('longest_uncovered_gap_seconds') or 0)
        }
        records.append(record)
    schema={'$schema':'https://json-schema.org/draft/2020-12/schema','title':'Loucka Atlas Statistics Contract','type':'object',
      'required':['statistics','snapshot_id','publication_authorized'],
      'properties':{'statistics':{'type':'array','items':{'type':'object','required':list(FIELDS),
      'properties':{k:{'type':v} for k,v in FIELDS.items()}}},'snapshot_id':{'type':'string'},'publication_authorized':{'type':'boolean'}}}
    out={'schema_version':'2.0.0','json_schema':schema,'snapshot_id':snapshot,'publication_authorized':False,
      'generated_utc':generated,'statistics':records,
      'contract_notes':['Readiness is not publication authorization; every record has publication_authorized=false.',
        'The contract contains all 248 priority monthly mean candidates with individual evidence linkage, not only candidates that passed validation.',
        'Values are slot-selected outputs from B_DOCUMENTED_SOURCE_AND_RECOVERY; interval_weighted_value is a separate clipped-interval diagnostic and is not silently substituted.',
        'time_coverage is actual interval overlap coverage only when overlap checks permit a safe value; null means not established or withheld.',
        'All 248 records remain private-station candidate evidence and do not claim full climatological representativeness.']}
    (ROOT/'ATLAS_STATISTICS_CONTRACT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'records':len(records),'candidate_records':len(candidates),'required_fields':len(FIELDS),
      'all_fields_present':all(set(FIELDS)<=r.keys() for r in records),'publication_authorized':False},indent=2))
if __name__=='__main__':main()
