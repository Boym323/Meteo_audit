#!/usr/bin/env python3
"""Validate the bounded six-archive 2024–2025 empty-source gap result."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
x=json.loads((R/'data/b5_2024_2025_gap_availability_summary.json').read_text())
assert [(y['year_utc'],y['gap_count']) for y in x['years']]==[(2024,7),(2025,8)]
assert x['total_gap_episodes']==15 and x['archive_episode_cells']==90 and x['source_rows']==0 and x['source_values']==0
for y in x['years']:
 assert y['all_source_archives_empty'] and len(y['archives'])==6
 for a in y['archives']:
  assert a['gaps_with_rows']==0 and a['gaps_without_rows']==y['gap_count'] and a['source_rows']==0
  assert all(v==0 for v in a['field_nonnull_rows'].values())
assert x['database_access'].startswith('READ_ONLY') and x['database_writes']==0 and not x['staging'] and x['application']=='NOT_APPLIED'
assert x['query_execution_utc'].startswith('NOT_RETURNED_BY_WEATHER_MCP')
print(json.dumps({'status':'PASS','gap_episodes':15,'archive_episode_cells':90,'empty_cells':90,'source_rows':0,'source_field_values':0,'writes':0},ensure_ascii=False))
