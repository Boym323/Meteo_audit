#!/usr/bin/env python3
"""Summarize pre-aggregated, exact-time 2025 temperature holdout SQL results."""
import csv, math
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/'reports/2026-11-12-temperature-transfer-2025-holdout-aggregates.csv'
OUT=ROOT/'reports/2026-11-12-temperature-transfer-2025-holdout-summary.csv'
REPORT=ROOT/'reports/2026-11-12-temperature-transfer-2025-holdout.md'
with IN.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
assert len(rows)==7
assert sum(int(r['n']) for r in rows)==98681
assert sum(int(r['n']) for r in rows if r['temp_group']=='FREEZE')==13510
assert {r['quarter'] for r in rows}=={'Q1','Q2','Q3','Q4'}
expected={'Q1':24698,'Q2':25803,'Q3':24754,'Q4':23426}
for q,n in expected.items(): assert sum(int(r['n']) for r in rows if r['quarter']==q)==n
models=[('M0_direct',0),('M1_global_train_bias',1),('M2_quarterly_train_bias',2)]
columns={0:('abs0','sq0','bias0','maxabs0'),1:('abs1','sq1','bias1','maxabs1'),2:('abs2','sq2','bias2','maxabs2')}
scopes=[('ALL','all rows'),('FREEZE','observed Loučka outTemp < 0 C')]
summary=[]
for q in ['ALL','Q1','Q2','Q3','Q4']:
 for scope,label in scopes:
  selected=[r for r in rows if (q=='ALL' or r['quarter']==q) and (scope=='ALL' or r['temp_group']=='FREEZE')]
  if not selected:continue
  n=sum(int(r['n']) for r in selected)
  for model,idx in models:
   ac,sc,bc,mc=columns[idx]
   ab=sum(float(r[ac]) for r in selected); sq=sum(float(r[sc]) for r in selected); bias=sum(float(r[bc]) for r in selected); mx=max(float(r[mc]) for r in selected)
   summary.append({'quarter':q,'scope':scope,'model':model,'n':n,'mae_c':ab/n,'rmse_c':math.sqrt(sq/n),'bias_c':bias/n,'max_abs_error_c':mx})
with OUT.open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=summary[0].keys());w.writeheader();w.writerows(summary)
# Build compact markdown tables from calculated results.
def get(q,scope,model):return next(x for x in summary if x['quarter']==q and x['scope']==scope and x['model']==model)
lines=['# Časově blokovaný teplotní transfer — holdout 2025','',
'## Protokol','',
'Trénink je předem časově oddělené UTC období 2022–2024; test je celý UTC rok 2025. Párování je exact timestamp s `luhamet_sehradice`, `source_resolution=5min`, `quality_status=reference_only`, obě teploty non-NULL a bez jakékoli `outTemp` change-history. Všechny vstupy a skórování jsou nad stejnými cíli. 2021 je mimo rozsah, Q1 2018 také. Modelové varianty jsou jednoduchý přenos bez bias (M0), globální offset z train (M1) a čtvrtletní offsety z train (M2). 2024 bylo použito jako předchozí experimentální holdout v dřívější exploraci, proto tento 2025 výsledek je nový chronologický test, ale ne zcela netknutý pre-registrační holdout pro rodinu modelů.','',
'## Trénovací offsety','',
'| Trénink 2022–2024 | n | Průměr Loučka−LuhaMet (°C) |','|---|---:|---:|']
with open(ROOT/'reports/2026-11-12-temperature-transfer-2025-training-biases.csv',newline='',encoding='utf-8') as f:
 for r in csv.DictReader(f):lines.append(f"| {r['quarter']} | {int(r['training_pairs']):,} | {float(r['bias_loucka_minus_luhamet_c']):+.4f} |")
lines += ['', 'Celkem 309 456 training pairs; globální offset M1 je +0,4328 °C.', '',
'## Holdout 2025', '',
'| Rozsah | n | M0 MAE/RMSE | M1 MAE/RMSE | M2 MAE/RMSE |','|---|---:|---:|---:|---:|']
for q,label in [('ALL','Vše'),('ALL','FREEZE')]:
 scope='ALL' if label=='Vše' else 'FREEZE';s0=get(q,scope,'M0_direct');s1=get(q,scope,'M1_global_train_bias');s2=get(q,scope,'M2_quarterly_train_bias')
 lines.append(f"| {label} | {s0['n']:,} | {s0['mae_c']:.4f}/{s0['rmse_c']:.4f} | {s1['mae_c']:.4f}/{s1['rmse_c']:.4f} | {s2['mae_c']:.4f}/{s2['rmse_c']:.4f} |")
lines += ['', 'Mrazová skupina je definována podle pozorované Loučka `outTemp<0 °C` (diagnostická stratifikace, nikoli modelový vstup).', '',
'### Po UTC čtvrtletích','',
'| Čtvrtletí | Páry | M0 MAE/RMSE | M1 MAE/RMSE | M2 MAE/RMSE |','|---|---:|---:|---:|---:|']
for q in ('Q1','Q2','Q3','Q4'):
 a=get(q,'ALL','M0_direct');b=get(q,'ALL','M1_global_train_bias');c=get(q,'ALL','M2_quarterly_train_bias')
 lines.append(f"| {q} | {a['n']:,} | {a['mae_c']:.4f}/{a['rmse_c']:.4f} | {b['mae_c']:.4f}/{b['rmse_c']:.4f} | {c['mae_c']:.4f}/{c['rmse_c']:.4f} |")
lines += ['', '### Mrazové páry po čtvrtletích','',
'| Čtvrtletí | n mrazových párů | M0 MAE/RMSE | M1 MAE/RMSE | M2 MAE/RMSE |','|---|---:|---:|---:|---:|']
for q in ('Q1','Q2','Q3','Q4'):
 try:
  a=get(q,'FREEZE','M0_direct');b=get(q,'FREEZE','M1_global_train_bias');c=get(q,'FREEZE','M2_quarterly_train_bias')
 except StopIteration:continue
 lines.append(f"| {q} | {a['n']:,} | {a['mae_c']:.4f}/{a['rmse_c']:.4f} | {b['mae_c']:.4f}/{b['rmse_c']:.4f} | {c['mae_c']:.4f}/{c['rmse_c']:.4f} |")
lines += ['', '## Interpretace / omezení','',
'Čtvrtletní varianta M2 používá na 2025 výhradně biasy natrénované 2022–2024; výsledky ukazují, zda se tento bias přenese do nového roku. Holdout tvoří kompletní pozorované exact-time páry, nikoli skutečné rekonstruované mezery. LuhaMet je `reference_only`, nikoli ground truth Loučky; cílové Loučka měření bez change-history nemusí být nezávisle původní. Modely proto hodnotí pouze prostorový transfer na pozorovaných dvojicích. Žádná varianta nebyla použita k tvorbě hodnot pro mezery.',
'2024 bylo použito v předchozím modelovém experimentu, takže rodina M0/M1/M2 není dokonale předem uzamčená; přesný 2025 holdout však nebyl použit k výběru offsetů. Mrazová skupina je podle lokální pozorované teploty; inverze, bezvětří, extrémy a dlouhé výpadky tím nejsou validovány. ER-02/ER-07 zůstávají otevřené.', '',
'Agregovaná SQL odpověď: `reports/2026-11-12-temperature-transfer-2025-holdout-aggregates.csv`; biasy: `reports/2026-11-12-temperature-transfer-2025-training-biases.csv`; score/reprodukce: `reports/2026-11-12-temperature-transfer-2025-holdout-summary.csv`, `sql/readonly/temperature_transfer_2025_holdout.sql`, `scripts/summarize_temperature_transfer_2025.py`.']
REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(f"validated holdout n=98681 freeze=13510; summary rows={len(summary)}")
for q in ('ALL','Q1','Q2','Q3','Q4'):
 for scope in (['ALL','FREEZE'] if q=='ALL' else ['ALL']):
  if q=='ALL' and scope=='FREEZE': name='FREEZE'
  else:name=q
  for m,_ in models:
   try:
    x=get(q,scope,m); print(name,m,round(x['mae_c'],4),round(x['rmse_c'],4),round(x['bias_c'],4),x['n'])
   except StopIteration:pass
