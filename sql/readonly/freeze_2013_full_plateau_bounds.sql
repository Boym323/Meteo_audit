-- SELECT-only exact 300s unchanged-value runs in UTC 2013, expanded around
-- five previously documented T/RH windows. This finds complete run bounds.
WITH episodes AS (
    SELECT 1 AS episode_id,1359072000 AS start_epoch,1359114900 AS end_epoch UNION ALL
    SELECT 2,1360929600,1360972500 UNION ALL
    SELECT 3,1362182400,1362225300 UNION ALL
    SELECT 4,1364342400,1364385300 UNION ALL
    SELECT 5,1364990400,1365033300
), raw_values AS (
    SELECT dateTime, `interval`, 'outTemp' AS variable_name, outTemp AS obs_value
    FROM loucka_reconstruction.archive
    WHERE dateTime >= 1356998400 AND dateTime < 1388534400
    UNION ALL
    SELECT dateTime, `interval`, 'outHumidity' AS variable_name, outHumidity AS obs_value
    FROM loucka_reconstruction.archive
    WHERE dateTime >= 1356998400 AND dateTime < 1388534400
), ordered AS (
    SELECT dateTime, `interval`, variable_name, obs_value,
           LAG(dateTime) OVER (PARTITION BY variable_name ORDER BY dateTime) AS prev_time,
           LAG(`interval`) OVER (PARTITION BY variable_name ORDER BY dateTime) AS prev_interval,
           LAG(obs_value) OVER (PARTITION BY variable_name ORDER BY dateTime) AS prev_value
    FROM raw_values
), marked AS (
    SELECT *, CASE WHEN prev_time IS NULL OR dateTime-prev_time <> 300
                          OR `interval` <> 5 OR prev_interval <> 5
                          OR obs_value <> prev_value
                   THEN 1 ELSE 0 END AS new_run
    FROM ordered
    WHERE obs_value IS NOT NULL
), runs AS (
    SELECT *, SUM(new_run) OVER (PARTITION BY variable_name ORDER BY dateTime) AS run_id
    FROM marked
), plateaus AS (
    SELECT variable_name,run_id,obs_value,
           MIN(dateTime) AS run_start_epoch,MAX(dateTime) AS run_end_epoch,
           COUNT(*) AS n_points,MAX(dateTime)-MIN(dateTime) AS elapsed_seconds
    FROM runs
    GROUP BY variable_name,run_id,obs_value
), target_values AS (
    SELECT episode_id,start_epoch,end_epoch,'outTemp' AS variable_name FROM episodes UNION ALL
    SELECT episode_id,start_epoch,end_epoch,'outHumidity' FROM episodes
)
SELECT e.episode_id,p.variable_name,p.obs_value,
       p.run_start_epoch,p.run_end_epoch,p.n_points,p.elapsed_seconds,
       (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c
        WHERE c.variable=p.variable_name
          AND c.target_time BETWEEN p.run_start_epoch AND p.run_end_epoch) AS history_events
FROM target_values e
JOIN plateaus p ON p.variable_name=e.variable_name
              AND p.run_start_epoch<=e.end_epoch
              AND p.run_end_epoch>=e.start_epoch
              AND p.n_points>=144
ORDER BY e.episode_id,p.variable_name,p.run_start_epoch;
