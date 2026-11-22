#!/usr/bin/env python3
"""Recompute selected B means using actual civil-period interval overlaps.

Intervals that overlap the preceding archive interval are excluded entirely;
this avoids allocating an ambiguous value to multiply-covered time. Output is
diagnostic and does not replace canonical variants or authorize publication.
"""
from __future__ import annotations
import hashlib,json,sqlite3,zlib,math
from collections import defaultdict
from decimal import Decimal
from datetime import datetime,timedelta
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data';sys.path.insert(0,str(ROOT/'src'))
from meteo_audit.time_bounds import local_period_bounds,interval_overlap_seconds,PRAGUE

def main():
    cand=json.loads((ROOT/'MONTHLY_PUBLICATION_CANDIDATES.json').read_text())['candidates']
    wanted={(r['period'],r['variable']) for r in cand}; bounds={p:local_period_bounds(p) for p,_ in wanted}
    dbp=DATA/'historical_value_concordance.sqlite';db=sqlite3.connect(f'file:{dbp.resolve()}?mode=ro',uri=True)
    acc=defaultdict(lambda:{'sum':Decimal(0),'weight':0,'sin':0.0,'cos':0.0,'rows':0,'overlap_excluded':0,'invalid_interval':0,'clipped':0,'calm_excluded':0,'previous_end':None})
    for i,(ts,iv,month,blob) in enumerate(db.execute('SELECT dateTime,target_interval,local_month,comparison_zlib FROM timestamp_evidence ORDER BY dateTime')):
        ts=int(ts);iv=int(iv or 0)
        local_period=datetime.fromtimestamp(ts,PRAGUE).strftime('%Y-%m')
        prior_date=datetime.fromtimestamp(ts,PRAGUE).replace(day=1)-timedelta(days=1)
        possible_periods={local_period,prior_date.strftime('%Y-%m')}
        candidate_periods=possible_periods.intersection(p for p,_ in wanted)
        if not candidate_periods:continue
        fields=None
        for target_month in candidate_periods:
          for var in {v for p,v in wanted if p==target_month}:
            # B consists only of exact source matched/recovered/restored values.
            if fields is None: fields=json.loads(zlib.decompress(blob))
            x=fields.get(var,{});value=x.get('target_value')
            if value is None or x.get('provenance_category') not in {'SOURCE_MATCHED','RECOVERED_SOURCE','RESTORED'}:continue
            a=acc[(target_month,var)]
            if iv<=0 or iv>1440:
                if target_month==local_period:
                    a['rows']+=1;a['invalid_interval']+=1
                continue
            lo,hi=bounds[target_month];overlap=interval_overlap_seconds(ts,iv*60,lo,hi)
            if not overlap:continue
            a['rows']+=1
            start=ts-iv*60
            prev=a['previous_end']
            if prev is not None and start<prev:
                a['overlap_excluded']+=1;a['previous_end']=max(prev,ts);continue
            if overlap<iv*60:a['clipped']+=1
            if var=='windDir':
                speed=fields.get('windSpeed',{}).get('target_value')
                if speed is None or Decimal(str(speed))<=0:
                    a['calm_excluded']+=1;a['previous_end']=ts;continue
                angle=math.radians(float(value));a['sin']+=math.sin(angle)*overlap;a['cos']+=math.cos(angle)*overlap
            else:a['sum']+=Decimal(str(value))*overlap
            a['weight']+=overlap;a['previous_end']=ts
        if i and i%250000==0:print(f'processed_rows={i}',flush=True)
    db.close(); rows=[]
    for r in cand:
        a=acc[(r['period'],r['variable'])];mean=(math.degrees(math.atan2(a['sin'],a['cos']))%360 if r['variable']=='windDir' and a['weight'] else (float(a['sum']/a['weight']) if a['weight'] else None));rows.append({**r,'canonical_mean':r['value'],'interval_adjusted_mean':mean,'retained_weight_seconds':a['weight'],'period_seconds':bounds[r['period']][1]-bounds[r['period']][0],'interval_time_coverage':a['weight']/(bounds[r['period']][1]-bounds[r['period']][0]),'included_rows':a['rows']-a['overlap_excluded']-a['invalid_interval'],'overlap_excluded_rows':a['overlap_excluded'],'invalid_interval_rows':a['invalid_interval'],'clipped_boundary_rows':a['clipped'],'calm_direction_rows_excluded':a['calm_excluded'],'mean_delta':((mean-r['value']+180)%360-180) if r['variable']=='windDir' and mean is not None and r['value'] is not None else ((mean-r['value']) if mean is not None and r['value'] is not None else None),'method':'Clip (end-interval,end] to Europe/Prague civil month; exclude overlapping interval records wholesale; duration-weight scalar means and use duration-weighted circular vectors for windDir, excluding calm/unknown-speed directions. Diagnostic only.'})
    out={'schema':'loucka-interval-adjusted-monthly-means-v1','snapshot_id':hashlib.sha256(dbp.read_bytes()).hexdigest(),'candidate_count':len(rows),'rows':rows}
    (ROOT/'INTERVAL_ADJUSTED_MONTHLY_MEANS.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'candidates':len(rows),'with_overlap_exclusions':sum(r['overlap_excluded_rows']>0 for r in rows),'max_abs_mean_delta':max((abs(r['mean_delta']) for r in rows if r['mean_delta'] is not None),default=0)},indent=2))
if __name__=='__main__':main()
