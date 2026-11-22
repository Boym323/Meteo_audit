#!/usr/bin/env python3
"""Derive compact annual/per-field concordance summaries from bounded SELECT output."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=json.loads((ROOT/'data/gw1000_gw3000_historical_yearly_concordance.json').read_text())
rows=src['rows']; fields=src['fields']
assert [int(r['utc_year']) for r in rows]==list(range(2009,2026))
annual=[]; totals={f:{'both_nonnull':0,'equal_nonnull':0,'one_sided_null':0} for f in fields}; diagnostic_totals={f:{'both_nonnull':0,'equal_nonnull':0,'one_sided_null':0} for f in fields}
csv_rows=[]
for r in rows:
    y=int(r['utc_year']); p=int(r['gw3000_rows']); g=int(r['gw1000_rows']); pairs=int(r['exact_timestamp_pairs'])
    annual.append({'utc_year':y,'gw3000_rows':p,'gw1000_rows':g,'exact_timestamp_pairs':pairs,
                   'gw3000_only_rows':p-pairs,'gw1000_only_rows':g-pairs,
                   'unit_mismatches':int(r['unit_mismatch_pairs']),'interval_mismatches':int(r['interval_mismatch_pairs']),
                   'scope_label':'DIAGNOSTIC_ONLY' if y==2021 else 'HISTORICAL_BASELINE'})
    for f in fields:
        both=int(r[f+'_both_nonnull']); equal=int(r[f+'_equal_nonnull']); asym=int(r[f+'_one_sided_null'])
        bucket=diagnostic_totals if y==2021 else totals
        bucket[f]['both_nonnull']+=both;bucket[f]['equal_nonnull']+=equal;bucket[f]['one_sided_null']+=asym
        csv_rows.append({'utc_year':y,'variable':f,'exact_timestamp_pairs':pairs,'both_nonnull':both,
                         'equal_nonnull':equal,'different_nonnull':both-equal,'one_sided_null':asym,
                         'both_null':pairs-both-asym,
                         'equal_fraction_paired_nonnull':(equal/both if both else None),
                         'year_scope':'DIAGNOSTIC_ONLY' if y==2021 else 'HISTORICAL_BASELINE'})
fields_summary=[]
for f,v in totals.items():
    fields_summary.append({'variable':f,**v,'different_nonnull':v['both_nonnull']-v['equal_nonnull'],
                           'equal_fraction_paired_nonnull':(v['equal_nonnull']/v['both_nonnull'] if v['both_nonnull'] else None)})
fields_summary.sort(key=lambda x:(x['equal_fraction_paired_nonnull'] if x['equal_fraction_paired_nonnull'] is not None else 1,x['variable']))
diagnostic_summary=[{'variable':f,**v,'different_nonnull':v['both_nonnull']-v['equal_nonnull'],'equal_fraction_paired_nonnull':(v['equal_nonnull']/v['both_nonnull'] if v['both_nonnull'] else None)} for f,v in diagnostic_totals.items()]
result={'query_date_utc':src['query_date_utc'],'source':src['source'],'scope_utc':src['scope_utc'],'table_pair':src['table_pair'],
        'annual':annual,'field_totals':fields_summary,'diagnostic_2021_field_totals':diagnostic_summary,'historical_baseline_exact_pairs_excluding_2021':sum(x['exact_timestamp_pairs'] for x in annual if x['utc_year']!=2021),
        'provenance_limit':'Exact copied values demonstrate database-level commonality, not independent sensor truth, source identity, or the historical merge/cleaning rule. OWNER_ATTESTED context is separate.',
        'diagnostic_years':[2021], 'database_writes':0}
(ROOT/'data/gw1000_gw3000_historical_concordance_summary.json').write_text(json.dumps(result,indent=2)+'\n')
with (ROOT/'reports/2026-11-13-gw1000-gw3000-historical-field-concordance.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(csv_rows[0]));w.writeheader();w.writerows(csv_rows)
print(json.dumps({'years':len(annual),'rows_per_archive':sum(x['gw3000_rows'] for x in annual),
 'exact_pairs':sum(x['exact_timestamp_pairs'] for x in annual),'one_sided_rows':sum(x['gw3000_only_rows']+x['gw1000_only_rows'] for x in annual),
 'unit_mismatches':sum(x['unit_mismatches'] for x in annual),'interval_mismatches':sum(x['interval_mismatches'] for x in annual),
 'worst_concordance_fields':fields_summary[:12]},indent=2))
