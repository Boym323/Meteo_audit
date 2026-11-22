#!/usr/bin/env python3
import json
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'data/rh_p2_2014_rare_value_review.json'
d=json.loads(p.read_text())
assert d['schema']=='rh_p2_2014_rare_value_review_v1'
assert d['candidate_count']==12 and len(d['rows'])==12
assert d['disposition']=='all 12 REVIEW_REQUIRED; no proposal'
assert d['query_execution_utc']=='NOT_CAPTURED_BY_WEATHER_MCP'
assert d['database_writes']==0 and d['staging'] is False and d['application']=='NOT_APPLIED'
assert d['mcp_dry_run']=='NOT_RUN'
expected={1400943900,1400944200,1400944500,1400944800,1400945100,1400945400,1401643800,1406126100,1406126400,1406126700,1406130900,1406133600}
assert {r['ts'] for r in d['rows']}==expected
for r in d['rows']:
    assert r['r_RH'] is None and r['rh_events']==0
    assert r['r_units']==16 and r['r_interval']==5
    assert r['old_RH']==r['wh_RH']==r['eo_RH']
    assert r['old_interval']==r['wh_interval']==r['eo_interval']==5
    assert r['old_units']==r['wh_units']==17 and r['eo_units']==16
s=d['context_summary']
assert s['43']['targets']==6 and s['97']['targets']==3
assert s['60']['source_rows_in_±30m']==16 and s['30']['source_rows_in_±30m']==22
assert 'apparent wind/gust inconsistency' in s['97']['issue']
print('PASS: 12 exact-target RH candidates verified; all held REVIEW_REQUIRED; no proposal.')
