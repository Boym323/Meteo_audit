#!/usr/bin/env python3
import csv,json
from datetime import datetime,timezone
import datetime as dt
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/b5_2014_2015_gap_source_concordance.json').read_text())
rows=d['records'];
for item in rows:item['year_utc']=dt.datetime.fromtimestamp(item['left_time'],dt.timezone.utc).year
(R/'data/b5_2014_2015_gap_source_concordance.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
fields=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','pressure','barometer','altimeter']
assert len(rows)==65 and sum(x['source_union_timestamps'] for x in rows)==1844
for x in rows: assert x['year_utc'] in (2014,2015)
def aggregate(group):
 return {'gap_events':len(group),'source_union_timestamps':sum(x['source_union_timestamps'] for x in group),'paired_timestamps':sum(x['exact_timestamp_pairs'] for x in group),'old_only':sum(x['old_only_timestamps'] for x in group),'wh1080_only':sum(x['wh1080_only_timestamps'] for x in group),'unit_interval_conflicts':sum(x['unit_interval_conflicts'] for x in group),'fields':{f:{k:sum(x['fields'][f][k] for x in group) for k in ['paired_nonnull','equal','conflict','null_asymmetry']} for f in fields}}
by_year={str(y):aggregate([x for x in rows if x['year_utc']==y]) for y in (2014,2015)}
allagg=aggregate(rows)
assert by_year['2014']['gap_events']==36 and by_year['2014']['source_union_timestamps']==794
assert by_year['2015']['gap_events']==29 and by_year['2015']['source_union_timestamps']==1050
assert allagg['paired_timestamps']==1844 and allagg['old_only']==allagg['wh1080_only']==allagg['unit_interval_conflicts']==0
assert allagg['fields']['altimeter']['conflict']==1704 and allagg['fields']['rainRate']['equal']==1843
summary={'schema':'b5-2014-2015-gap-source-concordance-summary-v1','processed_at_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'query_execution_timestamp_utc':'NOT_CAPTURED_BY_WEATHER_MCP','scope':'65 gaps under 24h; excludes one >=24h event; all row counts from exact source joins','by_year':by_year,'combined':allagg,'decision':'SOURCE_AVAILABILITY_AND_COPY_CONCORDANCE_ONLY; no correction proposal','database_mode':'READ_ONLY SELECT','writes':0,'limitations':d['limitations']}
(R/'data/b5_2014_2015_gap_source_concordance_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-14-B5-2014-2015-gap-source-concordance.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['year_utc','field','paired_nonnull','equal','conflict','null_asymmetry'])
 for y,agg in by_year.items():
  for field,x in agg['fields'].items():w.writerow([y,field,x['paired_nonnull'],x['equal'],x['conflict'],x['null_asymmetry']])
lines=['# B5 — 2014–2015 exact gap-interior source concordance','',f"Processed UTC: {summary['processed_at_utc']}. The MCP query execution time was not returned by the tool and remains uncaptured. Query: sql/readonly/b5_2014_2015_gap_source_concordance.sql.",'','## Scope and exact row-key result','', 'The screen covers the 65 frozen target gaps shorter than 24 hours; the single >=24-hour overlap in the 66-event inventory is excluded. Across 1,844 source timestamp rows, old_weewx and WH1080 have exactly matching keys, with no one-sided timestamps and no usUnits/interval conflicts. UTC split: 2014 has 36 gaps/794 rows; 2015 has 29 gaps/1,050 rows.','', '## Combined field results','']
for f,x in allagg['fields'].items():lines.append(f"- {f}: paired non-NULL {x['paired_nonnull']:,}; equal {x['equal']:,}; conflicts {x['conflict']:,}; NULL asymmetry {x['null_asymmetry']:,}.")
lines += ['', 'No both-non-NULL value conflicts were found for these ten fields, but altimeter disagrees at 1,704/1,720 paired non-NULL rows. Agreement in two archive copies does not make them independent measurements or prove that omitted merged rows were intended to be retained. Per-field availability is incomplete: outTemp matches at only 139 rows, RH at 19, and most wind values are NULL-asymmetric. Rain/rainRate semantics remain subject to E4.', '', '## Eligibility','', 'No RESTORED or ESTIMATED proposal is emitted. The exact source lineage and prior cleaning/merging rules remain unknown; no deletion cause or source quality is inferred. No source-only row is automatically approved.', '', 'Machine-readable per-gap values: data/b5_2014_2015_gap_source_concordance.json; year and combined summary: data/b5_2014_2015_gap_source_concordance_summary.json; CSV above. Reproduce query with scripts/build_b5_2014_2015_gap_source_concordance_sql.py and validate with scripts/validate_b5_2014_2015_gap_source_concordance.py.']
(R/'reports/2026-11-14-B5-2014-2015-gap-source-concordance.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status':'PASS','by_year':{k:{'gap_events':v['gap_events'],'rows':v['source_union_timestamps']} for k,v in by_year.items()},'combined':{k:allagg[k] for k in ['gap_events','source_union_timestamps','paired_timestamps','old_only','wh1080_only','unit_interval_conflicts']}},indent=2))
