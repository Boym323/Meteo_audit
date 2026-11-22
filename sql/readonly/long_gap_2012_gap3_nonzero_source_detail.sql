-- READ-ONLY source-row profile for long-gap catalog event 3.
-- The interval is open: reconstruction endpoints 2011-08-15 20:05Z to
-- 2012-03-01 09:25Z; source presence never proves the gap cause or validity.
SELECT COUNT(*) AS paired_interior_rows,
 SUM(o.outTemp<>0) AS nonzero_temperature_rows,
 SUM(o.outTemp=0) AS zero_temperature_rows,
 SUM(MOD(o.dateTime,300)=0) AS epoch_grid_rows,
 SUM(MOD(o.dateTime,300)<>0) AS offgrid_rows,
 SUM(o.outTemp=w.outTemp) AS exact_temperature_matches,
 SUM(o.outHumidity=w.outHumidity OR (o.outHumidity IS NULL AND w.outHumidity IS NULL)) AS RH_equal_or_both_null,
 SUM(NOT(o.outHumidity=w.outHumidity OR (o.outHumidity IS NULL AND w.outHumidity IS NULL))) AS RH_conflicts,
 SUM(o.rain=w.rain OR (o.rain IS NULL AND w.rain IS NULL)) AS rain_equal_or_both_null,
 SUM(o.rainRate=w.rainRate OR (o.rainRate IS NULL AND w.rainRate IS NULL)) AS rainRate_equal_or_both_null,
 MIN(o.outTemp) AS min_outTemp,MAX(o.outTemp) AS max_outTemp,COUNT(DISTINCT o.outTemp) AS distinct_outTemp,
 MIN(o.outHumidity) AS min_outHumidity,MAX(o.outHumidity) AS max_outHumidity,COUNT(DISTINCT o.outHumidity) AS distinct_outHumidity,
 MIN(o.rain) AS min_rain,MAX(o.rain) AS max_rain,COUNT(DISTINCT o.rain) AS distinct_rain,
 MIN(o.rainRate) AS min_rainRate,MAX(o.rainRate) AS max_rainRate,COUNT(DISTINCT o.rainRate) AS distinct_rainRate,
 MIN(o.usUnits) AS min_usUnits,MAX(o.usUnits) AS max_usUnits,
 MIN(o.`interval`) AS min_interval,MAX(o.`interval`) AS max_interval
FROM old_weewx.archive o
JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=o.dateTime
WHERE o.dateTime>1313445900 AND o.dateTime<1330593900 AND r.dateTime IS NULL;

-- Exact nonzero tuple groups; values remain stored raw according to usUnits=17.
SELECT o.outTemp,o.outHumidity,o.rain,o.rainRate,o.windSpeed,o.windGust,
 COUNT(*) AS row_count,MIN(o.dateTime) AS first_ts,MAX(o.dateTime) AS last_ts,
 COUNT(DISTINCT o.dateTime) AS distinct_timestamps
FROM old_weewx.archive o
JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=o.dateTime
WHERE o.dateTime>1313445900 AND o.dateTime<1330593900 AND r.dateTime IS NULL
 AND o.outTemp<>0 AND o.outTemp=w.outTemp
 AND (o.outHumidity=w.outHumidity OR (o.outHumidity IS NULL AND w.outHumidity IS NULL))
 AND (o.rain=w.rain OR (o.rain IS NULL AND w.rain IS NULL))
 AND (o.rainRate=w.rainRate OR (o.rainRate IS NULL AND w.rainRate IS NULL))
GROUP BY o.outTemp,o.outHumidity,o.rain,o.rainRate,o.windSpeed,o.windGust
ORDER BY row_count DESC;
