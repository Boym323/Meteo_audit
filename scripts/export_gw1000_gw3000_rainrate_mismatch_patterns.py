#!/usr/bin/env python3
"""Emit a flat CSV from the saved exact-pair aggregate (no database access)."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/gw1000_gw3000_rainrate_mismatch_patterns_2009_2020.json').read_text())
p=R/'reports/2026-11-14-gw1000-gw3000-rainrate-patterns.csv'
with p.open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(d['rows'][0]));w.writeheader();w.writerows(d['rows'])
print(f'Wrote {len(d["rows"])} grouped rows to {p}')
