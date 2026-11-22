#!/usr/bin/env python3
"""Deterministically validate the stored 2020 wind anomaly episode aggregates."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'data/historical_wind_2020_aug20_sep1_review.json').read_text())
rows=d['daily']
assert len(rows)==12
assert [x['utc_date'] for x in rows]==[f'2020-08-{day:02d}' for day in range(20,32)]
for x in rows:
    assert x['wh1080_rows'] in (287,288)
    assert x['eu_old_rows'] <= x['wh1080_rows']
    assert x['windSpeed_ratio_3_6']+x['windSpeed_other']==x['windSpeed_nonzero']
    assert x['windGust_ratio_3_6']+x['windGust_other']==x['windGust_nonzero']
assert sum(x['wh1080_rows'] for x in rows)==d['evidence']['wh1080_rows']==3454
assert sum(x['eu_old_rows'] for x in rows)==d['evidence']['eu_old_rows_on_wh_keys']==3446
assert sum(x['wh1080_rows']-x['eu_old_rows'] for x in rows)==d['evidence']['eu_old_missing_wh_keys']==8
assert sum(x['windSpeed_nonzero'] for x in rows)==d['evidence']['paired_nonzero_windSpeed']==3421
assert sum(x['windSpeed_ratio_3_6'] for x in rows)==d['evidence']['windSpeed_ratio_3_6_within_0_001']==801
assert sum(x['windSpeed_other'] for x in rows)==d['evidence']['windSpeed_other_ratio']==2620
assert sum(x['windGust_nonzero'] for x in rows)==d['evidence']['paired_nonzero_windGust']==3443
assert sum(x['windGust_ratio_3_6'] for x in rows)==d['evidence']['windGust_ratio_3_6_within_0_001']==1906
assert sum(x['windGust_other'] for x in rows)==d['evidence']['windGust_other_ratio']==1537
e=d['evidence']
assert e['windSpeed_ratio_1_within_0_001']==e['windGust_ratio_1_within_0_001']==0
assert e['old_weewx_rows_in_window']==0
assert e['wh1080_usUnits']==17 and e['eu_old_usUnits']==16 and e['wh1080_interval_minutes']==5
assert e['downstream_windSpeed_and_windGust_equal_to_eu_old_on_shared_keys'] is True
assert d['decision']['disposition']=='REVIEW_REQUIRED'
assert d['decision']['correction_proposals']==0
assert d['safety']['database_writes']==0 and d['safety']['staging'] is False
sql=(ROOT/'sql/readonly/historical_wind_2020_aug20_sep1_review.sql').read_text()
assert 'a0.dateTime>=1597881600 AND a0.dateTime<1598918400' in sql
assert 'database_name=weewx_WH1080' in sql and 'database_name=old_weewx' in sql
print(json.dumps({'status':'PASS','days':len(rows),'WH1080_rows':3454,'eu_old_rows':3446,'missing_eu_old_keys':8,'windSpeed_nonzero':3421,'windSpeed_ratio_3_6':801,'windSpeed_other':2620,'windGust_nonzero':3443,'windGust_ratio_3_6':1906,'windGust_other':1537,'disposition':'REVIEW_REQUIRED','new_corrections':0,'database_access':'READ_ONLY SELECT','writes':0},ensure_ascii=False))
