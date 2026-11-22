#!/usr/bin/env python3
"""Aggregate saved read-only gap-slot source availability query results."""
from __future__ import annotations
import csv, hashlib, json, re
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
query_index=json.loads((R/'data/p1p2_source_gap_overlay_summary.json').read_text())
fields=query_index['fields']; grouped=defaultdict(lambda:{'rows':0,'targets':0,'gaps':0,'nn':defaultdict(int)})
result_files=sorted((R/'data').glob('p1p2_source_gap_overlay_results_*.json'))
for p in result_files:
 m=re.search(r'results_(\d{4})_(\d{3})\.json$',p.name)
 if not m: raise ValueError(f'unexpected result filename: {p.name}')
 data=json.loads(p.read_text())
 if 'error_code' in data: raise ValueError(f'query result error: {p.name}: {data}')
 for row in data.get('result',[]):
  k=(int(m.group(1)),row['source_database'],row['gap_band'],row['protection_scope'])
  a=grouped[k];a['rows']+=int(row['source_archive_rows']);a['targets']+=int(row['unique_target_timestamps']);a['gaps']+=int(row['gaps_with_source'])
  for f in fields:a['nn'][f]+=int(row[f'{f}_nonnull'])
rows=[]
for (year,db,band,scope),a in sorted(grouped.items()):
 r={'year':year,'source_database':db,'gap_band':band,'protection_scope':scope,'source_archive_rows':a['rows'],'target_timestamps':a['targets'],'gaps_with_source':a['gaps']}
 r.update({f'{f}_nonnull':a['nn'][f] for f in fields});rows.append(r)
csv_path=R/'reports/2026-11-13-source-gap-overlay-availability.csv'
with csv_path.open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
expected=sum(y['candidate_slots'] for y in query_index['years'].values())
db_rows=defaultdict(int);db_targets=defaultdict(int);scopes=defaultdict(int);field_totals=defaultdict(int);year_rows=defaultdict(int);band_rows=defaultdict(int);band_gaps=defaultdict(int)
for r in rows:
 db_rows[r['source_database']]+=r['source_archive_rows'];db_targets[r['source_database']]+=r['target_timestamps'];scopes[r['protection_scope']]+=r['source_archive_rows'];year_rows[r['year']]+=r['source_archive_rows']
 band_rows[(r['source_database'],r['gap_band'],r['protection_scope'])]+=r['source_archive_rows'];band_gaps[(r['source_database'],r['gap_band'],r['protection_scope'])]+=r['gaps_with_source']
 for f in fields:field_totals[(r['source_database'],f)]+=r[f'{f}_nonnull']
source={'snapshot':'2026-11-12 reconstruction gap-event catalog; read-only Weather MCP exact-time source checks, results saved 2026-11-13','query_chunks':len(query_index['query_chunks']),'candidate_slots':expected,'gap_events':sum(v['gap_events'] for v in query_index['years'].values()),'source_archives':query_index['source_archives'],'archive_source_rows':dict(sorted(db_rows.items())),'source_target_timestamps_sum_per_archive':dict(sorted(db_targets.items())),'rows_by_protection_scope':dict(sorted(scopes.items())),'rows_by_year':dict(sorted(year_rows.items())),'nonnull_by_archive_and_field':{db:{f:field_totals[(db,f)] for f in fields} for db in sorted(db_rows)},'group_rows':len(rows),'interpretation':'Candidate slots are conditional interior points on 300-second grid between reconstruction records. They do not establish expected cadence or truth. Counts are per archive; matching historical archive copies are not independent observations. Q1 2018 is diagnostic only; no 2021 query targets were generated. No correction or write occurred.'}
(R/'data/p1p2_source_gap_overlay_aggregate.json').write_text(json.dumps({'summary':source,'rows':rows},ensure_ascii=False,indent=2)+'\n')
md=['# Source-only archive availability inside reconstruction gaps (2009–2020)','',f"Snapshot: {source['snapshot']}.",'','## Scope and interpretation','',f"The deterministic screen included {source['candidate_slots']:,} conditional 5-minute interior slots across {source['gap_events']:,} eligible gap events. Only interval pairs marked as exceeding both adjacent archive intervals, with a delta divisible by 300 seconds, were used. This is a search frame, not a claim that every slot was expected.",'','All six available archives were queried by exact timestamp. The reconstruction archive was anti-joined at query time. The query returns aggregate presence and per-field non-null counts only. Duplicate source archive copies are counted per database and are not treated as independent measurements. A source hit opens review; it does not authorize restoration. Q1 2018 is explicitly diagnostic/protected. 2021 was excluded.', '', '## Results by source archive','', '| Archive | Source rows | Candidate timestamps (per archive) |','|---|---:|---:|']
for db in sorted(db_rows):md.append(f"| `{db}` | {db_rows[db]:,} | {db_targets[db]:,} |")
md += ['', '## Result by year', '', '| UTC year | Source archive rows (sum across archives) |','|---:|---:|']
for y,n in sorted(year_rows.items()):md.append(f'| {y} | {n:,} |')
md += ['', '## Source availability by gap duration and protected scope', '', '| Archive | Band | Scope | Source rows | Gaps with at least one row (summed per chunk) |','|---|---|---|---:|---:|']
for (db,band,scope),n in sorted(band_rows.items()):md.append(f'| `{db}` | `{band}` | `{scope}` | {n:,} | {band_gaps[(db,band,scope)]:,} |')
md += ['', '## What the result does and does not support','',f"The two long-lived historical archives account for {db_targets.get('old_weewx',0):,} and {db_targets.get('weewx_WH1080',0):,} source rows respectively across conditional slots. These are mostly source-copy candidates and must be reviewed against lineage, units, sensor epoch, timestamps, history, sentinels, neighboring values, and plausibility before any RESTORED classification. Field-level non-null counts are in `data/p1p2_source_gap_overlay_aggregate.json`; grouped export is `reports/2026-11-13-source-gap-overlay-availability.csv`.",'','No candidate was promoted to RESTORED or ESTIMATED by this availability-only screen. It does not modify or supersede the P3 v1/v2 packages. P3 v2 treatment remains in its independent-review report. Short and long gaps require event-level assessment; source rows inside long gaps cannot imply continuous completeness.','', '## Reproduction and validation','', 'Regenerate bounded SQL from the frozen gap-event catalog using `python3 scripts/build_gap_slot_source_availability.py`; execute each `sql/readonly/gap_slot_source_availability/chunks/*.sql` through the READ-ONLY Weather MCP connection to `loucka_reconstruction`, save each aggregate result under the matching `data/p1p2_source_gap_overlay_results_YYYY_NNN.json`, then run `python3 scripts/build_gap_slot_source_availability_report.py` and `python3 scripts/validate_gap_slot_source_availability.py`. The result JSONs are aggregate-only; local source rows were not exported. SQL digests and exact target-generation rules are in `data/p1p2_source_gap_overlay_summary.json`.','']
md += ['', '### Non-null field counts in source rows','', 'Counts below are exact field non-null counts within the matched source archive rows (not quality approvals). The two archive copies are dependent and row counts may overlap.', '', '| Field | old_weewx | weewx_WH1080 |','|---|---:|---:|']
for f in ['outTemp','outHumidity','rain','rainRate','barometer','pressure','altimeter','windSpeed','windDir','windGust','windGustDir','dewpoint','windchill','heatindex']:
 md.append(f"| `{f}` | {field_totals[('old_weewx',f)]:,} | {field_totals[('weewx_WH1080',f)]:,} |")
md += ['', 'These counts show why a source archive row cannot be assumed to restore every variable: for example, many matched `old_weewx` rows have NULL `outTemp`, while other primary fields are populated. A row-level candidate package would require timestamp-specific values and lineage validation.','']
(R/'reports/SOURCE_ONLY_GAP_OVERLAY_2009_2020.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'candidate_slots':expected,'query_chunks':len(query_index['query_chunks']),'aggregate_rows':len(rows),'archive_source_rows':dict(db_rows),'csv_sha256':hashlib.sha256(csv_path.read_bytes()).hexdigest()},indent=2))
