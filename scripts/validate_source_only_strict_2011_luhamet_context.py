#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d=json.loads((root/'data/source_only_strict_2011_luhamet_context.json').read_text())
r=d['result']
assert d['schema']=='source-only-strict-2011-luhamet-context-v1'
assert r['source_candidates']==1201 and r['exact_LuhaMet_rows']==0 and r['exact_reference_T']==0
assert r['reference_min_T'] is None and r['reference_max_T'] is None
assert d['disposition']=='all 1201 remain REVIEW_REQUIRED_SOURCE_LINEAGE'
assert d['proposal_count']==0 and d['database_writes']==0 and d['application']=='NOT_APPLIED'
source=json.loads((root/'data/source_only_strict_2011_cohort.json').read_text())
assert source['aggregate']['timestamp_count']==r['source_candidates']
assert source['review_required']==1201 and source['restored']==0 and source['estimated']==0
print('PASS: LuhaMet exact-time coverage is zero for all 1,201 strict source-only 2011 rows; all remain held.')
