-- Read-only incremental check after reconstruction high-water epoch.
-- Cross-schema access via information_schema; all epochs are UTC Unix seconds.
WITH recent AS (
  SELECT p.dateTime,p.`interval`,p.usUnits,p.outTemp,p.outHumidity,p.rain,p.rainRate,
         p.radiation,p.UV,p.windSpeed,p.windGust,
         LAG(p.dateTime) OVER (ORDER BY p.dateTime) AS prev_time
  FROM `pocasi-loucka.eu`.archive p
  WHERE p.dateTime >= 1793286600
)
SELECT COUNT(*) AS rows_including_anchor,
       SUM(dateTime > 1793286600) AS rows_after_reconstruction_anchor,
       MIN(dateTime) AS first_epoch_utc,MAX(dateTime) AS last_epoch_utc,
       MIN(usUnits) AS usUnits_min,MAX(usUnits) AS usUnits_max,
       SUM(dateTime > 1793286600 AND usUnits <> 16) AS non16_rows,
       SUM(dateTime > 1793286600 AND `interval` <> 5) AS interval_not_5,
       SUM(dateTime > 1793286600 AND outTemp IS NULL) AS null_outTemp,
       SUM(dateTime > 1793286600 AND outHumidity IS NULL) AS null_outHumidity,
       SUM(dateTime > 1793286600 AND rain IS NULL) AS null_rain,
       SUM(dateTime > 1793286600 AND rainRate IS NULL) AS null_rainRate,
       SUM(dateTime > 1793286600 AND radiation IS NULL) AS null_radiation,
       SUM(dateTime > 1793286600 AND UV IS NULL) AS null_UV,
       SUM(dateTime > 1793286600 AND windSpeed IS NULL) AS null_windSpeed,
       SUM(dateTime > 1793286600 AND windGust IS NULL) AS null_windGust,
       SUM(prev_time IS NOT NULL AND dateTime-prev_time=300) AS delta_300s,
       SUM(prev_time IS NOT NULL AND dateTime-prev_time<>300) AS delta_not_300s,
       SUM(CASE WHEN prev_time IS NOT NULL AND dateTime-prev_time>300
                THEN FLOOR((dateTime-prev_time)/300)-1 ELSE 0 END) AS conditional_missing_5m_slots,
       MAX(radiation) AS max_radiation,MAX(UV) AS max_UV,
       SUM(radiation<0 OR radiation>1500) AS radiation_broad_flags,
       SUM(UV<0 OR UV>12) AS UV_broad_flags,
       SUM(windSpeed<0 OR windSpeed>100) AS windSpeed_broad_flags,
       SUM(windGust<0 OR windGust>150) AS windGust_broad_flags
FROM recent;

WITH recent AS (
  SELECT p.dateTime,LAG(p.dateTime) OVER (ORDER BY p.dateTime) AS prev_time
  FROM `pocasi-loucka.eu`.archive p
  WHERE p.dateTime >= 1793286600
)
SELECT prev_time AS previous_epoch,dateTime AS next_epoch,dateTime-prev_time AS delta_seconds
FROM recent
WHERE prev_time IS NOT NULL AND dateTime-prev_time<>300
ORDER BY dateTime;
