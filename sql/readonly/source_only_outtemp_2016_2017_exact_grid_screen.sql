-- READ-ONLY strict source-only exact-pair screen for 2016–2017.
-- Scope: reconstruction row absent; both legacy archives present; identical UTC timestamp;
-- both usUnits=17, both interval=5 min, exact 300-second epoch grid.
-- This is a source availability/quality screen, not proof of expected schedule or restoration eligibility.
WITH paired AS (
 SELECT o.dateTime, o.usUnits AS old_units, w.usUnits AS wh_units,
        o.`interval` AS old_interval, w.`interval` AS wh_interval,
        o.outTemp AS old_outTemp, w.outTemp AS wh_outTemp,
        o.outHumidity AS old_outHumidity, w.outHumidity AS wh_outHumidity,
        o.rain AS old_rain, w.rain AS wh_rain,
        o.rainRate AS old_rainRate, w.rainRate AS wh_rainRate,
        o.windSpeed AS old_windSpeed, w.windSpeed AS wh_windSpeed
 FROM old_weewx.archive o
 JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=o.dateTime
 WHERE o.dateTime >= 1451606400 AND o.dateTime < 1514764800
   AND r.dateTime IS NULL
   AND o.dateTime % 300 = 0
   AND o.usUnits=17 AND w.usUnits=17
   AND o.`interval`=5 AND w.`interval`=5
)
SELECT CASE WHEN dateTime < 1483228800 THEN 2016 ELSE 2017 END AS utc_year,
 COUNT(*) AS source_rows,
 SUM(old_outTemp IS NOT NULL) AS old_outTemp_nonnull,
 SUM(wh_outTemp IS NOT NULL) AS wh1080_outTemp_nonnull,
 SUM(old_outTemp IS NOT NULL AND wh_outTemp IS NOT NULL) AS both_outTemp_nonnull,
 SUM(old_outTemp IS NOT NULL AND wh_outTemp IS NOT NULL AND old_outTemp=wh_outTemp) AS equal_outTemp,
 SUM(old_outTemp=0) AS old_outTemp_zero,
 SUM(wh_outTemp=0) AS wh1080_outTemp_zero,
 SUM(old_outHumidity IS NOT NULL) AS old_outHumidity_nonnull,
 SUM(wh_outHumidity IS NOT NULL) AS wh1080_outHumidity_nonnull,
 SUM(old_rain IS NOT NULL) AS old_rain_nonnull,
 SUM(wh_rain IS NOT NULL) AS wh1080_rain_nonnull,
 SUM(old_rainRate IS NOT NULL) AS old_rainRate_nonnull,
 SUM(wh_rainRate IS NOT NULL) AS wh1080_rainRate_nonnull,
 SUM(old_windSpeed IS NOT NULL) AS old_windSpeed_nonnull,
 SUM(wh_windSpeed IS NOT NULL) AS wh1080_windSpeed_nonnull,
 MIN(dateTime) AS first_timestamp, MAX(dateTime) AS last_timestamp
FROM paired
GROUP BY utc_year
ORDER BY utc_year;
