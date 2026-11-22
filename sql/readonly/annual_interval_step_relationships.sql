-- SELECT-only annual relationship of adjacent timestamp deltas to both intervals.
-- Execute sequentially for each UTC year; bind numeric Unix epoch boundaries.
SELECT :utc_year AS utc_year, prev_interval, current_interval, step_relation,
       COUNT(*) AS pairs, MIN(delta_seconds) AS min_delta_seconds,
       MAX(delta_seconds) AS max_delta_seconds
FROM (
  SELECT prev_interval, current_interval, delta_seconds,
         CASE
           WHEN delta_seconds = prev_interval*60 AND delta_seconds = current_interval*60 THEN 'exact_both'
           WHEN delta_seconds = prev_interval*60 THEN 'exact_prev_only'
           WHEN delta_seconds = current_interval*60 THEN 'exact_current_only'
           WHEN delta_seconds > GREATEST(prev_interval,current_interval)*60 THEN 'above_both'
           WHEN delta_seconds > LEAST(prev_interval,current_interval)*60 THEN 'between_steps_unmatched'
           WHEN delta_seconds < LEAST(prev_interval,current_interval)*60 THEN 'below_both'
           ELSE 'exact_shorter_only'
         END AS step_relation
  FROM (
    SELECT prev_interval,current_interval,dateTime-prev_ts AS delta_seconds
    FROM (
      SELECT dateTime,current_interval,
             LAG(dateTime) OVER(ORDER BY dateTime) AS prev_ts,
             LAG(current_interval) OVER(ORDER BY dateTime) AS prev_interval
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
        WHERE dateTime >= :utc_year_start AND dateTime < :utc_year_end
      ) AS year_rows
    ) AS with_previous
    WHERE prev_ts IS NOT NULL AND dateTime >= :utc_year_start
  ) AS with_delta
) AS classified
GROUP BY prev_interval,current_interval,step_relation
ORDER BY prev_interval,current_interval,step_relation;
