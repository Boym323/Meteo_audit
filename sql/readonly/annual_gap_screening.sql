-- SELECT-only interval-aware annual screening. UTC year bounds must come from utc_year_bounds().
-- The single indexed predecessor is exact, so a long outage crossing Jan 1 is not hidden by a fixed lookback.
SELECT prev_interval, current_interval, COUNT(*) AS gap_events,
       SUM(delta_seconds > prev_interval * 60
           AND delta_seconds > current_interval * 60) AS exceeds_both_steps,
       SUM(delta_seconds <> prev_interval * 60
           AND delta_seconds <> current_interval * 60) AS matches_neither_step,
       MAX(delta_seconds) AS max_delta_seconds
FROM (
    SELECT dateTime, current_interval,
           LAG(dateTime) OVER (ORDER BY dateTime) AS prev_ts,
           LAG(current_interval) OVER (ORDER BY dateTime) AS prev_interval,
           dateTime - LAG(dateTime) OVER (ORDER BY dateTime) AS delta_seconds
    FROM (
        SELECT dateTime, current_interval
        FROM (
            SELECT dateTime, `interval` AS current_interval
            FROM loucka_reconstruction.archive
            WHERE dateTime < :utc_year_start
            ORDER BY dateTime DESC
            LIMIT 1
        ) AS predecessor
        UNION ALL
        SELECT dateTime, `interval` AS current_interval
        FROM loucka_reconstruction.archive
        WHERE dateTime >= :utc_year_start
          AND dateTime < :utc_year_end
    ) AS year_rows
) AS adjacent
WHERE prev_ts IS NOT NULL
  AND dateTime >= :utc_year_start
  AND delta_seconds > LEAST(prev_interval, current_interval) * 60
GROUP BY prev_interval, current_interval
ORDER BY prev_interval, current_interval;
