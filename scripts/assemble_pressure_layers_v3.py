#!/usr/bin/env python3
"""Assemble three non-coalesced pressure layers and audit support/statistics/joins."""
import argparse,csv,gzip,hashlib,json,statistics
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

def load_rows(path,key='dateTime_utc'):
 with path.open(newline='') as f:return {int(r[key]):r for r in csv.DictReader(f)}
def accum(store,period,layer,value):
 if value is None:return
 a=store[(period,layer)];a['n']+=1;a['sum']+=value;a['sum_sq']+=value*value;a['min']=value if a['min'] is None else min(a['min'],value);a['max']=value if a['max'] is None else max(a['max'],value)
def finish(a):
 if not a['n']:return {'n':0,'mean_hpa':None,'sd_hpa':None,'min_hpa':None,'max_hpa':None}
 m=a['sum']/a['n'];return {'n':a['n'],'mean_hpa':m,'sd_hpa':max(0,a['sum_sq']/a['n']-m*m)**.5,'min_hpa':a['min'],'max_hpa':a['max']}
def decision_period(t):
 d=datetime.fromtimestamp(t,timezone.utc);y=d.year
 if y<=2015:return '2009-2015'
 if y<=2017:return '2016-2017'
 if y==2018:return '2018 (Q1 protected)'
 if y==2019:return '2019-pre-2019-04-26T1445Z' if t<int(datetime(2019,4,26,14,45,tzinfo=timezone.utc).timestamp()) else '2019-post-2019-04-26T1445Z'
 if y<=2022:return '2020-2022'
 if y<=2025:return '2023-2025'
 return '2026 partial'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--archive-candidates',type=Path,required=True);ap.add_argument('--superseded-candidates',type=Path,required=True);ap.add_argument('--physical-series',type=Path,required=True);ap.add_argument('--physical-manifest',type=Path,required=True);ap.add_argument('--era5-hourly',type=Path,required=True);ap.add_argument('--daily-check',type=Path,required=True);ap.add_argument('--hybrid-check',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);a=ap.parse_args()
 candidates=load_rows(a.archive_candidates);old=load_rows(a.superseded_candidates);era={}
 with gzip.open(a.era5_hourly,'rt',newline='') as f:
  for r in csv.DictReader(f):era[int(r['dateTime_utc'])]=r
 daily_check=json.loads(a.daily_check.read_text());daily_year=daily_check['annual_daily_checks'];physical_manifest=json.loads(a.physical_manifest.read_text());hybrid=json.loads(a.hybrid_check.read_text());physical_file=gzip.open(a.physical_series,'rt',newline='');physical_reader=csv.DictReader(physical_file)
 out=a.out_dir;out.mkdir(parents=True,exist_ok=True);catalog=out/'pressure-layers-three-way-v1.csv.gz'
 sums=defaultdict(lambda:{'n':0,'sum':0.0,'sum_sq':0.0,'min':None,'max':None});jumps=defaultdict(lambda:{'n_steps':0,'max_abs_step_hpa':0.0,'steps_abs_gt_2_hpa':0,'steps_abs_gt_3_hpa':0});prev={};coalesced_jumps=[];coalesced_by_year=defaultdict(list);counts=defaultdict(lambda:defaultdict(int));support=defaultdict(lambda:defaultdict(int));decision_counts=defaultdict(lambda:defaultdict(int));q1a=int(datetime(2018,1,1,tzinfo=timezone.utc).timestamp());q1b=int(datetime(2018,4,1,tzinfo=timezone.utc).timestamp());rows=0
 try:
  with a.archive.open(newline='') as src,gzip.open(catalog,'wt',newline='') as dst:
   sr=csv.DictReader(src);w=csv.writer(dst);w.writerow(['dateTime_utc','original_pressure_hpa','original_status','archive_reconstruction_hpa','archive_reconstruction_status','archive_reconstruction_empirical_p95_hpa','superseded_legacy_v3_hpa','superseded_legacy_status','regional_reference_diagnostic_hpa','regional_estimate_hpa','regional_resolution_seconds','regional_source','regional_decision_status','regional_interstation_disagreement_p95_hpa_not_prediction_interval','regional_daily_check_p95_abs_hpa_diagnostic','reference_support','physical_temperature_source'])
   for s,p in zip(sr,physical_reader):
    t=int(s['dateTime_utc']);pt=int(p['dateTime_utc'])
    if t!=pt:raise ValueError(f'row timestamp mismatch: archive {t}, physical {pt}')
    rows+=1;dt=datetime.fromtimestamp(t,timezone.utc);y=dt.year;day=dt.strftime('%Y-%m-%d');month=dt.strftime('%Y-%m');yr=str(y);period=decision_period(t);q1=q1a<=t<q1b
    original=None if s['pressure_hpa']=='' else float(s['pressure_hpa']);c=candidates.get(t);oldc=old.get(t)
    archive_est=float(c['estimated_pressure_hpa']) if c else None
    archive_unc=float(c['empirical_uncertainty_p95_hpa']) if c and c.get('empirical_uncertainty_p95_hpa') else None
    era_row=era.get(t) if y<=2017 else None
    chmi_ref=None if q1 or p['chmi_reference_mean_hpa']=='' else float(p['chmi_reference_mean_hpa'])
    if era_row:regional_ref=float(era_row['physical_pressure_hpa_425m']);resolution=3600;source='ERA5_HOURLY_PHYSICAL_REANALYSIS';ref_support='EXACT_ERA5_HOUR'
    elif chmi_ref is not None:
     regional_ref=chmi_ref;source='CHMI_10MIN_TRANSFERRED_REFERENCE';ref_support=p['chmi_reference_support']
     spans=[int(token.split('_')[-1][:-1]) for token in ref_support.split(';') if 'LINEAR' in token];resolution=max(spans) if spans else 600
    else:regional_ref=None;resolution=None;source='';ref_support=''
    physical_est=None;decision='NO_REGIONAL_ESTIMATE'
    if q1:decision='PROTECTED_Q1_2018'
    elif original is not None:decision='EXISTING_SOURCE_VALUE_UNCALIBRATED'
    elif y<=2017 and era_row and daily_year.get(yr,{}).get('regional_daily_context_screen_pass'):
     physical_est=regional_ref;decision='ESTIMATED_UNAPPROVED_HOURLY_ERA5'
    elif p['regional_physical_estimate_hpa']:
     physical_est=float(p['regional_physical_estimate_hpa']);decision='ESTIMATED_UNAPPROVED_CHMI_REFERENCE'
    elif c:decision='CORRECTED_ARCHIVE_REPRODUCTION_ONLY'
    elif oldc:decision='UNRESOLVED_SUPERSEDED_VALUE_REJECTED'
    else:decision='UNRESOLVED'
    era_daily_p95=(daily_year.get(yr,{}).get('p95_abs_hpa') if y<=2017 else None)
    interstation_metric='' if q1 or not p['interstation_disagreement_p95_hpa_not_prediction_interval'] else p['interstation_disagreement_p95_hpa_not_prediction_interval']
    w.writerow([t,'' if original is None else f'{original:.5f}','EXISTING_SOURCE_NOT_CALIBRATION' if original is not None else '', '' if archive_est is None else f'{archive_est:.4f}','ESTIMATED_UNAPPROVED' if c else '', '' if archive_unc is None else f'{archive_unc:.4f}',oldc['estimated_pressure_hpa'] if oldc else '', 'SUPERSEDED_NOT_FOR_USE' if oldc else '', '' if regional_ref is None else f'{regional_ref:.4f}', '' if physical_est is None else f'{physical_est:.4f}',resolution,source,decision,interstation_metric,'' if era_daily_p95 is None else era_daily_p95,ref_support,p['transport_temperature_source']])
    if original is not None:counts[yr]['original_nonnull']+=1
    else:
     counts[yr]['original_null']+=1
     if q1:counts[yr]['protected_q1_2018']+=1
     elif decision=='ESTIMATED_UNAPPROVED_HOURLY_ERA5':counts[yr]['regional_hourly_estimates']+=1
     elif decision=='ESTIMATED_UNAPPROVED_CHMI_REFERENCE':counts[yr]['regional_chmi_estimates']+=1
     elif decision=='CORRECTED_ARCHIVE_REPRODUCTION_ONLY':counts[yr]['corrected_archive_only']+=1
     elif decision=='UNRESOLVED_SUPERSEDED_VALUE_REJECTED':counts[yr]['unresolved_superseded_legacy']+=1
     else:counts[yr]['unresolved']+=1
    if oldc:counts[yr]['superseded_legacy_values_retained_diagnostic_only']+=1
    if p['transport_temperature_source']=='local outTemp':counts[yr]['transport_temperature_local_outTemp']+=1
    elif p['transport_temperature_source']=='ERA5 2m temperature':counts[yr]['transport_temperature_era5_fallback']+=1
    else:counts[yr]['transport_temperature_unavailable']+=1
    if oldc and not c:decision_counts[period]['superseded_legacy_candidates_rejected']+=1
    if original is None:
     if q1:decision_counts[period]['protected_q1']+=1
     elif decision.startswith('ESTIMATED_UNAPPROVED'):decision_counts[period]['regional_unapproved_estimates']+=1
     elif decision=='CORRECTED_ARCHIVE_REPRODUCTION_ONLY':decision_counts[period]['corrected_archive_only']+=1
     else:decision_counts[period]['unresolved']+=1
    if p['chmi_reference_support']:
     counts[yr]['chmi_reference_timestamps']+=1
     if 'EXACT_10MIN' in p['chmi_reference_support']:support[yr]['both_stations_exact_10min']+=1
     else:support[yr]['both_station_reference_interpolated']+=1
    # Three independent statistical layers; no value is silently substituted for another.
    layers={'original_archive':original,'corrected_archive_reconstruction':archive_est,'regional_reference_diagnostic':regional_ref}
    for layer,val in layers.items():
     if val is None:continue
     accum(sums,yr,layer,val);accum(sums,month,layer,val);accum(sums,day,layer,val)
     prior=prev.get(layer);step=300 if layer!='regional_reference_diagnostic' or source.startswith('CHMI') else 3600
     if prior and t-prior[0]==step:
      delta=abs(val-prior[1]);st=jumps[(yr,layer)];st['n_steps']+=1;st['max_abs_step_hpa']=max(st['max_abs_step_hpa'],delta);st['steps_abs_gt_2_hpa']+=delta>2;st['steps_abs_gt_3_hpa']+=delta>3
     prev[layer]=(t,val)
    # A diagnostic simulation shows why these layers must not be coalesced across a drift.
    coalesced=original if original is not None else physical_est
    if coalesced is not None:
     pp=prev.get('naive_coalesced')
     if pp and t-pp[0]==300:
      jump=abs(coalesced-pp[1]);coalesced_jumps.append(jump);coalesced_by_year[yr].append(jump)
     prev['naive_coalesced']=(t,coalesced)
   if next(physical_reader,None) is not None:raise ValueError('physical series has extra rows beyond archive')
 except Exception:
  physical_file.close();raise
 physical_file.close()
 day_rows=[];month_rows=[];annual_rows=[]
 for (period,layer),acc in sorted(sums.items()):
  result={'period':period,'layer':layer,**finish(acc)}
  if len(period)==10:day_rows.append(result)
  elif len(period)==7:month_rows.append(result)
  elif len(period)==4:annual_rows.append(result)
 q1_estimate_count=0
 # The source archive is NULL-only in protected Q1; count was enforced while writing.
 # Re-open only the protected quarter to verify no layer estimate leaked in.
 with gzip.open(catalog,'rt',newline='') as f:
  rr=csv.DictReader(f)
  for r in rr:
   t=int(r['dateTime_utc'])
   if t<q1a: continue
   if t>=q1b: break
   if r['archive_reconstruction_hpa'] or r['regional_estimate_hpa']:q1_estimate_count+=1
 go_no_go=[]
 for period,c in sorted(decision_counts.items()):
  years=range(2009,2016) if period=='2009-2015' else range(2016,2018) if period=='2016-2017' else []
  if period=='2019-pre-2019-04-26T1445Z':keys=['2019-pre-2019-04-26T1445Z']
  elif period=='2019-post-2019-04-26T1445Z':keys=['2019-post-2019-04-26T1445Z']
  elif period=='2020-2022':keys=[str(y) for y in range(2020,2023)]
  elif period=='2023-2025':keys=[str(y) for y in range(2023,2026)]
  elif period=='2026 partial':keys=[]
  else:keys=[str(y) for y in years]
  if years:
   daily_pass=all(daily_year.get(str(y),{}).get('regional_daily_context_screen_pass',False) for y in years)
   regional_go='GO_SEPARATE_HOURLY_ERA5_DAILY_CONTEXT_ONLY' if daily_pass else 'NO_GO_ERA5_DAILY_CONTEXT_GATE'
   accuracy={str(y):{k:daily_year.get(str(y),{}).get(k) for k in ('matched_quality_zero_daily_values_with_complete_era5_days','mae_hpa','median_bias_hpa','p95_abs_hpa','daily_coverage')} for y in years}
  elif period=='2018 (Q1 protected)':
   gate=physical_manifest['epoch_validation'].get('2018',{}).get('regional_consistency_screen_pass',False);regional_go='GO_CHMI_REGIONAL_LAYER_DIAGNOSTIC' if gate else 'NO_GO_CHMI_REGIONAL_CONSISTENCY';accuracy=physical_manifest['epoch_validation'].get('2018',{})
  elif period.startswith('2019-'):
   gate=physical_manifest['epoch_validation'].get(keys[0],{}).get('regional_consistency_screen_pass',False);regional_go='GO_CHMI_REGIONAL_LAYER_DIAGNOSTIC' if gate else 'NO_GO_CHMI_REGIONAL_CONSISTENCY';accuracy=physical_manifest['epoch_validation'].get(keys[0],{})
  elif keys:
   gate=all(physical_manifest['epoch_validation'].get(y,{}).get('regional_consistency_screen_pass',False) for y in keys);regional_go='GO_CHMI_REGIONAL_LAYER_DIAGNOSTIC' if gate else 'NO_GO_CHMI_REGIONAL_CONSISTENCY';accuracy={y:physical_manifest['epoch_validation'].get(y,{}) for y in keys}
  else:regional_go='NO_GO_NO_2026_CHMI10_REFERENCE';accuracy={}
  go_no_go.append({'period':period,**dict(c),'go_for_separate_diagnostic_layer':regional_go,'validation_summary':accuracy,'database_replacement':'NO_GO_UNAPPROVED_NO_INDEPENDENT_LOUCKA_ABSOLUTE_CALIBRATION'})
 manifest={'schema':'pressure-three-layer-release-v1','state':'DIAGNOSTIC_ONLY_NO_APPLY','rows':rows,'source_archive_sha256':hashlib.sha256(a.archive.read_bytes()).hexdigest(),'corrected_archive_candidate_sha256':hashlib.sha256(a.archive_candidates.read_bytes()).hexdigest(),'superseded_legacy_candidate_sha256':hashlib.sha256(a.superseded_candidates.read_bytes()).hexdigest(),'physical_regional_series_sha256':hashlib.sha256(a.physical_series.read_bytes()).hexdigest(),'era5_hourly_series_sha256':hashlib.sha256(a.era5_hourly.read_bytes()).hexdigest(),'daily_chmi_check_sha256':hashlib.sha256(a.daily_check.read_bytes()).hexdigest(),'hybrid_holdout_sha256':hashlib.sha256(a.hybrid_check.read_bytes()).hexdigest(),'three_layer_catalog_sha256':hashlib.sha256(catalog.read_bytes()).hexdigest(),'q1_2018_estimate_rows':q1_estimate_count,'annual_counts':{k:dict(v) for k,v in sorted(counts.items())},'chmi_reference_support_counts':{k:dict(v) for k,v in sorted(support.items())},'annual_jump_checks':{f'{k[0]}|{k[1]}':v for k,v in sorted(jumps.items())},'daily_statistics_by_layer':day_rows,'monthly_statistics_by_layer':month_rows,'annual_statistics_by_layer':annual_rows,'decision_table_by_epoch':go_no_go,'hybrid_model_decision':{'status':'NO_GO_FOR_LAYER_USE' if hybrid['hybrid_increment_error']['mae_hpa']>hybrid['baseline_simple_interpolation_increment_error']['mae_hpa'] else 'GO_FOR_DIAGNOSTIC_TEST_ONLY','n':hybrid['n_targets'],'baseline_increment_mae_hpa':hybrid['baseline_simple_interpolation_increment_error']['mae_hpa'],'hybrid_increment_mae_hpa':hybrid['hybrid_increment_error']['mae_hpa'],'relative_mae_change':hybrid['hybrid_increment_mae_relative_change']},'naive_coalesced_layer_adjacent_steps':{'n':len(coalesced_jumps),'max_abs_step_hpa':max(coalesced_jumps) if coalesced_jumps else None,'p95_abs_step_hpa':sorted(coalesced_jumps)[int(.95*(len(coalesced_jumps)-1))] if coalesced_jumps else None,'steps_abs_gt_3_hpa':sum(x>3 for x in coalesced_jumps),'by_year':{y:{'n_steps':len(v),'max_abs_step_hpa':max(v),'p95_abs_step_hpa':sorted(v)[int(.95*(len(v)-1))],'steps_abs_gt_2_hpa':sum(x>2 for x in v),'steps_abs_gt_3_hpa':sum(x>3 for x in v)} for y,v in sorted(coalesced_by_year.items())},'decision':'diagnostic only; no coalesced output is emitted'},'known_boundaries_not_spliced':['2017-12-31/2018-01-01 ERA5 hourly to CHMI reference transition','2019-04-26T14:45:00Z local-source change','Q1 2018 protected; proposed values blank'],'layer_semantics':{'original_archive':'unaltered source values; non-NULL values are not thereby declared physically calibrated','corrected_archive_reconstruction':'corrected-QC V3 estimates reproducing the historical archive relationship; all unapproved','regional_reference_diagnostic':'ERA5 exact hourly at 2009-2017 support; CHMI transferred quality-0 references at 2018+ support; never silently merged with source layer','uncertainty':'interstation disagreement P95 and daily validation P95 are diagnostics, not calibrated per-row prediction intervals'},'limitations':['ERA5 hourly values are not independently verified at hourly support by daily CHMI checks.','CHMI station agreement does not independently validate absolute Loucka pressure.','Hybrid local-increment model failed the held-out increment comparison and is not used.']}
 (out/'pressure-three-layer-manifest-v1.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
 for path,items in ((out/'pressure-daily-layer-statistics-v1.csv',day_rows),(out/'pressure-monthly-layer-statistics-v1.csv',month_rows)):
  with path.open('w',newline='') as f:
   fields=list(items[0]) if items else ['period','layer','n','mean_hpa','sd_hpa','min_hpa','max_hpa'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(items)
 print(json.dumps({'rows':rows,'q1_estimates':q1_estimate_count,'catalog_sha256':manifest['three_layer_catalog_sha256'],'naive_steps':manifest['naive_coalesced_layer_adjacent_steps']}))
if __name__=='__main__':main()
