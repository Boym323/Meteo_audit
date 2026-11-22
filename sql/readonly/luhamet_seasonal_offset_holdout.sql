-- SELECT-only temporal holdout for a four-parameter quarterly offset.
-- Explicit UTC epoch boundaries avoid dependence on DB session timezone.
-- Training: UTC 2022-2023. Holdout: UTC 2024. No 2018 Q1 or 2021 rows.
-- Exact timestamp pairs; exclude any target with an outTemp change-history row.
WITH paired AS (
    SELECT a.dateTime,
           a.outTemp AS loucka_c,
           r.temperature_c AS reference_c,
           a.outTemp - r.temperature_c AS diff_c,
           CASE
             WHEN a.dateTime >= 1640995200 AND a.dateTime < 1648771200 THEN 'Q1'
             WHEN a.dateTime >= 1648771200 AND a.dateTime < 1656633600 THEN 'Q2'
             WHEN a.dateTime >= 1656633600 AND a.dateTime < 1664582400 THEN 'Q3'
             WHEN a.dateTime >= 1664582400 AND a.dateTime < 1672531200 THEN 'Q4'
             WHEN a.dateTime >= 1672531200 AND a.dateTime < 1680307200 THEN 'Q1'
             WHEN a.dateTime >= 1680307200 AND a.dateTime < 1688169600 THEN 'Q2'
             WHEN a.dateTime >= 1688169600 AND a.dateTime < 1696118400 THEN 'Q3'
             WHEN a.dateTime >= 1696118400 AND a.dateTime < 1704067200 THEN 'Q4'
             WHEN a.dateTime >= 1704067200 AND a.dateTime < 1711929600 THEN 'Q1'
             WHEN a.dateTime >= 1711929600 AND a.dateTime < 1719792000 THEN 'Q2'
             WHEN a.dateTime >= 1719792000 AND a.dateTime < 1727740800 THEN 'Q3'
             WHEN a.dateTime >= 1727740800 AND a.dateTime < 1735689600 THEN 'Q4'
           END AS quarter_utc,
           CASE WHEN a.outTemp < 0 THEN '<0 C'
                WHEN a.outTemp < 10 THEN '0-10 C'
                WHEN a.outTemp < 20 THEN '10-20 C'
                ELSE '>=20 C' END AS loucka_temp_band
    FROM loucka_reconstruction.archive AS a
    JOIN loucka_reconstruction.reference_observations AS r
      ON r.observed_at_utc = a.dateTime
     AND r.station_id = 'luhamet_sehradice'
    WHERE a.dateTime >= 1640995200
      AND a.dateTime < 1735689600
      AND a.outTemp IS NOT NULL
      AND r.temperature_c IS NOT NULL
      AND NOT EXISTS (
          SELECT 1
          FROM loucka_reconstruction.reconstruction_changes AS ch
          WHERE ch.target_time = a.dateTime
            AND ch.variable = 'outTemp'
      )
), train_offset AS (
    SELECT quarter_utc, COUNT(*) AS train_n, AVG(diff_c) AS offset_c
    FROM paired
    WHERE dateTime < 1704067200
    GROUP BY quarter_utc
), scored AS (
    SELECT p.*, t.train_n, t.offset_c,
           p.diff_c AS raw_error_c,
           p.diff_c - t.offset_c AS seasonal_error_c
    FROM paired AS p
    JOIN train_offset AS t USING (quarter_utc)
    WHERE p.dateTime >= 1704067200
)
SELECT quarter_utc, loucka_temp_band,
       COUNT(*) AS holdout_n,
       MIN(train_n) AS train_n_for_quarter,
       MIN(offset_c) AS train_offset_c,
       AVG(raw_error_c) AS raw_bias_c,
       AVG(ABS(raw_error_c)) AS raw_mae_c,
       SQRT(AVG(raw_error_c * raw_error_c)) AS raw_rmse_c,
       AVG(seasonal_error_c) AS seasonal_bias_c,
       AVG(ABS(seasonal_error_c)) AS seasonal_mae_c,
       SQRT(AVG(seasonal_error_c * seasonal_error_c)) AS seasonal_rmse_c,
       MAX(ABS(seasonal_error_c)) AS seasonal_max_abs_c
FROM scored
GROUP BY quarter_utc, loucka_temp_band
ORDER BY FIELD(quarter_utc,'Q1','Q2','Q3','Q4'), FIELD(loucka_temp_band,'<0 C','0-10 C','10-20 C','>=20 C');
