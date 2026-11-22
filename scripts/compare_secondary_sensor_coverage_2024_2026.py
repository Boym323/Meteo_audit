#!/usr/bin/env python3
"""Compare annual availability for 42 fields across 2024, 2025, partial 2026."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'reports'
def read(y):
 return {r['variable']:r for r in csv.DictReader((R/f'2026-11-13-annual-secondary-sensor-snapshot-{y}.csv').open(newline='',encoding='utf-8'))}
d={y:read(y) for y in (2024,2025,2026)}
assert set(d[2024])==set(d[2025])==set(d[2026]) and len(d[2024])==42
rows=[]
for v in sorted(d[2024]):
 r={'variable':v}
 for y in (2024,2025,2026):
  x=d[y][v]; r[f'rows_{y}']=int(x['archive_rows']);r[f'nonnull_{y}']=int(x['nonnull_rows']);r[f'null_share_{y}']=int(x['null_rows'])/int(x['archive_rows']);r[f'min_{y}']=x['min_value'];r[f'max_{y}']=x['max_value']
 r['availability_pattern']=''.join('1' if r[f'nonnull_{y}'] else '0' for y in (2024,2025,2026))
 rows.append(r)
with (R/'2026-11-13-secondary-sensor-availability-2024-2026.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
allnull={str(y):[r['variable'] for r in rows if r[f'nonnull_{y}']==0] for y in (2024,2025,2026)}
summary={'variables':42,'archive_rows':{str(y):int(next(iter(d[y].values()))['archive_rows']) for y in (2024,2025,2026)},'full_years':[2024,2025],'partial_year':2026,'all_null_fields':allnull,'newly_available_by_2025':[r['variable'] for r in rows if r['availability_pattern']=='011'],'newly_available_only_2025':[r['variable'] for r in rows if r['availability_pattern']=='010'],'newly_available_only_2026':[r['variable'] for r in rows if r['availability_pattern']=='001'],'disappeared_in_2026':[r['variable'] for r in rows if r['availability_pattern']=='110'],'present_all_three':[r['variable'] for r in rows if r['availability_pattern']=='111'],'scope_note':'2026 through 2026-10-29 only; counts use observed archive rows; availability transitions do not prove install date, quality, or cause'}
(R/'2026-11-13-secondary-sensor-availability-2024-2026.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=f'''# Roční availability 42 sekundárních polí — 2024 až 2026\n\nStejných 42 polí bylo agregováno nad {summary['archive_rows']['2024']:,} řádky v plném roce 2024, {summary['archive_rows']['2025']:,} v plném 2025 a {summary['archive_rows']['2026']:,} řádky partial 2026 do 29. října. Jmenovatelem jsou existující archive rows; nejde o expected measurement slots ani prokázanou dobu provozu senzoru. Min/max mezi roky nejsou trendovým porovnáním (2026 je částečný a sezónní).\n\nCeloročně NULL fields: 2024: {', '.join(allnull['2024']) or 'žádná'}; 2025: {', '.join(allnull['2025']) or 'žádná'}; 2026 partial: {', '.join(allnull['2026']) or 'žádná'}. Mezi patterny dostupnosti je {len(summary['disappeared_in_2026'])} polí dostupných v obou plných letech v partial 2026 zcela chybí; {len(summary['newly_available_only_2025'])} polí začalo mezi 2024 a 2025; {len(summary['newly_available_only_2026'])} polí je NULL v obou plných letech a v 2026 partial nově non-NULL. U onsetů 2026 jsou first non-NULL epochy v `2026-11-13-sensor-field-first-last-nonnull-2026.csv`. Tyto epochy jsou pozorovanou archive dostupností, nikoli datem instalace nebo důkazem driver příčiny.\n\nPer-field CSV `2026-11-13-secondary-sensor-availability-2024-2026.csv`; strojový souhrn `.json`. Roční raw aggregates a reprodukční SQL jsou v sousedních snapshots 2024–2026.\n'''
(R/'2026-11-13-secondary-sensor-availability-2024-2026.md').write_text(md,encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
