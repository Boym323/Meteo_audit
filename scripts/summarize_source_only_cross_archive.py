#!/usr/bin/env python3
"""Deterministic aggregations of the saved read-only cross-archive query."""
import csv,json
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]; rows=json.loads((R/'data/source_only_2009_2020_cross_archive_grouped_utc.json').read_text())
assert sum(int(x['timestamp_count']) for x in rows)==207182
keys=['utc_year','interval_min','usUnits','on_5m_grid','concordance','has_pocasi_main','has_gw1000','has_pocasi_old']
outs={}
for name,fields in [('year_interval_grid',['utc_year','interval_min','usUnits','on_5m_grid']),('copy_concordance',['utc_year','concordance']),('other_archive_presence',['utc_year','has_pocasi_main','has_gw1000','has_pocasi_old']),('availability_by_year',['utc_year'])]:
 d=defaultdict(lambda:{'timestamp_count':0})
 for x in rows:
  k=tuple(x[z] for z in fields);o=d[k];o.update({z:x[z] for z in fields});n=int(x['timestamp_count']);o['timestamp_count']+=n
  if name=='availability_by_year':
   for v in ['old_temp_present','wh_temp_present','old_rh_present','wh_rh_present','old_rain_present','wh_rain_present','old_rainrate_present','wh_rainrate_present','old_wind_present','wh_wind_present']:
    o[v]=o.get(v,0)+n*int(x[v])
   o['both_copies']=o.get('both_copies',0)+n*int(x['both_copies'])
   o['on_5m_grid']=o.get('on_5m_grid',0)+n*int(x['on_5m_grid'])
 outs[name]=list(d.values())
for name,rs in outs.items():
 with (R/f'reports/2026-11-13-source-only-{name.replace("_","-")}.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(sorted(rs,key=lambda z:tuple(str(z[k]) for k in fields) if False else str(z)))
# exact-source union headline and row-level classification counts
headline={'unique_timestamps':207182,'aggregated_query_groups':len(rows),'source_archives':['old_weewx','weewx_WH1080'],'source_only_scope':'No exact timestamp in loucka_reconstruction.archive; years 2009–2020 UTC','other_exact_archives':['pocasi-loucka.eu','pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old'],'timestamp_count_reconciles':sum(int(x['timestamp_count']) for x in rows)}
for k in ['copy_concordance','other_archive_presence','year_interval_grid','availability_by_year']:headline[k]=outs[k]
(R/'data/source_only_2009_2020_cross_archive_summary.json').write_text(json.dumps(headline,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'total':headline['timestamp_count_reconciles'],'groups':len(rows),'concordance_groups':len(outs['copy_concordance']),'archive_presence_groups':len(outs['other_archive_presence'])}))
