-- READ-ONLY exact target/source/reference state for a P1 NULL outTemp endpoint.
SELECT 'old_weewx' AS db, dateTime, usUnits, `interval`, outTemp, outHumidity, rain, rainRate, windSpeed FROM old_weewx.archive WHERE dateTime BETWEEN 1558340100 AND 1558341300
UNION ALL SELECT 'weewx_WH1080', dateTime, usUnits, `interval`, outTemp, outHumidity, rain, rainRate, windSpeed FROM weewx_WH1080.archive WHERE dateTime BETWEEN 1558340100 AND 1558341300
UNION ALL SELECT 'pocasi-loucka.eu_old', dateTime, usUnits, `interval`, outTemp, outHumidity, rain, rainRate, windSpeed FROM `pocasi-loucka.eu_old`.archive WHERE dateTime=1558341000
UNION ALL SELECT 'pocasi-loucka.eu', dateTime, usUnits, `interval`, outTemp, outHumidity, rain, rainRate, windSpeed FROM `pocasi-loucka.eu`.archive WHERE dateTime=1558341000
UNION ALL SELECT 'pocasi-loucka.eu_GW1000', dateTime, usUnits, `interval`, outTemp, outHumidity, rain, rainRate, windSpeed FROM `pocasi-loucka.eu_GW1000`.archive WHERE dateTime=1558341000
UNION ALL SELECT 'loucka_reconstruction', dateTime, usUnits, `interval`, outTemp, outHumidity, rain, rainRate, windSpeed FROM loucka_reconstruction.archive WHERE dateTime BETWEEN 1558340100 AND 1558341300
ORDER BY dateTime, db;

SELECT observed_at_utc, temperature_c, relative_humidity_pct, source_resolution, quality_status
FROM loucka_reconstruction.reference_observations
WHERE station_id='luhamet_sehradice' AND observed_at_utc BETWEEN 1558340100 AND 1558341300
ORDER BY observed_at_utc;

SELECT variable, state, old_value, new_value, source_database, source_time, source_value
FROM loucka_reconstruction.reconstruction_changes
WHERE target_time=1558341000 ORDER BY variable, state;
