-- SELECT-only cross-archive provenance screen for lightning_distance.
-- Exact source timestamps; report aggregates only, no candidate extraction.
SELECT COUNT(*) AS rows_after_cutoff,MIN(dateTime) AS first_epoch,MAX(dateTime) AS last_epoch,
       COUNT(lightning_distance) AS distance_nonnull,
       COUNT(lightning_strike_count) AS strike_count_nonnull,
       SUM(lightning_strike_count>0) AS strike_count_positive,
       SUM(lightning_strike_count=0) AS strike_count_zero
FROM `pocasi-loucka.eu`.archive WHERE dateTime>1772914200;
SELECT COUNT(*) AS rows_after_cutoff,MIN(dateTime) AS first_epoch,MAX(dateTime) AS last_epoch,
       COUNT(lightning_distance) AS distance_nonnull,
       COUNT(lightning_strike_count) AS strike_count_nonnull,
       SUM(lightning_strike_count>0) AS strike_count_positive,
       SUM(lightning_strike_count=0) AS strike_count_zero
FROM `pocasi-loucka.eu_GW1000`.archive WHERE dateTime>1772914200;
SELECT COUNT(*) AS common_main_gw_rows,MIN(p.dateTime) AS first_common_epoch,
       MAX(p.dateTime) AS last_common_epoch,
       COUNT(g.lightning_distance) AS gw_distance_nonnull,
       COUNT(r.lightning_distance) AS reconstruction_distance_nonnull,
       SUM(g.lightning_distance IS NOT NULL AND r.dateTime IS NOT NULL) AS gw_distance_with_reconstruction_row,
       SUM(g.lightning_distance IS NOT NULL AND r.dateTime IS NOT NULL AND r.lightning_distance IS NULL) AS gw_distance_but_reconstruction_null,
       SUM(g.lightning_distance IS NOT NULL AND r.dateTime IS NULL) AS gw_distance_without_reconstruction_row,
       MIN(CASE WHEN g.lightning_distance IS NOT NULL THEN p.dateTime END) AS first_gw_distance_epoch,
       MAX(CASE WHEN g.lightning_distance IS NOT NULL THEN p.dateTime END) AS last_gw_distance_epoch
FROM `pocasi-loucka.eu`.archive p
JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=p.dateTime
LEFT JOIN `loucka_reconstruction`.archive r ON r.dateTime=p.dateTime
WHERE p.dateTime>1772914200;
SELECT COUNT(*) AS exact_GW_main_rows_with_distance,
       COUNT(DISTINCT g.lightning_distance) AS distinct_distance_values,
       MIN(g.lightning_distance) AS min_distance,MAX(g.lightning_distance) AS max_distance,
       SUM(g.lightning_strike_count=0) AS strike_count_zero,
       SUM(g.lightning_strike_count>0) AS strike_count_positive,
       SUM(g.lightning_strike_count IS NULL) AS strike_count_null,
       SUM(g.usUnits<>16) AS non_metric_units,SUM(g.`interval`<>5) AS non_5min_interval,
       SUM(p.lightning_distance IS NULL) AS main_null,
       SUM(r.lightning_distance IS NULL) AS reconstruction_null,
       COUNT(c.id) AS matching_change_events
FROM `pocasi-loucka.eu_GW1000`.archive g
JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=g.dateTime
JOIN `loucka_reconstruction`.archive r ON r.dateTime=g.dateTime
LEFT JOIN `loucka_reconstruction`.reconstruction_changes c
  ON c.target_time=g.dateTime AND c.variable='lightning_distance'
WHERE g.dateTime>1772914200 AND g.lightning_distance IS NOT NULL;
SELECT CASE WHEN g.lightning_strike_count IS NULL THEN 'count_null'
            WHEN g.lightning_strike_count=0 THEN 'count_zero' ELSE 'count_positive' END AS count_class,
       COUNT(*) AS rows_n,COUNT(DISTINCT g.lightning_distance) AS distinct_distance_n,
       MIN(g.lightning_distance) AS min_distance,MAX(g.lightning_distance) AS max_distance,
       MIN(g.dateTime) AS first_epoch,MAX(g.dateTime) AS last_epoch,
       MIN(g.`interval`) AS min_interval,MAX(g.`interval`) AS max_interval
FROM `pocasi-loucka.eu_GW1000`.archive g
WHERE g.dateTime>1772914200 AND g.lightning_distance IS NOT NULL
GROUP BY count_class ORDER BY count_class;
-- Check whether the archived schemas retain the device's last-detection time field.
SELECT TABLE_SCHEMA,COLUMN_NAME
FROM information_schema.COLUMNS
WHERE TABLE_NAME='archive'
  AND TABLE_SCHEMA IN ('pocasi-loucka.eu','pocasi-loucka.eu_GW1000',
                       'pocasi-loucka.eu_old','loucka_reconstruction')
  AND COLUMN_NAME LIKE 'lightning%'
ORDER BY TABLE_SCHEMA,ORDINAL_POSITION;
