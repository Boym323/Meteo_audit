-- Read-only post-write checks for the July 2021 reconstruction.
-- WeeWX monthly interval: (start,end]. rain is stored in cm; SUM(rain)*10 is mm.

-- Every restored local source value should match all three read-only originals.
SELECT c.batch_key, COUNT(*) AS restored_rows,
       SUM(a.rain = p.rain) AS matches_production,
       SUM(a.rain = g.rain) AS matches_gw1000,
       SUM(a.rain = o.rain) AS matches_legacy,
       SUM(a.rain <> p.rain OR a.rain <> g.rain OR a.rain <> o.rain) AS mismatches
FROM loucka_reconstruction.reconstruction_changes AS c
JOIN loucka_reconstruction.archive AS a ON a.dateTime = c.target_time
JOIN `pocasi-loucka.eu`.archive AS p ON p.dateTime = c.target_time
JOIN `pocasi-loucka.eu_GW1000`.archive AS g ON g.dateTime = c.target_time
JOIN `pocasi-loucka.eu_old`.archive AS o ON o.dateTime = c.target_time
WHERE c.batch_key IN (
  'jul2021-restore-local-source-rain-v1-a',
  'jul2021-restore-local-source-rain-v1-b',
  'jul2021-restore-local-start-zero-v1'
)
  AND c.variable = 'rain' AND c.state = 'applied'
GROUP BY c.batch_key ORDER BY c.batch_key;

-- Expected: 8,928 rows, 0 rain NULL, total currently 70.5072658 mm.
SELECT COUNT(*) AS rows_in_month,
       SUM(rain IS NULL) AS rain_nulls,
       SUM(rain = 0) AS zeros,
       SUM(rain > 0) AS positive_values,
       SUM(rain) * 10 AS stored_sum_mm,
       SUM(rainRate IS NULL) AS rainRate_nulls
FROM loucka_reconstruction.archive
WHERE dateTime > 1625090400 AND dateTime <= 1627768800;

-- Daily sums by local date of interval start. July 2021 is CEST (UTC+02:00);
-- 5-minute rows at the next local midnight belong to the preceding interval day.
SELECT CEIL((dateTime - 1625090400) / 86400) AS july_day,
       COUNT(*) AS intervals,
       SUM(rain IS NULL) AS rain_nulls,
       SUM(rain) * 10 AS known_mm
FROM loucka_reconstruction.archive
WHERE dateTime > 1625090400 AND dateTime <= 1627768800
GROUP BY july_day ORDER BY july_day;

-- The seven generated grid rows have no counterpart in any original archive.
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
