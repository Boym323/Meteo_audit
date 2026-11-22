#!/usr/bin/env python3
"""Validate 2022 RH outage/source aggregates against monthly archive inventory."""
import csv,datetime,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'reports';STEM='2026-11-13-rh-luhamet-outage-2022-source-coverage'
def main():
 d=json.loads((R/f'{STEM}.json').read_text());monthly=d['monthly'];hist=d['history_reconciliation']
 assert len(monthly)==12
 assert d['target_archive_rows']==104142 and d['target_RH_null']==41727 and d['target_RH_nonnull']==62415
 assert int(hist['year_2022']['target_rows'])==104142
 assert int(hist['year_2022']['current_RH_null_rows'])==41727
 assert int(hist['year_2022']['null_rows_with_any_RH_history'])==85
 assert int(hist['year_2022']['null_rows_with_applied_RH_history'])==85
 assert int(hist['year_2022']['null_rows_without_RH_history'])==41642
 feb=monthly[1];assert int(feb['archive_rows'])==8058 and int(feb['target_RH_null'])==8058
 assert int(feb['exact_LuhaMet_RH_values'])==8057 and int(feb['comparable_RH_pairs'])==0
 assert int(hist['february_2022']['rows_n'])==8058 and int(hist['february_2022']['null_without_history'])==8058
 with (R/f'{STEM}-daily.csv').open(newline='') as f: daily=list(csv.DictReader(f))
 assert len(daily)==365
 assert sum(int(x['archive_rows']) for x in daily)==104142
 assert sum(int(x['target_RH_nonnull']) for x in daily)==62415
 zero=[x for x in daily if int(x['archive_rows'])>0 and int(x['target_RH_nonnull'])==0]
 assert len(zero)==112
 best=[];cur=[]
 for x in daily:
  day=datetime.date.fromisoformat(x['utc_date'])
  if int(x['target_RH_nonnull'])==0:
   if cur and day!=datetime.date.fromisoformat(cur[-1]['utc_date'])+datetime.timedelta(days=1):
    if len(cur)>len(best):best=cur
    cur=[]
   cur.append(x)
  elif cur:
   if len(cur)>len(best):best=cur
   cur=[]
 if len(cur)>len(best):best=cur
 assert len(best)==30 and best[0]['utc_date']=='2022-01-30' and best[-1]['utc_date']=='2022-02-28'
 assert sum(int(x['archive_rows']) for x in best)==8634
 assert sum(int(x['exact_LuhaMet_RH_values']) for x in best)==8632
 assert len(list(csv.DictReader((R/f'{STEM}-monthly.csv').open(newline=''))))==12
 assert (R/f'{STEM}.md').stat().st_size>900
 print('PASS: 2022 monthly/daily RH availability reconciles to 104,142 archive rows')
 print('PASS: 30-day Jan 30–Feb 28 zero-RH run; 8,632 exact LuhaMet RH candidates across 8,634 archive rows')
 print('PASS: annual and February RH history counts reconcile; no source values are promoted to target')
if __name__=='__main__':main()
