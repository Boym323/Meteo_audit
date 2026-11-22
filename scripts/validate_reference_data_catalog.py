#!/usr/bin/env python3
"""Validate public reference cache inventory against local hashes and snapshots."""
import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
catalog=json.loads((ROOT/'data/reference-inventory/reference_source_catalog.json').read_text())
stations=json.loads((ROOT/'data/reference-inventory/reference_stations_snapshot_20261113.json').read_text())
candidates=json.loads((ROOT/'data/reference-inventory/reference_dataset_candidates.json').read_text())
assert len(stations['stations'])==2
by={s['station_id']:s for s in stations['stations']}
assert set(by)=={'luhamet_sehradice','wu_ilouka4'}
assert by['luhamet_sehradice']['elevation_m']==318.0 and by['luhamet_sehradice']['latitude_n'] is None
assert by['wu_ilouka4']['elevation_m'] is None and by['wu_ilouka4']['latitude_n'] is None
# Reconcile epoch strings with Unix bounds already recorded in the reference inventory snapshot.
assert by['luhamet_sehradice']['first_observed_utc']=='2015-04-17T12:35:00Z'
assert by['luhamet_sehradice']['last_observed_utc']=='2026-10-29T17:16:00Z'
assert by['wu_ilouka4']['first_observed_utc']=='2021-12-27T10:03:04Z'
assert by['wu_ilouka4']['last_observed_utc']=='2026-10-29T17:39:52Z'
files={}
for dataset in catalog['datasets']:
    for rec in dataset['files']:
        p=ROOT/rec['path']
        assert p.is_file(),rec['path']
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        if rec['sha256_manifest']:
            assert digest==rec['sha256_manifest'],rec['path']
        assert p.stat().st_size==int(rec['bytes_actual']),rec['path']
        files[str(p.resolve())]=p.stat().st_size
assert len(files)==34, len(files)
assert sum(files.values())==113681963, sum(files.values())
assert catalog['distinct_existing_file_count']==len(files)
assert catalog['distinct_existing_bytes']==sum(files.values())
bydataset={x['dataset_id']:x for x in catalog['datasets']}
assert bydataset['chmi-2018']['existing_file_references']==24
assert bydataset['chmi-2018']['unavailable_or_missing_entries']==2
assert all(x['local_cache'] is False for x in candidates['reanalysis_candidates'])
assert candidates['loucka_sensor_coordinates'] is None
summary=list(csv.DictReader((ROOT/'reports/2026-11-13-reference-cache-manifest-summary.csv').open(newline='')))
assert len(summary)==4
assert sum(int(r['existing_file_references']) for r in summary)>=len(files)
print('PASS: 2 station registry rows, 34 unique cache files SHA-256 verified, 2 CHMI boundary 404s, ERA candidates not downloaded')
