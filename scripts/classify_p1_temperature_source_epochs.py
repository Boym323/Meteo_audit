#!/usr/bin/env python3
"""Classify existing aggregate P1 cohorts against documented station epochs; no DB access."""
import csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'reports/2026-11-12-outtemp-source-copy-annual.csv'
rows=list(csv.DictReader(src.open()))
out=ROOT/'proposals/restored_temperature/year_source_epoch_quality.csv'
fields=['utc_year','paired_candidate_rows','old_weewx_rows','weewx_WH1080_rows','copy_agreement_rows','documented_station_hardware_epoch','archive_lineage_status','quality_disposition','known_anomaly_subset_rows','restoration_eligible_rows','evidence_note']
with out.open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
 for r in rows:
  y=int(r['utc_year']); n=int(r['paired_targets'])
  w.writerow({'utc_year':y,'paired_candidate_rows':n,'old_weewx_rows':n,'weewx_WH1080_rows':n,'copy_agreement_rows':int(r['exact_equal']),'documented_station_hardware_epoch':'Watson W-8681 (site-level history; not linked to SQL exports)','archive_lineage_status':'UNVERIFIED_SOURCE_ARCHIVE_ROLE_AND_UNIT_TRANSFORM','quality_disposition':'EXCLUDE_ER12_ANOMALY_SUBSET_AND_REVIEW_REMAINDER' if y==2013 else 'REVIEW_REQUIRED_PROVENANCE','known_anomaly_subset_rows':18 if y==2013 else 0,'restoration_eligible_rows':0,'evidence_note':'Exact copy agreement is integrity evidence only; source archives and historical target unit conversion are not authenticated.'})
assert sum(int(r['paired_targets']) for r in rows)==8965
assert sum(int(r['exact_equal']) for r in rows)==8965
print(f'WROTE {len(rows)} UTC-year cohorts; 8965 candidate rows; 18 known 2013 anomaly subset; 0 restoration-eligible')
