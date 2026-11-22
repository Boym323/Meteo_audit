-- SELECT-only, exact-time LuhaMet transfer baseline.
-- Training: UTC 2022-2023. Holdout: UTC 2024. Exclude every outTemp target
-- appearing in reconstruction_changes, so no logged reconstruction is scored.
WITH paired AS (
    SELECT a.dateTime,
           a.outTemp - r.temperature_c AS diff_c,
           CASE WHEN a.dateTime < 1704067200 THEN 'train' ELSE 'test' END AS split,
           CASE WHEN a.dateTime < 1711929600 THEN 'Q1'
                WHEN a.dateTime < 1719792000 THEN 'Q2'
                WHEN a.dateTime < 1727740800 THEN 'Q3'
                ELSE 'Q4' END AS quarter_utc
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
), train AS (
    SELECT COUNT(*) AS n, AVG(diff_c) AS bias_c
    FROM paired
    WHERE split = 'train'
)
SELECT train.n AS train_pairs_2022_2023,
       train.bias_c AS training_mean_loucka_minus_luhamet_c,
       COUNT(*) AS test_pairs_2024_untouched,
       AVG(p.diff_c) AS raw_bias_c,
       AVG(ABS(p.diff_c)) AS raw_mae_c,
       SQRT(AVG(p.diff_c * p.diff_c)) AS raw_rmse_c,
       AVG(ABS(p.diff_c - train.bias_c)) AS bias_corrected_mae_c,
       SQRT(AVG((p.diff_c - train.bias_c) * (p.diff_c - train.bias_c))) AS bias_corrected_rmse_c,
       AVG(p.diff_c - train.bias_c) AS corrected_bias_c,
       MAX(ABS(p.diff_c - train.bias_c)) AS corrected_max_abs_error_c
FROM paired AS p
CROSS JOIN train
WHERE p.split = 'test';

-- Same heldout scoring by fixed UTC quarter, with the same training offset.
WITH paired AS (
    SELECT a.dateTime,
           a.outTemp - r.temperature_c AS diff_c,
           CASE WHEN a.dateTime < 1704067200 THEN 'train' ELSE 'test' END AS split,
           CASE WHEN a.dateTime < 1711929600 THEN 'Q1'
                WHEN a.dateTime < 1719792000 THEN 'Q2'
                WHEN a.dateTime < 1727740800 THEN 'Q3'
                ELSE 'Q4' END AS quarter_utc
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
), train AS (
    SELECT AVG(diff_c) AS bias_c
    FROM paired
    WHERE split = 'train'
)
SELECT p.quarter_utc,
       COUNT(*) AS n,
       AVG(p.diff_c) AS raw_bias,
       AVG(ABS(p.diff_c)) AS raw_mae,
       SQRT(AVG(p.diff_c * p.diff_c)) AS raw_rmse,
       AVG(ABS(p.diff_c - t.bias_c)) AS corrected_mae,
       SQRT(AVG((p.diff_c - t.bias_c) * (p.diff_c - t.bias_c))) AS corrected_rmse,
       AVG(p.diff_c - t.bias_c) AS corrected_bias,
       MAX(ABS(p.diff_c - t.bias_c)) AS corrected_max_abs
FROM paired AS p
CROSS JOIN train AS t
WHERE p.split = 'test'
GROUP BY p.quarter_utc
ORDER BY p.quarter_utc;
