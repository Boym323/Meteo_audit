-- SELECT-only annual stratification. Bind UTC year epoch boundaries and run sequentially.
SELECT :utc_year AS utc_year, temp_bin, COUNT(*) AS pairs,
       AVG(altimeter-barometer) AS mean_diff_hpa,
       AVG(ABS(altimeter-barometer)) AS mean_abs_diff_hpa,
       MIN(altimeter-barometer) AS min_diff_hpa,
       MAX(altimeter-barometer) AS max_diff_hpa,
       SUM(ABS(altimeter-barometer)>3) AS abs_gt_3_hpa,
       SUM(ABS(altimeter-barometer)>4) AS abs_gt_4_hpa,
       SUM(ABS(altimeter-barometer)>5) AS abs_gt_5_hpa
FROM (
  SELECT altimeter,barometer,
         CASE WHEN outTemp IS NULL THEN 'temp_null'
              WHEN outTemp<0 THEN 'lt_0c'
              WHEN outTemp<10 THEN '0_to_lt10c'
              ELSE 'ge_10c' END AS temp_bin
  FROM loucka_reconstruction.archive
  WHERE dateTime>=:utc_year_start AND dateTime<:utc_year_end
    AND altimeter IS NOT NULL AND barometer IS NOT NULL
) AS paired
GROUP BY temp_bin ORDER BY temp_bin;

-- Overall sign distribution by bin, aggregate only.
SELECT CASE WHEN outTemp<0 THEN 'lt_0c'
            WHEN outTemp<10 THEN '0_to_lt10c'
            ELSE 'ge_10c' END AS temp_bin,
       COUNT(*) AS pairs,
       SUM(altimeter-barometer<0) AS negative_diff,
       SUM(altimeter=barometer) AS equal_diff,
       SUM(altimeter-barometer>0) AS positive_diff,
       SUM(ABS(altimeter-barometer)>3) AS abs_gt_3_hpa,
       SUM(ABS(altimeter-barometer)>4) AS abs_gt_4_hpa,
       SUM(ABS(altimeter-barometer)>5) AS abs_gt_5_hpa
FROM loucka_reconstruction.archive
WHERE altimeter IS NOT NULL AND barometer IS NOT NULL AND outTemp IS NOT NULL
GROUP BY temp_bin ORDER BY temp_bin;
