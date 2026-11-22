-- Bounded UTC-year check of rows declaring interval=6; replace year placeholders.
-- Includes exactly one predecessor before and successor after each UTC year.
WITH year_rows AS (
 SELECT dateTime, `interval` FROM loucka_reconstruction.archive
 WHERE dateTime >= {{YEAR_START_EPOCH}} AND dateTime < {{NEXT_YEAR_START_EPOCH}}
), predecessor AS (
 SELECT dateTime, `interval` FROM loucka_reconstruction.archive
 WHERE dateTime < {{YEAR_START_EPOCH}} ORDER BY dateTime DESC LIMIT 1
), successor AS (
 SELECT dateTime, `interval` FROM loucka_reconstruction.archive
 WHERE dateTime >= {{NEXT_YEAR_START_EPOCH}} ORDER BY dateTime LIMIT 1
), points AS (
 SELECT * FROM predecessor UNION ALL SELECT * FROM year_rows
 UNION ALL SELECT * FROM successor
), linked AS (
 SELECT dateTime, `interval`, LAG(dateTime) OVER (ORDER BY dateTime) AS prev_ts,
        LAG(`interval`) OVER (ORDER BY dateTime) AS prev_interval,
        LEAD(dateTime) OVER (ORDER BY dateTime) AS next_ts,
        LEAD(`interval`) OVER (ORDER BY dateTime) AS next_interval
 FROM points
)
SELECT {{UTC_YEAR}} AS utc_year, COUNT(*) AS interval6_rows,
       SUM(prev_ts IS NOT NULL) AS rows_with_prev,
       SUM(next_ts IS NOT NULL) AS rows_with_next,
       SUM(dateTime-prev_ts=300) AS prev_delta_300,
       SUM(dateTime-prev_ts=360) AS prev_delta_360,
       SUM(dateTime-prev_ts=prev_interval*60) AS prev_delta_matches_prev_interval,
       SUM(dateTime-prev_ts=`interval`*60) AS prev_delta_matches_interval6,
       SUM(next_ts-dateTime=300) AS next_delta_300,
       SUM(next_ts-dateTime=360) AS next_delta_360,
       SUM(next_ts-dateTime=`interval`*60) AS next_delta_matches_interval6,
       SUM(next_ts-dateTime=next_interval*60) AS next_delta_matches_next_interval
FROM linked
WHERE dateTime >= {{YEAR_START_EPOCH}} AND dateTime < {{NEXT_YEAR_START_EPOCH}}
  AND `interval`=6;
