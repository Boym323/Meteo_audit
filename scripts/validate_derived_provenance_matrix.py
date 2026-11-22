#!/usr/bin/env python3
"""Validate field coverage and epistemic labels in the derived provenance matrix."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/derived_variable_historical_provenance_matrix.json').read_text())
a=d['rows']; schema=list(csv.DictReader((R/'reports/2026-11-13-derived-variable-schema-map.csv').open()))
assert len(a)==21 and len({x['variable'] for x in a})==21
assert {x['variable'] for x in a}=={x['variable'] for x in schema}
assert all(x['historical_loucka_formula']=='UNVERIFIED' for x in a)
assert all(x['historical_producer_version_config_epoch']=='UNVERIFIED' for x in a)
assert all(x['hardware_vs_software_preference']=='UNVERIFIED' for x in a)
assert all(x['recalculation_disposition'].startswith('DO_NOT_RECALCULATE') for x in a)
assert sum(x['current_documented_producer_class'].startswith('StdWXCalculate') for x in a)==11
assert len(list(csv.DictReader((R/'reports/2026-11-13-derived-variable-historical-provenance-matrix.csv').open())))==21
print('PASS: all 21 schema fields have current-reference status, local evidence, and explicit unverified historical provenance/recalculation gate.')
