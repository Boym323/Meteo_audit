-- Bounded UTC 2012 off-grid source-only rows and nearest target-slot availability.
-- READ-ONLY. Values are summarized locally; no row is proposed for shifting/insertion.
WITH source_rows AS (
 SELECT w.dateTime,w.usUnits AS wh_units,w.`interval` AS wh_interval,
        w.outTemp AS wh_temp,w.outHumidity AS wh_rh,w.rain AS wh_rain,
        w.rainRate AS wh_rate,w.windSpeed AS wh_wind,
        o.usUnits AS old_units,o.`interval` AS old_interval,
        o.outTemp AS old_temp,o.outHumidity AS old_rh,o.rain AS old_rain,
        o.rainRate AS old_rate,o.windSpeed AS old_wind,
        s.usUnits AS site_units,s.`interval` AS site_interval,
        s.outTemp AS site_temp,s.outHumidity AS site_rh,s.rain AS site_rain,
        s.rainRate AS site_rate,s.windSpeed AS site_wind,
        FLOOR((w.dateTime+150)/300)*300 AS nearest_300,
        t.dateTime AS target_time,t.usUnits AS target_units,t.`interval` AS target_interval
 FROM weewx_WH1080.archive w
 JOIN old_weewx.archive o ON o.dateTime=w.dateTime
 LEFT JOIN `pocasi-loucka.eu_old`.archive s ON s.dateTime=w.dateTime
 LEFT JOIN loucka_reconstruction.archive x ON x.dateTime=w.dateTime
 LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=FLOOR((w.dateTime+150)/300)*300
 WHERE w.dateTime>=1325376000 AND w.dateTime<1356998400
   AND w.usUnits=17 AND w.`interval`=5 AND x.dateTime IS NULL
)
SELECT dateTime%300 AS epoch_remainder,dateTime-nearest_300 AS offset_seconds,
 COUNT(*) AS timestamps,
 SUM(target_time IS NOT NULL) AS nearest_target_present,
 SUM(site_units IS NOT NULL) AS third_archive_present,
 SUM(wh_temp=old_temp) AS temp_equal,SUM(wh_temp<>old_temp) AS temp_conflicts,
 SUM(wh_rh IS NOT NULL AND old_rh IS NOT NULL AND wh_rh=old_rh) AS rh_equal,
 SUM(wh_rh IS NOT NULL AND old_rh IS NOT NULL AND wh_rh<>old_rh) AS rh_conflicts,
 SUM(wh_rain IS NOT NULL AND old_rain IS NOT NULL AND wh_rain=old_rain) AS rain_equal,
 SUM(wh_rate IS NOT NULL AND old_rate IS NOT NULL AND wh_rate=old_rate) AS rate_equal,
 SUM(wh_wind IS NOT NULL AND old_wind IS NOT NULL AND wh_wind=old_wind) AS wind_equal,
 SUM(wh_temp=0) AS wh_zero_temp,SUM(wh_rh IS NULL) AS wh_rh_null,
 MIN(dateTime) AS first_source_time,MAX(dateTime) AS last_source_time,
 SUM(target_interval=5) AS nearest_5min_rows,SUM(target_interval=6) AS nearest_6min_rows
FROM source_rows
GROUP BY epoch_remainder,offset_seconds
ORDER BY timestamps DESC;

-- Collision profile for nearest projected slots, kept separate from exact source rows.
WITH src AS (
 SELECT DISTINCT w.dateTime,FLOOR((w.dateTime+150)/300)*300 AS nearest_300
 FROM weewx_WH1080.archive w
 JOIN old_weewx.archive o ON o.dateTime=w.dateTime
 LEFT JOIN loucka_reconstruction.archive x ON x.dateTime=w.dateTime
 WHERE w.dateTime>=1325376000 AND w.dateTime<1356998400
   AND w.usUnits=17 AND w.`interval`=5 AND x.dateTime IS NULL
), per_slot AS (SELECT nearest_300,COUNT(*) AS source_times FROM src GROUP BY nearest_300)
SELECT source_times,COUNT(*) AS nearest_slot_count FROM per_slot
GROUP BY source_times ORDER BY source_times;

-- Existing change history at projected target slots, not at source-only timestamps.
WITH src AS (
 SELECT DISTINCT w.dateTime,FLOOR((w.dateTime+150)/300)*300 AS nearest_300
 FROM weewx_WH1080.archive w
 JOIN old_weewx.archive o ON o.dateTime=w.dateTime
 LEFT JOIN loucka_reconstruction.archive x ON x.dateTime=w.dateTime
 WHERE w.dateTime>=1325376000 AND w.dateTime<1356998400
   AND w.usUnits=17 AND w.`interval`=5 AND x.dateTime IS NULL
), k AS (SELECT DISTINCT nearest_300 FROM src)
SELECT c.variable,c.state,COUNT(*) AS event_rows,
 COUNT(DISTINCT c.target_time) AS target_times,
 MIN(c.target_time) AS first_target,MAX(c.target_time) AS last_target
FROM k JOIN loucka_reconstruction.reconstruction_changes c ON c.target_time=k.nearest_300
GROUP BY c.variable,c.state ORDER BY c.variable,c.state;
