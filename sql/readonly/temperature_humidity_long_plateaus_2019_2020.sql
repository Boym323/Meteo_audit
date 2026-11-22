-- SELECT-only long-plateau screening for UTC 2019 and 2020.
-- Exact 300s cadence, stored interval=5, unchanged value for at least 12h
-- (144 five-minute observations). Candidate episodes only; not automatic QC.
WITH raw_values AS (
    SELECT dateTime, `interval`, 'outTemp' AS variable_name, outTemp AS obs_value
    FROM loucka_reconstruction.archive
    WHERE dateTime >= 1546300800 AND dateTime < 1609459200
    UNION ALL
    SELECT dateTime, `interval`, 'outHumidity' AS variable_name, outHumidity AS obs_value
    FROM loucka_reconstruction.archive
    WHERE dateTime >= 1546300800 AND dateTime < 1609459200
), ordered AS (
    SELECT dateTime, `interval`, variable_name, obs_value,
           LAG(dateTime) OVER (PARTITION BY variable_name ORDER BY dateTime) AS prev_time,
           LAG(`interval`) OVER (PARTITION BY variable_name ORDER BY dateTime) AS prev_interval,
           LAG(obs_value) OVER (PARTITION BY variable_name ORDER BY dateTime) AS prev_value
    FROM raw_values
), marked AS (
    SELECT *,
           CASE WHEN prev_time IS NULL OR dateTime-prev_time <> 300
                     OR `interval` <> 5 OR prev_interval <> 5
                     OR obs_value <> prev_value
                THEN 1 ELSE 0 END AS new_run
    FROM ordered
    WHERE obs_value IS NOT NULL
), runs AS (
    SELECT *, SUM(new_run) OVER (PARTITION BY variable_name ORDER BY dateTime) AS run_id
    FROM marked
), plateaus AS (
    SELECT variable_name, run_id, obs_value,
           MIN(dateTime) AS start_epoch, MAX(dateTime) AS end_epoch,
           COUNT(*) AS n_points,
           (MAX(dateTime)-MIN(dateTime)) AS elapsed_seconds
    FROM runs
    GROUP BY variable_name, run_id, obs_value
)
SELECT variable_name, obs_value, start_epoch, end_epoch, n_points, elapsed_seconds,
       CASE WHEN start_epoch < 1577836800 THEN 2019 ELSE 2020 END AS utc_year
FROM plateaus
WHERE n_points >= 144
  AND end_epoch >= 1546300800
  AND start_epoch < 1609459200
ORDER BY n_points DESC, variable_name, start_epoch
LIMIT 100;
