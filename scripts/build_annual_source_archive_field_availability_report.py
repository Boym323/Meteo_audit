#!/usr/bin/env python3
"""Render UTC-year availability reports and read-only SQL from captured MCP aggregates."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data/annual_source_archive_field_availability_2009_2020.json').read_text())
fields=data['fields']; years=data['years']; databases=list(data['data'])
assert databases==['old_weewx','weewx_WH1080'] and len(fields)==50 and len(years)==12
out=[]
for db in databases:
 for yr in data['data'][db]:
  assert yr['year'] in years
  for field in fields:
   c=yr['fields'][field]
   assert c['nonnull']+c['null']==yr['archive_rows']
   out.append({'database':db,'year_utc':yr['year'],'archive_rows':yr['archive_rows'],'variable':field,'nonnull_rows':c['nonnull'],'null_rows':c['null'],'null_share':c['null']/yr['archive_rows'] if yr['archive_rows'] else None,'first_epoch':yr['first_epoch'],'last_epoch':yr['last_epoch'],'min_units':yr['min_units'],'max_units':yr['max_units'],'unit_count':yr['unit_count'],'min_interval':yr['min_interval'],'max_interval':yr['max_interval'],'interval_count':yr['interval_count']})
with (ROOT/'reports/2026-11-13-annual-source-archive-field-availability-2009-2020.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
# Emit exactly reproducible SELECT-only query chunks: 20 fields per bounded year range.
sqlroot=ROOT/'sql/readonly';sqlroot.mkdir(parents=True,exist_ok=True)
for db in databases:
 lines=[f'-- READ-ONLY annual field-availability aggregate for `{db}`.','-- Run each SELECT independently through Weather MCP against database_name shown above.','-- UTC calendar bounds are fixed Unix epochs; no session timezone conversion is used.','-- 20 common numeric fields per query keeps the query size bounded.']
 for y in years:
  lo=1704067200 if y==2024 else int(__import__('datetime').datetime(y,1,1,tzinfo=__import__('datetime').timezone.utc).timestamp())
  hi=int(__import__('datetime').datetime(y+1,1,1,tzinfo=__import__('datetime').timezone.utc).timestamp())
  for offset in range(0,len(fields),20):
   batch=fields[offset:offset+20]
   measures=', '.join(f'COUNT(`{c}`) AS `n_{c}`' for c in batch)
   lines += ['',f'-- {y}, field batch {offset//20+1}',f'SELECT COUNT(*) AS archive_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch, MIN(usUnits) AS min_units, MAX(usUnits) AS max_units, COUNT(DISTINCT usUnits) AS unit_count, MIN(`interval`) AS min_interval, MAX(`interval`) AS max_interval, COUNT(DISTINCT `interval`) AS interval_count, {measures}',f'FROM archive WHERE dateTime >= {lo} AND dateTime < {hi};']
 (sqlroot/f'annual_source_field_availability_{db}_2009_2020.sql').write_text('\n'.join(lines)+'\n')
# Summarize cross-archive availability differences; this is not a source value concordance test.
diffs=[]
for year in years:
 for field in fields:
  vals={db:data['data'][db][year-years[0]]['fields'][field]['nonnull'] for db in databases}
  if vals[databases[0]]!=vals[databases[1]]:
   diffs.append({'year_utc':year,'variable':field,'old_weewx_nonnull':vals['old_weewx'],'weewx_WH1080_nonnull':vals['weewx_WH1080'],'difference':vals['weewx_WH1080']-vals['old_weewx']})
summary={'as_of':'2026-11-13','database_scope':databases,'period':'UTC calendar years 2009–2020','common_numeric_field_count':len(fields),'year_count':len(years),'field_year_cells_per_archive':len(fields)*len(years),'archive_rows_total':{db:sum(x['archive_rows'] for x in data['data'][db]) for db in databases},'availability_cells_with_count_difference':len(diffs),'availability_difference_examples':diffs[:50],'all_difference_cells_file':'reports/2026-11-13-annual-source-archive-field-availability-2009-2020.csv','limitations':['Only numeric fields common to both original archives are included (50); archive-specific fields require separate lineage treatment.','Counts measure row/field availability, not measurement validity, equality, source independence or restoration eligibility.','Does not include the three production/merged archive databases; Weather MCP rejects their dotted database identifiers.','No target archive tail refresh, staging or database writes. Q1 2018 is included for descriptive inventory only and remains protected from new proposals; 2021 is outside the scope.']}
(ROOT/'data/annual_source_archive_field_availability_summary_2009_2020.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
md=['# Annual source archive field availability — 2009–2020 UTC','','Read-only bounded annual aggregates for the 50 numeric fields common to `old_weewx.archive` and `weewx_WH1080.archive`. Each year was queried using fixed Unix UTC bounds, 20 field counts per SELECT, sequentially. This is availability evidence only, not measurement validation.','','| Database | Rows 2009–2020 | Field/year cells |','|---|---:|---:|']
for db in databases:md.append(f"| `{db}` | {summary['archive_rows_total'][db]:,} | {len(fields)*len(years):,} |")
md += ['',f"Across {len(fields)*len(years)} cells per archive, **{len(diffs)}** field/year cells have different non-NULL counts between the two copies. The CSV contains all 1,200 cells per archive; the summary JSON contains 50 representative difference records and the total. Count differences do not identify which copy is valid.",'','The result does not infer that copies are independent; owner testimony says archive origin/merge rules are unknown and duplicates may derive from shared history. This availability aggregate does not explain why a row/value is absent or changed.','','## Reproduction and limitations','','Captured aggregate: `data/annual_source_archive_field_availability_2009_2020.json`. Render: `python3 scripts/build_annual_source_archive_field_availability_report.py`. Read-only SQL is in `sql/readonly/annual_source_field_availability_old_weewx_2009_2020.sql` and `sql/readonly/annual_source_field_availability_weewx_WH1080_2009_2020.sql`; each SELECT is bounded to one UTC year and 20 fields.','','MCP denied direct access to `pocasi-loucka.eu`, `pocasi-loucka.eu_GW1000` and `pocasi-loucka.eu_old` with `INVALID_ARGUMENT` despite listing them as databases. Therefore this report covers only the two permitted source archive names; it is not a complete six-archive readiness matrix. No writes, staging, or application occurred. Q1 2018 values are descriptive only; 2021 was not queried.']
(ROOT/'reports/2026-11-13-annual-source-archive-field-availability-2009-2020.md').write_text('\n'.join(md)+'\n')
print(f'PASS render: {len(out)} CSV cells; {len(diffs)} field/year availability count differences; rows={summary["archive_rows_total"]}')
