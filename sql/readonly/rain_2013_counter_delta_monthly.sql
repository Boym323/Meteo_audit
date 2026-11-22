-- Read-only UTC 2013 source-counter diagnostic.
-- Source rain is differenced only over consecutive exact 300-second source rows;
-- raw code-17 delta is divided by 10 solely as the documented standard-unit
-- comparison hypothesis. This does not assert historical driver semantics.
WITH src AS (
    SELECT o.dateTime,
           o.rain,
           LAG(o.dateTime) OVER (ORDER BY o.dateTime) AS prev_time,
           LAG(o.rain) OVER (ORDER BY o.dateTime) AS prev_rain
    FROM old_weewx.archive AS o
    WHERE o.dateTime >= 1356998400 AND o.dateTime < 1388534400
), paired AS (
    SELECT s.dateTime,
           r.rain AS recon_rain,
           CASE
             WHEN s.dateTime - s.prev_time = 300
              AND s.rain IS NOT NULL AND s.prev_rain IS NOT NULL
              AND s.rain >= s.prev_rain
             THEN (s.rain - s.prev_rain) / 10.0
             ELSE NULL
           END AS source_delta_cm
    FROM src AS s
    LEFT JOIN loucka_reconstruction.archive AS r
      ON r.dateTime = s.dateTime
)
SELECT CASE
         WHEN dateTime < 1359676800 THEN 1
         WHEN dateTime < 1362096000 THEN 2
         WHEN dateTime < 1364774400 THEN 3
         WHEN dateTime < 1367366400 THEN 4
         WHEN dateTime < 1369958400 THEN 5
         WHEN dateTime < 1372636800 THEN 6
         WHEN dateTime < 1375315200 THEN 7
         WHEN dateTime < 1377993600 THEN 8
         WHEN dateTime < 1380585600 THEN 9
         WHEN dateTime < 1383264000 THEN 10
         WHEN dateTime < 1385856000 THEN 11
         ELSE 12
       END AS utc_month,
       COUNT(*) AS source_rows,
       SUM(dateTime - prev_time = 300) AS exact_300_second_steps,
       SUM(source_delta_cm IS NOT NULL) AS usable_nonnegative_deltas,
       SUM(source_delta_cm > 0) AS positive_source_deltas,
       SUM(source_delta_cm IS NULL AND dateTime - prev_time = 300
           AND recon_rain IS NOT NULL) AS excluded_steps_or_counter_decreases,
       SUM(recon_rain IS NOT NULL AND source_delta_cm IS NOT NULL) AS paired_valid_rows,
       SUM(recon_rain IS NOT NULL AND source_delta_cm IS NOT NULL
           AND ABS(recon_rain - source_delta_cm) < 0.0000001) AS exact_scaled_value_matches,
       SUM(recon_rain > 0 AND source_delta_cm > 0) AS both_positive,
       SUM(recon_rain > 0 AND source_delta_cm > 0
           AND ABS(recon_rain - source_delta_cm) < 0.0000001) AS exact_positive_matches,
       SUM(recon_rain = 0 AND source_delta_cm > 0) AS source_positive_recon_zero,
       SUM(recon_rain IS NULL AND source_delta_cm > 0) AS source_positive_recon_null,
       ROUND(SUM(CASE WHEN source_delta_cm > 0 THEN source_delta_cm ELSE 0 END), 4)
           AS positive_source_delta_sum_cm,
       ROUND(SUM(CASE WHEN recon_rain > 0 THEN recon_rain ELSE 0 END), 4)
           AS recon_positive_sum_cm
FROM paired
GROUP BY utc_month
ORDER BY utc_month;
