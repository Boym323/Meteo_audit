#!/usr/bin/env python3
"""Validate the bounded reference-license evidence record offline."""
import json
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'data/reference-inventory/license_provenance_review_20261113.json'
d=json.loads(p.read_text());s=d['sources']
assert d['publication_authorized'] is False
assert set(s)=={'chmi_open_data','era5','era5_land','luhamet_sehradice','weather_underground_ilouka4_import'}
assert 'DATASET_SPECIFIC_TERMS_STILL_REQUIRED' in s['chmi_open_data']['status']
assert 'UNRESOLVED' in s['weather_underground_ilouka4_import']['status']
assert 'NOT_IDENTIFIED' in s['luhamet_sehradice']['status']
assert all(s[k]['data_downloaded_in_this_review'] is False for k in ('era5','era5_land'))
assert len(d['limitations'])>=4
print('PASS: 5 source records, unresolved imported rights, no publication or ERA downloads')
