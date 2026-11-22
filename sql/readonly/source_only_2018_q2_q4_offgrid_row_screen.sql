-- Bounded row-level screen for unprotected 2018 Q2-Q4 source-only rows.
-- READ-ONLY only; fixed UTC range [2018-04-01, 2019-01-01).
WITH source_rows AS (
 SELECT w.dateTime, w.usUnits AS wh_units, w.`interval` AS wh_interval,
        w.outTemp AS wh_temp, w.outHumidity AS wh_rh, w.rain AS wh_rain,
        w.rainRate AS wh_rate, w.windSpeed AS wh_wind,
        o.usUnits AS old_units, o.`interval` AS old_interval,
        o.outTemp AS old_temp, o.outHumidity AS old_rh, o.rain AS old_rain,
        o.rainRate AS old_rate, o.windSpeed AS old_wind,
        so.usUnits AS site_units, so.`interval` AS site_interval,
        so.outTemp AS site_temp, so.outHumidity AS site_rh, so.rain AS site_rain,
        so.rainRate AS site_rate, so.windSpeed AS site_wind,
        FLOOR((w.dateTime + 150) / 300) * 300 AS nearest_300
 FROM weewx_WH1080.archive w
 JOIN old_weewx.archive o ON o.dateTime=w.dateTime
 LEFT JOIN `pocasi-loucka.eu_old`.archive so ON so.dateTime=w.dateTime
 LEFT JOIN loucka_reconstruction.archive exact_target ON exact_target.dateTime=w.dateTime
 WHERE w.dateTime >= 1522540800 AND w.dateTime < 1546300800
   AND w.`interval`=5 AND w.usUnits=17
   AND exact_target.dateTime IS NULL
)
SELECT s.*, (s.dateTime % 300) AS epoch_remainder,
       s.dateTime-s.nearest_300 AS offset_to_nearest_300,
       t.dateTime AS nearest_target_time,t.usUnits AS target_units,t.`interval` AS target_interval,
       t.outTemp AS target_temp,t.outHumidity AS target_rh,t.rain AS target_rain,
       t.rainRate AS target_rate,t.windSpeed AS target_wind
FROM source_rows s
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=s.nearest_300
ORDER BY s.dateTime;
