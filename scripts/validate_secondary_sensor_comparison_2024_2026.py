#!/usr/bin/env python3
"""Validate three-year availability patterns and cautious scope summary."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'reports'
rows=list(csv.DictReader((R/'2026-11-13-secondary-sensor-availability-2024-2026.csv').open(newline='',encoding='utf-8')))
d=json.loads((R/'2026-11-13-secondary-sensor-availability-2024-2026.json').read_text(encoding='utf-8'))
assert len(rows)==42 and d['variables']==42
assert d['archive_rows']=={'2024':104935,'2025':102946,'2026':86877}
assert len(d['all_null_fields']['2024'])==11 and d['all_null_fields']['2024']==d['all_null_fields']['2025']
assert d['all_null_fields']['2026']==['lightning_energy']
assert len(d['newly_available_only_2026'])==10 and not d['newly_available_only_2025'] and not d['disappeared_in_2026']
assert all(x['availability_pattern']=='001' for x in rows if x['variable'] in d['newly_available_only_2026'])
md=(R/'2026-11-13-secondary-sensor-availability-2024-2026.md').read_text(encoding='utf-8')
assert 'nikoli datem instalace' in md.lower()
print('PASS: three-year availability matrix; ten 2026-only archive-onset fields')
