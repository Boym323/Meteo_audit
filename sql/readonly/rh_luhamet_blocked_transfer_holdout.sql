-- SELECT-only chronological RH transfer baseline; no application candidates.
-- Uses only observed, no-history target RH and reference_only exact-time pairs.
-- All boundaries are UTC Unix epochs to avoid DB session timezone shifts.
WITH paired AS (
  SELECT a.dateTime,a.outHumidity AS local_rh,
         r.relative_humidity_pct AS ref_rh,
         CASE
           WHEN a.dateTime<1427846400 THEN 1 WHEN a.dateTime<1435708800 THEN 2
           WHEN a.dateTime<1443657600 THEN 3 WHEN a.dateTime<1451606400 THEN 4
           WHEN a.dateTime<1459468800 THEN 1 WHEN a.dateTime<1467331200 THEN 2
           WHEN a.dateTime<1475280000 THEN 3 WHEN a.dateTime<1483228800 THEN 4
           WHEN a.dateTime<1491004800 THEN 1 WHEN a.dateTime<1498867200 THEN 2
           WHEN a.dateTime<1506816000 THEN 3 ELSE 4 END AS utc_quarter
  FROM loucka_reconstruction.archive a
  JOIN loucka_reconstruction.reference_observations r
    ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
  WHERE a.dateTime>=1420070400 AND a.dateTime<1514764800
    AND a.outHumidity BETWEEN 0 AND 100
    AND r.relative_humidity_pct BETWEEN 1 AND 100
    AND r.quality_status='reference_only' AND r.source_resolution='5min'
    AND NOT EXISTS (
      SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
      WHERE c.target_time=a.dateTime AND c.variable='outHumidity'
    )
), global_train AS (
  SELECT COUNT(*) AS train_pairs,AVG(local_rh-ref_rh) AS bias
  FROM paired WHERE dateTime<1483228800
), quarter_train AS (
  SELECT utc_quarter,COUNT(*) AS train_pairs,AVG(local_rh-ref_rh) AS bias
  FROM paired WHERE dateTime<1483228800 GROUP BY utc_quarter
)
SELECT (SELECT train_pairs FROM global_train) AS global_train_pairs,
       (SELECT bias FROM global_train) AS global_train_bias_pp,
       COUNT(*) AS test_pairs,
       AVG(local_rh-ref_rh) AS test_bias_pp,
       AVG(ABS(local_rh-ref_rh)) AS direct_mae_pp,
       SQRT(AVG(POW(local_rh-ref_rh,2))) AS direct_rmse_pp,
       AVG(ABS(local_rh-(ref_rh+global_train.bias))) AS global_offset_mae_pp,
       SQRT(AVG(POW(local_rh-(ref_rh+global_train.bias),2))) AS global_offset_rmse_pp,
       AVG(local_rh-(ref_rh+global_train.bias)) AS global_offset_residual_bias_pp,
       SUM(ref_rh+global_train.bias<0 OR ref_rh+global_train.bias>100) AS global_offset_out_of_range
FROM paired CROSS JOIN global_train
WHERE dateTime>=1483228800 AND dateTime<1514764800;

-- By UTC quarter: direct and train-only global/quarter-specific offset metrics.
WITH paired AS (
  SELECT a.dateTime,a.outHumidity AS local_rh,r.relative_humidity_pct AS ref_rh,
         CASE
           WHEN a.dateTime<1427846400 THEN 1 WHEN a.dateTime<1435708800 THEN 2
           WHEN a.dateTime<1443657600 THEN 3 WHEN a.dateTime<1451606400 THEN 4
           WHEN a.dateTime<1459468800 THEN 1 WHEN a.dateTime<1467331200 THEN 2
           WHEN a.dateTime<1475280000 THEN 3 WHEN a.dateTime<1483228800 THEN 4
           WHEN a.dateTime<1491004800 THEN 1 WHEN a.dateTime<1498867200 THEN 2
           WHEN a.dateTime<1506816000 THEN 3 ELSE 4 END AS utc_quarter
  FROM loucka_reconstruction.archive a
  JOIN loucka_reconstruction.reference_observations r
    ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
  WHERE a.dateTime>=1420070400 AND a.dateTime<1514764800
    AND a.outHumidity BETWEEN 0 AND 100
    AND r.relative_humidity_pct BETWEEN 1 AND 100
    AND r.quality_status='reference_only' AND r.source_resolution='5min'
    AND NOT EXISTS (
      SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
      WHERE c.target_time=a.dateTime AND c.variable='outHumidity'
    )
), global_train AS (
  SELECT AVG(local_rh-ref_rh) bias FROM paired WHERE dateTime<1483228800
), quarter_train AS (
  SELECT utc_quarter,AVG(local_rh-ref_rh) bias
  FROM paired WHERE dateTime<1483228800 GROUP BY utc_quarter
)
SELECT p.utc_quarter,COUNT(*) AS test_pairs,
       AVG(p.local_rh-p.ref_rh) AS test_bias_pp,
       AVG(ABS(p.local_rh-p.ref_rh)) AS direct_mae_pp,
       SQRT(AVG(POW(p.local_rh-p.ref_rh,2))) AS direct_rmse_pp,
       AVG(ABS(p.local_rh-(p.ref_rh+g.bias))) AS global_offset_mae_pp,
       SQRT(AVG(POW(p.local_rh-(p.ref_rh+g.bias),2))) AS global_offset_rmse_pp,
       MAX(q.bias) AS train_quarter_bias_pp,
       AVG(ABS(p.local_rh-(p.ref_rh+q.bias))) AS quarter_offset_mae_pp,
       SQRT(AVG(POW(p.local_rh-(p.ref_rh+q.bias),2))) AS quarter_offset_rmse_pp,
       SUM(p.ref_rh+q.bias<0 OR p.ref_rh+q.bias>100) AS quarter_offset_out_of_range
FROM paired p CROSS JOIN global_train g JOIN quarter_train q ON q.utc_quarter=p.utc_quarter
WHERE p.dateTime>=1483228800 AND p.dateTime<1514764800
GROUP BY p.utc_quarter ORDER BY p.utc_quarter;
