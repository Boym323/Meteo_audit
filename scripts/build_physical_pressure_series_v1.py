#!/usr/bin/env python3
"""Build a separate physically anchored pressure shadow and epoch decision ledger."""
import argparse,csv,gzip,hashlib,json,math,statistics
import bisect
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from backtest_pressure_reconstruction_v3 import load_chmi,load_era5,interp,hypsometric_transport,SITE,HEIGHT,metrics

def year(ts):return datetime.fromtimestamp(ts,timezone.utc).year
def epoch(y):
 if y<=2015:return '2009-2015'
 if y<=2017:return '2016-2017'
 if y==2018:return '2018 (source transition; Q1 protected)'
 if y<=2022:return '2019-2022'
 if y<=2025:return '2023-2025'
 return '2026 partial'
def validation_epoch(t):
 d=datetime.fromtimestamp(t,timezone.utc);y=d.year
 if y==2019:
  change=int(datetime(2019,4,26,14,45,tzinfo=timezone.utc).timestamp())
  return '2019-pre-2019-04-26T1445Z' if t<change else '2019-post-2019-04-26T1445Z'
 return str(y)
def decision_epoch(t):
 d=datetime.fromtimestamp(t,timezone.utc);y=d.year
 if y==2019:return validation_epoch(t)
 if y<=2015:return '2009-2015'
 if y<=2017:return '2016-2017'
 if y==2018:return '2018 (Q1 protected)'
 if y<=2022:return '2020-2022'
 if y<=2025:return '2023-2025'
 return '2026 partial'
def valid_temperature(value):return value is not None and math.isfinite(value) and -40<=value<=45
def interp_support(series,t):
 i=bisect.bisect_left(series[0],t)
 if i<len(series[0]) and series[0][i]==t:return 'EXACT_10MIN'
 if i==0 or i==len(series[0]):return 'UNAVAILABLE'
 return f'LINEAR_INTERPOLATION_{series[0][i]-series[0][i-1]}S'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--chmi10',type=Path,required=True);ap.add_argument('--era5',type=Path,required=True);ap.add_argument('--archive-candidates',type=Path,required=True);ap.add_argument('--superseded-candidates',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);a=ap.parse_args()
 chmi,chhash=load_chmi(a.chmi10);era,elev,ehash=load_era5(a.era5)
 era_points=era['loucka_era5_nearest'];era_t=(sorted(era_points),[era_points[t][1] for t in sorted(era_points)])
 # Pairwise same-time station disagreement is a regional-consistency diagnostic,
 # not independent validation of a blended estimate or a local prediction interval.
 annual=defaultdict(lambda:{'h_to_m':[],'m_to_h':[],'targets':0,'common':0,'local_delta_errors':[],'era5_errors':[],'local_level_errors':[]})
 with a.archive.open(newline='') as f:
  local={int(r['dateTime_utc']):r for r in csv.DictReader(f)}
 common=sorted(set(chmi['H'][0]).intersection(chmi['M'][0]))
 for t in common:
  y=year(t);ek=validation_epoch(t);r=local.get(t)
  if not r or not r['outTemp_c']:continue
  rawtemp=float(r['outTemp_c']) if r['outTemp_c'] else None
  temp=rawtemp if valid_temperature(rawtemp) else interp(era_t,t,7200)
  if not valid_temperature(temp):continue
  obs={}
  for station in ('H','M'):
   p=interp(chmi[station],t,600)
   if p is not None:obs[station]=hypsometric_transport(p,temp,HEIGHT[station],SITE)
  if len(obs)==2:
   g=annual[ek];g['targets']+=1
   g['h_to_m'].append(obs['H']-obs['M'])
   g['m_to_h'].append(obs['M']-obs['H'])
   if r['pressure_hpa']:
    g['local_level_errors'].append(float(r['pressure_hpa'])-statistics.fmean(obs.values()))
   if r['pressure_hpa']:
    # Compare local five-minute changes to reference changes over the same step;
    # level offsets cancel, so this diagnoses trend behavior rather than calibration.
    prev=local.get(t-600)
    ref_prev=interp(chmi['H'],t-600,1200)
    if prev and prev['pressure_hpa'] and ref_prev is not None:
     prevtemp=float(prev['outTemp_c']) if prev['outTemp_c'] else None
     if not valid_temperature(prevtemp):prevtemp=interp(era_t,t-600,7200)
     if valid_temperature(prevtemp):
      chmi_delta=obs['H']-hypsometric_transport(ref_prev,prevtemp,HEIGHT['H'],SITE)
      local_delta=float(r['pressure_hpa'])-float(prev['pressure_hpa'])
      g['local_delta_errors'].append(local_delta-chmi_delta)
  ep=era_predict_for_physical(t,era,elev)
  if ep is not None and len(obs)==2:annual[ek]['era5_errors'].append(ep-statistics.fmean(obs.values()))
 # Preserve the existing numerical limits as a regional consistency screen.
 gate={'minimum_pairs':1000,'maximum_mae_hpa':2.0,'maximum_p95_abs_hpa':4.0,'maximum_abs_median_bias_hpa':1.5}
 epoch_validation={}
 for y,g in sorted(annual.items()):
  hm=metrics(g['h_to_m']);mh=metrics(g['m_to_h'])
  disagreement=metrics(g['h_to_m'])
  passed=(disagreement['n']>=gate['minimum_pairs'] and disagreement['mae_hpa']<=gate['maximum_mae_hpa'] and disagreement['p95_abs_hpa']<=gate['maximum_p95_abs_hpa'] and abs(disagreement['bias_hpa'])<=gate['maximum_abs_median_bias_hpa'])
  epoch_validation[str(y)]={'paired_interstation_disagreement':disagreement,'signed_pair_directions_diagnostic_only':{'H_minus_M':hm,'M_minus_H':mh},'matched_10min_pairs':g['targets'],'local_pressure_level_minus_CHMI_transferred_mean':metrics(g['local_level_errors']),'local_pressure_change_vs_CHMI_delta':metrics(g['local_delta_errors']),'corrected_ERA5_vs_two_station_mean':metrics(g['era5_errors']),'regional_consistency_screen':gate,'regional_consistency_screen_pass':passed,'scope':'one station-pair consistency check; directional residuals are exact sign reversals; not independent evidence or a calibrated local prediction interval'}
 # Corrected QC archive shadow is authoritative. Earlier candidates are only retained
 # in a visibly superseded provenance column and never count as archive estimates.
 archive_candidates={};superseded={}
 with a.archive_candidates.open(newline='') as f:
  for r in csv.DictReader(f):archive_candidates[int(r['dateTime_utc'])]=r
 with a.superseded_candidates.open(newline='') as f:
  for r in csv.DictReader(f):superseded[int(r['dateTime_utc'])]=r
 out=a.out_dir;out.mkdir(parents=True,exist_ok=True);rows=[];decisions=defaultdict(lambda:defaultdict(int));support_annual=defaultdict(lambda:defaultdict(int))
 q1a=int(datetime(2018,1,1,tzinfo=timezone.utc).timestamp());q1b=int(datetime(2018,4,1,tzinfo=timezone.utc).timestamp())
 with a.archive.open(newline='') as f:
  for r in csv.DictReader(f):
   t=int(r['dateTime_utc']);y=year(t);orig=r['pressure_hpa'];label=decision_epoch(t);ek=validation_epoch(t)
   h=interp(chmi['H'],t,1200);m=interp(chmi['M'],t,1200);rawtemp=float(r['outTemp_c']) if r['outTemp_c'] else None;temp=rawtemp if valid_temperature(rawtemp) else interp(era_t,t,7200)
   if not valid_temperature(temp):temp=None
   hc=hypsometric_transport(h,temp,HEIGHT['H'],SITE) if h is not None and temp is not None else None
   mc=hypsometric_transport(m,temp,HEIGHT['M'],SITE) if m is not None and temp is not None else None
   candidate=statistics.fmean((hc,mc)) if hc is not None and mc is not None else None
   e=era_predict_for_physical(t,era,elev)
   archive_row=archive_candidates.get(t);archive_val=archive_row['estimated_pressure_hpa'] if archive_row else ''
   old_row=superseded.get(t);old_val=old_row['estimated_pressure_hpa'] if old_row else ''
   if orig:
    category='MEASURED_SOURCE';physical='';state='SOURCE'
   elif q1a<=t<q1b:
    category='PROTECTED_Q1_2018';physical='';state='PROTECTED'
   elif candidate is not None and epoch_validation.get(ek,{}).get('regional_consistency_screen_pass'):
    category='REGIONAL_REFERENCE_ESTIMATE';physical=f'{candidate:.4f}';state='ESTIMATED_UNAPPROVED'
   elif archive_row:
    category='ARCHIVE_REPRODUCTION_ONLY';physical='';state='UNAPPROVED'
   else:
    category='UNRESOLVED';physical='';state='UNRESOLVED'
   if not orig and not q1a<=t<q1b:decisions[label][category]+=1
   validation=epoch_validation.get(ek,{})
   uncertainty=validation.get('paired_interstation_disagreement',{}).get('p95_abs_hpa') if validation else None
   precision=('INTERSTATION_DISAGREEMENT_P95_NOT_PREDICTION_INTERVAL' if physical else ('ERA5_HOURLY_DIAGNOSTIC_ONLY' if e is not None else 'UNRESOLVED'))
   ref_support=f"H:{interp_support(chmi['H'],t)};M:{interp_support(chmi['M'],t)}" if candidate is not None else ''
   if ref_support and ref_support=='H:EXACT_10MIN;M:EXACT_10MIN':support_annual[y]['exact_10min_both_stations']+=1
   elif ref_support:support_annual[y]['interpolated_both_stations']+=1
   else:support_annual[y]['no_two_station_reference']+=1
   rows.append([t,orig,physical,'' if not physical or uncertainty is None else f'{uncertainty:.4f}',precision,category,state,ref_support,'' if hc is None else f'{hc:.4f}','' if mc is None else f'{mc:.4f}','' if e is None else f'{e:.4f}',archive_val,'CORRECTED_QC_ARCHIVE_ESTIMATE' if archive_row else '',old_val,'SUPERSEDED_NOT_FOR_USE' if old_row else '', '' if candidate is None else f'{candidate:.4f}', 'local outTemp' if rawtemp is not None and valid_temperature(rawtemp) else ('ERA5 2m temperature' if temp is not None else ''), 'ERA5 hourly; corrected hypsometric sign' if e is not None else '', 'ČHMÚ 10min P, quality 0; pressure transported station height to Loučka 425m' if candidate is not None else ''])
 series=out/'pressure-series-physical-calibrated-v1.csv.gz'
 with gzip.open(series,'wt',newline='') as f:
  w=csv.writer(f);w.writerow(['dateTime_utc','original_pressure_hpa','regional_physical_estimate_hpa','interstation_disagreement_p95_hpa_not_prediction_interval','precision_class','decision_class','approval_status','chmi_reference_support','chmi_holesov_transferred_hpa','chmi_mosnov_transferred_hpa','era5_corrected_hpa_diagnostic','corrected_qc_archive_estimate_hpa','corrected_archive_provenance','superseded_legacy_v3_estimate_hpa','superseded_legacy_status','chmi_reference_mean_hpa','transport_temperature_source','era5_method','chmi_method']);w.writerows(rows)
 table=[]
 for label,counts in sorted(decisions.items()):table.append({'period':label,'regional_reference_estimates':counts['REGIONAL_REFERENCE_ESTIMATE'],'corrected_archive_reproduction_only':counts['ARCHIVE_REPRODUCTION_ONLY'],'unresolved':counts['UNRESOLVED'],'basis':'regional consistency screen; excludes measured rows and protected Q1 2018; not local independent validation'})
 manifest={'schema':'pressure-physical-regional-shadow-v2','state':'ESTIMATES_UNAPPROVED_NO_APPLY','rows':len(rows),'archive_sha256':hashlib.sha256(a.archive.read_bytes()).hexdigest(),'chmi10_manifest_sha256':chhash,'era5_manifest_sha256':ehash,'corrected_archive_candidate_sha256':hashlib.sha256(a.archive_candidates.read_bytes()).hexdigest(),'corrected_archive_candidate_rows':len(archive_candidates),'superseded_legacy_candidate_sha256':hashlib.sha256(a.superseded_candidates.read_bytes()).hexdigest(),'superseded_legacy_candidate_rows':len(superseded),'superseded_only_rows_not_in_corrected_catalog':sum(t not in archive_candidates for t in superseded),'series_sha256':hashlib.sha256(series.read_bytes()).hexdigest(),'mosnov_height_epoch':{'250.4_m':'through 2016-05-23','252.8_m':'from 2016-05-24'},'local_source_break_utc':'2019-04-26T14:45:00Z','era5_transport':'corrected: p_target=p_source*exp(g*(z_source-z_target)/(Rd*T))','chmi_method':'quality-0 10-minute station pressure linearly interpolated only across spans <=20 minutes; each station pressure transported separately to 425m then station estimates averaged','uncertainty_semantics':'empirical interstation disagreement P95; not an independent prediction interval or per-row 95% coverage claim','reference_support_semantics':'exact 10-minute timestamp vs linear interpolation bracket span is recorded per row','reference_support_by_year_archive_timestamps':{str(y):dict(v) for y,v in sorted(support_annual.items())},'era5_and_local_change_role':'corrected ERA5 and archive local pressure changes are diagnostics; neither silently calibrates absolute CHMI candidate level','epoch_validation':epoch_validation,'decision_table':table,'limitations':['Station agreement is pairwise regional consistency, not independent local absolute validation.','2016-2017 has no 10-minute CHMI pressure reference; daily CHMI context can only check daily ERA5 means.','Superseded V3 candidate values are retained only as rejected provenance and are excluded from decision counts.','All numeric estimates remain unapproved; Q1 2018 is protected.']}
 (out/'manifest-physical-v1.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({'rows':len(rows),'decision_table':table,'series_sha256':manifest['series_sha256']}))
def era_predict_for_physical(t,era,elev):
 from backtest_pressure_reconstruction_v3 import era_predict
 return era_predict(t,era,elev)
if __name__=='__main__':main()
