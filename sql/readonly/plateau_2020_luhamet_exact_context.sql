-- SELECT-only exact-timestamp context for the eight 2020 RH=100 plateau episodes.
-- No nearest-time alignment; LuhaMet is regional context, not local ground truth.
WITH episodes AS (
    SELECT 1 AS episode_id, 1608650100 AS start_epoch, 1608883200 AS end_epoch UNION ALL
    SELECT 2,1601047200,1601192700 UNION ALL
    SELECT 3,1604258400,1604399700 UNION ALL
    SELECT 4,1604401800,1604525400 UNION ALL
    SELECT 5,1604085000,1604223900 UNION ALL
    SELECT 6,1603931700,1603997400 UNION ALL
    SELECT 7,1601413200,1601469600 UNION ALL
    SELECT 8,1608423000,1608468900
)
SELECT e.episode_id, e.start_epoch, e.end_epoch,
       COUNT(a.dateTime) AS loucka_rows,
       MIN(a.outTemp) AS loucka_outtemp_min_c,
       MAX(a.outTemp) AS loucka_outtemp_max_c,
       COUNT(r.observed_at_utc) AS exact_luhamet_pairs,
       GROUP_CONCAT(DISTINCT r.quality_status) AS ref_quality_statuses,
       GROUP_CONCAT(DISTINCT r.source_resolution) AS ref_source_resolutions,
       COUNT(r.relative_humidity_pct) AS luhamet_rh_nonnull_pairs,
       SUM(CASE WHEN r.relative_humidity_pct = 0 THEN 1 ELSE 0 END) AS luhamet_rh_zero_pairs,
       SUM(CASE WHEN r.relative_humidity_pct > 0 AND r.relative_humidity_pct < 15 THEN 1 ELSE 0 END) AS luhamet_rh_low_positive_pairs,
       MIN(r.relative_humidity_pct) AS luhamet_rh_min_pct,
       AVG(r.relative_humidity_pct) AS luhamet_rh_mean_pct,
       MAX(r.relative_humidity_pct) AS luhamet_rh_max_pct,
       MIN(r.temperature_c) AS luhamet_temp_min_c,
       AVG(r.temperature_c) AS luhamet_temp_mean_c,
       MAX(r.temperature_c) AS luhamet_temp_max_c,
       AVG(r.wind_speed_ms) AS luhamet_wind_mean_ms,
       SUM(CASE WHEN r.rain_interval_mm > 0 THEN 1 ELSE 0 END) AS exact_pairs_with_rain
FROM episodes AS e
LEFT JOIN loucka_reconstruction.archive AS a
  ON a.dateTime BETWEEN e.start_epoch AND e.end_epoch
 AND a.outHumidity = 100
LEFT JOIN loucka_reconstruction.reference_observations AS r
  ON r.station_id = 'luhamet_sehradice'
 AND r.observed_at_utc = a.dateTime
GROUP BY e.episode_id, e.start_epoch, e.end_epoch
ORDER BY e.episode_id;
