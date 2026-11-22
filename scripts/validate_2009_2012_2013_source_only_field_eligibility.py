#!/usr/bin/env python3
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((R/'reports/2026-11-14-2009-2012-2013-source-only-field-eligibility.csv').open()))
assert len(rows)==150
for y,n in [(2009,3811),(2012,8424),(2013,2025)]:
 d=json.loads((R/f'data/{y}_source_only_field_eligibility.json').read_text()); src=json.loads((R/f'data/{y}_source_only_field_month.json').read_text())
 assert d['source_only_timestamps']==n==src['source_only_rows'] and len(d['fields'])==50
 assert sum(m['source_only_rows'] for m in src['monthly'])==n
 for f in d['fields']:
  assert f['eligible_for_restoration'] is False
  assert f['old_nonnull']==f['paired_equal']+f['paired_conflict']+f['old_only_nonnull']
  assert f['wh_nonnull']==f['paired_equal']+f['paired_conflict']+f['wh_only_nonnull']
  assert f['source_only_timestamps']==f['paired_equal']+f['paired_conflict']+f['old_only_nonnull']+f['wh_only_nonnull']+f['both_null']
assert not any(r['eligible_for_restoration']!='False' for r in rows)
print('PASS: 2009/2012/2013 cohorts (3,811/8,424/2,025) partition across 50 fields each; no restoration eligibility inferred.')
