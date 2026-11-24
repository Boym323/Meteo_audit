#!/usr/bin/env python3
"""Paired temporal-only interpolation baseline on masked local 5-minute pressure truth."""
import argparse,csv,hashlib,json,statistics
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

def metrics(es):
 a=sorted(abs(x) for x in es)
 if not es:return {'n':0,'mae_hpa':None,'bias_hpa':None,'p95_abs_hpa':None}
 p=.95*(len(a)-1);i=int(p)
 return {'n':len(es),'mae_hpa':statistics.fmean(abs(x) for x in es),'bias_hpa':statistics.median(es),'p95_abs_hpa':a[i]+(a[min(i+1,len(a)-1)]-a[i])*(p-i)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 rows={}
 with a.archive.open(newline='') as f:
  for r in csv.DictReader(f):
   t=int(r['dateTime_utc']);p=None if not r['pressure_hpa'] else float(r['pressure_hpa']);rows[t]=p
 groups=defaultdict(lambda:{'e10':[],'e60':[],'neligible':0})
 for t,p in rows.items():
  d=datetime.fromtimestamp(t,timezone.utc)
  if d.year<2023 or d.year>2025 or p is None or t%600!=300:continue
  y=d.year;h=t//3600*3600
  # Masked :05/:15/:25/:35/:45/:55 target; same exact target for both methods.
  endpoints=(rows.get(t-300),rows.get(t+300),rows.get(h),rows.get(h+3600))
  if any(x is None for x in endpoints):continue
  if any(not 900<=x<=1050 for x in endpoints) or not 900<=p<=1050:continue
  # The review's fixed QC requires all twelve 5-minute values in the hour and
  # adjacent 5-minute station-pressure steps no greater than 2 hPa.
  hour_times=range(h,h+3600,300)
  hourvals=[rows.get(x) for x in hour_times]
  if len(hourvals)!=12 or any(x is None or not 900<=x<=1050 for x in hourvals):continue
  if any(abs(v-u)>2 for u,v in zip(hourvals,hourvals[1:])):continue
  # linear between adjacent real 10-minute pressure anchors, and between hourly anchors
  f10=.5; f60=(t-h)/3600
  i10=endpoints[0]+f10*(endpoints[1]-endpoints[0]);i60=endpoints[2]+f60*(endpoints[3]-endpoints[2])
  g=groups[y];g['neligible']+=1;g['e10'].append(i10-p);g['e60'].append(i60-p)
 result={'schema':'pressure-v3-temporal-interpolation-paired-v1','target':'existing local pressure at masked five-minute timestamp; synthetic temporally masked controls, not evidence of long-gap transfer accuracy','mask':'UTC minutes 05,15,25,35,45,55','quality':'complete 12-record hour; pressure 900..1050 hPa; all adjacent five-minute steps <=2 hPa; exact same target timestamps for both models','archive_sha256':hashlib.sha256(a.archive.read_bytes()).hexdigest(),'annual':{str(y):{'eligible_targets':v['neligible'],'ten_minute_linear':metrics(v['e10']),'hourly_linear':metrics(v['e60'])} for y,v in sorted(groups.items())}}
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['annual']))
if __name__=='__main__':main()
