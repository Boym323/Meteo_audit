-- Focused rows where available primary values disagree across old_weewx and WH1080.
-- READ-ONLY, bounded UTC 2012 source-only cohort.
SELECT w.dateTime,w.usUnits AS wh_units,w.`interval` AS wh_interval,
       w.outTemp AS wh_temp,w.outHumidity AS wh_rh,w.rain AS wh_rain,
       w.rainRate AS wh_rate,w.windSpeed AS wh_wind,
       o.usUnits AS old_units,o.`interval` AS old_interval,
       o.outTemp AS old_temp,o.outHumidity AS old_rh,o.rain AS old_rain,
       o.rainRate AS old_rate,o.windSpeed AS old_wind,
       s.usUnits AS site_units,s.`interval` AS site_interval,
       s.outTemp AS site_temp,s.outHumidity AS site_rh,s.rain AS site_rain,
       s.rainRate AS site_rate,s.windSpeed AS site_wind,
       FLOOR((w.dateTime+150)/300)*300 AS nearest_target_time,
       t.outTemp AS target_temp,t.outHumidity AS target_rh,t.rain AS target_rain,
       t.rainRate AS target_rate,t.windSpeed AS target_wind
FROM weewx_WH1080.archive w
JOIN old_weewx.archive o ON o.dateTime=w.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive s ON s.dateTime=w.dateTime
LEFT JOIN loucka_reconstruction.archive x ON x.dateTime=w.dateTime
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=FLOOR((w.dateTime+150)/300)*300
WHERE w.dateTime>=1325376000 AND w.dateTime<1356998400
  AND w.usUnits=17 AND w.`interval`=5 AND x.dateTime IS NULL
  AND (NOT(w.outTemp <=> o.outTemp)
    OR NOT(w.outHumidity <=> o.outHumidity)
    OR NOT(w.rain <=> o.rain)
    OR NOT(w.rainRate <=> o.rainRate)
    OR NOT(w.windSpeed <=> o.windSpeed))
ORDER BY w.dateTime;
