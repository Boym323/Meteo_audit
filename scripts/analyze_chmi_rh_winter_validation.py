#!/usr/bin/env python3
"""Summarize official CHMI winter T/RH files against exact-hour Loucka rows.
No training or correction proposal is produced. Quality code 0 only is admitted.
"""
import csv,glob,json,math,statistics
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/chmi-rh-winter-validation/raw'
OUT=ROOT/'reports'
def epoch(dt): return int(datetime.strptime(dt,'%Y-%m-%dT%H:%MZ').replace(tzinfo=timezone.utc).timestamp())
def load_chmi():
 d={}
 quality={}; flags={}
 for f in glob.glob(str(RAW/'*.csv')):
  with open(f,newline='',encoding='utf-8') as h:
   for r in csv.DictReader(h):
    key=(r['STATION'],epoch(r['DT']))
    quality[(r['ELEMENT'],r['QUALITY'])]=quality.get((r['ELEMENT'],r['QUALITY']),0)+1
    flags[(r['ELEMENT'],r['FLAG'])]=flags.get((r['ELEMENT'],r['FLAG']),0)+1
    val=float(r['VALUE']) if r['VALUE'] else None
    rec=d.setdefault(key,{})
    rec[r['ELEMENT']]={'v':val,'quality':r['QUALITY'],'flag':r['FLAG']}
 return d,quality,flags
def pct(v,p):
 if not v:return None
 x=sorted(v); k=(len(x)-1)*p; lo=math.floor(k); hi=math.ceil(k)
 return round(x[lo]+(x[hi]-x[lo])*(k-lo),3)
def stats(errors):
 if not errors:return {'n':0}
 return {'n':len(errors),'bias':round(statistics.mean(errors),3),'mae':round(statistics.mean(map(abs,errors)),3),'rmse':round(math.sqrt(statistics.mean(x*x for x in errors)),3),'p05':pct(errors,.05),'median':pct(errors,.5),'p95':pct(errors,.95)}
def main():
 chmi,qc,flags=load_chmi(); rows=json.loads((ROOT/'data/chmi-rh-winter-validation/loucka_hourly_complete_cases.json').read_text())
 bytime={int(r['dateTime']):r for r in rows}
 stations={'0-203-0-11777':'Vizovice','0-203-0-11778':'Kladna-Zilin'}
 # 10-minute official values, paired station intercomparison
 station_rows=[]
 for y in (2019,2020,2021,2022):
  for regime,cond in [('all',lambda t,h:True),('frost_t_le_0',lambda t,h:t is not None and t<=0),('high_rh_ge_95',lambda t,h:h is not None and h>=95),('frost_and_high_rh',lambda t,h:t is not None and t<=0 and h is not None and h>=95)]:
   ts=[]; hs=[]; pair=0; frost=0; fog=0
   for (sid,ep),rec in chmi.items():
    if datetime.fromtimestamp(ep,timezone.utc).year!=y:continue
    T=rec.get('T',{}); H=rec.get('H',{})
    if T.get('quality')!='0.0' or H.get('quality')!='0.0' or T.get('v') is None or H.get('v') is None:continue
    if not cond(T['v'],H['v']):continue
    if sid=='0-203-0-11777':ts.append(T['v']);hs.append(H['v'])
   for ep in set(e for (sid,e) in chmi if sid=='0-203-0-11777'):
    a=chmi.get(('0-203-0-11777',ep),{});b=chmi.get(('0-203-0-11778',ep),{})
    if datetime.fromtimestamp(ep,timezone.utc).year!=y:continue
    if all(a.get(k,{}).get('quality')=='0.0' and b.get(k,{}).get('quality')=='0.0' and a[k].get('v') is not None and b[k].get('v') is not None for k in ('T','H')):
     if cond(a['T']['v'],a['H']['v']):pair+=1;frost+=a['T']['v']<=0;fog+=a['H']['v']>=95
   station_rows.append({'year':y,'regime':regime,'vizovice_n':len(ts),'vizovice_temp_c_p05_p50_p95':[pct(ts,.05),pct(ts,.5),pct(ts,.95)],'vizovice_rh_pct_p05_p50_p95':[pct(hs,.05),pct(hs,.5),pct(hs,.95)],'paired_station_n':pair})
 # Pair exact-hour local archive with both station observations, requiring CHMI Q=0 and no RH history.
 comparisons=[]
 for y in (2019,2020,2021,2022):
  for sid,name in stations.items():
   for regime in ('all','frost_local_t_le_0','local_rh_ge_95','frost_and_local_rh_ge_95'):
    local=[];luha=[]
    for ep,r in bytime.items():
     if datetime.fromtimestamp(ep,timezone.utc).year!=y:continue
     c=chmi.get((sid,ep));
     if not c or any(c.get(k,{}).get('quality')!='0.0' or c.get(k,{}).get('v') is None for k in ('T','H')):continue
     lt=r.get('outTemp');lr=r.get('outHumidity');lh=r.get('luhamet_rh')
     def passes():
      if regime=='frost_local_t_le_0':return lt is not None and lt<=0
      if regime=='local_rh_ge_95':return lr is not None and lr>=95
      if regime=='frost_and_local_rh_ge_95':return lt is not None and lt<=0 and lr is not None and lr>=95
      return True
     if not passes():continue
     if lr is not None and not r.get('rh_has_history'):
      local.append((lr-c['H']['v'],lt-c['T']['v'] if lt is not None else None))
     if lh is not None and r.get('quality_status')=='reference_only' and r.get('source_resolution')=='5min':luha.append(lh-c['H']['v'])
    rherr=[x[0] for x in local];terr=[x[1] for x in local if x[1] is not None]
    comparisons.append({'year':y,'station':sid,'station_name':name,'regime':regime,'local_rh_vs_chmi':stats(rherr),'local_temp_vs_chmi':stats(terr),'luhamet_rh_vs_chmi':stats(luha),'protected_scope':'2021 diagnostic_only' if y==2021 else 'validation_or_target_context'})
 target_start=1643500800 # 2022-01-30T00Z
 target_end=1646006400 # 2022-02-28T00Z exclusive
 # Exact-hour station-to-station agreement by year and regimes; never treated as independent local truth.
 station_pair=[]
 for y in (2019,2020,2021,2022):
  for regime in ('all','both_frost','both_high_rh','both_frost_high_rh'):
   de_t=[];de_h=[]
   for ep in set(e for (sid,e) in chmi if sid=='0-203-0-11777'):
    if datetime.fromtimestamp(ep,timezone.utc).year!=y:continue
    a=chmi.get(('0-203-0-11777',ep),{});b=chmi.get(('0-203-0-11778',ep),{})
    if any(a.get(k,{}).get('quality')!='0.0' or b.get(k,{}).get('quality')!='0.0' or a.get(k,{}).get('v') is None or b.get(k,{}).get('v') is None for k in ('T','H')):continue
    ta,ha=a['T']['v'],a['H']['v'];tb,hb=b['T']['v'],b['H']['v']
    if regime=='both_frost' and not (ta<=0 and tb<=0):continue
    if regime=='both_high_rh' and not (ha>=95 and hb>=95):continue
    if regime=='both_frost_high_rh' and not (ta<=0 and tb<=0 and ha>=95 and hb>=95):continue
    de_t.append(ta-tb);de_h.append(ha-hb)
   station_pair.append({'year':y,'regime':regime,'temperature_vizovice_minus_kladna_c':stats(de_t),'rh_vizovice_minus_kladna_pp':stats(de_h),'protected_scope':'2021 diagnostic_only' if y==2021 else 'context'})
 # Context specifically during the target outage: comparison of two CHMI stations and LuhaMet exact pairs.
 outage_context=[]
 for sid,name in stations.items():
  for regime in ('all','chmi_frost','chmi_high_rh','chmi_frost_high_rh'):
   er=[];et=[];n=0
   for ep,r in bytime.items():
    if not (target_start<=ep<target_end):continue
    c=chmi.get((sid,ep))
    if not c or any(c.get(k,{}).get('quality')!='0.0' or c.get(k,{}).get('v') is None for k in ('T','H')):continue
    ct,ch=c['T']['v'],c['H']['v']
    if regime=='chmi_frost' and ct>0:continue
    if regime=='chmi_high_rh' and ch<95:continue
    if regime=='chmi_frost_high_rh' and not (ct<=0 and ch>=95):continue
    n+=1
    if r.get('luhamet_rh') is not None and r.get('quality_status')=='reference_only' and r.get('source_resolution')=='5min':er.append(r['luhamet_rh']-ch)
    if r.get('luhamet_temp') is not None:et.append(r['luhamet_temp']-ct)
   outage_context.append({'station':sid,'station_name':name,'regime':regime,'chmi_n':n,'luhamet_rh_vs_chmi':stats(er),'luhamet_temp_vs_chmi':stats(et)})
 # Focus on actual 2022 outage versus exact local hourly row coverage and reference pairs.
 gap={'start_utc':'2022-01-30T00:00Z','end_utc':'2022-02-28T00:00Z','hourly_rows':0,'local_rh_nonnull':0,'luhamet_rh_valid':0,'chmi_both_station_q0':0}
 for ep,r in bytime.items():
  if target_start<=ep<target_end:
   gap['hourly_rows']+=1;gap['local_rh_nonnull']+=r.get('outHumidity') is not None
   gap['luhamet_rh_valid']+=r.get('luhamet_rh') is not None and r.get('quality_status')=='reference_only' and r.get('source_resolution')=='5min'
   gap['chmi_both_station_q0']+=all((sid,ep) in chmi and all(chmi[(sid,ep)].get(k,{}).get('quality')=='0.0' for k in ('T','H')) for sid in stations)
 history=json.loads((ROOT/'data/chmi-rh-winter-validation/source_history_summary.json').read_text())
 result={'source':'CHMI official historical CSV; source quality code 0 only for point comparisons','local_change_history_by_year':history['rows'],'retrieved_files':len(glob.glob(str(RAW/'*.csv'))),'chmi_10min_rows':len(chmi),'chmi_quality_code_counts':{f'{k[0]}:{k[1]}':v for k,v in sorted(qc.items())},'chmi_flag_counts':{f'{k[0]}:{k[1]}':v for k,v in sorted(flags.items())},'station_regime_summary':station_rows,'exact_hour_station_pair_agreement':station_pair,'exact_hour_local_comparisons':comparisons,'2022_outage_coverage':gap,'2022_outage_reference_context':outage_context,'method_limits':['This is regional representativeness/context analysis on exact-hour complete cases, not validation of outage estimates.','No fitting, corrections, or candidate records are created.','2021 rows are isolated and labeled diagnostic only.','CHMI station proximity does not establish Loucka sensor identity or equal exposure.','All RH comparisons exclude Loucka outHumidity reconstruction history; counts are reported by year.','Loucka outTemp history count is zero at all 5,608 exact-hour archive rows (counts verified by separate SELECT); 2021 is diagnostic only.','LuhaMet is reference_only exact source_resolution 5min.']}
 (OUT/'2026-11-13-chmi-winter-rh-reference-validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 lines=['# Nezávislý zimní kontext RH: ČHMÚ Vizovice a Kladná-Žilín','', '**Snapshot:** 2026-11-13. Lokální agregace oficiálních 10min CSV ČHMÚ a přesných hodinových UTC shod s Loučka archive.','', '## Zdroj a QC','',f"Načteno {result['retrieved_files']} souborů, {len(chmi)} station-timestamp klíčů. Jen QUALITY=0 (Good/Kvalitní) vstupuje do porovnání. Číselník meta4 ČHMÚ uvádí QUALITY=3 jako Estimated; řádky s jiným kódem nejsou použity. FLAG zůstává zachován a spočítán; T/H neměly neprázdný FLAG.",'','## Rozsah výpadku 2022','',f"V přesné hodinové projekci období {gap['start_utc']}–{gap['end_utc']} je {gap['hourly_rows']} řádků archivu; RH Loučka non-NULL {gap['local_rh_nonnull']}, referenční LuhaMet RH použitelná {gap['luhamet_rh_valid']}, obě stanice ČHMÚ s QC 0 {gap['chmi_both_station_q0']}. Tyto reference popisují regionální počasí, nikoli místní RH truth.",'','## Srovnání při dostupné lokální RH','', '| Rok | CHMI | Režim | n RH | bias Loučka−CHMI | MAE RH | RMSE RH | LuhaMet n | LuhaMet MAE |','|---:|---|---|---:|---:|---:|---:|---:|---:|']
 for x in comparisons:
  if x['regime'] in ('all','frost_and_local_rh_ge_95'):
   a=x['local_rh_vs_chmi'];b=x['luhamet_rh_vs_chmi']; lines.append(f"| {x['year']} | {x['station_name']} | {x['regime']} | {a.get('n',0)} | {a.get('bias','—')} | {a.get('mae','—')} | {a.get('rmse','—')} | {b.get('n',0)} | {b.get('mae','—')} |")
 hist=history['rows']; lines += ['', '## Historie lokálních vstupů', '', 'Přesný SELECT audit změnové historie pokryl 5 608 hodinových target rows: outTemp history **0** ve všech čtyřech rocích; outHumidity history byla přítomna pouze v 55 bodech roku 2019 a všechny jsou v RH srovnání vynechány. 2021 je označen pouze jako diagnostický.', '', '## 2022 outage: intervalní reference a dvě stanice','', '| CHMI | Režim | CHMI n | LuhaMet RH n | LuhaMet−CHMI RH bias | MAE |', '|---|---|---:|---:|---:|---:|']
 for x in outage_context:
  if x['regime'] in ('all','chmi_frost_high_rh'):
   a=x['luhamet_rh_vs_chmi']; lines.append(f"| {x['station_name']} | {x['regime']} | {x['chmi_n']} | {a.get('n',0)} | {a.get('bias','—')} | {a.get('mae','—')} |")
 lines += ['','## Rozdíl mezi stanicemi ČHMÚ','', '| Rok | Režim | n | RH bias Vizovice−Kladná | RH MAE | T MAE °C |','|---:|---|---:|---:|---:|---:|']
 for x in station_pair:
  if x['regime'] in ('all','both_frost_high_rh'):
   a=x['rh_vizovice_minus_kladna_pp'];b=x['temperature_vizovice_minus_kladna_c']; lines.append(f"| {x['year']} | {x['regime']} | {a.get('n',0)} | {a.get('bias','—')} | {a.get('mae','—')} | {b.get('mae','—')} |")
 lines += ['','## Výklad a hranice','', 'Tato kontrola je nezávislý regionální kontext a ověřuje zejména dostupnost zimních mrazových/vlhkých situací, stabilitu dvou stanic a jejich vztah k místním pozorováním. Nevaliduje hodnoty v chybějícím intervalu; bez místního truth nelze z ní vyrobit modelový odhad RH. Ani dvě blízké stanice nejsou zaměnitelné s Loučkou. Před jakýmkoli modelem je stále třeba odborně posoudit inverze, mlhu, námrazu, výměnu senzorů a referenční časovou/kalibrační historii.','', '2021 je zahrnut pouze v samostatně označené diagnostické tabulce; není použit jako kandidátní období ani k návrhu korekcí. Databáze byla dotazována pouze SELECT; nic nebylo aplikováno ani publikováno.','']
 (OUT/'2026-11-13-chmi-winter-rh-reference-validation.md').write_text('\n'.join(lines))
 print(json.dumps({'chmi_keys':len(chmi),'quality':result['chmi_quality_code_counts'],'gap':gap,'comparison_rows':len(comparisons),'report':str(OUT/'2026-11-13-chmi-winter-rh-reference-validation.md')},indent=2))
if __name__=='__main__':main()
