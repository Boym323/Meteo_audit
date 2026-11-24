-- Aggregate-only screening of every WH1080 pressure value at a target NULL.
-- Execute with the existing read-only Weather MCP connection. No DML/DDL.
WITH source_with_prev AS (
    SELECT w.dateTime, w.pressure, w.barometer,
           LAG(w.dateTime) OVER (ORDER BY w.dateTime) AS prev_time,
           LAG(w.pressure) OVER (ORDER BY w.dateTime) AS prev_pressure
    FROM weewx_WH1080.archive AS w
    WHERE w.dateTime >= 1451606400 AND w.dateTime < 1546300800
), candidates AS (
    SELECT CASE
             WHEN s.dateTime < 1483228800 THEN 2016
             WHEN s.dateTime < 1514764800 THEN 2017
             ELSE 2018
           END AS utc_year,
           s.*,
           r.pressure AS target_pressure
    FROM source_with_prev AS s
    JOIN loucka_reconstruction.archive AS r ON r.dateTime = s.dateTime
    WHERE r.pressure IS NULL AND s.pressure IS NOT NULL
)
SELECT utc_year,
       COUNT(*) AS candidate_pressure_values,
       SUM(pressure < 900 OR pressure > 1050) AS outside_900_1050,
       SUM(barometer IS NOT NULL) AS source_barometer_available,
       ROUND(AVG(barometer - pressure), 3) AS source_barometer_minus_pressure_mean_hpa,
       ROUND(STDDEV_POP(barometer - pressure), 3) AS source_reduction_sd_hpa,
       MIN(pressure) AS source_pressure_min_hpa,
       MAX(pressure) AS source_pressure_max_hpa,
       SUM(prev_time IS NOT NULL AND dateTime - prev_time = 300
           AND ABS(pressure - prev_pressure) > 3) AS adjacent_5m_jumps_over_3,
       SUM(prev_time IS NOT NULL AND dateTime - prev_time = 300
           AND pressure = prev_pressure) AS adjacent_5m_identical
FROM candidates
GROUP BY utc_year
ORDER BY utc_year;
