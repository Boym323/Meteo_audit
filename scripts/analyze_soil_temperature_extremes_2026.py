#!/usr/bin/env python3
"""Summarize bounded 2026 soilTemp5/6 extreme cases without exposing full rows."""
import csv,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'reports/2026-11-13-soil-temperature-extremes-2026.csv'
rows=list(csv.DictReader(source.open(newline='',encoding='utf-8')))
def vals(c):return [float(r[c]) for r in rows if r[c] != '']
soil5=[float(r['soilTemp5']) for r in rows if r['soilTemp5'] and float(r['soilTemp5']) < -40]
soil6=[float(r['soilTemp6']) for r in rows if r['soilTemp6'] and float(r['soilTemp6']) < -40]
times=[int(r['dateTime']) for r in rows]
gaps=[b-a for a,b in zip(times,times[1:])]
result={
 'snapshot_year':2026,'case_rows':len(rows),'soilTemp5_below_minus40_count':len(soil5),'soilTemp6_below_minus40_count':len(soil6),
 'both_below_minus40_count':sum(float(r['soilTemp5'] or 0)<-40 and float(r['soilTemp6'] or 0)<-40 for r in rows),
 'soilTemp5_min':min(soil5),'soilTemp6_min':min(soil6),'main_archive_exact_matches':sum(r['soilTemp5']==r['main_soilTemp5'] and r['soilTemp6']==r['main_soilTemp6'] for r in rows),
 'outTemp_nonnull':sum(bool(r['outTemp']) for r in rows),'soilTemp1_nonnull':sum(bool(r['soilTemp1']) for r in rows),'soilTemp2_nonnull':sum(bool(r['soilTemp2']) for r in rows),'soilTemp3_nonnull':sum(bool(r['soilTemp3']) for r in rows),'soilTemp4_nonnull':sum(bool(r['soilTemp4']) for r in rows),
 'outTemp_min_at_cases':min(vals('outTemp')),'outTemp_max_at_cases':max(vals('outTemp')),
 'soilTemp1_min_at_cases':min(vals('soilTemp1')),'soilTemp1_max_at_cases':max(vals('soilTemp1')),
 'soilTemp3_min_at_cases':min(vals('soilTemp3')),'soilTemp3_max_at_cases':max(vals('soilTemp3')),
 'soilTemp4_min_at_cases':min(vals('soilTemp4')),'soilTemp4_max_at_cases':max(vals('soilTemp4')),
 'adjacent_300_second_case_pairs':sum(x==300 for x in gaps),'case_gap_min_seconds':min(gaps),'case_gap_median_seconds':statistics.median(gaps),'case_gap_max_seconds':max(gaps),
 'scope_note':'31 rows selected by soilTemp5<−40 or soilTemp6<−40 in partial 2026; source exact-match is not independent ground truth.'}
assert result['case_rows']==31 and result['soilTemp5_below_minus40_count']==10 and result['soilTemp6_below_minus40_count']==21
assert result['both_below_minus40_count']==0 and result['main_archive_exact_matches']==31
assert result['adjacent_300_second_case_pairs']==0 and result['case_gap_min_seconds']==7800
(ROOT/'reports/2026-11-13-soil-temperature-extremes-summary-2026.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=f'''# Kontext extrémů `soilTemp5/6` — 2026\n\nV bounded 2026 screenu bylo {len(rows)} záznamů s `soilTemp5<-40` nebo `soilTemp6<-40`: {len(soil5)} pro soilTemp5 (minimum {min(soil5)} °C) a {len(soil6)} pro soilTemp6 (minimum {min(soil6)} °C). Žádný řádek neobsahuje oba extrémy současně. Všechny cíle jsou ve 300s archive záznamech, ale extrémní targety samy nejsou sousední: počet sousedních 300s dvojic mezi případy je 0; nejmenší rozestup {min(gaps)} s, medián {statistics.median(gaps)} s, maximum {max(gaps)} s.\n\n`outTemp`, `soilTemp1`, `soilTemp3` a `soilTemp4` jsou přítomné ve všech 31 řádcích (rozsahy při těchto targetech: {min(vals('outTemp')):.2f}…{max(vals('outTemp')):.2f}, {min(vals('soilTemp1')):.1f}…{max(vals('soilTemp1')):.1f}, {min(vals('soilTemp3')):.1f}…{max(vals('soilTemp3')):.1f}, {min(vals('soilTemp4')):.1f}…{max(vals('soilTemp4')):.1f} °C). `soilTemp2` je NULL ve všech 31 případech. Všech 31 dvojic `soilTemp5/6` se přesně shoduje s hlavním production archive; to není nezávislá validace.\n\nŘídký, ne-sousední vzor a současné běžné outTemp/soilTemp hodnoty jsou slučitelné s izolovaným field/payload/sensor artefaktem, ale bez známé identifikace sondy, hloubky, kalibrace a nezávislého raw zdroje nelze vyřadit legitimní lokální signál ani společný export artefakt. Ponechat ER-20 `REVIEW_REQUIRED`; žádné NULL/odstranění/oprava. Detailní target context je uložen pro odborné ověření v `2026-11-13-soil-temperature-extremes-2026.csv`; agregovaný JSON je vedle něj.\n'''
(ROOT/'reports/2026-11-13-soil-temperature-extremes-2026.md').write_text(md,encoding='utf-8')
print('PASS: soil extremes summarized',result['case_rows'],'cases; no 5-minute-adjacent cases')
