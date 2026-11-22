#!/usr/bin/env python3
"""Derive a pre-2021 core-field concordance view from saved yearly exact-pair aggregates."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=json.loads((ROOT/'data/gw1000_gw3000_historical_yearly_concordance.json').read_text())
years=list(range(2009,2021)); fields=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','barometer','pressure','altimeter','dewpoint']
rows=[r for r in src['rows'] if int(r['utc_year']) in years]
assert {int(r['utc_year']) for r in rows}==set(years)
assert all(int(r['gw3000_rows'])==int(r['gw1000_rows'])==int(r['exact_timestamp_pairs']) for r in rows)
per=[];totals=[]
for field in fields:
 agg={'both_nonnull':0,'equal_nonnull':0,'one_sided_null':0}
 for r in rows:
  item={'year_utc':int(r['utc_year']),'variable':field,'exact_timestamp_pairs':int(r['exact_timestamp_pairs']),'both_nonnull':int(r[f'{field}_both_nonnull']),'equal_nonnull':int(r[f'{field}_equal_nonnull']),'one_sided_null':int(r[f'{field}_one_sided_null'])}
  item['different_values_when_both_nonnull']=item['both_nonnull']-item['equal_nonnull']
  per.append(item)
  for k in agg: agg[k]+=item[k]
 agg['different_values_when_both_nonnull']=agg['both_nonnull']-agg['equal_nonnull'];agg['variable']=field;totals.append(agg)
obj={'schema':'gw1000-gw3000-core-concordance-2009-2020-v1','source_snapshot':'data/gw1000_gw3000_historical_yearly_concordance.json','years_utc':years,'fields':fields,'exact_timestamp_pairs':sum(int(r['exact_timestamp_pairs']) for r in rows),'unit_mismatch_pairs':sum(int(r['unit_mismatch_pairs']) for r in rows),'interval_mismatch_pairs':sum(int(r['interval_mismatch_pairs']) for r in rows),'rowset_note':'All yearly row counts equal exact_timestamp_pairs in both databases for these 12 years, as already captured in the saved exact-pair snapshot.','totals':totals,'per_year_field':per,'interpretation':'Exact row-key pair and field value comparison from previous SELECT-only snapshot. Equal rows are shared historical copies, not independent sensors. Value equality or difference does not determine meteorological truth or the merge direction.'}
(ROOT/'data/gw1000_gw3000_core_concordance_2009_2020.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
with (ROOT/'reports/2026-11-13-gw1000-gw3000-core-concordance-2009-2020.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(per[0]));w.writeheader();w.writerows(per)
md=['# GW1000 / GW3000 core-field concordance — 2009–2020 UTC','','This is a deterministic year-slice of the previously captured exact-pair SELECT aggregates in `data/gw1000_gw3000_historical_yearly_concordance.json`; no database query was repeated. For every UTC year both archive row counts equal the exact timestamp-pair count; total pairs are **1,073,011** with zero unit or interval mismatches. Shared keys demonstrate a common rowset, not independent sensors or correct values.','','| Field | Both non-NULL | Equal values | Different values | One-sided NULL |','|---|---:|---:|---:|---:|']
for x in totals:md.append(f"| `{x['variable']}` | {x['both_nonnull']:,} | {x['equal_nonnull']:,} | {x['different_values_when_both_nonnull']:,} | {x['one_sided_null']:,} |")
md+=['','## Interpretation','','Core sensor fields `outTemp`, `outHumidity`, `rain`, `windSpeed`, and `windGust` match exactly wherever both copies are non-NULL in this interval. `barometer` also matches. `rainRate` has 30,728 differing paired values despite no one-sided NULL in the subset. In contrast, `pressure` has 907,237 differing values among 940,456 both-non-NULL pairs plus 54,839 one-sided NULLs; `altimeter` has 908,487 differences among 940,456 both-non-NULL pairs plus 54,839 one-sided NULLs. This aligns with the six-archive availability finding that pressure/altimeter availability diverges, while showing the stronger value-level difference on exact shared timestamps. `dewpoint` has 90 differences and 293 one-sided NULL cases; windDir has 3 differences and 11 one-sided NULLs.','','These discrepancies may arise from merge choice, field-specific transformation, differing producers or later cleanup. Current evidence does not establish which archive value is original or correct. The result is not a migration algorithm and does not support bulk restoration or conversion. The overall historic/2026 split and source caveats remain in `GW1000_GW3000_CONCORDANCE_REPORT.md`.','','Reproduce from saved aggregates: `python3 scripts/summarize_gw1000_gw3000_core_concordance_2009_2020.py`. Machine output: `data/gw1000_gw3000_core_concordance_2009_2020.json`; per-year/field output: `reports/2026-11-13-gw1000-gw3000-core-concordance-2009-2020.csv`. Year 2021 was excluded; no DB query or write occurred.']
(ROOT/'reports/2026-11-13-gw1000-gw3000-core-concordance-2009-2020.md').write_text('\n'.join(md)+'\n')
print('years',len(rows),'pairs',obj['exact_timestamp_pairs'],'fields',len(fields))
for x in totals:print(x['variable'],x['both_nonnull'],x['equal_nonnull'],x['different_values_when_both_nonnull'],x['one_sided_null'])
