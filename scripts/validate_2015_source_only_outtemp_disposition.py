#!/usr/bin/env python3
"""Validate row-level outTemp triage for the 2015 source-only cohort."""
import csv, json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
base=list(csv.DictReader((ROOT/'data/2015_source_only_row_dispositions.csv').open()))
triage=list(csv.DictReader((ROOT/'data/2015_source_only_outtemp_field_disposition.csv').open()))
assert len(base)==2147 and len(triage)==2147
assert len({r['target_time'] for r in base})==2147
assert len({r['target_time'] for r in triage})==2147
b={r['target_time']:r for r in base}
q={r['target_time']:r for r in triage}
assert b.keys()==q.keys()
assert all(r['wh_outTemp']=='0' and r['old_outTemp']=='' for r in base)
assert all(r['reconstruction_exact_row']=='0' and r['merged_exact_row']=='0' for r in base)
assert all(r['altimeter_copy_status']=='CONFLICT' for r in base)
assert sum(r['rain_copy_status']=='CONFLICT' for r in base)==2
assert all(r['rainrate_copy_status']=='AGREE' for r in base)
assert all(r['wh_outTemp']=='0' and r['old_outTemp']=='' and r['restoration_decision']=='DO_NOT_RESTORE_SOURCE_ZERO' for r in triage)
for r in triage:
    both=r['both_neighbors_zero']=='1'
    luha=r['exact_luhamet_nonzero_conflict']=='1'
    expected='SOURCE_SENSOR_STUCK_SUSPECTED' if both else ('SOURCE_ZERO_REGIONAL_CONFLICT_REVIEW' if luha else 'SOURCE_ZERO_UNRESOLVED')
    assert r['field_quality_disposition']==expected
    assert bool(r['luhamet_exact_temp'] not in ('',None))==bool(luha or (r['luhamet_exact_temp'] not in ('',None) and float(r['luhamet_exact_temp'])==0))
counts=Counter(r['field_quality_disposition'] for r in triage)
summary={
 'status':'PASS','records':len(triage),'unique_timestamps':len(q),
 'wh1080_zero_outTemp':sum(r['wh_outTemp']=='0' for r in triage),
 'old_weewx_null_outTemp':sum(r['old_outTemp']=='' for r in triage),
 'neighbor_both_zero':sum(r['both_neighbors_zero']=='1' for r in triage),
 'exact_luhamet_nonzero':sum(r['exact_luhamet_nonzero_conflict']=='1' for r in triage),
 'both_neighbor_zero_and_luhamet_nonzero':sum(r['both_neighbors_zero']=='1' and r['exact_luhamet_nonzero_conflict']=='1' for r in triage),
 'field_quality_counts':dict(counts),
 'interpretation':'field-level suspicion only; exact regional disagreement is not proof of local sensor error; no restoration is proposed'
}
(ROOT/'data/2015_source_only_outtemp_disposition_validation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
