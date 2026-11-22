-- SELECT-only interval-aware duration bands for one UTC calendar year.
-- :utc_year_start and :utc_year_end are Unix UTC bounds [start,end).
-- The indexed predecessor prevents an arbitrarily long year-boundary gap from
-- being missed. This counts candidate adjacent pairs, not missing observations.
SELECT CASE WHEN delta_seconds < 3600 THEN '01_lt_1h'
            WHEN delta_seconds < 86400 THEN '02_1h_to_lt_1d'
            WHEN delta_seconds < 604800 THEN '03_1d_to_lt_7d'
            WHEN delta_seconds < 2592000 THEN '04_7d_to_lt_30d'
            WHEN delta_seconds < 7776000 THEN '05_30d_to_lt_90d'
            ELSE '06_ge_90d' END AS duration_band,
       COUNT(*) AS gap_pairs,
       SUM(delta_seconds > prev_interval * 60
           AND delta_seconds > current_interval * 60) AS exceeds_both_steps,
       SUM(prev_interval <> current_interval) AS interval_transitions,
       SUM(delta_seconds <> prev_interval * 60
           AND delta_seconds <> current_interval * 60) AS matches_neither_step,
       MIN(dateTime) AS first_target_epoch,
       MAX(dateTime) AS last_target_epoch,
       MAX(delta_seconds) AS max_delta_seconds
FROM (
    SELECT dateTime,
           current_interval,
           LAG(dateTime) OVER (ORDER BY dateTime) AS prev_ts,
           LAG(current_interval) OVER (ORDER BY dateTime) AS prev_interval,
           dateTime - LAG(dateTime) OVER (ORDER BY dateTime) AS delta_seconds
    FROM (
        SELECT dateTime,current_interval
        FROM (
            SELECT dateTime,`interval` AS current_interval
            FROM loucka_reconstruction.archive
            WHERE dateTime < :utc_year_start
            ORDER BY dateTime DESC LIMIT 1
        ) AS predecessor
        UNION ALL
        SELECT dateTime,`interval` AS current_interval
        FROM loucka_reconstruction.archive
        WHERE dateTime >= :utc_year_start
          AND dateTime < :utc_year_end
    ) AS year_rows
) AS adjacent
WHERE prev_ts IS NOT NULL
  AND dateTime >= :utc_year_start
  AND delta_seconds > LEAST(prev_interval,current_interval) * 60
GROUP BY duration_band
ORDER BY duration_band;
