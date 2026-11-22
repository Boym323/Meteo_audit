#!/usr/bin/env python3
"""Offline consistency checks for A/B/C handoff artifacts."""
import csv,json,collections,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
# A: exact candidate inventory and cohort accounting.
a=json.loads((R/'data/EXACT_SOURCE_COHORT_DECISIONS.json').read_text())
with (R/'data/REMAINING_EXACT_SOURCE_CANDIDATES.csv').open(newline='') as f:candidates=list(csv.DictReader(f))
assert a['unique_keys']==4862 and len(a['records'])==4862 and len(candidates)==4862
co=collections.Counter(x['cohort'] for x in a['records'])
assert co==collections.Counter(a['cohort_counts'])
assert sum(co.values())==4862 and not any('SAFE' in k for k in co)
assert co['PROBABLE_SOURCE_VALUE_REQUIRES_VALIDATION']==4463
assert co['HISTORICALLY_REMOVED_INVALID_DATA']==288
assert co['SOURCE_CONFLICT_SUSPECTED_STALE_PLATEAU']==102
assert co['SOURCE_CONFLICT']==1 and co['SOURCE_ZERO_REVIEW']==8
# B: full frozen payload matches manifest and null counts.
m=json.loads((R/'data/GW3000_INSERT_ONLY_BACKFILL_MANIFEST.json').read_text())
p=R/'data/GW3000_INSERT_ONLY_BACKFILL_PAYLOAD.jsonl'; payload=[json.loads(x) for x in p.open()]
assert len(payload)==m['row_counts']['source_rows']==4651 and len(payload[0])==80
assert hashlib.sha256(p.read_bytes()).hexdigest()==m['payload']['sha256']
assert payload[0]['dateTime']==1793286900 and payload[-1]['dateTime']==1794682800
# C: full frozen 2009-2026 core-variable readiness outputs and estimate disclosure.
with (R/'data/DAILY_STATISTICAL_COVERAGE.csv').open(newline='') as f:daily=list(csv.DictReader(f))
with (R/'data/MONTHLY_STATISTICAL_READINESS.csv').open(newline='') as f:months_stat=list(csv.DictReader(f))
with (R/'data/ANNUAL_STATISTICAL_READINESS.csv').open(newline='') as f:years_stat=list(csv.DictReader(f))
assert len(daily)==52088 and len({(x['local_day'],x['variable']) for x in daily})==52088
assert len(months_stat)==1696 and len(years_stat)==144
assert sum(int(x['estimated_values_in_archive']) for x in daily)==30537
assert sum(int(x['estimated_values_in_archive']) for x in months_stat)==30537
assert sum(int(x['estimated_values_in_archive']) for x in years_stat)==30537
assert any(x['status']=='PROTECTED_Q1_2018_REVIEW_REQUIRED' for x in months_stat)
assert any(x['status']=='DIAGNOSTIC_2021_NO_PRODUCTION_DECISION' for x in months_stat)
assert all(x['status']=='PARTIAL_CURRENT_MONTH_NOT_CERTIFIABLE' for x in months_stat if x['period']=='2026-10')
assert all(x['status']=='PARTIAL_YEAR_NOT_CERTIFIABLE' for x in years_stat if x['period']=='2026')
assert all(x['variable'] not in ('rain','rainRate') for x in months_stat)
with (R/'data/remaining_monthly_period_screen.csv').open(newline='') as f:months=list(csv.DictReader(f))
with (R/'data/remaining_annual_period_screen.csv').open(newline='') as f:years=list(csv.DictReader(f))
assert len(months)==16632 and len(years)==1386
assert all(x['readiness'] in ('PROTECTED_E4_RAINFALL_NO_STATISTICAL_CLASSIFICATION','DIAGNOSTIC_ONLY_PROTECTED','PROTECTED_Q1_2018') for x in months if x['variable'] in ('rain','rainRate'))
# Gap classification: all unresolved prefixes included.
with (R/'ARCHIVE_GAP_INTERVALS.csv').open(newline='') as f:gaps=list(csv.DictReader(f))
counts=collections.Counter(x['gap_classification'] for x in gaps)
assert len(gaps)==24488 and counts['UNRESOLVED_CADENCE_GAP']+counts['UNRESOLVED_CADENCE_GAP_KNOWN_2013_TEN_MINUTE_EXCEPTION']==12510
assert sum(int(x['unobserved_grid_slots_candidate'] or 0) for x in gaps)==63897
progress=json.loads((R/'UNIFIED_ARCHIVE_PROGRESS.json').read_text());assert progress['completed_stages']==12 and progress['completion_percent']==100
print(json.dumps({'status':'PASS','A_keys':len(candidates),'A_cohorts':dict(co),'B_rows':len(payload),'B_sha256':m['payload']['sha256'],'C_daily_primary_cells':len(daily),'C_monthly_primary_cells':len(months_stat),'C_annual_primary_cells':len(years_stat),'C_monthly_availability_fields':len(months),'C_annual_availability_fields':len(years),'gap_edges':len(gaps),'unresolved_edges':12510,'candidate_slots':63897,'stages':12},indent=2))
