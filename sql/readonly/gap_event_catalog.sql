-- SELECT-only complete interval-aware event catalog.
-- Bind one UTC calendar month at a time and run sequentially.
-- UTC bounds are Unix seconds. Include the exact preceding archive row so a
-- long gap ending at the month boundary is not hidden by a fixed lookback.
SELECT :utc_year AS utc_year, :utc_month AS utc_month,
       target_ts, prev_ts, delta_seconds, prev_interval, current_interval,
       (delta_seconds > prev_interval * 60
        AND delta_seconds > current_interval * 60) AS exceeds_both_steps,
       (delta_seconds = prev_interval * 60
        OR delta_seconds = current_interval * 60) AS matches_either_step
FROM (
  SELECT dateTime AS target_ts, current_interval,
         LAG(dateTime) OVER (ORDER BY dateTime) AS prev_ts,
         LAG(current_interval) OVER (ORDER BY dateTime) AS prev_interval,
         dateTime - LAG(dateTime) OVER (ORDER BY dateTime) AS delta_seconds
  FROM (
    SELECT dateTime, current_interval
    FROM (
      SELECT dateTime, `interval` AS current_interval
      FROM loucka_reconstruction.archive
      WHERE dateTime < :utc_month_start
      ORDER BY dateTime DESC LIMIT 1
    ) AS predecessor
    UNION ALL
    SELECT dateTime, `interval` AS current_interval
    FROM loucka_reconstruction.archive
    WHERE dateTime >= :utc_month_start AND dateTime < :utc_month_end
  ) AS month_rows
) AS adjacent
WHERE prev_ts IS NOT NULL AND target_ts >= :utc_month_start
  AND delta_seconds > LEAST(prev_interval, current_interval) * 60
ORDER BY target_ts;
