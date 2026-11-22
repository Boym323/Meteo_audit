-- Per-row source-only disposition; exact timestamps only. READ-ONLY.
-- 2015 cohort pre-screened at 2,147 timestamps; Q1 2018 and 2021 are outside scope.
SELECT w.dateTime AS target_time,
       FROM_UNIXTIME(w.dateTime) AS source_time_utc,
       w.usUnits AS wh_usUnits, w.interval AS wh_interval,
       o.usUnits AS old_usUnits, o.interval AS old_interval,
       MOD(w.dateTime,300) AS grid_remainder_s,
       CASE WHEN MOD(w.dateTime,300)<=150 THEN -MOD(w.dateTime,300)
            ELSE 300-MOD(w.dateTime,300) END AS nearest_300s_offset_s,
       w.outTemp AS wh_outTemp, o.outTemp AS old_outTemp,
       w.outHumidity AS wh_outHumidity, o.outHumidity AS old_outHumidity,
       w.rain AS wh_rain, o.rain AS old_rain,
       w.rainRate AS wh_rainRate, o.rainRate AS old_rainRate,
       w.windSpeed AS wh_windSpeed, o.windSpeed AS old_windSpeed,
       w.windGust AS wh_windGust, o.windGust AS old_windGust,
       w.windDir AS wh_windDir, o.windDir AS old_windDir,
       w.barometer AS wh_barometer, o.barometer AS old_barometer,
       w.altimeter AS wh_altimeter, o.altimeter AS old_altimeter,
       w.pressure AS wh_pressure, o.pressure AS old_pressure,
       CASE WHEN r.dateTime IS NULL THEN 0 ELSE 1 END AS reconstruction_exact_row,
       CASE WHEN m.dateTime IS NULL THEN 0 ELSE 1 END AS merged_exact_row,
       CASE WHEN w.outTemp IS NULL THEN 'MISSING' ELSE 'SOURCE_PRESENT' END AS wh_temperature_availability,
       CASE WHEN o.outTemp IS NULL THEN 'MISSING' ELSE 'SOURCE_PRESENT' END AS old_temperature_availability,
       CASE WHEN w.altimeter <=> o.altimeter THEN 'AGREE' ELSE 'CONFLICT' END AS altimeter_copy_status,
       CASE WHEN w.rain <=> o.rain THEN 'AGREE' ELSE 'CONFLICT' END AS rain_copy_status,
       CASE WHEN w.rainRate <=> o.rainRate THEN 'AGREE' ELSE 'CONFLICT' END AS rainrate_copy_status,
       'UNRESOLVED_SOURCE_ONLY' AS disposition
FROM weewx_WH1080.archive w
JOIN old_weewx.archive o ON o.dateTime=w.dateTime
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=w.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive m ON m.dateTime=w.dateTime
WHERE w.dateTime >= 1420070400 AND w.dateTime < 1451606400
  AND r.dateTime IS NULL AND m.dateTime IS NULL
ORDER BY w.dateTime;
