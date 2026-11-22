#!/usr/bin/env python3
"""Build daily/monthly/annual statistical screens from frozen read-only archive exports.

Values describe the current raw archive and deliberately retain their provenance limits.
Estimated rows are counted and disclosed, not silently presented as measurements.
"""
from __future__ import annotations
import csv, datetime as dt, json
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
TZ=ZoneInfo('Europe/Prague')
VARS=('outTemp','outHumidity','windSpeed','windGust','windDir','barometer','pressure','altimeter')
UNITS={'outTemp':'degC','outHumidity':'percent','windSpeed':'km_per_hour','windGust':'km_per_hour','barometer':'hPa','pressure':'hPa','altimeter':'hPa','windDir':'degrees_from_north'}

def read_csv(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))

raw={}
for year in range(2009,2027):
    p=ROOT/f'data/daily_archive_core_{year}.csv'
    if not p.exists():raise SystemExit(f'missing required frozen archive export: {p}')
    for r in read_csv(p):raw[(r['local_day'],r['variable'])]=r
for p in sorted((ROOT/'data').glob('daily_archive_additional_primary_*.csv')):
    for r in read_csv(p):
        if r['variable'] in ('pressure','altimeter'):raw[(r['local_day'],r['variable'])]=r
changes={(r['local_day'],r['variable']):r for r in read_csv(ROOT/'data/applied_change_counts_all_periods.csv')}
changes.update({(r['local_day'],r['variable']):r for r in read_csv(ROOT/'data/additional_primary_change_counts.csv')})
direction={r['local_day']:r for r in read_csv(ROOT/'data/wind_direction_daily_circular.csv')}
cadence=defaultdict(int)
for r in read_csv(ROOT/'data/monthly_interval_histogram_2009_2026.csv'):
    cadence[(r['local_month'],int(r['interval_minutes']))]=int(r['archive_rows'])
estimates=json.loads((ROOT/'data/applied_estimated_operations.json').read_text())
est_by_day=defaultdict(int)
first_observed={}
for (day,var),r in raw.items():
    if int(r.get('measured_rows') or 0) and (var not in first_observed or day<first_observed[var]):first_observed[var]=day
for day,r in direction.items():
    if int(r.get('measured_rows') or 0) and ('windDir' not in first_observed or day<first_observed['windDir']):first_observed['windDir']=day
for r in estimates:
    day=dt.datetime.fromtimestamp(int(r['target_time']),TZ).date().isoformat()
    est_by_day[(day,r['variable'])]+=1

first=dt.date(2009,1,1); last=dt.date(2026,10,29)
daily=[]; day_index={}
d=first
while d<=last:
    day=d.isoformat(); expected=288 if d.year>2009 or day>='2009-03-29' else 0
    # The station's operating epoch begins during 2009; absence before the first
    # archive point is not counted as a full day of missing observations.
    if d.year==2009 and day<'2009-03-29': expected=0
    dst_expected=int((dt.datetime.combine(d+dt.timedelta(days=1),dt.time(),TZ).timestamp()-dt.datetime.combine(d,dt.time(),TZ).timestamp())/300)
    # Use actual local-day slot count, including 23/25-hour DST days.
    expected=dst_expected if expected else 0
    daylight=144 if expected else 0
    for var in VARS:
        r=direction.get(day,{}) if var=='windDir' else raw.get((day,var),{})
        core_row=raw.get((day,'outTemp'),{})
        archive_rows=int(r.get('archive_rows') or core_row.get('archive_rows') or 0)
        n=int(r.get('measured_rows') or 0)
        estimated=est_by_day.get((day,var),0)
        a=changes.get((day,var),{})
        restored=int(a.get('restored_events') or 0); corrected=int(a.get('corrected_events') or 0)
        rawmean=(r.get('circular_mean_direction_deg') or '') if var=='windDir' else (r.get('weighted_mean_value') or r.get('mean_value') or '')
        mins=float(r['min_value']) if var!='windDir' and r.get('min_value') not in ('',None) else None
        maxs=float(r['max_value']) if var!='windDir' and r.get('max_value') not in ('',None) else None
        dn=int(r.get('daytime_measured') or 0); nn=int(r.get('nighttime_measured') or 0)
        exp=expected if day>=first_observed.get(var,day) else 0
        cov=n/exp if exp else 0.0
        dc=dn/max(1,daylight) if exp else 0.0; nc=nn/max(1,exp-daylight) if exp else 0.0
        step=int(float(r.get('max_valid_step_seconds') or 0))
        meanpass=bool(exp and cov>=.95 and dc>=.90 and nc>=.90 and step<=3600)
        extremepass=bool(exp and cov>=.99 and dc>=.98 and nc>=.98 and step<=1800)
        status=('NOT_AVAILABLE_BEFORE_FIRST_OBSERVED_EPOCH' if not exp else ('NO_ARCHIVE_ROWS_SENSOR_EPOCH_VS_UNRESOLVED_GAP' if not archive_rows else ('REVIEW_REQUIRED_ESTIMATED_ROWS_PRESENT' if estimated else ('NOT_REPRESENTATIVE_COVERAGE_OR_GAP' if not meanpass else 'READY_WITH_LIMITATIONS_ORIGIN_UNCLASSIFIED'))))
        if var=='windDir' and n and float(r.get('direction_resultant_length') or 0)<.20:status='REVIEW_REQUIRED_LOW_DIRECTION_CONCENTRATION'
        x={'local_day':day,'variable':var,'unit':UNITS[var],'archive_rows':archive_rows,'raw_nonnull_values':n,'estimated_values_in_archive':estimated,'estimated_share_of_nonnull':f'{estimated/n:.8f}' if n else '', 'restored_events':restored,'corrected_events':corrected,'other_applied_events':max(0,int(a.get('applied_events') or 0)-estimated-restored-corrected),'original_documented_values':0,'unclassified_origin_nonnull':max(0,n-estimated-restored-corrected),'value_mean_current_archive':rawmean,'value_min_current_archive':mins if mins is not None else '', 'value_max_current_archive':maxs if maxs is not None else '', 'value_semantics':('TIME_WEIGHTED_CIRCULAR_DIRECTION_MEAN; MIN/MAX_NOT_APPLICABLE' if var=='windDir' and n else ('CURRENT_ARCHIVE_RAW; ESTIMATES NOT REMOVED' if n else '')),'direction_resultant_length':r.get('direction_resultant_length','') if var=='windDir' else '', 'daytime_nonnull_06_18':dn,'nighttime_nonnull_18_06':nn,'expected_5min_slots_operating_epoch':exp,'coverage_ratio':f'{cov:.8f}' if exp else '', 'day_coverage_ratio':f'{dc:.8f}' if exp else '', 'night_coverage_ratio':f'{nc:.8f}' if exp else '', 'max_valid_step_seconds':step,'daily_mean_sampling_rule_pass':meanpass,'daily_extrema_sampling_rule_pass':False if var=='windDir' else extremepass,'daily_mean_status':status if d!=last else 'PARTIAL_CURRENT_DAY','daily_extrema_status':('NOT_APPLICABLE_CIRCULAR_DIRECTION' if var=='windDir' else ('REVIEW_REQUIRED_ESTIMATED_ROWS_PRESENT' if estimated else ('READY_WITH_LIMITATIONS_ORIGIN_UNCLASSIFIED' if extremepass else 'NOT_REPRESENTATIVE_COVERAGE_OR_GAP')) if archive_rows else 'NO_ARCHIVE_ROWS_SENSOR_EPOCH_VS_UNRESOLVED_GAP'),'limitations':'Exact source lineage for target rows is not fully known; estimated values remain in current-archive mean/extrema; cadence is assessed against nominal 5-minute slots.'}
        daily.append(x);day_index[(day,var)]=x
    d+=dt.timedelta(days=1)

# period values are time-weighted from daily exports when interval weights exist;
# otherwise daily means are weighted by measured slot counts and flagged accordingly.
def summarize(label, items, kind):
    rows=[x for x in items if x['expected_5min_slots_operating_epoch']>0]
    n=sum(x['raw_nonnull_values'] for x in rows); expected=sum(x['expected_5min_slots_operating_epoch'] for x in rows)
    est=sum(x['estimated_values_in_archive'] for x in rows); rest=sum(x['restored_events'] for x in rows); corr=sum(x['corrected_events'] for x in rows)
    coverage=n/expected if expected else 0
    means=[]; weights=[]
    for x in rows:
        try: val=float(x['value_mean_current_archive'])
        except (ValueError,TypeError): continue
        w=int((direction[x['local_day']].get('valid_interval_minutes') if x['variable']=='windDir' else raw[(x['local_day'],x['variable'])].get('valid_interval_minutes')) or x['raw_nonnull_values'])
        means.append(val);weights.append(w)
    mean=sum(v*w for v,w in zip(means,weights))/sum(weights) if weights and sum(weights) else ''
    direction_resultant=''
    if rows and rows[0]['variable']=='windDir':
        sin_sum=sum(float(direction[x['local_day']]['weighted_sin_component']) for x in rows if x['local_day'] in direction)
        cos_sum=sum(float(direction[x['local_day']]['weighted_cos_component']) for x in rows if x['local_day'] in direction)
        direction_resultant=((sin_sum*sin_sum+cos_sum*cos_sum)**.5)/sum(weights) if sum(weights) else 0
        import math
        mean=(math.degrees(math.atan2(sin_sum,cos_sum))%360) if sum(weights) else ''
    valsmin=[float(x['value_min_current_archive']) for x in rows if x['value_min_current_archive']!=''] if rows and rows[0]['variable']!='windDir' else []
    valsmax=[float(x['value_max_current_archive']) for x in rows if x['value_max_current_archive']!=''] if rows and rows[0]['variable']!='windDir' else []
    daypass=sum(x['daily_mean_sampling_rule_pass'] for x in rows);extpass=sum(x['daily_extrema_sampling_rule_pass'] for x in rows)
    maxstep=max([x['max_valid_step_seconds'] for x in rows] or [0])
    if kind=='monthly':
        mp=coverage>=.95 and daypass/max(1,len(rows))>=.90 and maxstep<=21600
        ep=coverage>=.99 and extpass/max(1,len(rows))>=.95 and maxstep<=1800
    else:
        months=defaultdict(list)
        for x in rows:months[x['local_day'][:7]].append(x)
        def month_pass(g, strict=False):
            month_n=sum(z['raw_nonnull_values'] for z in g)
            month_expected=sum(z['expected_5min_slots_operating_epoch'] for z in g)
            daily_share=sum(z['daily_extrema_sampling_rule_pass'] if strict else z['daily_mean_sampling_rule_pass'] for z in g)/max(1,len(g))
            month_gap=max(z['max_valid_step_seconds'] for z in g)
            cadence_counts={i:c for (m,i),c in cadence.items() if m==g[0]['local_day'][:7]}
            cadence_share=max(cadence_counts.values())/sum(cadence_counts.values()) if cadence_counts else 0
            return (month_n/max(1,month_expected)>=.99 and daily_share>=.95 and month_gap<=1800) if strict else (month_n/max(1,month_expected)>=.95 and daily_share>=.90 and cadence_share>=.90 and month_gap<=21600)
        mp=sum(month_pass(g) for g in months.values())
        ep=sum(month_pass(g,True) for g in months.values())
        mp=coverage>=.95 and mp>=11;ep=coverage>=.99 and ep>=11
    st='REVIEW_REQUIRED_ESTIMATED_ROWS_PRESENT' if est else ('READY_WITH_LIMITATIONS_ORIGIN_UNCLASSIFIED' if mp or ep else 'NOT_REPRESENTATIVE_COVERAGE_OR_GAP')
    monthkey=label.split(':',1)[0]
    hist={i:c for (m,i),c in cadence.items() if m==monthkey} if kind=='monthly' else {}
    modal=max(hist,key=hist.get) if hist else ''
    cadence_share=(hist[modal]/sum(hist.values())) if hist and modal else ''
    if kind=='monthly':
        mp=mp and cadence_share>=.90
    return {'period':monthkey,'variable':rows[0]['variable'] if rows else '', 'unit':rows[0]['unit'] if rows else '', 'days_in_observed_epoch':len(rows),'expected_5min_slots_operating_epoch':expected,'raw_nonnull_values':n,'estimated_values_in_archive':est,'estimated_share_of_nonnull':f'{est/n:.8f}' if n else '', 'restored_events':rest,'corrected_events':corr,'other_applied_events':sum(x['other_applied_events'] for x in rows),'original_documented_values':0,'unclassified_origin_nonnull':max(0,n-est-rest-corr),'coverage_ratio':f'{coverage:.8f}' if expected else '', 'value_mean_current_archive':mean,'value_min_current_archive':min(valsmin) if valsmin else '', 'value_max_current_archive':max(valsmax) if valsmax else '', 'direction_resultant_length':f'{direction_resultant:.8f}' if direction_resultant!='' else '', 'value_semantics':('TIME_WEIGHTED_CIRCULAR_DIRECTION_MEAN; MIN/MAX_NOT_APPLICABLE' if rows and rows[0]['variable']=='windDir' else 'CURRENT_ARCHIVE_RAW; ESTIMATES NOT REMOVED'),'days_pass_daily_mean_rule':daypass,'days_pass_daily_extrema_rule':extpass,'max_valid_step_seconds':maxstep,'modal_interval_minutes':modal,'modal_cadence_share':f'{cadence_share:.8f}' if cadence_share!='' else '', 'months_pass_mean_rule':mp if kind=='annual' else '', 'months_pass_extrema_rule':ep if kind=='annual' else '', 'mean_sampling_rule_pass':mp,'extrema_sampling_rule_pass':False if rows and rows[0]['variable']=='windDir' else ep,'status':('REVIEW_REQUIRED_LOW_DIRECTION_CONCENTRATION' if direction_resultant!='' and direction_resultant<.20 else ('REVIEW_REQUIRED_CIRCULAR_ORIGIN_UNCLASSIFIED' if rows and rows[0]['variable']=='windDir' and mp else ('NOT_REPRESENTATIVE_COVERAGE_OR_GAP' if rows and rows[0]['variable']=='windDir' else st))),'limitations':'Thresholds are project screens, not an official climate standard. Estimates remain included in values; full target-row original provenance is unknown.'}

monthly=defaultdict(list); annual=defaultdict(list)
for x in daily:
    if x['expected_5min_slots_operating_epoch']>0:
        monthly[(x['local_day'][:7],x['variable'])].append(x)
        annual[(x['local_day'][:4],x['variable'])].append(x)
monthrows=[summarize(f'{period}:{var}',v,'monthly') for (period,var),v in sorted(monthly.items())]
yearrows=[summarize(f'{period}:{var}',v,'annual') for (period,var),v in sorted(annual.items())]
# Q1 2018 is explicitly protected; 2021 is diagnostic only; current 2026 year/month partial.
for x in monthrows:
    if x['period'] in ('2018-01','2018-02','2018-03'):x['status']='PROTECTED_Q1_2018_REVIEW_REQUIRED'
    if x['period'].startswith('2021-'):x['status']='DIAGNOSTIC_2021_NO_PRODUCTION_DECISION'
    if x['period']=='2026-10':x['status']='PARTIAL_CURRENT_MONTH_NOT_CERTIFIABLE'
for x in yearrows:
    if x['period']=='2021':x['status']='DIAGNOSTIC_2021_NO_PRODUCTION_DECISION'
    if x['period']=='2018':x['status']='REVIEW_REQUIRED_Q1_2018_PROTECTED_SUBPERIOD'
    if x['period']=='2009':x['status']='PARTIAL_FIRST_OBSERVED_YEAR_NOT_CERTIFIABLE'
    if x['period']=='2026':x['status']='PARTIAL_YEAR_NOT_CERTIFIABLE'

def write(name,rows):
    p=ROOT/'data'/name
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
write('DAILY_STATISTICAL_COVERAGE.csv',daily)
write('MONTHLY_STATISTICAL_READINESS.csv',monthrows)
write('ANNUAL_STATISTICAL_READINESS.csv',yearrows)
(ROOT/'data/STATISTICAL_READINESS_API.json').write_text(json.dumps({'archive_coverage_through_local':'2026-10-29','snapshot_date':'2026-11-14','timezone':'Europe/Prague','variables':list(VARS),'units':UNITS,'method':'Current archive values; estimated rows counted but not excluded, therefore estimate-contaminated groups are review-only.','daily':daily,'monthly':monthrows,'annual':yearrows},ensure_ascii=False,separators=(',',':'))+'\n')
print(f'daily={len(daily)} monthly={len(monthrows)} annual={len(yearrows)} estimate_keys={len(estimates)}')
