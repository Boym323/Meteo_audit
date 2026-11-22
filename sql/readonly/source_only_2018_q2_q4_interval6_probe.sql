-- Single UTC Q3 2018 interval-6 source-only row; diagnostic nearest-target lookup.
-- READ-ONLY only. The surrounding Q1 2018 period is excluded.
SELECT w.dateTime,w.usUnits,w.`interval`,w.outTemp,w.outHumidity,w.rain,w.rainRate,w.windSpeed,
       o.usUnits AS old_units,o.`interval` AS old_interval,o.outTemp AS old_temp,o.outHumidity AS old_rh,
       o.rain AS old_rain,o.rainRate AS old_rate,o.windSpeed AS old_wind,
       s.usUnits AS site_units,s.`interval` AS site_interval,s.outTemp AS site_temp,s.outHumidity AS site_rh,
       s.rain AS site_rain,s.rainRate AS site_rate,s.windSpeed AS site_wind,
       FLOOR((w.dateTime+150)/300)*300 AS nearest_300,
       t.dateTime AS nearest_target_time,t.usUnits AS target_units,t.`interval` AS target_interval,
       t.outTemp AS target_temp,t.outHumidity AS target_rh,t.rain AS target_rain,
       t.rainRate AS target_rate,t.windSpeed AS target_wind
FROM weewx_WH1080.archive w
JOIN old_weewx.archive o ON o.dateTime=w.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive s ON s.dateTime=w.dateTime
LEFT JOIN loucka_reconstruction.archive x ON x.dateTime=w.dateTime
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=FLOOR((w.dateTime+150)/300)*300
WHERE w.dateTime=1534221780 AND w.usUnits=17 AND w.`interval`=6 AND x.dateTime IS NULL;
