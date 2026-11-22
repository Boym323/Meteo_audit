#!/usr/bin/env python3
"""Render 2014 exact source-only alignment and 50-field availability."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=json.loads((R/'data/2014_target_absent_source_field_availability.json').read_text());fields=D['common_fields']
with (R/'reports/2026-11-13-2014-target-absent-source-field-availability.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['field','old_weewx_nonnull','weewx_WH1080_nonnull','both_nonnull_equal','both_nonnull_conflict'])
 for x in fields:
  v=D['field_counts'][x];w.writerow([x,v['old_nonnull'],v['wh1080_nonnull'],v['both_equal'],v['both_conflict']])
cols=['COUNT(*) AS `source_only_rows`']
for x in fields:cols += [f'SUM(a0.`{x}` IS NOT NULL) AS `{x}_old_nonnull`',f'SUM(a1.`{x}` IS NOT NULL) AS `{x}_wh_nonnull`',f'SUM(a0.`{x}` IS NOT NULL AND a1.`{x}` IS NOT NULL AND a0.`{x}`=a1.`{x}`) AS `{x}_both_equal`',f'SUM(a0.`{x}` IS NOT NULL AND a1.`{x}` IS NOT NULL AND a0.`{x}`<>a1.`{x}`) AS `{x}_both_conflict`']
(R/'sql/readonly/2014_target_absent_source_field_availability.sql').write_text('-- READ-ONLY aggregate; fixed UTC 2014 whole-row source-only cohort.\nSELECT\n  '+',\n  '.join(cols)+'''\nFROM `old_weewx`.`archive` a0
JOIN `weewx_WH1080`.`archive` a1 ON a1.`dateTime`=a0.`dateTime`
LEFT JOIN `pocasi-loucka.eu_old`.`archive` a2 ON a2.`dateTime`=a0.`dateTime`
WHERE a0.`dateTime`>=1388534400 AND a0.`dateTime`<1420070400 AND a2.`dateTime` IS NULL;\n''')
(R/'sql/readonly/2014_target_absent_source_timestamp_inventory.sql').write_text('''-- READ-ONLY timestamp inventory; fixed UTC 2014.
SELECT 'old_weewx' AS source_name, `dateTime` FROM `old_weewx`.`archive` WHERE `dateTime`>=1388534400 AND `dateTime`<1420070400
UNION ALL SELECT 'weewx_WH1080', `dateTime` FROM `weewx_WH1080`.`archive` WHERE `dateTime`>=1388534400 AND `dateTime`<1420070400
UNION ALL SELECT 'pocasi-loucka.eu_old', `dateTime` FROM `pocasi-loucka.eu_old`.`archive` WHERE `dateTime`>=1388534400 AND `dateTime`<1420070400;
''')
(R/'sql/readonly/2014_target_absent_source_unit_interval.sql').write_text('''-- READ-ONLY unit/interval profile for exact 2014 source-only whole rows.
SELECT a0.usUnits AS old_units,a0.interval AS old_interval,a1.usUnits AS wh_units,a1.interval AS wh_interval,COUNT(*) AS rows_n,MIN(a0.dateTime) AS first_epoch,MAX(a0.dateTime) AS last_epoch
FROM `old_weewx`.`archive` a0 JOIN `weewx_WH1080`.`archive` a1 ON a1.dateTime=a0.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.`archive` a2 ON a2.dateTime=a0.dateTime
WHERE a0.dateTime>=1388534400 AND a0.dateTime<1420070400 AND a2.dateTime IS NULL
GROUP BY old_units,old_interval,wh_units,wh_interval;
''')
a=D['alignment'];nearest=a['nearest_offsets_within_150s']
lines=['# 2014 source-only whole-row cohort: field coverage, interval, and near-slot review','',
 'This report compares exact timestamp keys in both historical source archives with whole-row presence in `pocasi-loucka.eu_old`. Presence is not measurement validity.', '',
 '## Row-set and time alignment','',
 f"- `old_weewx` and `weewx_WH1080`: {a['source_rows_by_archive']['old_weewx']:,} rows each with the same {a['source_union_keys']:,}-key timestamp set. `pocasi-loucka.eu_old`: {a['target_rows']:,} rows; {a['source_only']:,} source-only whole-row timestamps.",
 f"- {a['off_grid_source_only']:,} source-only timestamps are off a 300-second grid. {a['source_only_without_nearby_target']:,} have no target row within ±150 seconds; {a['source_only']-a['source_only_without_nearby_target']:,} are near a target row and {a['target_slot_collisions']} target-slot collision(s) occur.",
 f"- Nearest signed offsets for the seven near cases (seconds): `{nearest}`. Treat them as `TIMESTAMP_SHIFT_OR_DUPLICATE_REVIEW_REQUIRED`; do not shift or insert automatically.",
 f"- The 1,071 rows form {a['runs']:,} exact 300-second runs. Missing source rows are concentrated in June ({a['monthly'][5]['source_only']}), July ({a['monthly'][6]['source_only']}), and September ({a['monthly'][8]['source_only']}).", '',
 '## Source unit/interval','',
 'All 1,071 source-only keys have old_weewx/WH1080 `usUnits=17`, `interval=5`.', '',
 '## Field availability','', '| Field | old_weewx non-NULL | WH1080 non-NULL | both non-NULL equal | both non-NULL conflict |','|---|---:|---:|---:|---:|']
for f in fields:
 x=D['field_counts'][f];lines.append(f"| `{f}` | {x['old_nonnull']:,} | {x['wh1080_nonnull']:,} | {x['both_equal']:,} | {x['both_conflict']:,} |")
r=D['longest_run_review'];lines += ['', '## Nejdelší běh', '', f"{r['rows']} řádků, {r['first_utc']}–{r['last_utc']}. Old_weewx má outTemp/RH/windSpeed/windGust/windDir/barometer NULL po celý běh; WH1080 má teplotu, vítr a směr, ale RH je NULL v obou kopiích. Rain a rainRate jsou konstantní a kopie souhlasí; pressure souhlasí, altimeter se liší. Jde o field-set asymetrii, nikoli prokázanou závadu ani prokázané odstranění.", '', '## Rozhodnutí','',
 '- **No RESTORED proposals.** 120 source rows carry outTemp in old_weewx versus 1,071 in WH1080; RH is present only in 120 old rows and NULL in WH1080 throughout this source-only cohort. Wind and barometer availability also differs by source. The export/sensor epoch and reason for omission are unresolved.',
 '- Seven near-slot cases remain `TIMESTAMP_SHIFT_OR_DUPLICATE_REVIEW_REQUIRED`; the other 1,064 remain `UNRESOLVED_SOURCE_ONLY`. No `HISTORICALLY_REMOVED_SUSPECTED` label is assigned from absence alone.',
 '- Evidence and three bounded READ-ONLY SQL files are reproducible. Year 2021 was not queried.']
(R/'reports/2026-11-13-2014-target-absent-source-field-availability.md').write_text('\n'.join(lines)+'\n')
