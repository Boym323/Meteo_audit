-- Read-only diagnostic: test a source counter reset at exact UTC midnight.
-- On a negative 300-second step exactly at UTC midnight, the current source
-- value is treated as a candidate first post-reset increment. This is a test
-- hypothesis only, not a correction rule or proof of driver semantics.
WITH src AS (
    SELECT o.dateTime,
           o.rain,
           LAG(o.dateTime) OVER (ORDER BY o.dateTime) AS prev_time,
           LAG(o.rain) OVER (ORDER BY o.dateTime) AS prev_rain
    FROM old_weewx.archive AS o
    WHERE o.dateTime >= 1356998400 AND o.dateTime < 1388534400
), x AS (
    SELECT s.dateTime,
           s.rain,
           s.prev_time,
           s.prev_rain,
           r.rain AS recon_rain,
           CASE
             WHEN s.dateTime - s.prev_time = 300
              AND s.rain IS NOT NULL AND s.prev_rain IS NOT NULL
              AND s.rain >= s.prev_rain
             THEN (s.rain - s.prev_rain) / 10.0
             WHEN s.dateTime - s.prev_time = 300
              AND s.rain IS NOT NULL AND s.prev_rain IS NOT NULL
              AND s.rain < s.prev_rain
              AND MOD(s.dateTime, 86400) = 0
             THEN s.rain / 10.0
             ELSE NULL
           END AS reset_aware_increment_cm,
           CASE WHEN s.dateTime - s.prev_time = 300
                  AND s.rain IS NOT NULL AND s.prev_rain IS NOT NULL
                  AND s.rain < s.prev_rain
                  AND MOD(s.dateTime, 86400) = 0
                THEN 1 ELSE 0 END AS exact_utc_midnight_reset
    FROM src AS s
    LEFT JOIN loucka_reconstruction.archive AS r
      ON r.dateTime = s.dateTime
)
SELECT CASE
         WHEN x.dateTime < 1359676800 THEN 1
         WHEN x.dateTime < 1362096000 THEN 2
         WHEN x.dateTime < 1364774400 THEN 3
         WHEN x.dateTime < 1367366400 THEN 4
         WHEN x.dateTime < 1369958400 THEN 5
         WHEN x.dateTime < 1372636800 THEN 6
         WHEN x.dateTime < 1375315200 THEN 7
         WHEN x.dateTime < 1377993600 THEN 8
         WHEN x.dateTime < 1380585600 THEN 9
         WHEN x.dateTime < 1383264000 THEN 10
         WHEN x.dateTime < 1385856000 THEN 11
         ELSE 12
       END AS utc_month,
       SUM(x.dateTime - x.prev_time = 300 AND x.rain < x.prev_rain) AS negative_300s_steps,
       SUM(x.exact_utc_midnight_reset) AS exact_utc_midnight_resets,
       SUM(x.reset_aware_increment_cm IS NOT NULL) AS usable_increments,
       SUM(x.reset_aware_increment_cm > 0) AS positive_increments,
       SUM(x.reset_aware_increment_cm > 0 AND x.recon_rain > 0) AS both_positive,
       SUM(x.reset_aware_increment_cm > 0 AND x.recon_rain > 0
           AND ABS(x.reset_aware_increment_cm - x.recon_rain) < 0.0000001)
           AS exact_positive_matches,
       SUM(x.reset_aware_increment_cm > 0 AND x.recon_rain = 0) AS positive_increment_recon_zero,
       SUM(x.reset_aware_increment_cm > 0 AND x.recon_rain IS NULL) AS positive_increment_recon_null,
       SUM(x.recon_rain > 0 AND x.reset_aware_increment_cm IS NULL) AS recon_positive_source_unknown,
       ROUND(SUM(CASE WHEN x.reset_aware_increment_cm > 0
                      THEN x.reset_aware_increment_cm ELSE 0 END), 4) AS source_positive_increment_sum_cm,
       ROUND(SUM(CASE WHEN x.recon_rain > 0 THEN x.recon_rain ELSE 0 END), 4) AS recon_positive_sum_cm
FROM x
GROUP BY utc_month
ORDER BY utc_month;
