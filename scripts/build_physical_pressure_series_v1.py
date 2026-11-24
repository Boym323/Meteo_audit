#!/usr/bin/env python3
"""Build a separate physically anchored pressure shadow and epoch decision ledger."""
import argparse,csv,gzip,hashlib,json,math,statistics
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
  return '2019-pre-2019-04-26' if d.strftime('%Y-%m-%d')<'2019-04-26' else '2019-post-2019-04-26'
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
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--chmi10',type=Path,required=True);ap.add_argument('--era5',type=Path,required=True);ap.add_argument('--legacy-candidates',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);a=ap.parse_args()
 chmi,chhash=load_chmi(a.chmi10);era,elev,ehash=load_era5(a.era5)
 era_points=era['loucka_era5_nearest'];era_t=(sorted(era_points),[era_points[t][1] for t in sorted(era_points)])
 # Independent station-to-station holdout: each station is input alone while the other is truth.
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
 # Cross-station gate preserves strict existing V2 limits; validation is regional transfer
 # only, not a claim that Loucka's historic sensor was independently calibrated.
 gate={'minimum_pairs':1000,'maximum_mae_hpa':2.0,'maximum_p95_abs_hpa':4.0,'maximum_abs_median_bias_hpa':1.5}
 epoch_validation={}
 for y,g in sorted(annual.items()):
  hm=metrics(g['h_to_m']);mh=metrics(g['m_to_h'])
  def pass_gate(m):return m['n']>=gate['minimum_pairs'] and m['mae_hpa']<=gate['maximum_mae_hpa'] and m['p95_abs_hpa']<=gate['maximum_p95_abs_hpa'] and abs(m['bias_hpa'])<=gate['maximum_abs_median_bias_hpa']
  passed=pass_gate(hm) and pass_gate(mh)
  epoch_validation[str(y)]={'independent_leave_one_station_out':{'H_input_predicts_M':hm,'M_input_predicts_H':mh},'matched_10min_targets':g['targets'],'local_pressure_level_minus_CHMI_transferred_mean':metrics(g['local_level_errors']),'local_pressure_change_vs_CHMI_delta':metrics(g['local_delta_errors']),'corrected_ERA5_vs_two_station_mean':metrics(g['era5_errors']),'regional_transfer_gate':gate,'regional_transfer_gate_pass':passed,'scope':'both directional station transfers must pass; regional cross-station check does not validate local absolute sensor/field'}
 # Candidate row source data; direct 10-minute CHMI mean is the physical anchor.
 legacy={}
 with a.legacy_candidates.open(newline='') as f:
  for r in csv.DictReader(f):legacy[int(r['dateTime_utc'])]=r
 out=a.out_dir;out.mkdir(parents=True,exist_ok=True);rows=[];decisions=defaultdict(lambda:defaultdict(int))
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
   legacy_row=legacy.get(t);legacy_val=legacy_row['estimated_pressure_hpa'] if legacy_row else ''
   if orig:
    category='MEASURED_SOURCE';physical='';state='SOURCE'
   elif q1a<=t<q1b:
    category='PROTECTED_Q1_2018';physical='';state='PROTECTED'
   elif candidate is not None and epoch_validation.get(ek,{}).get('regional_transfer_gate_pass'):
    category='PHYSICALLY_VALIDATED_REGIONAL_REFERENCE';physical=f'{candidate:.4f}';state='ESTIMATED_UNAPPROVED'
   elif legacy_row:
    category='ARCHIVE_REPRODUCTION_ONLY';physical='';state='UNAPPROVED'
   else:
    category='UNRESOLVED';physical='';state='UNRESOLVED'
   if not orig and not q1a<=t<q1b:decisions[label][category]+=1
   validation=epoch_validation.get(ek,{})
   uncertainty=max(validation.get('independent_leave_one_station_out',{}).get(k,{}).get('p95_abs_hpa') or 0 for k in ('H_input_predicts_M','M_input_predicts_H')) if validation else None
   precision='REGIONAL_CROSS_STATION_P95_UNAPPROVED' if physical else ('ERA5_HOURLY_DIAGNOSTIC_ONLY' if e is not None else 'UNRESOLVED')
   rows.append([t,orig,physical,'' if not physical else f'{uncertainty:.4f}',precision,category,state,'' if hc is None else f'{hc:.4f}','' if mc is None else f'{mc:.4f}','' if e is None else f'{e:.4f}',legacy_val, '' if candidate is None else f'{candidate:.4f}', 'local outTemp' if rawtemp is not None and valid_temperature(rawtemp) else ('ERA5 2m temperature' if temp is not None else ''), 'ERA5 hourly; corrected hypsometric sign' if e is not None else '', 'ČHMÚ 10min P, quality 0; pressure transported station height to Loučka 425m' if candidate is not None else ''])
 series=out/'pressure-series-physical-calibrated-v1.csv.gz'
 with gzip.open(series,'wt',newline='') as f:
  w=csv.writer(f);w.writerow(['dateTime_utc','original_pressure_hpa','physical_estimate_hpa','physical_uncertainty_p95_hpa','precision_class','decision_class','approval_status','chmi_holesov_transferred_hpa','chmi_mosnov_transferred_hpa','era5_corrected_hpa_diagnostic','legacy_v3_archive_replica_hpa','chmi_reference_mean_hpa','transport_temperature_source','era5_method','chmi_method']);w.writerows(rows)
 table=[]
 for label,counts in sorted(decisions.items()):table.append({'period':label,'physically_validated_estimates':counts['PHYSICALLY_VALIDATED_REGIONAL_REFERENCE'],'archive_reproducing_only':counts['ARCHIVE_REPRODUCTION_ONLY'],'unresolved':counts['UNRESOLVED'],'basis':'epoch-specific independent leave-one-station-out regional transfer gate; counts exclude measured rows and protected Q1 2018'})
 manifest={'schema':'pressure-physical-calibrated-shadow-v1','state':'ESTIMATES_UNAPPROVED_NO_APPLY','rows':len(rows),'archive_sha256':hashlib.sha256(a.archive.read_bytes()).hexdigest(),'chmi10_manifest_sha256':chhash,'era5_manifest_sha256':ehash,'legacy_v3_candidate_sha256':hashlib.sha256(a.legacy_candidates.read_bytes()).hexdigest(),'series_sha256':hashlib.sha256(series.read_bytes()).hexdigest(),'mosnov_height_epoch':{'250.4_m':'through 2016-05-23','252.8_m':'from 2016-05-24'},'era5_transport':'corrected: p_target=p_source*exp(g*(z_source-z_target)/(Rd*T))','chmi_method':'quality-0 10-minute station pressure linearly interpolated only across spans <=20 minutes; each station pressure transported separately to 425m then station estimates averaged','era5_and_local_change_role':'corrected ERA5 and archive local pressure changes are independent diagnostics; neither silently calibrates the absolute candidate level','epoch_validation':epoch_validation,'decision_table':table,'limitations':['Regional leave-one-station-out skill does not prove Loucka sensor absolute calibration.','2016-2017 has no 10-minute CHMI pressure reference; daily CHMI context cannot validate individual timestamps, so physical point estimates are withheld.','All numeric estimates remain unapproved; Q1 2018 is protected.']}
 (out/'manifest-physical-v1.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({'rows':len(rows),'decision_table':table,'series_sha256':manifest['series_sha256']}))
def era_predict_for_physical(t,era,elev):
 from backtest_pressure_reconstruction_v3 import era_predict
 return era_predict(t,era,elev)
if __name__=='__main__':main()
