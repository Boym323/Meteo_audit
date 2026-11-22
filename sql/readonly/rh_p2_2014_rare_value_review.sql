-- READ-ONLY exact-target audit of 12 lower-frequency 2014 RH source-copy candidates.
-- Candidate timestamps were selected from the existing 2014 null-target cohort
-- (RH values 30, 43, 46, 60, 97). No writes or staging.
SELECT t.ts,
r.outTemp r_T,r.outHumidity r_RH,r.rain r_rain,r.rainRate r_rr,r.windSpeed r_wind,r.windGust r_gust,r.windDir r_dir,r.barometer r_baro,r.usUnits r_units,r.`interval` r_interval,
eo.outTemp eo_T,eo.outHumidity eo_RH,eo.rain eo_rain,eo.rainRate eo_rr,eo.windSpeed eo_wind,eo.windGust eo_gust,eo.windDir eo_dir,eo.barometer eo_baro,eo.usUnits eo_units,eo.`interval` eo_interval,
o.outTemp old_T,o.outHumidity old_RH,o.rain old_rain,o.rainRate old_rr,o.windSpeed old_wind,o.windGust old_gust,o.windDir old_dir,o.barometer old_baro,o.usUnits old_units,o.`interval` old_interval,
w.outTemp wh_T,w.outHumidity wh_RH,w.rain wh_rain,w.rainRate wh_rr,w.windSpeed wh_wind,w.windGust wh_gust,w.windDir wh_dir,w.barometer wh_baro,w.usUnits wh_units,w.`interval` wh_interval,
(SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes h WHERE h.target_time=t.ts AND h.variable='outHumidity') rh_events
FROM (SELECT 1400943900 ts UNION ALL SELECT 1400944200 UNION ALL SELECT 1400944500 UNION ALL SELECT 1400944800 UNION ALL SELECT 1400945100 UNION ALL SELECT 1400945400 UNION ALL SELECT 1401643800 UNION ALL SELECT 1406126100 UNION ALL SELECT 1406126400 UNION ALL SELECT 1406126700 UNION ALL SELECT 1406130900 UNION ALL SELECT 1406133600) t
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=t.ts
LEFT JOIN `pocasi-loucka.eu_old`.archive eo ON eo.dateTime=t.ts
LEFT JOIN old_weewx.archive o ON o.dateTime=t.ts
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=t.ts
ORDER BY t.ts;
