#!/usr/bin/env python3
import json
from pathlib import Path
x=json.loads(Path('data/source_only_cohort_scope_matrix.json').read_text())
assert x['authoritative_global_cohort']['rows']==207182
assert len(x['field_matrix_scopes'])==12
assert x['reconstruction_target_field_matrix_records_represented']==26114
m={ (int(s['year']),s['scope_kind']):s['source_only_rows'] for s in x['field_matrix_scopes'] }
assert m[(2014,'EU_OLD_TARGET_FIELD_MATRIX')]==1071
assert next(s for s in x['field_matrix_scopes'] if s['year']==2015)['fields_partitioned']==10
assert m[(2016,'EU_OLD_TARGET_FIELD_MATRIX')]==16330 and m[(2017,'EU_OLD_TARGET_FIELD_MATRIX')]==28015
assert m[(2018,'RECONSTRUCTION_TARGET_FIELD_MATRIX_PARTIAL_YEAR')]==422
assert x['overlapping_limited_scopes'][0]['rows']==30271
assert x['safety']['q1_2018_in_new_scope'] is False and x['safety']['year_2021_included'] is False
assert 'not complete coverage' in x['coverage_warning'].lower()
print('PASS: source-only target definitions, partial years, dual-target and overlap are explicit; no coverage conflation.')
