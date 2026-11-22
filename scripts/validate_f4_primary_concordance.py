#!/usr/bin/env python3
"""Validate bounded F4 primary-field concordance snapshots without DB access."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
expected={2009:78248,2010:104116,2011:67329,2012:75372,2013:95495,2015:104063,2016:104785,2017:104873,2019:105133,2020:62652}
fields={'outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','barometer','pressure','altimeter'}
summary=[]
for year,pairs in expected.items():
 p=R/f'data/f4_migration_concordance_{year}_primary_fields.json'
 d=json.loads(p.read_text());assert d['utc_year']==year and d['source_timestamp_pairs']==pairs and d['field_count']==10
 assert d['database_access']=='READ_ONLY_SELECT' and d['database_writes']==0
 grouped={}
 for x in d['fields']:grouped.setdefault(x['variable'],{})[x['metric']]=x['count']
 assert set(grouped)==fields and all(len(x)==8 for x in grouped.values())
 assert all(isinstance(n,int) and n>=0 for x in grouped.values() for n in x.values())
 q=R/d['query_file'];sql=q.read_text();assert 'SELECT' in sql.upper() and 'INSERT' not in sql.upper() and 'UPDATE' not in sql.upper() and 'DELETE' not in sql.upper()
 bounds={2009:(1230768000,1262304000),2010:(1262304000,1293840000),2011:(1293840000,1325376000),2012:(1325376000,1356998400),2013:(1356998400,1388534400),2015:(1420070400,1451606400),2016:(1451606400,1483228800),2017:(1483228800,1514764800),2019:(1546300800,1577836800),2020:(1577836800,1609459200)}[year]
 assert f'o.dateTime>={bounds[0]}' in sql and f'o.dateTime<{bounds[1]}' in sql
 summary.append({'year':year,'pairs':pairs,'source_conflict_fields':sum(v['source_conflict']>0 for v in grouped.values())})
# 2014 full 50-field snapshot is validated by validate_f4_field_provenance_matrix.py.
print(json.dumps({'status':'PASS','snapshots':summary,'fields_per_year':10,'q1_2018':'NOT_QUERIED','year_2021':'NOT_QUERIED','database_access':'NONE'}))
