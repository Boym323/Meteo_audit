-- READ-ONLY exact-time external regional context for the 2019-05-19/20 source-only block.
-- Query independently sums errors over only rows with both source-copy equality and a local reference.
SELECT COUNT(*) AS n,
       SUM(r.temperature_c IS NOT NULL) AS paired_temp,
       SUM(r.relative_humidity_pct IS NOT NULL) AS paired_rh,
       ROUND(AVG(ABS(a.outTemp-r.temperature_c)),3) AS temp_mae_c,
       ROUND(AVG(a.outTemp-r.temperature_c),3) AS temp_bias_c,
       ROUND(MAX(ABS(a.outTemp-r.temperature_c)),3) AS temp_max_abs_error_c,
       SUM(ABS(a.outTemp-r.temperature_c)>1) AS temp_error_gt1,
       SUM(ABS(a.outTemp-r.temperature_c)>2) AS temp_error_gt2,
       SUM(ABS(a.outTemp-r.temperature_c)>3) AS temp_error_gt3,
       ROUND(AVG(ABS(a.outHumidity-r.relative_humidity_pct)),2) AS rh_mae_pct,
       ROUND(MAX(ABS(a.outHumidity-r.relative_humidity_pct)),2) AS rh_max_abs_error_pct,
       MIN(a.outHumidity) AS source_rh_min, MAX(a.outHumidity) AS source_rh_max,
       MIN(r.relative_humidity_pct) AS ref_rh_min, MAX(r.relative_humidity_pct) AS ref_rh_max,
       SUM(r.quality_status<>'reference_only') AS non_reference_only
FROM old_weewx.archive a
JOIN weewx_WH1080.archive w ON w.dateTime=a.dateTime
 AND w.outTemp <=> a.outTemp AND w.outHumidity <=> a.outHumidity
 AND w.rain <=> a.rain AND w.rainRate <=> a.rainRate AND w.windSpeed <=> a.windSpeed
JOIN loucka_reconstruction.reference_observations r
 ON r.observed_at_utc=a.dateTime AND r.station_id='luhamet_sehradice'
WHERE a.dateTime BETWEEN 1558259700 AND 1558341000
 AND a.interval=5 AND a.usUnits=17
 AND a.outTemp IS NOT NULL AND a.outHumidity IS NOT NULL
 AND a.rain IS NOT NULL AND a.rainRate IS NOT NULL AND a.windSpeed IS NOT NULL
 AND NOT EXISTS (SELECT 1 FROM loucka_reconstruction.archive t WHERE t.dateTime=a.dateTime);
