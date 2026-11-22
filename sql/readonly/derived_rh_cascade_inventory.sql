-- SELECT-only availability inventory for derived channels at applied RH target times.
-- UTC month April 2022: [1648771200, 1651363200).
SELECT CASE WHEN c.old_value IS NULL THEN 'filled_from_null'
            WHEN c.new_value IS NULL THEN 'cleared_to_null'
            ELSE 'changed_nonnull' END AS rh_change_type,
       COUNT(*) AS rh_events,
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
FROM loucka_reconstruction.reconstruction_changes AS c
JOIN loucka_reconstruction.archive AS a ON a.dateTime = c.target_time
WHERE c.variable = 'outHumidity'
  AND c.state = 'applied'
  AND c.target_time >= 1648771200
  AND c.target_time < 1651363200
GROUP BY rh_change_type
ORDER BY rh_change_type;

-- Check whether downstream derived channels have their own audit events.
SELECT variable,state,COUNT(*) AS events,COUNT(DISTINCT target_time) AS unique_targets
FROM loucka_reconstruction.reconstruction_changes
WHERE target_time >= 1648771200
  AND target_time < 1651363200
  AND variable IN ('dewpoint','heatindex','humidex','appTemp','cloudbase',
                   'vpd','wbgt','outHumAbs','outThetaE')
GROUP BY variable,state
ORDER BY variable,state;
