-- Read-only post-write checks for the July 2021 reconstruction.
-- WeeWX monthly interval: (start,end]. rain is stored in cm; SUM(rain)*10 is mm.
-- The current rain values reproduce the stored IDW2 candidate on the overlapping
-- interval grid. This does not independently reproduce the IDW2 inputs/weights.

-- Current month archive: expected 8,928 rows, 0 rain NULL, 42.5672658 mm;
-- rainRate stays separate and 250 values are NULL.
SELECT COUNT(*) AS rows_in_month,
       SUM(rain IS NULL) AS rain_nulls,
       SUM(rain = 0) AS zeros,
       SUM(rain > 0) AS positive_values,
       SUM(rain) * 10 AS stored_sum_mm,
       SUM(rainRate IS NULL) AS rainRate_nulls
FROM loucka_reconstruction.archive
WHERE dateTime > 1625090400 AND dateTime <= 1627768800;

-- Compare rain values on common WeeWX/model timestamps. The start point is
-- excluded from (start,end] and the model does not contain the closing end point.
-- Expected: common_rows=8927, rain_mismatches=0. Do not compare rainRate as a
-- precipitation amount; it is a separate instantaneous/driver field.
SELECT COUNT(*) AS common_rows,
       SUM(ABS(a.rain - m.rain_cm) > 0.0000001) AS rain_mismatches,
       SUM(ABS(a.rainRate - m.rainRate_cm_h) > 0.0000001) AS rainRate_mismatches
FROM loucka_reconstruction.archive AS a
JOIN loucka_reconstruction.rain_reconstruction_202107_chmi_v1 AS m
  ON m.dateTime = a.dateTime
WHERE a.dateTime > 1625090400 AND a.dateTime <= 1627768800;

-- Two audited batches reclassified 71 suspect positive local archive values
-- to zero estimates: 21 for July 22-24 and 50 for July 7, 13, 16, 19 and 30.
SELECT batch_key, variable, state, COUNT(*) AS changed_fields,
       SUM(old_value - new_value) * 10 AS removed_mm
FROM loucka_reconstruction.reconstruction_changes
WHERE batch_key IN (
  'july2021_chmi_dry_days_local_pulses_v1',
  'july2021_dry_pulse_estimates_v1'
)
GROUP BY batch_key, variable, state
ORDER BY batch_key, variable, state;

-- The original local values remain represented by the immutable snapshot;
-- this query checks that the current archive has zero on the 71 changed times.
SELECT c.batch_key, COUNT(*) AS audit_events,
       SUM(a.rain = 0) AS current_zero_values,
       SUM(o.original_rain_cm > 0) AS original_positive_values,
       SUM(a.rainRate IS NULL) AS rate_unknown
FROM loucka_reconstruction.reconstruction_changes AS c
JOIN loucka_reconstruction.archive AS a ON a.dateTime = c.target_time
JOIN loucka_reconstruction.rain_archive_original_202107 AS o
  ON o.target_time = c.target_time
WHERE c.batch_key IN (
  'july2021_chmi_dry_days_local_pulses_v1',
  'july2021_dry_pulse_estimates_v1'
)
  AND c.variable = 'rain' AND c.state = 'applied'
GROUP BY c.batch_key ORDER BY c.batch_key;

-- Daily sums by local date of interval start. July 2021 is CEST (UTC+02:00);
-- the row ending at local midnight belongs to the preceding interval day.
SELECT CEIL((dateTime - 1625090400) / 86400) AS july_day,
       COUNT(*) AS intervals,
       SUM(rain IS NULL) AS rain_nulls,
       SUM(rain) * 10 AS known_mm
FROM loucka_reconstruction.archive
WHERE dateTime > 1625090400 AND dateTime <= 1627768800
GROUP BY july_day ORDER BY july_day;

-- Seven generated grid rows have no counterpart in any original archive.
SELECT a.dateTime, a.rain, a.rainRate,
       p.dateTime IS NULL AS absent_production,
       g.dateTime IS NULL AS absent_gw1000,
       o.dateTime IS NULL AS absent_legacy
FROM loucka_reconstruction.archive AS a
LEFT JOIN `pocasi-loucka.eu`.archive AS p ON p.dateTime = a.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive AS g ON g.dateTime = a.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive AS o ON o.dateTime = a.dateTime
WHERE a.dateTime IN (
  1625319000, 1625324100, 1625324400, 1625324700,
  1625325000, 1625325300, 1625325600
)
ORDER BY a.dateTime;
