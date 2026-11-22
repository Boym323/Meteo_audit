#!/usr/bin/env python3
"""Create indexed, READ-ONLY per-episode aggregation for 2014-2015 gap sources."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
records=json.loads((R/'data/b5_2014_2015_gap_source_concordance.json').read_text())['records']
cte='WITH gaps AS (\n'+'\nUNION ALL\n'.join(f"SELECT {x['gap_no']} AS gap_id,{x['year_utc']} AS year_utc,{x['left_time']} AS left_time,{x['right_time']} AS right_time" for x in records)+'\n)\n'
fields=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','pressure','barometer','altimeter']
sel=['g.gap_id','g.year_utc','COUNT(*) AS paired_rows','SUM(a.`dateTime` % 300 <> 0) AS off_300s_grid','COUNT(DISTINCT CONCAT(a.`usUnits`,"/",a.`interval`)) AS old_unit_interval_codes','COUNT(DISTINCT CONCAT(w.`usUnits`,"/",w.`interval`)) AS wh_unit_interval_codes','COUNT(DISTINCT CONCAT(e.`usUnits`,"/",e.`interval`)) AS euold_unit_interval_codes','SUM(e.`dateTime` IS NOT NULL) AS euold_exact_rows','SUM(e.`outTemp` IS NOT NULL) AS euold_outTemp_nonnull','MIN(l.`outTemp`) AS left_reconstruction_outTemp','MAX(r.`outTemp`) AS right_reconstruction_outTemp','COUNT(DISTINCT ref.`observed_at_utc`) AS exact_luhamet_pairs','SUM(ref.`temperature_c` IS NOT NULL) AS luhamet_temp_nonnull','SUM(ch.`target_time` IS NOT NULL) AS any_outTemp_change_event']
for f in fields:
 sel.extend([f'SUM(a.`{f}` IS NOT NULL) AS old_{f}_nonnull',f'SUM(w.`{f}` IS NOT NULL) AS wh_{f}_nonnull',f'SUM(a.`{f}` IS NOT NULL AND w.`{f}` IS NOT NULL AND a.`{f}`=w.`{f}`) AS {f}_paired_equal',f'SUM(a.`{f}` IS NOT NULL AND w.`{f}` IS NOT NULL AND a.`{f}`<>w.`{f}`) AS {f}_paired_conflict'])
sel += ['SUM(a.`outTemp`=0) AS old_outTemp_zero','SUM(w.`outTemp`=0) AS wh_outTemp_zero','SUM(e.`outTemp`=0) AS euold_outTemp_zero','MIN(a.`outTemp`) AS old_outTemp_min','MAX(a.`outTemp`) AS old_outTemp_max','MIN(w.`outTemp`) AS wh_outTemp_min','MAX(w.`outTemp`) AS wh_outTemp_max','COUNT(DISTINCT a.`outTemp`) AS old_outTemp_distinct','COUNT(DISTINCT w.`outTemp`) AS wh_outTemp_distinct','AVG(ABS(w.`outTemp`-ref.`temperature_c`)) AS wh_outTemp_LuhaMet_MAE','MAX(ABS(w.`outTemp`-ref.`temperature_c`)) AS wh_outTemp_LuhaMet_max_abs']
where=' OR '.join(f'(a.`dateTime`>{x["left_time"]} AND a.`dateTime`<{x["right_time"]})' for x in records)
q=cte+'SELECT '+',\n       '.join(sel)+'''\nFROM gaps g
JOIN `old_weewx`.`archive` a ON a.`dateTime`>g.left_time AND a.`dateTime`<g.right_time
JOIN `weewx_WH1080`.`archive` w ON w.`dateTime`=a.`dateTime`
LEFT JOIN `pocasi-loucka.eu_old`.`archive` e ON e.`dateTime`=a.`dateTime`
LEFT JOIN `loucka_reconstruction`.`archive` l ON l.`dateTime`=g.left_time
LEFT JOIN `loucka_reconstruction`.`archive` r ON r.`dateTime`=g.right_time
LEFT JOIN `loucka_reconstruction`.`reference_observations` ref ON ref.`observed_at_utc`=a.`dateTime` AND ref.`station_id`='luhamet_sehradice'
LEFT JOIN (SELECT DISTINCT `target_time` FROM `loucka_reconstruction`.`reconstruction_changes` WHERE `variable`='outTemp') ch ON ch.`target_time`=a.`dateTime`
WHERE '''+where+'''\nGROUP BY g.gap_id,g.year_utc\nORDER BY g.year_utc,g.gap_id;\n'''
out=R/'sql/readonly/b5_2014_2015_episode_aggregate.sql';out.write_text('-- READ-ONLY SQL; bounded to frozen 65-gap cohort.\n'+q)
print(out)
