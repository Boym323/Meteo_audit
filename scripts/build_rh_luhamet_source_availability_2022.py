#!/usr/bin/env python3
"""Build monthly/daily source-coverage evidence for the 2022 RH gap."""
import csv,datetime,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/rh_luhamet_source_availability_2022';R=ROOT/'reports';STEM='2026-11-13-rh-luhamet-outage-2022-source-coverage'
def main():
 monthly=json.loads((D/'monthly.json').read_text())
 history=json.loads((D/'history.json').read_text())
 feb_context=json.loads((D/'february_context.json').read_text())
 daily=[]
 for m in range(1,13):
  with (D/f'daily_{m}.tsv').open(newline='') as f: rows=list(csv.DictReader(f,delimiter='\t'))
  for x in rows:
   day=datetime.datetime.fromtimestamp(int(x['utc_day_epoch'])*86400,datetime.timezone.utc).date()
   daily.append({'utc_date':day.isoformat(),**{k:v for k,v in x.items() if k!='utc_day_epoch'}})
 daily.sort(key=lambda x:x['utc_date'])
 assert len(daily)==365
 allnull=[x for x in daily if int(x['target_RH_nonnull'])==0]
 runs=[];cur=[]
 for x in daily:
  day=datetime.date.fromisoformat(x['utc_date'])
  if int(x['archive_rows'])>0 and int(x['target_RH_nonnull'])==0:
   if cur and day!=datetime.date.fromisoformat(cur[-1]['utc_date'])+datetime.timedelta(days=1):runs.append(cur);cur=[]
   cur.append(x)
  elif cur:runs.append(cur);cur=[]
 if cur:runs.append(cur)
 runs.sort(key=len,reverse=True)
 summary={'station_id':'luhamet_sehradice','year':2022,'target_archive_rows':sum(int(x['archive_rows']) for x in daily),
  'target_RH_nonnull':sum(int(x['target_RH_nonnull']) for x in daily),'target_RH_null':sum(int(x['archive_rows'])-int(x['target_RH_nonnull']) for x in daily),
  'days_with_archive_rows':len(daily),'days_with_zero_target_RH':len(allnull),'longest_consecutive_zero_RH_day_runs':[
   {'start':r[0]['utc_date'],'end':r[-1]['utc_date'],'days':len(r),'archive_rows':sum(int(x['archive_rows']) for x in r),'exact_reference_RH_values':sum(int(x['exact_LuhaMet_RH_values']) for x in r)} for r in runs if len(r)>=2],
 'monthly':monthly,'history_reconciliation':history,'february_context':feb_context,
  'limitations':['LuhaMet observations are reference_only, not Loucka truth','station coordinates and distance are absent in local registry','sensor continuity and licensing are not fully documented','some current target RH values may be previously applied corrections; complete-case monthly metrics are descriptive, not independent validation','RH exact candidates do not justify direct replacement without transfer validation']}
 (R/f'{STEM}.json').write_text(json.dumps(summary,indent=2)+'\n')
 with (R/f'{STEM}-daily.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(daily[0]));w.writeheader();w.writerows(daily)
 with (R/f'{STEM}-monthly.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(monthly[0]));w.writeheader();w.writerows(monthly)
 lines=['# Dlouhý výpadek outHumidity 2022 a exact LuhaMet source coverage','',
 'Měsíční/daily exact-timestamp agregace nad `loucka_reconstruction.archive` a `reference_observations` (`luhamet_sehradice`). V roce 2022 má archive 104 142 rows a current `outHumidity` je NULL v 41 727 (40,1 %); 41 642 NULL targetů nemá RH event v `reconstruction_changes`, zatímco 85 má applied RH history. V samotném únoru je všech 8 058 rows current RH NULL a žádný nemá RH history event.', '',
 '## Výpadky a reference coverage','',
 '| UTC měsíc | Archive rows | Target RH non-NULL | Přesný LuhaMet RH timestamp | Srovnatelné target/source RH páry | Bias target−reference | MAE | RMSE |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for x in monthly:
  def fmt(k):return '—' if x[k] is None else f"{float(x[k]):.3f}"
  lines.append(f"| 2022-{int(x['month_utc']):02d} | {int(x['archive_rows']):,} | {int(x['target_RH_nonnull']):,} | {int(x['exact_LuhaMet_RH_values']):,} | {int(x['comparable_RH_pairs']):,} | {fmt('target_minus_LuhaMet_bias_pct')} | {fmt('RH_MAE_pct')} | {fmt('RH_RMSE_pct')} |".replace(',',' '))
 lines += ['',f"Denní longest-run audit nalezl {len(allnull)} dnů s archive rows a nulovým target RH. Nejdelší souvislý interval je {runs[0][0]['utc_date']} až {runs[0][-1]['utc_date']} ({len(runs[0])} dnů, {sum(int(x['archive_rows']) for x in runs[0]):,} archive rows, {sum(int(x['exact_LuhaMet_RH_values']) for x in runs[0]):,} exact LuhaMet RH values). Další intervaly jsou ve strojovém JSON. Target/reference RH srovnání mimo gap je malý nebo korigovaný complete-case vzorek (např. březen n=1 692; bias −1,58 pp, MAE 2,82 pp, RMSE 4,22 pp); nejde o předregistrovaný maskovaný holdout.",'',
 'Reference metadata: LuhaMet Sehradice, elevation 318 m, převážně 5min cadence; přesné senzorové souřadnice a vzdálenost od Loučky v registru chybí, data mají `reference_only` a licence/sensor continuity nejsou plně doloženy. Zdrojová metadata: `data/reference-inventory/reference_stations_snapshot_20261113.json`.', '',
 'Interpretace: exact reference humidity values exist for nearly every February target timestamp, but they are measurements at another station. February target/source temperature pairs (n=8 013) have bias +0,32 °C, MAE 1,16 °C and RMSE 1,51 °C; this is context only and does not validate RH transfer. The potential gap is marked for expert review. No estimates/candidates were created and no database write occurred. Daily CSV and monthly CSV are bounded aggregates only; reproducing SQL is `sql/readonly/rh_luhamet_outage_2022_source_coverage.sql`.']
 (R/f'{STEM}.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
