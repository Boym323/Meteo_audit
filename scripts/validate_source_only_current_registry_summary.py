#!/usr/bin/env python3
"""Check current source-only proposal counts against the active registry."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
reg=json.loads((ROOT/'config/active_proposal_registry.json').read_text())
ids={'restored-source-only-2013-july-pilot','restored-source-only-2019-may30-outtemp','restored-source-only-2020-isolated-outtemp'}
pkgs=[p for p in reg['packages'] if p['package_id'] in ids]
assert len(pkgs)==3 and all(p['status']=='ACTIVE' and p['classification']=='RESTORED' for p in pkgs)
operations=sum(p['field_operations'] for p in pkgs)
target_timestamps=sum(p['unique_timestamps'] for p in pkgs)
assert operations==35 and target_timestamps==32
assert [(p['package_id'],p['field_operations'],p['unique_timestamps']) for p in pkgs]==[
 ('restored-source-only-2013-july-pilot',7,4),
 ('restored-source-only-2019-may30-outtemp',1,1),
 ('restored-source-only-2020-isolated-outtemp',27,27)]
source_only_timestamps=target_timestamps-1 # 2013 includes one pre-existing NULL target
population=207182
outside=population-source_only_timestamps
assert source_only_timestamps==31 and outside==207151
doc=(ROOT/'SOURCE_ONLY_RESTORATION_ELIGIBILITY.md').read_text()
consolidated=(ROOT/'reports/CONSOLIDATED_CORRECTIONS_REPORT.md').read_text()
plan=(ROOT/'MASTER_PLAN.md').read_text()
assert '35 field operations' in doc and '31 unikátních source-only timestampů' in doc
assert '207 151' in doc and '27 `RESTORED`' in doc
assert '8 RESTORED field operations across 5 target timestamps' in consolidated and '35 source-only RESTORED operations' in consolidated
assert 'superseded' in consolidated.lower()
assert '27 remain active `RESTORED` inserts and two are held `REVIEW_REQUIRED`' in consolidated
assert '52 physical inserts and 13 update operations across 7 packages' in consolidated
assert '29 exact-grid outTemp-only `RESTORED` proposals are in' not in consolidated
assert '35 RESTORED operacemi přes 31 unikátních source-only timestampů' in plan
for text in (doc,consolidated):
    assert 'The other 29 exact-grid values' not in text
print(json.dumps({'status':'PASS','source_only_operations':operations,'source_only_timestamp_targets':source_only_timestamps,'other_target_inserts_or_updates':1,'outside_source_only_proposals':outside,'packages':len(pkgs)}))
