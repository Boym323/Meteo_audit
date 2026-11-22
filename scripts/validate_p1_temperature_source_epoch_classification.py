#!/usr/bin/env python3
"""Validate deterministic P1 year/source/epoch classification against frozen aggregates."""
import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1]
base={int(x['utc_year']):int(x['paired_targets']) for x in csv.DictReader((R/'reports/2026-11-12-outtemp-source-copy-annual.csv').open())}
rows=list(csv.DictReader((R/'proposals/restored_temperature/year_source_epoch_quality.csv').open()))
assert len(rows)==len(base)==11
assert {int(x['utc_year']):int(x['paired_candidate_rows']) for x in rows}==base
assert sum(int(x['paired_candidate_rows']) for x in rows)==8965
assert sum(int(x['copy_agreement_rows']) for x in rows)==8965
assert sum(int(x['known_anomaly_subset_rows']) for x in rows)==18
assert sum(int(x['restoration_eligible_rows']) for x in rows)==0
assert all(x['archive_lineage_status']=='UNVERIFIED_SOURCE_ARCHIVE_ROLE_AND_UNIT_TRANSFORM' for x in rows)
assert all(x['documented_station_hardware_epoch'].startswith('Watson W-8681') for x in rows)
print('PASS: all 11 year cohorts reconcile to frozen 8,965; known anomaly subset=18; eligible=0')
