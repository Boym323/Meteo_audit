#!/usr/bin/env python3
"""Render saved field-availability and timestamp-alignment evidence for 2017."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=json.loads((R/'data/2017_target_absent_source_field_availability.json').read_text())
with (R/'reports/2026-11-13-2017-target-absent-source-field-availability.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['field','old_weewx_nonnull','weewx_WH1080_nonnull','both_nonnull_equal','both_nonnull_conflict'])
 for field in D['common_fields']:
  x=D['field_counts'][field];w.writerow([field,x['old_nonnull'],x['wh1080_nonnull'],x['both_equal'],x['both_conflict']])
# Bounded cohort aggregate SQL for field availability and source-copy relationship.
fields=D['common_fields']
cols=['COUNT(*) AS `source_only_rows`']
for x in fields:
 cols += [f'SUM(a0.`{x}` IS NOT NULL) AS `{x}_old_nonnull`',f'SUM(a1.`{x}` IS NOT NULL) AS `{x}_wh_nonnull`',f'SUM(a0.`{x}` IS NOT NULL AND a1.`{x}` IS NOT NULL AND a0.`{x}`=a1.`{x}`) AS `{x}_both_equal`',f'SUM(a0.`{x}` IS NOT NULL AND a1.`{x}` IS NOT NULL AND a0.`{x}`<>a1.`{x}`) AS `{x}_both_conflict`']
sql='''-- READ-ONLY; exact whole-row absence in the merged archive; fixed UTC 2017.
SELECT\n  '''+',\n  '.join(cols)+'''
FROM `old_weewx`.`archive` a0
JOIN `weewx_WH1080`.`archive` a1 ON a1.`dateTime`=a0.`dateTime`
LEFT JOIN `pocasi-loucka.eu_old`.`archive` a2 ON a2.`dateTime`=a0.`dateTime`
WHERE a0.`dateTime`>=1483228800 AND a0.`dateTime`<1514764800
  AND a2.`dateTime` IS NULL;
'''
(R/'sql/readonly/2017_target_absent_source_field_availability.sql').write_text(sql)
a=D['alignment']
lines=['# 2017 source-only whole-row cohort: time alignment and field availability','',
 'All numbers below describe archive presence only, not measured-value validity. The cohort uses exact source timestamp keys and is separate from source-only rows relative to the reconstruction archive.', '',
 '## Timestamp relation','',
 f"- `old_weewx`: {a['source_rows_by_archive']['old_weewx']:,} rows; `weewx_WH1080`: {a['source_rows_by_archive']['weewx_WH1080']:,}; exact source timestamp union {a['source_union_keys']:,}.",
 f"- `pocasi-loucka.eu_old`: {a['target_rows']:,} rows; exact shared keys {a['exact_shared']:,}; source-only whole-row keys {a['source_only']:,}.",
 f"- {a['off_grid_source_only']:,} source-only keys are off-grid modulo 300 seconds. None has a target archive row within ±150 seconds; no nearby timestamp shift or occupied-target collision was found.",
 '- The 28,015 source-only keys split into 1,827 exact 300-second runs; most are fragmented, with 12 monthly groups shown in the data JSON. Fragmentation is not proof of selective deletion.', '',
 '## Primary-field availability in the missing whole-row cohort','',
 '| Field | old_weewx non-NULL | WH1080 non-NULL | both non-NULL equal | both non-NULL conflict |', '|---|---:|---:|---:|---:|']
for f in D['common_fields']:
 x=D['field_counts'][f];lines.append(f"| `{f}` | {x['old_nonnull']:,} | {x['wh1080_nonnull']:,} | {x['both_equal']:,} | {x['both_conflict']:,} |")
lines += ['', '## Decision','',
 '- Key channels are not uniformly represented: outTemp is non-NULL at only 12 old_weewx rows but all 28,015 WH1080 rows; outHumidity is NULL in both copies across all 28,015; windSpeed/windGust are nearly/all NULL in old_weewx but non-NULL in WH1080; rainRate and pressure are non-NULL and equal in both copies; altimeter is frequently unequal. This is a mixed provenance/availability cohort, not a complete independent measurement set.',
 '- Five longest source-only runs (5,527 rows combined) were screened: old_weewx outTemp/RH/wind were NULL throughout, while rain and rainRate were fixed zero and copy-equal. The available rows therefore do not contain a complete suite of observations. The run evidence and full field counts are in the JSON.',
 '- **Classification: `UNRESOLVED_SOURCE_ONLY`; no RESTORED proposals.** `HISTORICALLY_REMOVED_SUSPECTED` is not assigned solely from absence. To move any subset, establish source selection lineage for the field/epoch, resolve WH1080-only T/wind and all-NULL RH, review transformation factors and neighboring values, and seek independent local context where available.',
 '- Read-only SQL reproduces the 50-field aggregate; alignment was computed locally from timestamp-only SELECT result sets. No writes, 2021, or Q1 2018 operations were involved.']
(R/'reports/2026-11-13-2017-target-absent-source-field-availability.md').write_text('\n'.join(lines)+'\n')
