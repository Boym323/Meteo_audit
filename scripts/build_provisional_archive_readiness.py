#!/usr/bin/env python3
"""Build a conservative year-variable readiness grid from saved monthly aggregates."""
from __future__ import annotations
import csv, json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'reports/2026-11-12-monthly-sensor-null-coverage.csv'
TEMPORAL=ROOT/'reports/2026-11-12-monthly-temporal-completeness.csv'
VARS=('outTemp','outHumidity','rain','rainRate','windSpeed','pressure','radiation','UV','pm25','soilMoist1','lightning_distance')
NULLCOL={v:f'{v}_null' for v in VARS}
TAGS={
 ('outTemp',2011):'long_archive_outage_ER01_ER02',('outTemp',2012):'long_archive_outage_ER01_ER02',
 ('outTemp',2013):'freeze_plateau_and_source_conflicts_ER02_ER11_ER12',('outTemp',2026):'daily_summary_extrema_conflict_ER29',
 ('outHumidity',2015):'null_reference_coverage_source_quality_ER26',('outHumidity',2016):'null_reference_coverage_source_quality_ER26',('outHumidity',2017):'null_reference_coverage_source_quality_ER26',
 ('outHumidity',2019):'source_conflicts_and_plateaus_ER11_ER26',('outHumidity',2022):'applied_reconstruction_and_derived_cascade_ER08_ER09',('outHumidity',2026):'daily_summary_extrema_conflict_ER30',
 ('rain',2010):'historical_phaseA_events_source_truth_limited_ER04',('rain',2011):'historical_phaseA_events_source_truth_limited_ER04',('rain',2013):'counter_epoch_and_reset_semantics_ER04',('rain',2021):'protected_diagnostic_only_ER24',('rain',2026):'partial_live_year',
 ('rainRate',2013):'driver_unit_epoch_semantics_ER04',('rainRate',2018):'q1_interim_live_ER23',('rainRate',2021):'protected_diagnostic_only_ER24',('rainRate',2023):'source_restore_conflict_ER04',('rainRate',2024):'source_restore_conflict_ER04',('rainRate',2025):'applied_restore_conflict_ER04',
 ('windSpeed',2013):'historical_unit_epoch_review_ER15',('windSpeed',2026):'daily_summary_minimum_conflict_ER30',
 ('pressure',2016):'pressure_source_gap_review_ER17',('pressure',2017):'pressure_source_gap_review_ER17',('pressure',2018):'q1_interim_and_pressure_source_gap_ER17_ER23',
 ('radiation',2026):'sensor_source_extreme_review_ER18',('UV',2026):'sensor_source_extreme_review_ER18',
 ('pm25',2024):'saturation_episode_review_ER19',('soilMoist1',2024):'sensor_availability_and_zero_null_review_ER21'}
EVIDENCE={
 'outTemp':'reports/TEMPERATURE_AUDIT.md; reports/2026-11-13-production-outtemp-daily-summary-consistency-annual.csv',
 'outHumidity':'reports/HUMIDITY_AUDIT.md; reports/2026-11-13-primary-daily-extrema-consistency-annual.csv',
 'rain':'reports/RAIN_AUDIT.md; reports/PROPOSAL_INVENTORY.md',
 'rainRate':'reports/RAIN_AUDIT.md; reports/PROPOSAL_INVENTORY.md',
 'windSpeed':'reports/SECONDARY_SENSORS_AUDIT.md; reports/2026-11-13-primary-daily-extrema-consistency-annual.csv',
 'pressure':'reports/SECONDARY_SENSORS_AUDIT.md; reports/REFERENCE_DATA_INVENTORY.md',
 'radiation':'reports/SECONDARY_SENSORS_AUDIT.md', 'UV':'reports/SECONDARY_SENSORS_AUDIT.md',
 'pm25':'reports/SECONDARY_SENSORS_AUDIT.md', 'soilMoist1':'reports/SECONDARY_SENSORS_AUDIT.md',
 'lightning_distance':'reports/SECONDARY_SENSORS_AUDIT.md'}

def read_csv(path):
 with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def build():
 null_months=read_csv(SOURCE); temporal=read_csv(TEMPORAL)
 null_by_year=defaultdict(lambda:{'rows':0,**{f'{v}_null':0 for v in VARS}})
 for r in null_months:
  y=int(r['utc_month'][:4]); x=null_by_year[y]; x['rows']+=int(r['rows_n'])
  for v,c in NULLCOL.items():x[c]+=int(r[c])
 temp_by_year=defaultdict(lambda:{'months':0,'rows':0,'internal_empty_months':0,'review_flags':set()})
 for r in temporal:
  y=int(r['utc_year']);x=temp_by_year[y];x['months']+=int(int(r['archive_rows'])>0);x['rows']+=int(r['archive_rows'])
  x['review_flags'].update(filter(None,r['review_flags'].split(';')))
 years=sorted(temp_by_year)
 first_month=min(r['utc_month'] for r in null_months if int(r['rows_n'])>0)
 last_month=max(r['utc_month'] for r in null_months if int(r['rows_n'])>0)
 for r in temporal:
  month=f"{int(r['utc_year']):04d}-{int(r['utc_month']):02d}"
  if first_month<=month<=last_month and int(r['archive_rows'])==0:
   temp_by_year[int(r['utc_year'])]['internal_empty_months']+=1
 out=[]
 for y in years:
  t=temp_by_year[y]; n=null_by_year[y]
  for v in VARS:
   null_n=n[f'{v}_null']; nonnull=n['rows']-null_n
   tag=TAGS.get((v,y),'')
   reasons=[]
   if y==2021: reasons.append('2021 is protected and diagnostic only; no correction proposals')
   if y==2018: reasons.append('Q1 2018 is interim/live; yearly evidence is not final')
   if y==2026: reasons.append('2026 is partial; monthly snapshot ends 2026-10-29')
   if t['internal_empty_months']: reasons.append(f"{t['internal_empty_months']} month(s) without archive rows inside observed archive span; do not infer expected slots")
   if tag: reasons.append(tag)
   if y==2021: status='REVIEW_REQUIRED'; reasons.append('protected year: diagnostic evidence only; no reconstruction readiness decision')
   elif nonnull==0: status='NOT_AVAILABLE'; reasons.append('variable is entirely NULL in this annual archive snapshot; physical installation/operation is not inferred')
   else: status='REVIEW_REQUIRED'; reasons.append('comprehensive year-variable validation is incomplete; no READY status assigned')
   out.append({
    'utc_year':y,'variable':v,'readiness':status,'archive_rows':n['rows'],
    'months_with_archive_rows':t['months'],'internal_zero_row_months':t['internal_empty_months'],
    'nonnull_rows':nonnull,'null_rows':null_n,'null_share_of_archive_rows':round(null_n/n['rows'],8) if n['rows'] else None,
    'measured_value_availability':'present' if nonnull else 'none_in_archive_snapshot',
    'known_issue_tag':tag or None,'validated_recommended_corrections':0,
    'conditional_candidate_count':None,'unresolvable_gap_count':None,
    'chart_impact':'review_required' if nonnull else 'unavailable_in_archive',
    'daily_annual_statistics_impact':'review_required' if nonnull else 'unavailable_in_archive',
    'records_impact':'review_required' if nonnull else 'unavailable_in_archive',
    'atlas_suitability':'review_required' if nonnull else 'unavailable_in_archive',
    'reason':' | '.join(reasons),'evidence_refs':EVIDENCE[v],
    'source_snapshot':'reports/2026-11-12-monthly-sensor-null-coverage.csv; reports/2026-11-12-monthly-temporal-completeness.csv',
    'denominator_note':'archive rows only; not expected measurement slots or proven sensor operating time',
   })
 return out, years,first_month,last_month

def main():
 rows,years,first,last=build()
 csv_path=ROOT/'reports/2026-11-13-provisional-archive-readiness.csv'
 json_path=ROOT/'reports/2026-11-13-provisional-archive-readiness.json'
 with csv_path.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 json_path.write_text(json.dumps({'classification_version':'provisional-v1','snapshot_period_months':[first,last], 'years':years,'variables':list(VARS),'records':rows,'scope_limitations':['11 variables only','snapshot is historical through 2026-10-29','no expected-slot denominators','no year-specific validated correction packages','Q1 2018 interim','2021 diagnostic only']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 counts={s:sum(r['readiness']==s for r in rows) for s in ('READY','READY_WITH_LIMITATIONS','RECONSTRUCTION_REQUIRED','REVIEW_REQUIRED','NOT_AVAILABLE')}
 lines=['# Předběžná readiness archivu po roce a veličině','', '**Stav: PŘEDBĚŽNÉ; není to finální schválení archivu pro publikaci.** Matice pokrývá 11 kanálů s uloženým měsíčním NULL snapshotem a roky 2009–2026. Snapshot končí 2026-10-29.','', '## Metoda','', 'Pro každý rok a kanál uvádí počet archive řádků, počet NULL/non-NULL, měsíce s řádky a měsíce bez řádků uvnitř pozorovaného časového rozsahu. Jmenovatelem jsou skutečné archive rows, nikoli odvozená pětiminutová mřížka nebo prokázaná doba provozu senzoru. `NOT_AVAILABLE` znamená pouze celoroční NULL ve snapshotu; nedokazuje, že senzor fyzicky nebyl instalován. 2021 je označen pouze diagnosticky a 2018 zůstává interim kvůli Q1.','', 'Ke kompletní validační matici chybí důkazní pokrytí všech proměnných a fyzických epoch. Proto žádná buňka nedostala `READY`, `READY_WITH_LIMITATIONS` ani `RECONSTRUCTION_REQUIRED` bez reprodukovatelné roční klasifikace; hodnoty zůstávají `REVIEW_REQUIRED` nebo `NOT_AVAILABLE`. Nula validovaných doporučených korekcí neznamená nula chyb; podmíněné kandidáty a neřešitelné mezery nejsou v podkladech bezpečně rozděleny do všech ročních buněk a jsou `null`.','', '## Přehled','', f"- Rozsah: {len(years)} roků × {len(VARS)} veličin = {len(rows)} buněk; bez celkového procenta dokončení.",f'- Stavové počty: {counts}.','- Měsíční a roční archivní řádky: zdroj `reports/2026-11-12-monthly-temporal-completeness.csv`; NULL stav pro 11 kanálů: `reports/2026-11-12-monthly-sensor-null-coverage.csv`.','- Strojově čitelná matice: `2026-11-13-provisional-archive-readiness.csv` a `.json`.','', '## Kritické blokátory','', '- Ověřit expected cadence, provozní epochy a kompletní fyzickou identitu senzorů; roční row count není časová úplnost.', '- Uzavřít odborné případy dlouhých výpadků a mrazů/inverzí, nejistoty modelů a konfliktů zdrojů (ER-01/02/07/20/28/29/30).', '- Získat provenance historických konfigurací/driverů, zejména jednotkových epoch, rainRate, derived fields a sekundárních kanálů.', '- Dokončit source-specific annual QC a přesné roční korekční inventáře; pouze validované návrhy lze počítat jako doporučené.', '- Počkat na potvrzení dokončení souběžných schválených zásahů Q1 2018; 2021 vyžaduje samostatné výslovné schválení.','', '## Interpretace dopadu','', 'Grafy, denní/roční statistiky, rekordy a atlas mají v každé buňce status `review_required` nebo `unavailable_in_archive`; žádná funkce se na základě tohoto předběžného souhrnu nemá přepnout na sjednocený archiv. Dopady nejsou nahrazeny souhrnným skóre.','']
 (ROOT/'reports/FINAL_ARCHIVE_READINESS.md').write_text('\n'.join(lines),encoding='utf-8')
 print(f'Wrote {len(rows)} cells for {len(years)} years x {len(VARS)} variables; counts={counts}')
if __name__=='__main__':main()
