-- READ-ONLY exact-time regional temperature cross-check for the 36-row 2019 RH-NULL cohort.
SELECT COUNT(DISTINCT a.dateTime) AS source_only_grid_rows,
       COUNT(DISTINCT CASE WHEN r.temperature_c IS NOT NULL THEN a.dateTime END) AS exact_luhamet_T_pairs,
       ROUND(AVG(ABS(a.outTemp-r.temperature_c)),3) AS temp_mae_c,
       ROUND(AVG(a.outTemp-r.temperature_c),3) AS temp_bias_c,
       ROUND(MAX(ABS(a.outTemp-r.temperature_c)),3) AS temp_max_abs_error_c,
       SUM(ABS(a.outTemp-r.temperature_c)>1) AS ref_error_gt1_count,
       SUM(ABS(a.outTemp-r.temperature_c)>2) AS ref_error_gt2_count,
       SUM(ABS(a.outTemp-r.temperature_c)>3) AS ref_error_gt3_count,
       MIN(a.outTemp) AS source_temp_min, MAX(a.outTemp) AS source_temp_max,
       MIN(r.temperature_c) AS luhamet_temp_min, MAX(r.temperature_c) AS luhamet_temp_max
FROM old_weewx.archive a
JOIN weewx_WH1080.archive w ON w.dateTime=a.dateTime
 AND w.outTemp <=> a.outTemp AND w.rain <=> a.rain
 AND w.rainRate <=> a.rainRate AND w.windSpeed <=> a.windSpeed
 AND w.outHumidity IS NULL
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=a.dateTime
LEFT JOIN loucka_reconstruction.reference_observations r
 ON r.observed_at_utc=a.dateTime AND r.station_id='luhamet_sehradice'
 AND r.quality_status='reference_only'
WHERE a.dateTime BETWEEN 1558260000 AND 1558283100
 AND a.usUnits=17 AND w.usUnits=17 AND a.interval=5 AND w.interval=5
 AND MOD(a.dateTime,300)=0 AND a.outTemp IS NOT NULL AND a.outHumidity IS NULL
 AND a.rain IS NOT NULL AND a.rainRate IS NOT NULL AND a.windSpeed IS NOT NULL
 AND t.dateTime IS NULL;
