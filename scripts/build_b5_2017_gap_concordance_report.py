#!/usr/bin/env python3
import csv,json
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/b5_2017_gap_source_concordance.json').read_text())
rows=d['records']; assert len(rows)==263
fields=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','pressure','barometer','altimeter']
def total(key):return sum(int(r[key]) for r in rows)
agg={f:{k:sum(int(r['fields'][f][k]) for r in rows) for k in ['paired_nonnull','equal','conflict','null_asymmetry']} for f in fields}
assert total('source_union_timestamps')==8359 and total('exact_timestamp_pairs')==8359
assert total('old_only_timestamps')==0 and total('wh1080_only_timestamps')==0
assert total('unit_interval_conflicts')==0
assert agg['rainRate']['paired_nonnull']==agg['rainRate']['equal']==8359
assert agg['pressure']['paired_nonnull']==agg['pressure']['equal']==8359
assert agg['altimeter']['paired_nonnull']==8359 and agg['altimeter']['conflict']==8277 and agg['altimeter']['equal']==82
assert agg['outTemp']['paired_nonnull']==45 and agg['outTemp']['equal']==45
summary={'schema':'b5-2017-gap-source-concordance-summary-v1','processed_at_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'query_execution_timestamp_utc':'NOT_CAPTURED_BY_WEATHER_MCP','gap_events':263,'source_union_timestamps':8359,'exact_timestamp_pairs':8359,'old_only_timestamps':0,'wh1080_only_timestamps':0,'unit_interval_conflicts':0,'field_concordance':agg,'wh1080_outTemp_zero_rows':sum(int(x['per_archive']['wh1080']['outTemp_zero']) for x in json.loads((R/'data/b5_2017_per_gap_availability.json').read_text())['records']),'decision':'SOURCE_AVAILABILITY_AND_COPY_CONCORDANCE_ONLY; no correction proposal','limitations':d['limitations'],'database_access':'READ_ONLY SELECT only','writes':0}
(R/'data/b5_2017_gap_source_concordance_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-14-B5-2017-gap-source-concordance.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['field','paired_nonnull','equal','conflict','null_asymmetry']);[w.writerow([field,*[agg[field][k] for k in ['paired_nonnull','equal','conflict','null_asymmetry']]]) for field in fields]
lines=['# B5 — 2017 per-gap source-copy concordance','',f"**Processed:** `{summary['processed_at_utc']}`. The Weather MCP tool did not expose an execution timestamp, so `query_execution_timestamp_utc` remains explicitly uncaptured. Query: `sql/readonly/b5_2017_gap_source_concordance.sql`; live database access was SELECT-only.",'','## Scope and exact-key result','','The frozen catalog contains 263 target gaps from 1 hour to under 24 hours. Across their interiors, `old_weewx` and `weewx_WH1080` have 8,359 timestamp keys each; all 8,359 match exactly. There are no one-sided timestamp keys and no unit/interval conflicts. This strengthens the prior equal-per-gap-count check with exact key matching.','', '## Field concordance','']
for f in fields:
 x=agg[f]; lines.append(f"- `{f}`: {x['paired_nonnull']:,} paired non-NULL; {x['equal']:,} equal; {x['conflict']:,} conflicts; {x['null_asymmetry']:,} NULL-asymmetric timestamp pairs.")
lines += ['', 'The exact agreement is concentrated in several fields but does not make the old archives independent measurements. In particular, outTemp is non-NULL in both copies at only 45 timestamps (all equal); the remainder is NULL-asymmetric, while per-gap availability records 8,316 WH1080 zero temperatures. Rain and rainRate largely match across copies; rain semantics remain unresolved. Pressure is exactly equal in all pairs, while altimeter conflicts in 8,277 of 8,359 non-NULL pairs. Wind channels are sparse in old_weewx and often present only in WH1080.', '', '## Eligibility decision','', 'No RESTORED or ESTIMATED proposal is created. Exact timestamp/value concordance does not establish source identity, physical sensor independence, migration selection rules, or whether records were intentionally removed. Potential wind transformations and rain semantics remain separate gates. The source rows only establish availability and field-specific copy patterns. No 2017 correction is proposed in this review; this does not classify 2017 as a protected year. The Q1 2018 protection and 2021 diagnostic-only policy remain unchanged.', '', 'Per-gap machine-readable results: `data/b5_2017_gap_source_concordance.json`; summary: `data/b5_2017_gap_source_concordance_summary.json`; reproduction SQL: `sql/readonly/b5_2017_gap_source_concordance.sql`. Validator: `scripts/validate_b5_2017_gap_source_concordance.py`.']
(R/'reports/2026-11-14-B5-2017-gap-source-concordance.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status':'PASS','summary':summary},indent=2))
