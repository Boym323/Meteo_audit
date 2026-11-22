#!/usr/bin/env python3
"""Build deterministic reports and READ-ONLY SQL for merged archives, 2009-2020."""
import csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/annual_all_channel_availability_merged_archives_2009_2020.json'
OUT=ROOT/'reports'
SQL=ROOT/'sql/readonly'
data=json.loads(SRC.read_text())
dbs=data['databases']; years=data['years']
OUT.mkdir(exist_ok=True); SQL.mkdir(parents=True,exist_ok=True)
with (OUT/'2026-11-13-annual-all-channel-availability-merged-archives-2009-2020.csv').open('w',newline='') as f:
 w=csv.writer(f); w.writerow(['database','year','archive_rows','field','nonnull','null','nonnull_share'])
 for db in dbs:
  for item in data['data'][db]:
   rows=item['archive_rows']
   for field,v in sorted(item['fields'].items()):
    w.writerow([db,item['year'],rows,field,v['nonnull'],v['null'],f"{v['nonnull']/rows:.8f}" if rows else ''])
# Per archive/year, request up to 50 field aggregates; fixed UTC calendar bounds.
for db in dbs:
 fields=sorted({f for y in data['data'][db] for f in y['fields']})
 safe=db.replace('.','_')
 for chunk_i in range(0,len(fields),50):
  group=fields[chunk_i:chunk_i+50]
  for year in years:
   lo=int(__import__('datetime').datetime(year,1,1,tzinfo=__import__('datetime').timezone.utc).timestamp())
   hi=int(__import__('datetime').datetime(year+1,1,1,tzinfo=__import__('datetime').timezone.utc).timestamp())
   selects=['COUNT(*) AS archive_rows']+[f"COUNT(`{x}`) AS `{x}_nonnull`" for x in group]
   sql=("-- READ-ONLY; fixed UTC year bounds; diagnostic availability only.\n"
        f"-- Source schema: `{db}`. Year: {year}. Fields: {', '.join(group)}\n"
        "SELECT\n  "+',\n  '.join(selects)+f"\nFROM `{db}`.`archive`\nWHERE `dateTime` >= {lo} AND `dateTime` < {hi};\n")
   (SQL/f'annual_all_channel_{safe}_{year}_chunk{chunk_i//50+1}.sql').write_text(sql)
# Summary with conservative interpretation.
lines=['# Roční dostupnost všech číselných polí v novějších archivech (2009–2020)','',
       'Read-only agregace `COUNT(field)` a `COUNT(*)` pro všechny číselné kanály ve třech novějších archivech. Výstupy měří pouze přítomnost neprázdné hodnoty; nepotvrzují provenienci, správnost, nezávislost zdrojů ani způsobilost k obnově.','',
       '## Rozsah','',f"- Léta: {years[0]}–{years[-1]} UTC; rok 2021 nebyl dotazován.",
       '- Databáze jsou historicky sloučené podle OWNER_ATTESTED výpovědi; shoda není nezávislé měření.',
       '- Q1 2018 zůstává pouze popisné/chráněné a není podkladem pro návrhy aplikace.',
       '- Zahrnuté tabulky a polí jsou:']
for db in dbs:
 per=data['data'][db]; fields=len(per[0]['fields']); row_sum=sum(x['archive_rows'] for x in per)
 allnull=sum(1 for x in per for v in x['fields'].values() if v['nonnull']==0)
 lines.append(f"  - `{db}`: {fields} polí, {len(per)*fields} buněk, {row_sum:,} součet ročních row-countů (ne unikátní záznamy), {allnull} field-year buněk zcela NULL.")
lines += ['', 'Podrobné výsledky jsou v CSV a zdrojové agregaci JSON. SQL soubory lze znovu spustit pouze jako SELECT; slouží k reprodukci, nikoli k validaci meteorologické kvality.']
(OUT/'2026-11-13-annual-all-channel-availability-merged-archives-2009-2020.md').write_text('\n'.join(lines)+'\n')
