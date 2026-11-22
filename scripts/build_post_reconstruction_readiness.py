#!/usr/bin/env python3
"""Rebuild year×field availability counts and operation annotations from live U1 snapshots."""
import csv, datetime, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
base=list(csv.DictReader((ROOT/'data/final_readiness_matrix_77x18.csv').open()))
coverage=json.loads((ROOT/'data/post_reconstruction_coverage_77x18.json').read_text())
ops_doc=json.loads((ROOT/'reports/v1_2/approved_operations_322.json').read_text())
coverage_by_year={str(x['utc_year']):x for x in coverage}
ops={}
for batch in ops_doc['batches']:
    classification=batch['classification']
    for op in batch['corrections']:
        year=str(datetime.datetime.fromtimestamp(op['timestamp'],datetime.timezone.utc).year)
        key=(year,op['variable'])
        val=ops.setdefault(key,{'total':0,'RESTORED':0,'ESTIMATED':0})
        val['total']+=1
        val[classification]=val.get(classification,0)+1
for row in base:
    year=row['utc_year']; variable=row['variable']; cov=coverage_by_year[year]
    row['archive_rows']=str(cov['row_count'])
    row['null_rows']=str(cov[variable])
    row['nonnull_rows']=str(int(cov['row_count'])-int(cov[variable]))
    row['active_unapproved_proposal_operations']='1' if (year=='2018' and variable in ('rain','rainRate')) else '0'
    applied=ops.get((year,variable),{'total':0,'RESTORED':0,'ESTIMATED':0})
    row['applied_reconstruction_operations_this_phase']=str(applied['total'])
    row['restored_operations_this_phase']=str(applied['RESTORED'])
    row['estimated_operations_this_phase']=str(applied['ESTIMATED'])
    row['coverage_snapshot']='LIVE_POST_322_UTC_EPOCH_AGGREGATE'
    if applied['ESTIMATED']:
        row['raw_origin_classification']='CELL_CONTAINS_ESTIMATED_VALUES; OTHER_VALUE_ORIGIN_UNCERTAIN'
        row['raw_value_display']='READY_WITH_LIMITATIONS_ESTIMATES_AND_PROVENANCE_FLAGS_REQUIRED'
        row['historical_graph']='READY_WITH_LIMITATIONS_GAPS_AND_ESTIMATES_MUST_BE_DISTINGUISHED'
    elif applied['RESTORED']:
        row['raw_origin_classification']='CELL_CONTAINS_RESTORED_VALUES; OTHER_VALUE_ORIGIN_UNCERTAIN'
        row['raw_value_display']='READY_WITH_LIMITATIONS_RESTORED_PROVENANCE_FLAG_REQUIRED'
        row['historical_graph']='READY_WITH_LIMITATIONS_GAPS_AND_RESTORED_PROVENANCE_FLAGS'
    if year=='2021':
        row['protection_status']='DIAGNOSTIC_2021_NO_CORRECTION_AUTHORIZED'
        row['raw_value_display']='DIAGNOSTIC_ONLY_2021'
        row['historical_graph']='DIAGNOSTIC_ONLY_2021'
    if year=='2018':
        row['protection_status']='Q1_2018_PROTECTED_ANNUAL_CELL_CONTAINS_INTERIM_PERIOD'
        row['raw_value_display']='REVIEW_REQUIRED_PROTECTED_Q1_2018_ANNUAL_MIXED_PERIOD'
        row['historical_graph']='REVIEW_REQUIRED_PROTECTED_Q1_2018_ANNUAL_MIXED_PERIOD'
# Statistical readiness remains as established; do not upgrade to READY based on filling NULLs.
fields=list(base[0])
for name in ['applied_reconstruction_operations_this_phase','restored_operations_this_phase','estimated_operations_this_phase','coverage_snapshot']:
    if name not in fields: fields.append(name)
with (ROOT/'ARCHIVE_STATISTICAL_QUALITY_MATRIX.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(base)
(ROOT/'POST_RECONSTRUCTION_READINESS.json').write_text(json.dumps({'snapshot_utc':'2026-11-14','matrix_rows':len(base),'years':18,'variables':77,'coverage_source':'data/post_reconstruction_coverage_77x18.json','operation_source':'reports/v1_2/approved_operations_322.json','rows':base},ensure_ascii=False,indent=2)+'\n')
print(f'updated {len(base)} year-variable cells; rows={sum(int(r["archive_rows"]) for r in base if r["variable"]=="outTemp")}; applied_ops={sum(int(r["applied_reconstruction_operations_this_phase"]) for r in base)}')
