-- SELECT-only comparison of direct RH and a simple equal-vapor-pressure
-- station transfer, including water/ice sensitivity for sub-zero pairs.
-- WMO Annex 4.B pure-phase e_s approximations; UTC epoch bounds.
WITH p AS (
  SELECT a.dateTime,a.outHumidity AS local_rh,a.outTemp AS local_t,
         r.relative_humidity_pct AS ref_rh,r.temperature_c AS ref_t,
         CASE
           WHEN a.dateTime<1427846400 THEN 1 WHEN a.dateTime<1435708800 THEN 2
           WHEN a.dateTime<1443657600 THEN 3 WHEN a.dateTime<1451606400 THEN 4
           WHEN a.dateTime<1459468800 THEN 1 WHEN a.dateTime<1467331200 THEN 2
           WHEN a.dateTime<1475280000 THEN 3 WHEN a.dateTime<1483228800 THEN 4
           WHEN a.dateTime<1491004800 THEN 1 WHEN a.dateTime<1498867200 THEN 2
           WHEN a.dateTime<1506816000 THEN 3 ELSE 4 END AS utc_quarter,
         6.112*EXP(17.62*r.temperature_c/(243.12+r.temperature_c)) AS ew_ref,
         6.112*EXP(17.62*a.outTemp/(243.12+a.outTemp)) AS ew_local,
         6.112*EXP(22.46*r.temperature_c/(272.62+r.temperature_c)) AS ei_ref,
         6.112*EXP(22.46*a.outTemp/(272.62+a.outTemp)) AS ei_local
  FROM loucka_reconstruction.archive a
  JOIN loucka_reconstruction.reference_observations r
    ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
  WHERE a.dateTime>=1420070400 AND a.dateTime<1514764800
    AND a.outHumidity BETWEEN 0 AND 100 AND a.outTemp BETWEEN -45 AND 60
    AND r.temperature_c BETWEEN -45 AND 60
    AND r.relative_humidity_pct BETWEEN 1 AND 100
    AND r.quality_status='reference_only' AND r.source_resolution='5min'
    AND NOT EXISTS (
      SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
      WHERE c.target_time=a.dateTime AND c.variable IN ('outHumidity','outTemp')
    )
), global_train AS (
  SELECT COUNT(*) AS n,AVG(local_rh-ref_rh) AS bias
  FROM p WHERE dateTime<1483228800
), quarter_train AS (
  SELECT utc_quarter,AVG(local_rh-ref_rh) AS bias
  FROM p WHERE dateTime<1483228800 GROUP BY utc_quarter
), predictions AS (
  SELECT p.*,g.bias AS global_bias,q.bias AS quarter_bias,
         ref_rh*ew_ref/ew_local AS rh_hat_water,
         ref_rh*ei_ref/ei_local AS rh_hat_ice
  FROM p CROSS JOIN global_train g JOIN quarter_train q ON q.utc_quarter=p.utc_quarter
)
SELECT MAX(global_train.n) AS train_n,
       MAX(global_train.bias) AS train_bias_pp,
       COUNT(*) AS test_n,
       AVG(ABS(local_rh-ref_rh)) AS direct_mae_pp,
       SQRT(AVG(POW(local_rh-ref_rh,2))) AS direct_rmse_pp,
       AVG(ABS(local_rh-(ref_rh+global_bias))) AS global_bias_mae_pp,
       SQRT(AVG(POW(local_rh-(ref_rh+global_bias),2))) AS global_bias_rmse_pp,
       AVG(ABS(local_rh-(ref_rh+quarter_bias))) AS quarter_bias_mae_pp,
       SQRT(AVG(POW(local_rh-(ref_rh+quarter_bias),2))) AS quarter_bias_rmse_pp,
       AVG(ABS(local_rh-rh_hat_water)) AS vapor_water_mae_pp,
       SQRT(AVG(POW(local_rh-rh_hat_water,2))) AS vapor_water_rmse_pp,
       SUM(rh_hat_water<0 OR rh_hat_water>100) AS vapor_water_out_of_range,
       SUM(local_t<0 AND ref_t<0) AS cold_pairs,
       AVG(CASE WHEN local_t<0 AND ref_t<0 THEN ABS(local_rh-rh_hat_water) END) AS cold_water_mae_pp,
       SQRT(AVG(CASE WHEN local_t<0 AND ref_t<0 THEN POW(local_rh-rh_hat_water,2) END)) AS cold_water_rmse_pp,
       AVG(CASE WHEN local_t<0 AND ref_t<0 THEN ABS(local_rh-rh_hat_ice) END) AS cold_ice_mae_pp,
       SQRT(AVG(CASE WHEN local_t<0 AND ref_t<0 THEN POW(local_rh-rh_hat_ice,2) END)) AS cold_ice_rmse_pp,
       SUM(local_t<0 AND ref_t<0 AND (rh_hat_ice<0 OR rh_hat_ice>100)) AS cold_ice_out_of_range
FROM predictions CROSS JOIN global_train
WHERE dateTime>=1483228800 AND dateTime<1514764800;
