#!/usr/bin/env python3
"""Deterministic internal consistency checks for the read-only 2015 cohort snapshot."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'data/2015_source_only_cohort.json').read_text())
assert d['counts']['source_only_rows']==2147
assert sum(d['monthly_source_only_rows'].values())==2147
assert d['counts']['off_300_second_grid']+d['counts']['on_300_second_grid']==2147
assert sum(x['rows'] for x in d['unit_interval_profiles'])==2147
assert d['counts']['also_absent_from_reconstruction_exact_timestamp']==2147
assert d['classification']['UNRESOLVED']==2147
assert d['classification']['SOURCE_ONLY_POTENTIALLY_RESTORABLE']==0
assert d['primary_field_availability']['outTemp']['old_weewx_nonnull']==0
assert d['primary_field_availability']['outTemp']['weewx_WH1080_nonnull']==2147
assert d['primary_field_availability']['altimeter']['conflict_both_nonnull']==2147
for f in d['sql_files']:
    text=(ROOT/f).read_text().upper()
    assert text.lstrip().startswith('-- READ-ONLY')
    assert not any(x in text for x in ('INSERT ', 'UPDATE ', 'DELETE ', 'REPLACE '))
print('PASS: 2015 source-only counts, months, units, field evidence, unresolved disposition, and read-only SQL.')
