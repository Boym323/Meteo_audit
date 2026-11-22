#!/usr/bin/env python3
"""Render field-availability report and SQL for 2016 whole-row source-only cohort."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=json.loads((R/'data/2016_target_absent_source_field_availability.json').read_text())
with (R/'reports/2026-11-13-2016-target-absent-source-field-availability.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['field','old_weewx_nonnull','weewx_WH1080_nonnull','both_nonnull_equal','both_nonnull_conflict'])
 for field in D['common_fields']:
  x=D['field_counts'][field];w.writerow([field,x['old_nonnull'],x['wh1080_nonnull'],x['both_equal'],x['both_conflict']])
cols=['COUNT(*) AS `source_only_rows`']
for x in D['common_fields']:
 cols += [f'SUM(a0.`{x}` IS NOT NULL) AS `{x}_old_nonnull`',f'SUM(a1.`{x}` IS NOT NULL) AS `{x}_wh_nonnull`',f'SUM(a0.`{x}` IS NOT NULL AND a1.`{x}` IS NOT NULL AND a0.`{x}`=a1.`{x}`) AS `{x}_both_equal`',f'SUM(a0.`{x}` IS NOT NULL AND a1.`{x}` IS NOT NULL AND a0.`{x}`<>a1.`{x}`) AS `{x}_both_conflict`']
(R/'sql/readonly/2016_target_absent_source_field_availability.sql').write_text('-- READ-ONLY aggregate; exact whole-row absence; fixed UTC 2016.\nSELECT\n  '+',\n  '.join(cols)+'''\nFROM `old_weewx`.`archive` a0
JOIN `weewx_WH1080`.`archive` a1 ON a1.`dateTime`=a0.`dateTime`
LEFT JOIN `pocasi-loucka.eu_old`.`archive` a2 ON a2.`dateTime`=a0.`dateTime`
WHERE a0.`dateTime`>=1451606400 AND a0.`dateTime`<1483228800
  AND a2.`dateTime` IS NULL;\n''')
(R/'sql/readonly/2016_target_absent_source_timestamp_inventory.sql').write_text('''-- READ-ONLY timestamp evidence; fixed UTC 2016; compare labels locally.
SELECT 'old_weewx' AS source_name, `dateTime` FROM `old_weewx`.`archive` WHERE `dateTime`>=1451606400 AND `dateTime`<1483228800
UNION ALL
SELECT 'weewx_WH1080', `dateTime` FROM `weewx_WH1080`.`archive` WHERE `dateTime`>=1451606400 AND `dateTime`<1483228800
UNION ALL
SELECT 'pocasi-loucka.eu_old', `dateTime` FROM `pocasi-loucka.eu_old`.`archive` WHERE `dateTime`>=1451606400 AND `dateTime`<1483228800;
''')
a=D['alignment'];lines=['# 2016 source-only whole-row cohort: field availability and alignment','',
 'Rozsah tvoří přesné timestampy, které jsou v `old_weewx` a `weewx_WH1080`, ale celý row chybí v `pocasi-loucka.eu_old`. Availability není potvrzení kvality.', '',
 '## Časová osa','',
 f"- Source row counts: {a['source_rows_by_archive']['old_weewx']:,} v každé kopii; exact timestamp union {a['source_union_keys']:,}. Cílový merged archiv má {a['target_rows']:,} rows a všech {a['target_rows']:,} timestampů je přesně sdíleno se zdroji.",
 f"- Whole-row source-only: {a['source_only']:,}; {a['off_grid_source_only']:,} jsou mimo 300s grid; {a['source_runs']:,} přesných 300-second runs.",
 f"- U všech {a['source_only']:,} source-only timestamps není target row do ±150 s; žádný nearest-target collision. Malý clock offset proto nevysvětluje jejich absenci.",
 '- Rozložení podle měsíce UTC:']
for x in a['monthly']:lines.append(f"  - {x['month']:02d}: {x['source_only']:,} source-only")
lines += ['', '## Jednotky a intervaly','', '| old_weewx units/interval | WH1080 units/interval | rows | first–last epoch |','|---|---|---:|---|']
for x in D['unit_interval_profile']:lines.append(f"| {x['old_units']}/{x['old_interval']} | {x['wh_units']}/{x['wh_interval']} | {x['rows']:,} | {x['first_epoch']}–{x['last_epoch']} |")
lines += ['', '## Field availability v source-only řádcích','', '| Field | old_weewx non-NULL | WH1080 non-NULL | both equal | both conflict |','|---|---:|---:|---:|---:|']
for f in D['common_fields']:
 x=D['field_counts'][f];lines.append(f"| `{f}` | {x['old_nonnull']:,} | {x['wh1080_nonnull']:,} | {x['both_equal']:,} | {x['both_conflict']:,} |")
lines += ['', '## Závěr','',
 '- Tato skupina je charakteristická velmi asymetrickou dostupností: outTemp je non-NULL pouze ve 2/16 330 řádcích old_weewx, ale ve všech 16 330 WH1080; outHumidity je NULL v obou zdrojích; windSpeed/windGust jsou téměř NULL v old_weewx, ale plné v WH1080. RainRate a pressure jsou plné a shodné; altimeter se výrazně liší.',
 '- Off-grid sekvence zahrnují denní bloky s postupným posunem sekund, ale nejsou blízkými kopiemi cílových řádků. To podporuje časovou/source-epoch anomálii jako hypotézu, nikoli prokázané clock-drift pravidlo.',
 '- **Klasifikace `UNRESOLVED_SOURCE_ONLY`; bez RESTORED návrhu.** Dostupnost WH1080 teploty/větru sama neověřuje původ měření ani důvod, proč je merged archive vynechal. Před případným návrhem je nutné rozřešit field-specific lineage, timestamp epochu a historické výběrové/čisticí pravidlo.',
 '- READ-ONLY. Nezahrnuje 2021 ani chráněný Q1 2018. JSON obsahuje detailní měsíční časovou a field availability evidenci.']
(R/'reports/2026-11-13-2016-target-absent-source-field-availability.md').write_text('\n'.join(lines)+'\n')
