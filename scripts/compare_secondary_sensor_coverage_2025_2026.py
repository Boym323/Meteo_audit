#!/usr/bin/env python3
"""Compare 2025 full-year and 2026 partial-year aggregate availability."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'reports'
def read(year):
 p=ROOT/f'2026-11-13-annual-secondary-sensor-snapshot-{year}.csv'
 return {r['variable']:r for r in csv.DictReader(p.open(newline='',encoding='utf-8'))}
a,b=read(2025),read(2026)
assert set(a)==set(b) and len(a)==42
rows=[]
for v in sorted(a):
 x,y=a[v],b[v]
 r25=float(x['nonnull_rows'])/int(x['archive_rows']);r26=float(y['nonnull_rows'])/int(y['archive_rows'])
 rows.append({'variable':v,'rows_2025':int(x['archive_rows']),'nonnull_2025':int(x['nonnull_rows']),'null_share_2025':r25,'min_2025':x['min_value'],'max_2025':x['max_value'],'rows_2026_partial':int(y['archive_rows']),'nonnull_2026_partial':int(y['nonnull_rows']),'null_share_2026_partial':r26,'null_share_change_2026_minus_2025':r26-r25,'min_2026_partial':y['min_value'],'max_2026_partial':y['max_value']})
with (ROOT/'2026-11-13-secondary-sensor-availability-2025-2026.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
summary={'variables':42,'rows_2025':int(next(iter(a.values()))['archive_rows']),'rows_2026_partial':int(next(iter(b.values()))['archive_rows']),'lower_null_share_in_2026':sum(r['null_share_change_2026_minus_2025']<0 for r in rows),'higher_null_share_in_2026':sum(r['null_share_change_2026_minus_2025']>0 for r in rows),'same_null_share':sum(r['null_share_change_2026_minus_2025']==0 for r in rows),'all_null_2025':[r['variable'] for r in rows if int(r['nonnull_2025'])==0],'all_null_2026':[r['variable'] for r in rows if int(r['nonnull_2026_partial'])==0],'newly_nonnull_2026':[r['variable'] for r in rows if int(r['nonnull_2025'])==0 and int(r['nonnull_2026_partial'])>0],'scope':'availability ratio uses observed archive rows; 2026 is partial through 2026-10-29; differences do not infer installation or quality'}
(ROOT/'2026-11-13-secondary-sensor-availability-2025-2026.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
changed=sorted(rows,key=lambda r:r['null_share_change_2026_minus_2025'])
md=f'''# Srovnání dostupnosti sekundárních polí — 2025 vs. partial 2026\n\nPorovnáno je {summary['variables']} polí nad 102 946 archive rows v plném UTC roce 2025 a 86 877 řádky v neúplném 2026 snapshotu (do 29. 10.). Poměry non-NULL jsou děleny počtem existujících archive rows v daném snapshotu; nejsou expected-slot completeness ani installed sensor periods. Rozsahy min/max nejsou trendové srovnání, protože 2026 je částečný rok se sezónně odlišným pokrytím.\n\nZměna NULL podílu 2026−2025: {summary['lower_null_share_in_2026']} polí má nižší, {summary['higher_null_share_in_2026']} vyšší a {summary['same_null_share']} stejný podíl. All-NULL pole 2025: {', '.join(summary['all_null_2025']) or 'žádná'}; 2026: {', '.join(summary['all_null_2026']) or 'žádná'}. Rozdíl může odrážet zařízení, zdroj, export, archive path nebo sezónu; bez sensor epoch/provenance není důkazem instalace či zlepšení kvality.\n\nNejvětší pokles NULL podílu: {', '.join(f"{r['variable']} ({r['null_share_change_2026_minus_2025']:+.3f})" for r in changed[:5])}. Největší nárůst: {', '.join(f"{r['variable']} ({r['null_share_change_2026_minus_2025']:+.3f})" for r in changed[-5:][::-1])}.\n\nPer-field CSV: `2026-11-13-secondary-sensor-availability-2025-2026.csv`; compact summary JSON: `.json`. Sources are the bounded annual snapshots for 2025 and partial 2026.\n'''
first_last={r['variable']:r['first_nonnull_utc'] for r in csv.DictReader((ROOT/'2026-11-13-sensor-field-first-last-nonnull-2026.csv').open(newline='',encoding='utf-8'))}
md += '\n\n**10 fields are NULL in full 2025 and populated in 2026 partial:** ' + ', '.join(f"{v} (first observed {first_last.get(v,'date unavailable')})" for v in summary['newly_nonnull_2026']) + '. These observed archive onsets are not physical installation dates.\n'
(ROOT/'2026-11-13-secondary-sensor-availability-2025-2026.md').write_text(md,encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
