#!/usr/bin/env python3
"""Validate cross-archive aggregate arithmetic against annual reconstruction snapshots."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'reports';STEM='2026-11-13-secondary-exact-cross-archive-2024-2026'
def main():
 d=json.loads((R/f'{STEM}.json').read_text());assert d['fields']==42; assert len(d['summary'])==3;assert len(d['field_results'])==126
 by={(x['year'],x['variable']):x for x in d['field_results']}
 for s in d['summary']:
  y=s['year'];assert s['production_rows']==s['exact_timestamp_pairs'];assert s['production_without_reconstruction_row']==0;assert s['usUnits_mismatches']==0;assert s['interval_mismatches']==0
  snap=json.loads((R/f'2026-11-13-annual-secondary-sensor-snapshot-{y}.json').read_text())
  assert s['production_rows']==snap['rows_n']
  for v in snap['variables']:
   x=by[(y,v['variable'])]
   assert x['production_nonnull']==v['nonnull_rows']
   assert x['reconstruction_nonnull']==v['nonnull_rows']
   assert x['both_nonnull']==v['nonnull_rows']
   assert x['equal_nonnull_values']==v['nonnull_rows']
   assert x['different_nonnull_values']==0 and x['production_only_nonnull']==0 and x['reconstruction_only_nonnull']==0
 with (R/f'{STEM}.csv').open(newline='') as f:assert len(list(csv.DictReader(f)))==126
 assert (R/f'{STEM}.md').stat().st_size>700
 print('PASS: 42 fields × 2024/2025/partial-2026 exact timestamp and value concordance')
 print('PASS: all counts reconcile to existing annual reconstruction snapshots; no field disagreements or one-sided values')
if __name__=='__main__':main()
