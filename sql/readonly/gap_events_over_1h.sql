-- SELECT-only event catalog for gaps strictly greater than one hour.
-- Substitute UTC epoch bounds per year and execute sequentially to limit load.
SELECT target_ts, prev_ts, delta_seconds, prev_interval, current_interval
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
      WHERE dateTime < :utc_year_start
      ORDER BY dateTime DESC LIMIT 1
    ) AS predecessor
    UNION ALL
    SELECT dateTime, `interval` AS current_interval
    FROM loucka_reconstruction.archive
    WHERE dateTime >= :utc_year_start AND dateTime < :utc_year_end
  ) AS year_rows
) AS adjacent
WHERE prev_ts IS NOT NULL AND target_ts >= :utc_year_start
  AND delta_seconds > 3600
ORDER BY target_ts;
