#!/usr/bin/env python3
"""Aggregate frozen 2014 gap catalog and six read-only per-archive query outputs."""
import csv,json
from collections import Counter
from pathlib import Path

R=Path(__file__).resolve().parents[1]
catalog=R/'reports/2026-11-12-gap-event-catalog.csv'
query_data=json.loads((R/'data/b5_2014_gap_per_archive_availability.json').read_text())
archives=('reconstruction','eu','gw1000','eu_old','old_weewx','wh1080')
events=[]
with catalog.open(newline='',encoding='utf-8') as f:
 for row in csv.DictReader(f):
  if row['utc_year']=='2014' and int(row['delta_seconds'])>=3600:
   events.append({'gap_id':f"2014:{row['prev_ts']}:{row['target_ts']}",'left_time':int(row['prev_ts']),'right_time':int(row['target_ts']),'gap_seconds':int(row['delta_seconds'])})
assert len(events)==37
by_archive={a:{x['gap_id']:x for x in result['rows']} for a,result in ((x['archive'],x) for x in query_data['archives'])}
assert set(by_archive)==set(archives)
fields=('row_count','outTemp_nonnull','outTemp_zero','outHumidity_nonnull','rain_nonnull','rainRate_nonnull','windSpeed_nonnull','windGust_nonnull','windDir_nonnull','barometer_nonnull','distinct_usUnits','distinct_interval')
records=[]
for event in events:
 counts={}
 for archive in archives:
  item=by_archive[archive].get(event['gap_id'],{})
  counts[archive]={field:int(item.get(field,0) or 0) for field in fields}
 legacy_both=counts['old_weewx']['row_count']>0 and counts['wh1080']['row_count']>0
 if sum(v['row_count'] for v in counts.values())==0: state='NO_SOURCE_ROW_OBSERVED_IN_SIX_ARCHIVES'
 elif legacy_both and counts['old_weewx']['row_count']==counts['wh1080']['row_count']:
  state='LEGACY_COPIES_HAVE_ROWS_AND_EQUAL_COUNTS_ROW_LEVEL_MATCH_NOT_TESTED_HERE'
 elif counts['eu_old']['row_count'] and not legacy_both: state='EU_OLD_ONLY_OR_LEGACY_COUNT_CONFLICT_REVIEW'
 else: state='MIXED_SOURCE_AVAILABILITY_REVIEW'
 record={**event,'source_state':state,'per_archive':counts,
         'already_in_ge24h_review':event['gap_seconds']>=86400,
         'source_copy_identity_or_quality_proven':False}
 records.append(record)
by_archive_summary={a:{'gaps_with_rows':sum(x['per_archive'][a]['row_count']>0 for x in records),'rows':sum(x['per_archive'][a]['row_count'] for x in records),'outTemp_nonnull':sum(x['per_archive'][a]['outTemp_nonnull'] for x in records),'outTemp_zero':sum(x['per_archive'][a]['outTemp_zero'] for x in records),'outHumidity_nonnull':sum(x['per_archive'][a]['outHumidity_nonnull'] for x in records)} for a in archives}
state_counts=Counter(x['source_state'] for x in records)
new_scope=[x for x in records if not x['already_in_ge24h_review']]
data={'schema':'b5-2014-gap-per-archive-source-availability-v1','catalog':'reports/2026-11-12-gap-event-catalog.csv','range_utc_year':2014,
 'scope':'37 exact open gaps >=3600 seconds; 36 are <24h; one >=24h event overlaps the existing 44-long-gap review.',
 'source_query_execution_timestamp':'NOT_CAPTURED_BY_WEATHER_MCP','database_mode':'READ_ONLY_SELECT_ONLY','candidate_policy':'Exact open intervals (left_time < source.dateTime < right_time); presence does not prove expected measurement or cause.',
 'records':records,'state_counts':dict(state_counts),'new_subhour_or_1h_24h_scope_count':len(new_scope),'per_archive_summary':by_archive_summary,
 'source_row_sum_non_additive':True,'all_rows_restored_or_proposed':False,'correction_proposals':0,
 'limitations':['Counts include off-grid source timestamps and any source rows, not only conditional 300-second slots.','Equal counts in the two legacy archives are not proof of matching timestamps or independent measurement.','No source values, row-level concordance, historical cleaning cause, station downtime, or local meteorological truth is inferred from this availability report.','This is a bounded 2014 cohort and does not close B5 across all 24,523 gap events.','The >=24-hour event overlaps prior all-six long-gap evidence; do not add its rows to prior totals.']}
(R/'data/b5_2014_gap_per_archive_availability.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
csvpath=R/'reports/2026-11-14-B5-2014-per-gap-source-availability.csv'
with csvpath.open('w',newline='',encoding='utf-8') as f:
 cols=['gap_id','left_time','right_time','gap_seconds','source_state','already_in_ge24h_review']+[f'{a}_{field}' for a in archives for field in fields]
 w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
 for rec in records:
  row={k:rec[k] for k in ('gap_id','left_time','right_time','gap_seconds','source_state','already_in_ge24h_review')}
  for a in archives:
   for field in fields:row[f'{a}_{field}']=rec['per_archive'][a][field]
  w.writerow(row)
lines=['# B5: 2014 mezery ≥ 1 hodina — dostupnost zdrojových řádků po archivech','',
       '## Výsledek',
       f"READ-ONLY souhrn pokrývá {len(records)} mezer roku 2014 s trváním alespoň 3 600 s. Z toho {len(new_scope)} mezer je kratších než 24 hodin; jeden ≥24hodinový případ se překrývá s dřívější kompletní kontrolou 44 nejdelších mezer.",
       '', '| Archiv | Mezery s řádky | Řádků v otevřených intervalech | outTemp non-NULL | RH non-NULL |', '|---|---:|---:|---:|---:|']
for a in archives:
 x=by_archive_summary[a];lines.append(f"| `{a}` | {x['gaps_with_rows']} | {x['rows']} | {x['outTemp_nonnull']} | {x['outHumidity_nonnull']} |")
lines+=['',f"Per-gap states: `{json.dumps(dict(state_counts),ensure_ascii=False)}`.",
        'Source row counts include off-grid rows and are not counts of expected five-minute observations. Equal row counts in old_weewx and weewx_WH1080 do not establish timestamp equality, sensor independence, or measurement correctness. This query did not compare individual source values or determine why a row is absent from the reconstruction archive.',
        '', 'No correction proposal was created. All source availability states are evidence only; historical removal, stuck-sensor behavior, and source lineage remain unresolved. B5 remains IN_PROGRESS because the full 24,523-gap catalog is not source-cause classified.',
        '', 'Reproduction: the six one-archive SQL statements under `sql/readonly/b5_2014_gap_availability_*.sql`, then `python3 scripts/build_b5_2014_per_gap_report.py` and `python3 scripts/validate_b5_2014_per_gap_report.py`. Results are frozen in `data/b5_2014_gap_per_archive_availability.json`. Weather MCP does not expose query execution timestamps; no run time is fabricated.']
(R/'reports/2026-11-14-B5-2014-per-gap-source-availability.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'gaps':len(records),'new_under_24h':len(new_scope),'states':dict(state_counts),'archives':by_archive_summary},ensure_ascii=False,indent=2))
