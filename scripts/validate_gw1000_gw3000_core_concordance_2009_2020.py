#!/usr/bin/env python3
"""Verify the pre-2021 core concordance slice against saved yearly SELECT results."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=json.loads((ROOT/'data/gw1000_gw3000_historical_yearly_concordance.json').read_text())
out=json.loads((ROOT/'data/gw1000_gw3000_core_concordance_2009_2020.json').read_text())
years=list(range(2009,2021)); fields=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','barometer','pressure','altimeter','dewpoint']
sr={int(x['utc_year']):x for x in src['rows'] if int(x['utc_year']) in years}
assert len(sr)==12 and out['exact_timestamp_pairs']==sum(int(x['exact_timestamp_pairs']) for x in sr.values())==1073011
assert out['unit_mismatch_pairs']==0 and out['interval_mismatch_pairs']==0
with (ROOT/'reports/2026-11-13-gw1000-gw3000-core-concordance-2009-2020.csv').open(newline='',encoding='utf-8') as f: csvrows=list(csv.DictReader(f))
assert len(csvrows)==132
for r in csvrows:
 y=int(r['year_utc']);f=r['variable'];raw=sr[y]
 for k in ['both_nonnull','equal_nonnull','one_sided_null']:
  assert int(r[k])==int(raw[f'{f}_{k}'])
for x in out['totals']:
 f=x['variable'];
 for k in ['both_nonnull','equal_nonnull','one_sided_null']:
  assert x[k]==sum(int(r[f'{f}_{k}']) for r in sr.values())
report=(ROOT/'reports/2026-11-13-gw1000-gw3000-core-concordance-2009-2020.md').read_text()
assert '907,237' in report and '908,487' in report and 'not independent sensors' in report
print('PASS: 132 field/year cells and all 11 variable totals match saved exact-pair snapshot; 1,073,011 pairs, zero unit/interval mismatches.')
