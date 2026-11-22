-- READ-ONLY 2013 exact source-only alignment, six-archive presence and cadence review.
-- Every source-only target key is absent from reconstruction.archive by cohort definition.
SELECT MOD(o.dateTime,300) AS grid_remainder,o.usUnits,o.`interval`,COUNT(*) AS source_only_rows,
       SUM(w.dateTime IS NOT NULL) AS wh_rows,SUM(t.dateTime IS NOT NULL) AS exact_target_rows,
       SUM(r.dateTime IS NOT NULL) AS nearest_reconstruction_rows,
       SUM(r.outTemp<=>o.outTemp) AS nearest_outTemp_equal
FROM archive o LEFT JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=CASE WHEN MOD(o.dateTime,300)<=150 THEN o.dateTime-MOD(o.dateTime,300) ELSE o.dateTime+(300-MOD(o.dateTime,300)) END
WHERE o.dateTime>=1356998400 AND o.dateTime<1388534400 AND t.dateTime IS NULL
GROUP BY MOD(o.dateTime,300),o.usUnits,o.`interval` ORDER BY grid_remainder;

-- Source-copy field equality and non-NULL availability for the exact cohort.
SELECT COUNT(*) AS n,SUM(w.outTemp<=>o.outTemp) AS outTemp_equal,
 SUM(w.outHumidity<=>o.outHumidity) AS outHumidity_equal,SUM(w.rain<=>o.rain) AS rain_equal,
 SUM(w.rainRate<=>o.rainRate) AS rainRate_equal,SUM(w.windSpeed<=>o.windSpeed) AS windSpeed_equal,
 SUM(w.windGust<=>o.windGust) AS windGust_equal,SUM(w.windDir<=>o.windDir) AS windDir_equal,
 SUM(w.barometer<=>o.barometer) AS barometer_equal,SUM(o.outTemp IS NOT NULL) AS outTemp_nonnull,
 SUM(o.outHumidity IS NOT NULL) AS outHumidity_nonnull,SUM(o.rain IS NOT NULL) AS rain_nonnull,
 SUM(o.rainRate IS NOT NULL) AS rainRate_nonnull,SUM(o.windSpeed IS NOT NULL) AS windSpeed_nonnull,
 SUM(o.windGust IS NOT NULL) AS windGust_nonnull,SUM(o.windDir IS NOT NULL) AS windDir_nonnull,
 SUM(o.barometer IS NOT NULL) AS barometer_nonnull
FROM archive o JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=o.dateTime
WHERE o.dateTime>=1356998400 AND o.dateTime<1388534400 AND t.dateTime IS NULL;

-- Three on-grid exact rows; inspect all values and per-archive row presence.
SELECT o.dateTime,o.outTemp,o.outHumidity,o.rain,o.rainRate,o.windSpeed,o.windGust,o.windDir,o.barometer,
       o.usUnits,o.`interval`,w.dateTime AS wh_time,eo.dateTime AS euold_time,
       eu.dateTime AS current_eu_time,gw.dateTime AS gw1000_time,t.dateTime AS reconstruction_time
FROM archive o JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive eo ON eo.dateTime=o.dateTime
LEFT JOIN `pocasi-loucka.eu`.archive eu ON eu.dateTime=o.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive gw ON gw.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=o.dateTime
WHERE o.dateTime>=1356998400 AND o.dateTime<1388534400 AND t.dateTime IS NULL AND MOD(o.dateTime,300)=0
ORDER BY o.dateTime;

-- Local source/target context around 2013-07-09 records; do not interpolate or shift.
SELECT o.dateTime,o.outTemp,o.outHumidity,o.rain,o.rainRate,o.windSpeed,o.windGust,o.windDir,o.barometer,
       t.dateTime AS reconstruction_time,t.outTemp AS reconstruction_outTemp,t.outHumidity AS reconstruction_RH,
       l.temperature_c AS luhamet_T,l.quality_status AS luhamet_quality
FROM archive o LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.reference_observations l ON l.station_id='luhamet_sehradice' AND l.observed_at_utc=o.dateTime
WHERE o.dateTime BETWEEN 1373318400 AND 1373320800 ORDER BY o.dateTime;
