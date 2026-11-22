-- SELECT-only diagnostic of archived dewpoint after applied RH changes.
-- UTC calendar April 2022: [1648771200, 1651363200).
-- Formula is a Magnus screening approximation, not asserted as the historical
-- station/WeeWX configuration.
WITH rh_changes AS (
    SELECT DISTINCT target_time
    FROM loucka_reconstruction.reconstruction_changes
    WHERE variable = 'outHumidity'
      AND state = 'applied'
      AND target_time >= 1648771200
      AND target_time < 1651363200
), dewpoint_changes AS (
    SELECT DISTINCT target_time
    FROM loucka_reconstruction.reconstruction_changes
    WHERE variable = 'dewpoint'
      AND target_time >= 1648771200
      AND target_time < 1651363200
), calc AS (
    SELECT a.dateTime,
           a.dewpoint,
           243.04 * (
               LN(a.outHumidity / 100) + 17.625 * a.outTemp / (243.04 + a.outTemp)
           ) / (
               17.625 - (
                   LN(a.outHumidity / 100) + 17.625 * a.outTemp / (243.04 + a.outTemp)
               )
           ) AS diagnostic_dewpoint,
           r.target_time AS rh_reconstructed,
           d.target_time AS dewpoint_changed
    FROM loucka_reconstruction.archive AS a
    LEFT JOIN rh_changes AS r ON r.target_time = a.dateTime
    LEFT JOIN dewpoint_changes AS d ON d.target_time = a.dateTime
    WHERE a.dateTime >= 1648771200
      AND a.dateTime < 1651363200
      AND a.outTemp IS NOT NULL
      AND a.outHumidity BETWEEN 1 AND 100
      AND a.dewpoint IS NOT NULL
)
SELECT CASE WHEN rh_reconstructed IS NULL
            THEN 'no_applied_RH_change'
            ELSE 'applied_RH_change'
       END AS rh_state,
       COUNT(*) AS compared,
       SUM(ABS(dewpoint - diagnostic_dewpoint) > 2) AS discrepancy_gt2,
       MAX(ABS(dewpoint - diagnostic_dewpoint)) AS max_abs_delta_c,
       AVG(ABS(dewpoint - diagnostic_dewpoint)) AS mean_abs_delta_c,
       SUM(dewpoint_changed IS NOT NULL) AS with_dewpoint_history
FROM calc
GROUP BY rh_state
ORDER BY rh_state;

-- Change log count over the same UTC month, by derived/base variable and state.
SELECT variable,state,COUNT(*) AS events,COUNT(DISTINCT target_time) AS unique_targets,
       MIN(target_time) AS min_target_epoch,MAX(target_time) AS max_target_epoch
FROM loucka_reconstruction.reconstruction_changes
WHERE target_time >= 1648771200
  AND target_time < 1651363200
  AND variable IN ('outHumidity','dewpoint','heatindex','humidex','appTemp','outTemp')
GROUP BY variable,state
ORDER BY variable,state;
