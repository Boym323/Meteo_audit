-- SELECT-only consistency screen; 2021 is excluded and Q1 2018 is interim.
-- Magnus constants are a diagnostic approximation, not historical provenance.
WITH calc AS (
    SELECT dateTime, inTemp, inHumidity, inDewpoint,
           243.04 * (
             LN(inHumidity / 100) + 17.625 * inTemp / (243.04 + inTemp)
           ) / (
             17.625 - (LN(inHumidity / 100) + 17.625 * inTemp / (243.04 + inTemp))
           ) AS diagnostic_indewpoint
    FROM `loucka_reconstruction`.archive
    WHERE inDewpoint IS NOT NULL
      AND inTemp IS NOT NULL
      AND inHumidity BETWEEN 1 AND 100
      AND NOT (dateTime >= 1609459200 AND dateTime < 1640995200)
)
SELECT COUNT(*) AS compared,
       SUM(ABS(inDewpoint - diagnostic_indewpoint) <= 0.1) AS within_0_1c,
       SUM(ABS(inDewpoint - diagnostic_indewpoint) > 0.1) AS greater_0_1c,
       SUM(ABS(inDewpoint - diagnostic_indewpoint) > 1) AS greater_1c,
       SUM(ABS(inDewpoint - diagnostic_indewpoint) > 2) AS greater_2c,
       AVG(ABS(inDewpoint - diagnostic_indewpoint)) AS mean_abs_delta_c,
       MAX(ABS(inDewpoint - diagnostic_indewpoint)) AS max_abs_delta_c,
       MIN(inHumidity) AS min_humidity_pct, MAX(inHumidity) AS max_humidity_pct,
       MIN(inTemp) AS min_temp_c, MAX(inTemp) AS max_temp_c
FROM calc;
