-- Diagnostic only: compares rainRate scaled by stored interval with rain.
-- Does not assert equivalence: rainRate may be instantaneous/rolling and
-- driver/unit semantics remain unresolved. Q1 2018 is live/interim; 2021
-- is diagnostic only. SELECT-only; bounded to the two requested scopes.
SELECT scope, COUNT(*) AS rows_total,
       SUM(rain IS NULL) AS rain_null, SUM(rainRate IS NULL) AS rate_null,
       SUM(rain > 0) AS rain_positive, SUM(rainRate > 0) AS rate_positive,
       SUM(rain > 0 AND rainRate > 0) AS both_positive,
       SUM(rain > 0 AND rainRate = 0) AS rain_pos_rate_zero,
       SUM(rain = 0 AND rainRate > 0) AS rain_zero_rate_pos,
       SUM(rain > 0 AND rainRate > 0 AND ratio < 0.5) AS ratio_lt_0_5,
       SUM(rain > 0 AND rainRate > 0 AND ratio >= 0.5 AND ratio < 0.9) AS ratio_0_5_0_9,
       SUM(rain > 0 AND rainRate > 0 AND ratio >= 0.9 AND ratio <= 1.1) AS ratio_0_9_1_1,
       SUM(rain > 0 AND rainRate > 0 AND ratio > 1.1 AND ratio <= 2) AS ratio_1_1_2,
       SUM(rain > 0 AND rainRate > 0 AND ratio > 2) AS ratio_gt_2,
       SUM(rain > 0 AND rainRate > 0 AND ABS(ratio - 1) <= 0.02) AS ratio_within_2pct
FROM (
    SELECT CASE
             WHEN dateTime >= 1514764800 AND dateTime < 1522540800 THEN '2018_Q1_INTERIM'
             WHEN dateTime >= 1609459200 AND dateTime < 1640995200 THEN '2021_DIAGNOSTIC_ONLY'
           END AS scope,
           rain, rainRate, `interval`, (rainRate * `interval`) / (rain * 60) AS ratio
    FROM `loucka_reconstruction`.archive
    WHERE (dateTime >= 1514764800 AND dateTime < 1522540800)
       OR (dateTime >= 1609459200 AND dateTime < 1640995200)
) AS scoped
GROUP BY scope
ORDER BY scope;
