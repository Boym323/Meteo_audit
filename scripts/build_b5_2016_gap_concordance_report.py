#!/usr/bin/env python3
import csv,json
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/b5_2016_gap_source_concordance.json').read_text())
rows=d['records']; assert len(rows)==135
fields=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','pressure','barometer','altimeter']
def total(key):return sum(int(r[key]) for r in rows)
agg={f:{k:sum(int(r['fields'][f][k]) for r in rows) for k in ['paired_nonnull','equal','conflict','null_asymmetry']} for f in fields}
assert total('source_union_timestamps')==5381 and total('exact_timestamp_pairs')==5381
assert total('old_only_timestamps')==0 and total('wh1080_only_timestamps')==0
assert total('unit_interval_conflicts')==0
assert agg['rainRate']['paired_nonnull']==agg['rainRate']['equal']==5381
assert agg['pressure']['paired_nonnull']==agg['pressure']['equal']==5381
assert agg['altimeter']['paired_nonnull']==5381 and agg['altimeter']['conflict']==5300 and agg['altimeter']['equal']==81
assert agg['outTemp']['paired_nonnull']==70 and agg['outTemp']['equal']==70
summary={'schema':'b5-2016-gap-source-concordance-summary-v1','processed_at_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'query_execution_timestamp_utc':'NOT_CAPTURED_BY_WEATHER_MCP','gap_events':135,'source_union_timestamps':5381,'exact_timestamp_pairs':5381,'old_only_timestamps':0,'wh1080_only_timestamps':0,'unit_interval_conflicts':0,'field_concordance':agg,'wh1080_outTemp_zero_rows':5313,'decision':'SOURCE_AVAILABILITY_AND_COPY_CONCORDANCE_ONLY; no correction proposal','limitations':d['limitations'],'database_access':'READ_ONLY SELECT only','writes':0}
(R/'data/b5_2016_gap_source_concordance_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-14-B5-2016-gap-source-concordance.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['field','paired_nonnull','equal','conflict','null_asymmetry']);[w.writerow([field,*[agg[field][k] for k in ['paired_nonnull','equal','conflict','null_asymmetry']]]) for field in fields]
lines=['# B5 — 2016 per-gap source-copy concordance','',f"**Processed:** `{summary['processed_at_utc']}`. The Weather MCP tool did not expose an execution timestamp, so `query_execution_timestamp_utc` remains explicitly uncaptured. Query: `sql/readonly/b5_2016_gap_source_concordance.sql`; live database access was SELECT-only.",'','## Scope and exact-key result','','The frozen catalog contains 135 target gaps from 1 hour to under 24 hours. Across their interiors, `old_weewx` and `weewx_WH1080` have 5,381 timestamp keys each; all 5,381 match exactly. There are no one-sided timestamp keys and no unit/interval conflicts. This strengthens the prior equal-per-gap-count check with exact key matching.','', '## Field concordance','']
for f in fields:
 x=agg[f]; lines.append(f"- `{f}`: {x['paired_nonnull']:,} paired non-NULL; {x['equal']:,} equal; {x['conflict']:,} conflicts; {x['null_asymmetry']:,} NULL-asymmetric timestamp pairs.")
lines += ['', 'The exact agreement is concentrated in several fields but does not make the old archives independent measurements. In particular, outTemp is non-NULL in both copies at only 70 timestamps (all equal); the remainder is NULL-asymmetric, while prior availability evidence found 5,313 WH1080 zero temperatures. Rain and rainRate largely match across copies; rain semantics remain unresolved. Pressure is exactly equal in all pairs, while altimeter conflicts in 5,300 of 5,381 non-NULL pairs. Wind channels are sparse in old_weewx and often present only in WH1080.', '', '## Eligibility decision','', 'No RESTORED or ESTIMATED proposal is created. Exact timestamp/value concordance does not establish source identity, physical sensor independence, migration selection rules, or whether records were intentionally removed. Potential wind transformations and rain semantics remain separate gates. The source rows only establish availability and field-specific copy patterns. No restoration is proposed in this review under the available source evidence; the Q1 2018 and 2021 safety policies remain unchanged.', '', 'Per-gap machine-readable results: `data/b5_2016_gap_source_concordance.json`; summary: `data/b5_2016_gap_source_concordance_summary.json`; reproduction SQL: `sql/readonly/b5_2016_gap_source_concordance.sql`. Validator: `scripts/validate_b5_2016_gap_source_concordance.py`.']
(R/'reports/2026-11-14-B5-2016-gap-source-concordance.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status':'PASS','summary':summary},indent=2))
