-- Bounded single-month query template. Replace {{START_EPOCH}}, {{END_EPOCH}},
-- {{UTC_YEAR}}, {{UTC_MONTH}} with numeric literals and execute separately.
-- The only pre-period row is the exact indexed predecessor for month boundary.
WITH month_rows AS (
 SELECT dateTime, `interval` FROM loucka_reconstruction.archive
 WHERE dateTime >= {{START_EPOCH}} AND dateTime < {{END_EPOCH}}
), predecessor AS (
 SELECT dateTime, `interval` FROM loucka_reconstruction.archive
 WHERE dateTime < {{START_EPOCH}} ORDER BY dateTime DESC LIMIT 1
), points AS (
 SELECT * FROM predecessor UNION ALL SELECT * FROM month_rows
), edges AS (
 SELECT dateTime, `interval`, LAG(dateTime) OVER (ORDER BY dateTime) AS prev_ts,
        LAG(`interval`) OVER (ORDER BY dateTime) AS prev_interval
 FROM points
)
SELECT {{UTC_YEAR}} AS utc_year, {{UTC_MONTH}} AS utc_month,
       (SELECT COUNT(*) FROM month_rows) AS archive_rows,
       COUNT(*) AS edge_count,
       SUM(dateTime-prev_ts=prev_interval*60) AS matches_previous_step,
       SUM(dateTime-prev_ts=`interval`*60) AS matches_current_step,
       SUM(dateTime-prev_ts>GREATEST(prev_interval,`interval`)*60) AS exceeds_both_steps,
       SUM(dateTime-prev_ts<LEAST(prev_interval,`interval`)*60) AS shorter_than_both_steps,
       SUM(prev_interval<>`interval`) AS interval_transitions,
       MIN(dateTime-prev_ts) AS min_delta_sec, MAX(dateTime-prev_ts) AS max_delta_sec
FROM edges
WHERE dateTime >= {{START_EPOCH}} AND dateTime < {{END_EPOCH}} AND prev_ts IS NOT NULL;
