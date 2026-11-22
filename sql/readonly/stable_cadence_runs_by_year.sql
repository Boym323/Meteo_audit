-- Bounded UTC-year candidate cadence runs; execute once per year and replace
-- {{UTC_YEAR}}, {{YEAR_START_EPOCH}}, {{NEXT_YEAR_START_EPOCH}}.
-- A regular edge requires same `interval` at both ends and exact delta equality.
WITH year_rows AS (
 SELECT dateTime, `interval` FROM loucka_reconstruction.archive
 WHERE dateTime >= {{YEAR_START_EPOCH}} AND dateTime < {{NEXT_YEAR_START_EPOCH}}
), predecessor AS (
 SELECT dateTime, `interval` FROM loucka_reconstruction.archive
 WHERE dateTime < {{YEAR_START_EPOCH}} ORDER BY dateTime DESC LIMIT 1
), points AS (
 SELECT * FROM predecessor UNION ALL SELECT * FROM year_rows
), lag1 AS (
 SELECT dateTime, `interval`, LAG(dateTime) OVER (ORDER BY dateTime) AS prev_ts,
        LAG(`interval`) OVER (ORDER BY dateTime) AS prev_interval
 FROM points
), edges AS (
 SELECT *, CASE WHEN prev_ts IS NOT NULL AND `interval`=prev_interval
                     AND dateTime-prev_ts=`interval`*60 THEN 1 ELSE 0 END AS is_regular
 FROM lag1
 WHERE dateTime >= {{YEAR_START_EPOCH}} AND dateTime < {{NEXT_YEAR_START_EPOCH}}
), lag2 AS (
 SELECT *, LAG(is_regular) OVER (ORDER BY dateTime) AS prev_regular,
        LAG(`interval`) OVER (ORDER BY dateTime) AS prev_edge_interval
 FROM edges
), breaks AS (
 SELECT *, CASE WHEN is_regular=1 AND prev_regular=1
                     AND `interval`=prev_edge_interval THEN 0 ELSE 1 END AS run_start
 FROM lag2
), labeled AS (
 SELECT *, SUM(run_start) OVER (ORDER BY dateTime) AS run_id FROM breaks
), runs AS (
 SELECT run_id, MIN(`interval`) AS interval_min, SUM(is_regular) AS regular_edges,
        SUM(is_regular)*MIN(`interval`)*60 AS duration_sec
 FROM labeled GROUP BY run_id HAVING regular_edges>0
)
SELECT {{UTC_YEAR}} AS utc_year, interval_min,
       CASE WHEN duration_sec>=86400 THEN 'ge_24h'
            WHEN duration_sec>=3600 THEN '1h_to_24h' ELSE 'lt_1h' END AS duration_band,
       COUNT(*) AS run_count, SUM(regular_edges) AS regular_edges,
       MAX(regular_edges) AS max_run_edges,
       SUM(duration_sec) AS total_regular_duration_sec
FROM runs GROUP BY interval_min,duration_band
ORDER BY interval_min,duration_band;
