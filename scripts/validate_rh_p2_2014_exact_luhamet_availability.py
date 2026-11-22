#!/usr/bin/env python3
import json
from pathlib import Path
d=json.loads((Path(__file__).resolve().parents[1]/'data/rh_p2_2014_exact_luhamet_availability.json').read_text())
assert sum(x['candidate_rows'] for x in d['by_source_rh'])==1236
assert sum(x['exact_luhamet_rh'] for x in d['by_source_rh'])==0
assert sum(x['source_temp_present'] for x in d['by_source_rh'])==1236
assert d['summary']['regional_rh_comparison_possible'] is False
assert 'No nearest-time substitution' in d['interpretation']
print('PASS: 1,236 candidates, zero exact LuhaMet RH values; no nearest-time fallback or additional proposal.')
