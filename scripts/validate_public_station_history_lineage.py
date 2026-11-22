#!/usr/bin/env python3
"""Deterministic integrity checks for bounded public station-lineage evidence."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'data/source-lineage/public_station_history_20261113.json'
d=json.loads(p.read_text())
assert len(d['evidence']) == 3
assert '2009-03-29' in d['evidence'][0]['claims'][0]
assert '2022-08-20' in d['evidence'][0]['claims'][1]
assert 'Watson-8681' in d['evidence'][1]['claims'][0]
assert 'Cumulus v1.8.7' in d['evidence'][1]['claims'][0]
assert 'WeeWX 5.5.2' in d['evidence'][2]['claims'][0]
assert 'does not prove' in d['decision']
assert all(x['limitation'] for x in d['evidence'])
assert not json.loads((ROOT/'proposals/restored_temperature/corrections.json').read_text())
assert not json.loads((ROOT/'proposals/restored_humidity/corrections.json').read_text())
assert not json.loads((ROOT/'proposals/restored_secondary_sensors/corrections.json').read_text())
print('PASS: station-level hardware history is bounded; archival lineage limitations explicit; no unsupported RESTORED rows')
