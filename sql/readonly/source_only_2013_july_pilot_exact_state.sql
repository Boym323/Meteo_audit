-- READ-ONLY exact source and current target state for the 2013-07-08 21:30–21:50 UTC candidate episode.
START TRANSACTION READ ONLY;
SELECT w.dateTime,w.usUnits AS wh_units,w.`interval` AS wh_interval,
 w.outTemp AS wh_outTemp,w.outHumidity AS wh_outHumidity,w.rain AS wh_rain,w.rainRate AS wh_rainRate,w.windSpeed AS wh_windSpeed,
 s.usUnits AS old_units,s.`interval` AS old_interval,s.outTemp AS old_outTemp,s.outHumidity AS old_outHumidity,
 s.rain AS old_rain,s.rainRate AS old_rainRate,s.windSpeed AS old_windSpeed,
 t.dateTime IS NOT NULL AS target_row_present,t.usUnits AS target_units,t.`interval` AS target_interval,
 t.outTemp AS target_outTemp,t.outHumidity AS target_outHumidity,
 so.dateTime IS NOT NULL AS site_old_row_present,p.dateTime IS NOT NULL AS gw3000_row_present,g.dateTime IS NOT NULL AS gw1000_row_present,
 (SELECT COUNT(*) FROM `loucka_reconstruction`.reconstruction_changes c WHERE c.target_time=w.dateTime) AS change_events_all_variables
FROM `weewx_WH1080`.archive w
JOIN `old_weewx`.archive s ON s.dateTime=w.dateTime
LEFT JOIN `loucka_reconstruction`.archive t ON t.dateTime=w.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive so ON so.dateTime=w.dateTime
LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=w.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=w.dateTime
WHERE w.dateTime IN (1373319000,1373319600,1373320200,1373320800)
ORDER BY w.dateTime;
