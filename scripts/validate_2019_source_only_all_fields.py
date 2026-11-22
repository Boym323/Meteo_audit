#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/2019_source_only_field_month.json').read_text())
assert d['source_only_rows']==814 and d['off_grid_rows']==512 and d['on_grid_rows']==302
assert sum(m['source_only_rows'] for m in d['monthly'])==814
assert len(d['monthly'])==10 and all(len(m['fields'])==50 for m in d['monthly'])
assert sum(x['rows'] for x in d['alignment_groups'])==814
assert sum(x['projected_rows'] for x in d['alignment_groups'])==447
assert sum(x['projected_temp_equal'] for x in d['alignment_groups'])==394
assert sum(x['projected_temp_conflict'] for x in d['alignment_groups'])==53
assert d['aggregate_field_totals']['outTemp']['both_equal']==814
assert d['aggregate_field_totals']['outHumidity']['both_conflict']==26
assert d['archive_exact_presence']['pocasi_loucka_eu_old_rows']==394
assert d['strict_review_cohort']['rows']==233 and d['strict_review_cohort']['eu_old_rows']==0
assert d['database_writes']==0
for name in ['2019_source_only_monthly_field_availability.sql','2019_source_only_alignment_and_archive_concordance.sql','2019_source_only_archive_presence_and_strict_subset.sql']:
    q=(R/'sql/readonly'/name).read_text().upper()
    assert q.lstrip().startswith('-- READ-ONLY')
    assert not any(x in q for x in ('INSERT ','UPDATE ','DELETE ','REPLACE '))
print('PASS: 814 rows, 50 fields/month, offsets, third-archive and strict subset, READ-ONLY SQL.')
