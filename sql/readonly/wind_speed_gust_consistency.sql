-- Read-only triage of wind speed/gust consistency in current reconstruction.
-- Unix epoch boundaries are UTC. Q1 2018 is separately marked interim;
-- 2021 is diagnostic-only. usUnits is included because speed units vary by code.
-- Run via Weather MCP against information_schema; no writes are issued.
SELECT
  CASE
    WHEN a.dateTime >= 1514764800 AND a.dateTime < 1522540800 THEN '2018_Q1_INTERIM'
    WHEN a.dateTime >= 1609459200 AND a.dateTime < 1640995200 THEN '2021_DIAGNOSTIC'
    ELSE 'other'
  END AS scope,
  a.usUnits,
  COUNT(*) AS rows_n,
  SUM(a.windSpeed IS NOT NULL) AS windSpeed_n,
  SUM(a.windGust IS NOT NULL) AS windGust_n,
  SUM(a.windDir IS NOT NULL) AS windDir_n,
  SUM(a.windGustDir IS NOT NULL) AS windGustDir_n,
  SUM(a.windSpeed < 0) AS negative_windSpeed,
  SUM(a.windGust < 0) AS negative_windGust,
  SUM(a.windSpeed IS NOT NULL AND a.windGust IS NOT NULL AND a.windGust < a.windSpeed) AS gust_below_speed_n,
  SUM(a.windSpeed IS NOT NULL AND a.windGust IS NOT NULL AND a.windGust < a.windSpeed AND a.windSpeed-a.windGust > 0.01) AS gap_gt_0_01,
  SUM(a.windSpeed IS NOT NULL AND a.windGust IS NOT NULL AND a.windGust < a.windSpeed AND a.windSpeed-a.windGust > 1) AS gap_gt_1,
  SUM(a.windSpeed IS NOT NULL AND a.windGust IS NOT NULL AND a.windGust=0 AND a.windSpeed>1) AS zero_gust_speed_gt_1,
  SUM(a.windDir < 0 OR a.windDir >= 360) AS windDir_outside_0_360,
  SUM(a.windGustDir < 0 OR a.windGustDir >= 360) AS windGustDir_outside_0_360,
  SUM(a.windSpeed=0 AND a.windDir IS NOT NULL) AS direction_at_zero_speed,
  SUM(a.windSpeed>0 AND a.windDir IS NULL) AS direction_missing_at_positive_speed,
  MIN(a.windSpeed) AS min_windSpeed,
  MAX(a.windSpeed) AS max_windSpeed,
  MIN(a.windGust) AS min_windGust,
  MAX(a.windGust) AS max_windGust
FROM `loucka_reconstruction`.archive a
WHERE a.dateTime >= 1235865600 AND a.dateTime < 1793328000
GROUP BY scope, a.usUnits
ORDER BY scope, a.usUnits;

-- Follow-up: strict cases with meaningful gap (>0.01 km/h), excluding live Q1 2018
-- and protected 2021. Main production exact-value reconciliation.
SELECT
  COUNT(*) AS flagged_n,
  SUM(p.dateTime IS NOT NULL) AS production_target_rows,
  SUM(p.dateTime IS NOT NULL AND p.windSpeed=a.windSpeed AND p.windGust=a.windGust) AS exact_production_match,
  SUM(h.target_time IS NOT NULL) AS any_wind_change_history,
  SUM(a.windGust=0 AND a.windSpeed>1) AS zero_gust_speed_gt_1,
  MAX(a.windSpeed-a.windGust) AS max_difference_kmh
FROM `loucka_reconstruction`.archive a
LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=a.dateTime
LEFT JOIN (
  SELECT DISTINCT target_time FROM `loucka_reconstruction`.reconstruction_changes
  WHERE variable IN ('windSpeed','windGust')
) h ON h.target_time=a.dateTime
WHERE a.dateTime >= 1235865600 AND a.dateTime < 1793328000
  AND NOT (a.dateTime >= 1514764800 AND a.dateTime < 1522540800)
  AND NOT (a.dateTime >= 1609459200 AND a.dateTime < 1640995200)
  AND a.windSpeed IS NOT NULL AND a.windGust IS NOT NULL
  AND a.windSpeed-a.windGust > 0.01;

-- Annual detail uses explicit UTC epoch bounds; Q1 2018 and 2021 are excluded.
SELECT
  CASE
    WHEN a.dateTime >= 1230768000 AND a.dateTime < 1262304000 THEN 2009
    WHEN a.dateTime >= 1262304000 AND a.dateTime < 1293840000 THEN 2010
    WHEN a.dateTime >= 1293840000 AND a.dateTime < 1325376000 THEN 2011
    WHEN a.dateTime >= 1325376000 AND a.dateTime < 1356998400 THEN 2012
    WHEN a.dateTime >= 1356998400 AND a.dateTime < 1388534400 THEN 2013
    WHEN a.dateTime >= 1388534400 AND a.dateTime < 1420070400 THEN 2014
    WHEN a.dateTime >= 1420070400 AND a.dateTime < 1451606400 THEN 2015
    WHEN a.dateTime >= 1451606400 AND a.dateTime < 1483228800 THEN 2016
    WHEN a.dateTime >= 1483228800 AND a.dateTime < 1514764800 THEN 2017
    WHEN a.dateTime >= 1514764800 AND a.dateTime < 1546300800 THEN 2018
    WHEN a.dateTime >= 1546300800 AND a.dateTime < 1577836800 THEN 2019
    WHEN a.dateTime >= 1577836800 AND a.dateTime < 1609459200 THEN 2020
    WHEN a.dateTime >= 1609459200 AND a.dateTime < 1640995200 THEN 2021
    WHEN a.dateTime >= 1640995200 AND a.dateTime < 1672531200 THEN 2022
    WHEN a.dateTime >= 1672531200 AND a.dateTime < 1704067200 THEN 2023
    WHEN a.dateTime >= 1704067200 AND a.dateTime < 1735689600 THEN 2024
    WHEN a.dateTime >= 1735689600 AND a.dateTime < 1767225600 THEN 2025
    WHEN a.dateTime >= 1767225600 AND a.dateTime < 1798761600 THEN 2026
    ELSE NULL
  END AS utc_year,
  COUNT(*) AS gust_below_speed_n,
  SUM(a.windSpeed-a.windGust > 0.01) AS gap_gt_0_01_kmh,
  SUM(a.windSpeed-a.windGust > 1) AS gap_gt_1_kmh,
  SUM(a.windSpeed-a.windGust > 5) AS gap_gt_5_kmh,
  SUM(a.windGust=0 AND a.windSpeed>1) AS zero_gust_speed_gt_1,
  ROUND(MAX(a.windSpeed-a.windGust),3) AS max_gap_kmh
FROM `loucka_reconstruction`.archive a
WHERE a.dateTime >= 1235865600 AND a.dateTime < 1793328000
  AND NOT (a.dateTime >= 1514764800 AND a.dateTime < 1522540800)
  AND NOT (a.dateTime >= 1609459200 AND a.dateTime < 1640995200)
  AND a.windSpeed IS NOT NULL AND a.windGust IS NOT NULL
  AND a.windGust < a.windSpeed
GROUP BY utc_year
ORDER BY utc_year;
