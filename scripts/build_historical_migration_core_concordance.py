#!/usr/bin/env python3
"""Render exact-time, three-archive core concordance evidence and repeatable SELECTs."""
import csv,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'data/historical_migration_core_exact_concordance_2009_2020.json').read_text())
fields=D['fields']; schemas=D['schemas']; years=[x['year'] for x in D['years']]
REPORT=ROOT/'reports'; SQL=ROOT/'sql/readonly'; SQL.mkdir(exist_ok=True,parents=True)
path=REPORT/'2026-11-13-historical-migration-core-exact-concordance-2009-2020.csv'
with path.open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['year','field','both_source_values','source_copies_equal','source_copies_conflict','target_row_field_nonnull_on_source_agreement','target_same_raw','target_changed_raw','target_null','target_row_absent_on_source_agreement'])
 for item in D['years']:
  s=item['stats']
  for field in fields:
   v=lambda k:int(s[f'{field}_{k}'])
   absent=v('source_equal')-v('target_same_raw')-v('target_changed_raw')-v('target_null')
   w.writerow([item['year'],field,v('both_sources'),v('source_equal'),v('source_conflict'),v('target_with_source_agreement'),v('target_same_raw'),v('target_changed_raw'),v('target_null'),absent])
# Exact, bounded SELECT per year.
for y in years:
 lo=int(datetime(y,1,1,tzinfo=timezone.utc).timestamp());hi=int(datetime(y+1,1,1,tzinfo=timezone.utc).timestamp())
 key_sql=' UNION '.join(f"SELECT `dateTime` FROM `{db}`.`archive` WHERE `dateTime` >= {lo} AND `dateTime` < {hi}" for db in schemas)
 cols=['COUNT(*) AS `union_keys`']+[f"COUNT(a{i}.`dateTime`) AS `rows_{i}`" for i in range(3)]
 for f in fields:
  both=f'a0.`{f}` IS NOT NULL AND a1.`{f}` IS NOT NULL'; equal=f'{both} AND a0.`{f}` = a1.`{f}`'
  exprs={'both_sources':both,'source_equal':equal,'source_conflict':f'{both} AND NOT (a0.`{f}` = a1.`{f}`)',
   'target_with_source_agreement':f'{equal} AND a2.`{f}` IS NOT NULL','target_same_raw':f'{equal} AND a2.`{f}` = a0.`{f}`',
   'target_changed_raw':f'{equal} AND a2.`{f}` IS NOT NULL AND NOT (a2.`{f}` = a0.`{f}`)',
   'target_null':f'{equal} AND a2.`dateTime` IS NOT NULL AND a2.`{f}` IS NULL'}
  cols += [f"SUM({expr}) AS `{f}_{name}`" for name,expr in exprs.items()]
 joins=' '.join(f'LEFT JOIN `{db}`.`archive` a{i} ON a{i}.`dateTime`=k.`dateTime`' for i,db in enumerate(schemas))
 sql='-- READ-ONLY. Exact timestamp union, fixed UTC year; raw equality is not a unit-normalized quality decision.\nSELECT\n  '+',\n  '.join(cols)+f'\nFROM ({key_sql}) k\n{joins};\n'
 (SQL/f'historical_migration_core_concordance_{y}.sql').write_text(sql)
# Human-readable annual evidence.
lines=['# Přesný cross-archive soulad hlavních polí při historickém sloučení (2009–2020)','',
 'Pro každý UTC rok byly porovnány klíče `dateTime` sjednocené ze tří archivů: `old_weewx`, `weewx_WH1080` a `pocasi-loucka.eu_old`. Agregace rozlišuje shodu dvou starých kopií a stav cílové hodnoty při této shodě. Žádný výsledek sám nedokazuje správnost, odstranění ani pravidlo merge. Raw equality může být ovlivněna odlišnými `usUnits`; není to porovnání po standardizaci jednotek.', '',
 '## Souhrn po rocích','', '| Rok | Klíčů v unii | old_weewx | WH1080 | eu_old | outTemp source conflicts | RH target changed | rain target changed | rainRate target changed | windSpeed target changed | windGust target changed |', '|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for item in D['years']:
 s=item['stats'];y=item['year'];v=lambda f,k:int(s[f'{f}_{k}'])
 lines.append(f"| {y} | {s['union_keys']} | {s['rows_0']} | {s['rows_1']} | {s['rows_2']} | {v('outTemp','source_conflict')} | {v('outHumidity','target_changed_raw')} | {v('rain','target_changed_raw')} | {v('rainRate','target_changed_raw')} | {v('windSpeed','target_changed_raw')} | {v('windGust','target_changed_raw')} |")
lines += ['', '## Výklad a limity','', '- `source_equal`/`source_conflict` počítá jen případy, kdy obě historické kopie mají non-NULL hodnotu. `target_changed_raw` jen když kopie souhlasí a sloučený archiv má jinou non-NULL raw hodnotu. `target_null` rozlišuje existující cílový řádek s NULL; zbytek mezi souhlasnými kopiemi označuje cílový řádek chybějící.',
 '- `rain` a `rainRate` vykazují četné raw rozdíly, ale tento report nezohledňuje intervalové součty, dešťové konvence ani jednotkový kontrakt. Neinterpretovat je jako chybu či potvrzené čištění.',
 '- U polí, jejichž source values se liší nebo target row chybí, není rozhodnuto, která kopie byla vybrána či proč. Nepřítomnost reconstruction eventu nevylučuje předchozí úpravy.',
 '- Vlastník potvrzuje historické merge a čištění (OWNER_ATTESTED), ale původ jednotlivých DB a selekční algoritmus nejsou známy. Níže uvedené četnosti jsou TECHNICALLY_OBSERVED; vysvětlení zůstává hypotézou.',
 '- Bounded SQL dotazy jsou v `sql/readonly/historical_migration_core_concordance_<year>.sql`. Rok 2021 nebyl dotazován; Q1 2018 zůstává pouze popisný/chráněný.']
(REPORT/'2026-11-13-historical-migration-core-exact-concordance-2009-2020.md').write_text('\n'.join(lines)+'\n')
