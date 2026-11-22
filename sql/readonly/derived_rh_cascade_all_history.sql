-- SELECT-only inventory of derived-field availability at the latest applied
-- outHumidity target for each timestamp, excluding protected year 2021.
WITH ranked AS (
    SELECT target_time, old_value, new_value, created_at, id,
           ROW_NUMBER() OVER (
               PARTITION BY target_time ORDER BY created_at DESC, id DESC
           ) AS rn
    FROM `loucka_reconstruction`.reconstruction_changes
    WHERE variable = 'outHumidity' AND state = 'applied'
      AND (target_time < 1609459200 OR target_time >= 1640995200)
), latest AS (
    SELECT * FROM ranked WHERE rn = 1
)
SELECT CASE WHEN l.old_value IS NULL THEN 'filled_from_null'
            WHEN l.new_value IS NULL THEN 'cleared_to_null'
            ELSE 'changed_nonnull' END AS change_type,
       COUNT(*) AS target_count,
       SUM(a.outHumidity <=> l.new_value) AS current_matches_latest_new,
       SUM(a.outTemp IS NOT NULL AND a.outHumidity IS NOT NULL) AS current_temp_rh_available,
       SUM(a.windSpeed IS NOT NULL) AS wind_available,
       SUM(a.dewpoint IS NOT NULL) AS dewpoint_present,
       SUM(a.heatindex IS NOT NULL) AS heatindex_present,
       SUM(a.humidex IS NOT NULL) AS humidex_present,
       SUM(a.appTemp IS NOT NULL) AS appTemp_present,
       SUM(a.cloudbase IS NOT NULL) AS cloudbase_present,
       SUM(a.vpd IS NOT NULL) AS vpd_present,
       SUM(a.wbgt IS NOT NULL) AS wbgt_present,
       SUM(a.outHumAbs IS NOT NULL) AS outHumAbs_present,
       SUM(a.outThetaE IS NOT NULL) AS outThetaE_present
FROM latest l
JOIN `loucka_reconstruction`.archive a ON a.dateTime = l.target_time
GROUP BY change_type ORDER BY change_type;

-- There are no recorded derived-channel change events outside protected 2021
-- in this snapshot; this is limited to the current contents of this log.
SELECT variable, state, COUNT(*) AS events,
       COUNT(DISTINCT target_time) AS unique_targets,
       MIN(target_time) AS first_target, MAX(target_time) AS last_target
FROM `loucka_reconstruction`.reconstruction_changes
WHERE target_time < 1609459200 OR target_time >= 1640995200
GROUP BY variable, state ORDER BY variable, state;
