WITH p AS (SELECT 1685274900 AS left_ts,1685332200 AS right_ts,30 AS window_days),
e AS (SELECT p.left_ts,p.right_ts,p.window_days,l.outTemp AS left_temp,r.outTemp AS right_temp FROM p LEFT JOIN loucka_reconstruction.archive l ON l.dateTime=p.left_ts LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=p.right_ts),
source_rows AS (
 SELECT 'SOURCE_GAP_2023_MAY' AS segment,a.dateTime,a.outTemp AS station_temp,ref.temperature_c AS reference_temp,
 e.left_temp+(e.right_temp-e.left_temp)*(a.dateTime-e.left_ts)/(e.right_ts-e.left_ts) AS interpolation_temp
 FROM `pocasi-loucka.eu_old`.archive a CROSS JOIN e
 LEFT JOIN loucka_reconstruction.reference_observations ref ON ref.station_id='luhamet_sehradice' AND ref.observed_at_utc=a.dateTime
 WHERE a.dateTime>e.left_ts AND a.dateTime<e.right_ts),
baseline AS (
 SELECT CASE WHEN a.dateTime<e.left_ts THEN 'LOCAL_REFERENCE_30D_BEFORE' ELSE 'LOCAL_REFERENCE_30D_AFTER' END AS segment,
 a.dateTime,a.outTemp AS station_temp,ref.temperature_c AS reference_temp,CAST(NULL AS DECIMAL(12,5)) AS interpolation_temp
 FROM loucka_reconstruction.archive a CROSS JOIN e
 LEFT JOIN loucka_reconstruction.reference_observations ref ON ref.station_id='luhamet_sehradice' AND ref.observed_at_utc=a.dateTime
 WHERE a.interval=5 AND a.outTemp IS NOT NULL
 AND ((a.dateTime>=e.left_ts-e.window_days*86400 AND a.dateTime<e.left_ts) OR (a.dateTime>e.right_ts AND a.dateTime<=e.right_ts+e.window_days*86400))
 AND NOT EXISTS (SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=a.dateTime AND c.variable='outTemp')),
all_rows AS (SELECT * FROM source_rows UNION ALL SELECT * FROM baseline)
SELECT segment,COUNT(*) AS rows_total,SUM(station_temp IS NOT NULL) AS station_temp_nonnull,SUM(reference_temp IS NOT NULL) AS exact_reference_pairs,
 AVG(station_temp-reference_temp) AS station_minus_reference_bias_c,AVG(ABS(station_temp-reference_temp)) AS station_reference_mae_c,MAX(ABS(station_temp-reference_temp)) AS station_reference_max_abs_c,
 AVG(station_temp-interpolation_temp) AS source_minus_interpolation_bias_c,AVG(ABS(station_temp-interpolation_temp)) AS source_interpolation_mae_c,MAX(ABS(station_temp-interpolation_temp)) AS source_interpolation_max_abs_c,
 MIN(station_temp) AS source_or_target_temp_min_c,MAX(station_temp) AS source_or_target_temp_max_c,MIN(reference_temp) AS reference_temp_min_c,MAX(reference_temp) AS reference_temp_max_c
FROM all_rows GROUP BY segment ORDER BY segment