#!/usr/bin/env python3
"""Combine six frozen/annual archive availability sources for 11 core fields, 2009-2020."""
import csv,json
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
years=list(range(2009,2021)); core=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','barometer','pressure','altimeter','dewpoint']
recon=json.loads((ROOT/'reports/2026-11-13-annual-archive-field-availability-2009-2026.json').read_text())
sources=json.loads((ROOT/'data/annual_source_archive_field_availability_2009_2020.json').read_text())
merged=json.loads((ROOT/'data/annual_merged_archive_core_availability_2009_2020.json').read_text())
by={}
for year in years:
 rec=[x for x in recon['records'] if x['year']==year]
 by[('loucka_reconstruction',year)]={'archive_rows':int(recon['year_row_counts'][str(year)]),'fields':{x['variable']:{'nonnull':int(x['nonnull_rows']),'null':int(x['null_rows'])} for x in rec}}
 for db in ('old_weewx','weewx_WH1080'):
  x=sources['data'][db][year-2009];by[(db,year)]={'archive_rows':x['archive_rows'],'first_epoch':x['first_epoch'],'last_epoch':x['last_epoch'],'min_units':x['min_units'],'max_units':x['max_units'],'unit_count':x['unit_count'],'min_interval':x['min_interval'],'max_interval':x['max_interval'],'interval_count':x['interval_count'],'fields':x['fields']}
 for db in merged['databases']:
  x=merged['data'][db][year-2009];by[(db,year)]={'archive_rows':x['archive_rows'],'first_epoch':x['first_epoch'],'last_epoch':x['last_epoch'],'min_units':x['min_units'],'max_units':x['max_units'],'unit_count':x['unit_count'],'min_interval':x['min_interval'],'max_interval':x['max_interval'],'interval_count':x['interval_count'],'fields':x['fields']}
archives=['loucka_reconstruction','old_weewx','weewx_WH1080','pocasi-loucka.eu','pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old']
rows=[]
for db in archives:
 for year in years:
  item=by[(db,year)]
  for field in core:
   v=item['fields'][field]
   rows.append({'database':db,'year_utc':year,'archive_rows':item['archive_rows'],'variable':field,'nonnull_rows':v['nonnull'],'null_rows':v['null'],'null_share':v['null']/item['archive_rows'] if item['archive_rows'] else None,'first_epoch':item.get('first_epoch'),'last_epoch':item.get('last_epoch'),'min_units':item.get('min_units'),'max_units':item.get('max_units'),'unit_count':item.get('unit_count'),'min_interval':item.get('min_interval'),'max_interval':item.get('max_interval'),'interval_count':item.get('interval_count')})
with (ROOT/'reports/2026-11-13-six-archive-core-field-availability-2009-2020.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Pairwise availability count comparisons (not equality of measurements).
pairs=[('pocasi-loucka.eu','pocasi-loucka.eu_GW1000'),('old_weewx','weewx_WH1080'),('loucka_reconstruction','pocasi-loucka.eu'),('loucka_reconstruction','pocasi-loucka.eu_old')]
comparisons=[]
for a,b in pairs:
 same=[];different=[]
 for year in years:
  for field in core:
   na=by[(a,year)]['fields'][field]['nonnull'];nb=by[(b,year)]['fields'][field]['nonnull']
   row={'year_utc':year,'variable':field,'a_nonnull':na,'b_nonnull':nb,'difference_b_minus_a':nb-na}
   (same if na==nb else different).append(row)
 comparisons.append({'archive_a':a,'archive_b':b,'field_year_cells':len(years)*len(core),'equal_nonnull_counts':len(same),'different_nonnull_counts':len(different),'row_count_equal_years':sum(by[(a,y)]['archive_rows']==by[(b,y)]['archive_rows'] for y in years),'difference_examples':different})
summary={'schema':'six-archive-core-availability-v1','as_of':'2026-11-13','years_utc':years,'fields':core,'field_year_cells_per_archive':len(years)*len(core),'archive_count':len(archives),'cell_count':len(rows),'archive_rows_by_year':{db:{str(y):by[(db,y)]['archive_rows'] for y in years} for db in archives},'pairwise_nonnull_count_comparisons':comparisons,'interpretation':'Presence/non-NULL availability only. Equal counts do not mean same timestamps or equal values. Differences do not identify which archive is correct. Source archives may share lineage and prior cleaning.','scope_limitations':['11 primary/core fields only; not all channel-specific fields.','2009–2020 UTC only; Q1 2018 descriptive diagnostic, no new proposal; year 2021 excluded.','Three dotted production databases were queried via fully-qualified quoted schema references from the allowed loucka_reconstruction database context.','Rows in newer merged/production databases are not independent evidence of original measurements.','No database writes, staging, corrections or tail refresh.']}
(ROOT/'data/six_archive_core_availability_2009_2020.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
# SQL used for the three previously blocked schemas, one bounded year per SELECT.
for db in merged['databases']:
 sql=[]
 for y in years:
  lo=int(datetime(y,1,1,tzinfo=timezone.utc).timestamp());hi=int(datetime(y+1,1,1,tzinfo=timezone.utc).timestamp())
  mets=', '.join(f'COUNT(`{f}`) AS `nonnull_{f}`' for f in core)
  sql += [f'-- READ-ONLY; execute with Weather MCP database_name=loucka_reconstruction; fixed UTC year {y}.',f'SELECT COUNT(*) AS archive_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch, MIN(usUnits) AS min_units, MAX(usUnits) AS max_units, COUNT(DISTINCT usUnits) AS unit_count, MIN(`interval`) AS min_interval, MAX(`interval`) AS max_interval, COUNT(DISTINCT `interval`) AS interval_count, {mets}',f'FROM `{db}`.archive WHERE dateTime >= {lo} AND dateTime < {hi};','']
 (ROOT/'sql/readonly'/f'annual_core_availability_{db}_2009_2020.sql').write_text('\n'.join(sql))
md=['# Six-archive core-field availability — 2009–2020 UTC','','The six archive snapshots were compared for 11 primary fields across 12 UTC years (792 availability cells). The five historical/source/production archives are not independent measurements; table shows row/field availability only.','','| Archive | Rows 2009–2020 |','|---|---:|']
for db in archives:md.append(f"| `{db}` | {sum(by[(db,y)]['archive_rows'] for y in years):,} |")
md+=['','## Pairwise availability comparison','','| Pair | Equal non-NULL counts | Different counts | Scope |','|---|---:|---:|---:|']
for c in comparisons:md.append(f"| `{c['archive_a']}` vs `{c['archive_b']}` | {c['equal_nonnull_counts']} | {c['different_nonnull_counts']} | {c['field_year_cells']} field/year cells |")

md += ['', '## Dva novější archivy: počet řádků vs availability', '', '| Rok | pocasi-loucka.eu rows | GW1000 rows | row counts |', '|---:|---:|---:|---|']
for y in years: md.append(f"| {y} | {by[('pocasi-loucka.eu',y)]['archive_rows']} | {by[('pocasi-loucka.eu_GW1000',y)]['archive_rows']} | {'equal' if by[('pocasi-loucka.eu',y)]['archive_rows']==by[('pocasi-loucka.eu_GW1000',y)]['archive_rows'] else 'different'} |")
fielddiff=defaultdict(int)
for y in years:
 for field in core:
  if by[('pocasi-loucka.eu',y)]['fields'][field]['nonnull']!=by[('pocasi-loucka.eu_GW1000',y)]['fields'][field]['nonnull']: fielddiff[field]+=1
md += ['', 'Non-NULL count differences by field for this pair:', '', '| Field | Different year cells (of 12) |', '|---|---:|']
for field,n in sorted(fielddiff.items(),key=lambda kv:(-kv[1],kv[0])): md.append(f'| `{field}` | {n} |')
md.extend(["", "The equality figures compare **counts only**, not exact keys or values. The historical shared-database-base assertion for the two newer databases needs row-key/value concordance; this report is only one bounded availability check. Likewise, a source count or non-NULL value cannot establish quality or provenance.", "", "Machine-readable output: `data/six_archive_core_availability_2009_2020.json`; all per-archive cells: `reports/2026-11-13-six-archive-core-field-availability-2009-2020.csv`. Source SQL for three schemas is in `sql/readonly/annual_core_availability_*_2009_2020.sql`. For old_weewx and WH1080 use `sql/readonly/annual_source_field_availability_*_2009_2020.sql`; reconstruction uses `reports/2026-11-13-annual-archive-field-availability-2009-2026.json`.", "", "This does not resolve the owner-attested merge/cleaning rules or permit restoration. 2021 was excluded; Q1 2018 is descriptive only. No DB writes, staging, application or archive-tail refresh."])
(ROOT/'reports/2026-11-13-six-archive-core-field-availability-2009-2020.md').write_text('\n'.join(md)+'\n')
print('cells',len(rows),'archive row totals',{db:sum(by[(db,y)]['archive_rows'] for y in years) for db in archives})
print('comparisons',[(x['archive_a'],x['archive_b'],x['equal_nonnull_counts'],x['different_nonnull_counts']) for x in comparisons])
