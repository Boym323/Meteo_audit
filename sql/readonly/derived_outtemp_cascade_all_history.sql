-- SELECT-only inventory of derived-channel availability at each latest
-- applied outTemp target outside protected 2021.
WITH ranked AS (
    SELECT target_time, old_value, new_value, created_at, id,
           ROW_NUMBER() OVER (
               PARTITION BY target_time ORDER BY created_at DESC, id DESC
           ) AS rn
    FROM `loucka_reconstruction`.reconstruction_changes
    WHERE variable = 'outTemp' AND state = 'applied'
      AND (target_time < 1609459200 OR target_time >= 1640995200)
), latest AS (
    SELECT * FROM ranked WHERE rn = 1
)
SELECT CASE WHEN l.old_value IS NULL THEN 'filled_from_null'
            WHEN l.new_value IS NULL THEN 'cleared_to_null'
            ELSE 'changed_nonnull' END AS change_type,
       COUNT(*) AS target_count,
       SUM(a.outTemp <=> l.new_value) AS current_matches_latest_new,
       SUM(a.outTemp IS NOT NULL AND a.outHumidity IS NOT NULL) AS current_temp_rh_available,
       SUM(a.windSpeed IS NOT NULL) AS wind_available,
       SUM(a.dewpoint IS NOT NULL) AS dewpoint_present,
       SUM(a.heatindex IS NOT NULL) AS heatindex_present,
       SUM(a.humidex IS NOT NULL) AS humidex_present,
       SUM(a.appTemp IS NOT NULL) AS appTemp_present,
       SUM(a.windchill IS NOT NULL) AS windchill_present,
       SUM(a.cloudbase IS NOT NULL) AS cloudbase_present,
       SUM(a.vpd IS NOT NULL) AS vpd_present,
       SUM(a.wbgt IS NOT NULL) AS wbgt_present,
       SUM(a.outHumAbs IS NOT NULL) AS outHumAbs_present,
       SUM(a.outThetaE IS NOT NULL) AS outThetaE_present
FROM latest l
JOIN `loucka_reconstruction`.archive a ON a.dateTime = l.target_time
GROUP BY change_type ORDER BY change_type;

-- UTC-year distribution of all unique applied temperature targets.
SELECT CASE
         WHEN target_time >= 1514764800 AND target_time < 1546300800 THEN '2018'
         WHEN target_time >= 1546300800 AND target_time < 1577836800 THEN '2019'
         WHEN target_time >= 1577836800 AND target_time < 1609459200 THEN '2020'
         WHEN target_time >= 1609459200 AND target_time < 1640995200 THEN '2021_PROTECTED'
         WHEN target_time >= 1640995200 AND target_time < 1672531200 THEN '2022'
         WHEN target_time >= 1672531200 AND target_time < 1704067200 THEN '2023'
         WHEN target_time >= 1704067200 AND target_time < 1735689600 THEN '2024'
         WHEN target_time >= 1735689600 AND target_time < 1767225600 THEN '2025'
         WHEN target_time >= 1767225600 AND target_time < 1798761600 THEN '2026'
         ELSE 'other'
       END AS utc_year,
       COUNT(DISTINCT target_time) AS targets,
       MIN(target_time) AS first_target, MAX(target_time) AS last_target
FROM `loucka_reconstruction`.reconstruction_changes
WHERE variable = 'outTemp' AND state = 'applied'
  AND (target_time < 1609459200 OR target_time >= 1640995200)
GROUP BY utc_year ORDER BY utc_year;
