#!/usr/bin/env python3
import csv,json,datetime
from datetime import timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/b5_2018_gap_source_concordance.json').read_text());rows=d['records'];fs=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','pressure','barometer','altimeter']
assert len(rows)==63 and sum(r['source_union_timestamps'] for r in rows)==4717
assert all(datetime.datetime.fromtimestamp(r['left_time'],timezone.utc).year==2018 and datetime.datetime.fromtimestamp(r['left_time'],timezone.utc).month<=3 for r in rows)
fields={f:{k:sum(r['fields'][f][k] for r in rows) for k in ['paired_nonnull','equal','conflict','null_asymmetry']} for f in fs}
assert fields['rainRate']['equal']==4717 and fields['pressure']['equal']==4717
assert fields['altimeter']['conflict']==4717 and fields['outTemp']['paired_nonnull']==0
prev=json.loads((R/'data/b5_2018_per_gap_availability.json').read_text())
zero=sum(x['per_archive']['wh1080']['outTemp_zero'] for x in prev['records'])
assert zero==4717
summary={'schema':'b5-2018-gap-source-concordance-summary-v1','processed_at_utc':datetime.datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'query_execution_timestamp_utc':'NOT_CAPTURED_BY_WEATHER_MCP','gap_events':63,'protected_q1_events':63,'source_union_timestamps':4717,'exact_timestamp_pairs':4717,'old_only_timestamps':0,'wh1080_only_timestamps':0,'unit_interval_conflicts':0,'field_concordance':fields,'wh1080_outTemp_zero_rows':zero,'old_weewx_outTemp_null_rows':4717,'decision':'DIAGNOSTIC_ONLY_Q1_2018_PROTECTED; no proposals','database_mode':'READ_ONLY SELECT','writes':0}
(R/'data/b5_2018_gap_source_concordance_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-14-B5-2018-gap-source-concordance.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['field','paired_nonnull','equal','conflict','null_asymmetry']);[w.writerow([field,*[fields[field][k] for k in ['paired_nonnull','equal','conflict','null_asymmetry']]]) for field in fs]
lines=['# B5 — Q1 2018 gap-interior source-copy concordance','',f"Processed UTC: {summary['processed_at_utc']}. The query tool did not supply its execution timestamp; it remains uncaptured. Query: sql/readonly/b5_2018_gap_source_concordance.sql.",'','## Scope and exact-key result','', 'All 63 frozen 1h-to-under-24h gap events are in protected Q1 2018. The old_weewx and WH1080 interiors contain 4,717 rows each, matching on all 4,717 exact timestamp keys. There are no one-sided keys and no unit/interval mismatch. This converts the earlier equal per-gap row-count observation into an exact timestamp-key comparison.','', '## Field-level summary','']
for f,x in fields.items():lines.append(f"- {f}: paired non-NULL {x['paired_nonnull']:,}; equal {x['equal']:,}; conflicts {x['conflict']:,}; NULL asymmetry {x['null_asymmetry']:,}.")
lines+=['', 'WH1080 has zero outTemp at all 4,717 timestamps; old_weewx has outTemp NULL at all 4,717. Rain, rainRate and pressure match exactly in both copies; altimeter conflicts at all 4,717 pairs. Other fields show matching NULL status or broad availability asymmetry. These are archive-copy facts only; neither source independence nor historical removal intent is established.', '', '## Safety and eligibility','', 'Q1 2018 remains protected by the parallel reconstruction. This is a bounded diagnostic review only: no correction proposal, timestamp shift, insertion, staging or application was created. The exact copy concordance does not override the protection or prove meteorological truth.', '', 'Machine-readable per-gap details: data/b5_2018_gap_source_concordance.json; summary: data/b5_2018_gap_source_concordance_summary.json; CSV above. SQL builder: scripts/build_b5_2018_gap_source_concordance_sql.py; validator: scripts/validate_b5_2018_gap_source_concordance.py.']
(R/'reports/2026-11-14-B5-2018-gap-source-concordance.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status':'PASS','gap_events':63,'q1_events':63,'rows':4717,'zero_temp_wh1080':zero,'outTemp_paired_nonnull':fields['outTemp']['paired_nonnull'],'rainRate_equal':fields['rainRate']['equal'],'pressure_equal':fields['pressure']['equal'],'altimeter_conflict':fields['altimeter']['conflict']},indent=2))
