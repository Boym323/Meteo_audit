#!/usr/bin/env python3
"""Build year-level raw-ratio classes and bounded SQL for historical archive joins."""
import csv,json
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=json.loads((R/'data/historical_migration_conversion_factor_2009_2020.json').read_text())
F=D['fields']; schemas=['old_weewx','weewx_WH1080','pocasi-loucka.eu_old']
with (R/'reports/2026-11-13-historical-migration-conversion-factor-2009-2020.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['year','field','expected_factor','expected_unit_triplets','expected_unit_interval_triplets','source_equal','target_null','target_row_absent','target_nonzero_pairs','expected_factor_count','ratio_1_count','other_factor_count'])
 for item in D['years']:
  s=item['stats'];
  for field,meta in F.items():
   w.writerow([item['year'],field,meta['expected_factor'],s['expected_unit_triplets'],s['expected_unit_interval_triplets'],s[f'{field}_source_equal'],s[f'{field}_target_null'],s[f'{field}_target_row_absent'],s[f'{field}_target_nonzero_pairs'],s[f'{field}_expected_factor'],s[f'{field}_ratio_1'],s[f'{field}_other_factor']])
# Reproduction SQL, fixed year and exact keys.
for item in D['years']:
 y=item['year'];lo=int(datetime(y,1,1,tzinfo=timezone.utc).timestamp());hi=int(datetime(y+1,1,1,tzinfo=timezone.utc).timestamp())
 keys=' UNION '.join(f"SELECT `dateTime` FROM `{db}`.`archive` WHERE `dateTime` >= {lo} AND `dateTime` < {hi}" for db in schemas)
 cols=['COUNT(*) AS `union_keys`','SUM(a0.usUnits=17 AND a1.usUnits=17 AND a2.usUnits=16) AS `expected_unit_triplets`','SUM(a0.usUnits=17 AND a1.usUnits=17 AND a2.usUnits=16 AND a0.interval=5 AND a1.interval=5 AND a2.interval=5) AS `expected_unit_interval_triplets`']
 for field,meta in F.items():
  fac=meta['expected_factor'];base=f'a0.`{field}` IS NOT NULL AND a1.`{field}` IS NOT NULL AND a0.`{field}`=a1.`{field}`';nz=f'{base} AND a0.`{field}`<>0 AND a2.`{field}` IS NOT NULL';
  for name,expr in [('source_equal',base),('target_null',f'{base} AND a2.`dateTime` IS NOT NULL AND a2.`{field}` IS NULL'),('target_row_absent',f'{base} AND a2.`dateTime` IS NULL'),('target_nonzero_pairs',nz),('expected_factor',f'{nz} AND ABS(a2.`{field}`/a0.`{field}`-{fac})<0.001'),('ratio_1',f'{nz} AND ABS(a2.`{field}`/a0.`{field}`-1)<0.001'),('other_factor',f'{nz} AND ABS(a2.`{field}`/a0.`{field}`-{fac})>=0.001 AND ABS(a2.`{field}`/a0.`{field}`-1)>=0.001')]: cols.append(f'SUM({expr}) AS `{field}_{name}`')
 joins=' '.join(f'LEFT JOIN `{db}`.`archive` a{i} ON a{i}.`dateTime`=k.`dateTime`' for i,db in enumerate(schemas))
 sql='-- READ-ONLY; exact timestamp union, fixed UTC year; tolerance 0.001 on raw ratios.\nSELECT\n '+',\n '.join(cols)+f'\nFROM ({keys}) k\n{joins};\n'
 (R/'sql/readonly'/f'historical_migration_conversion_factor_{y}.sql').write_text(sql)
# Reporting summary.
lines=['# Unit-factor screening of source-to-merged values — 2009–2020','',
 'Exact timestamp rows where `old_weewx` and `weewx_WH1080` contain the same non-NULL, nonzero raw value were compared with `pocasi-loucka.eu_old`. The source and merged unit-code triple is 17/17/16 for the shared rowset. Ratio classes use tolerance ±0.001. This is evidence of stored transformations, not proof of intent, source accuracy, or a safe inverse correction. `rain` and `rainRate` are included as controls; their counter/interval behavior prevents a simple blanket factor.', '',
 '| UTC period | Field | Source equal, target nonzero | Ratio 1 | Expected unit factor | Other |', '|---|---|---:|---:|---:|---:|']
for lo,hi in [(2009,2012),(2013,2013),(2014,2020)]:
 for field,meta in F.items():
  rows=[x['stats'] for x in D['years'] if lo<=x['year']<=hi]
  sm=lambda k:sum(int(r[f'{field}_{k}']) for r in rows)
  lines.append(f"| {lo}–{hi} | {field} | {sm('target_nonzero_pairs')} | {sm('ratio_1')} | {sm('expected_factor')} (factor {meta['expected_factor']}) | {sm('other_factor')} |")
lines += ['', '## Rozhodovací interpretace','',
 '- `windSpeed` and `windGust` show a clear stored-value epoch: 2009–2012 matched raw ratio 1 (311,710 speed and 313,823 gust pairs); 2013 is mixed (48,202/63,337 speed and 51,314/67,483 gust pairs fit 3.6); 2014–2020 matches ratio 3.6 in 553,259 speed and 575,382 gust nonzero pairs. This aligns with METRICWX m/s to METRIC km/h, while the earlier raw equality despite 17→16 codes indicates that the archive history is not explained by a uniform contemporary unit conversion alone.',
 '- The 2013 transition is interval-bounded by the available exact pairs; existing focused report gives the last ratio-1 and first ratio-3.6 timestamps. Do not interpolate a conversion boundary through the missing interval.',
 '- `rain` frequently falls outside 0.1, while `rainRate` generally follows 0.1 with localized exceptions. Rain aggregation, rounding, counter semantics and interval differences remain candidate explanations, not conclusions.',
 '- Source-copy equality is not two independent sensors. Before labeling a value historically transformed, inspect field-specific neighboring values, intervals, zeros, extremes and sensor epoch; no restoration decision follows from this screen.',
 '- SQL per UTC year: `sql/readonly/historical_migration_conversion_factor_<year>.sql`. Year 2021 excluded; Q1 2018 is descriptive/protected.']
(R/'reports/2026-11-13-historical-migration-conversion-factor-2009-2020.md').write_text('\n'.join(lines)+'\n')
