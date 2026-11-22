-- Read-only 2025 chronological confirmation block.
-- Run each SELECT separately. All epochs are UTC; 2021 and 2018 Q1 excluded.
-- Eligibility: exact LuhaMet timestamp, 5min, reference_only, both temperatures
-- non-NULL, and no outTemp history event at the reconstruction target.

-- 1) Global training bias from 2022-01-01 through 2024-12-31 UTC.
SELECT COUNT(*) AS n, AVG(a.outTemp-r.temperature_c) AS global_bias_loucka_minus_luhamet
FROM loucka_reconstruction.archive a
JOIN loucka_reconstruction.reference_observations r
  ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
WHERE a.dateTime>=1640995200 AND a.dateTime<1735689600
  AND a.outTemp IS NOT NULL AND r.temperature_c IS NOT NULL
  AND r.source_resolution='5min' AND r.quality_status='reference_only'
  AND NOT EXISTS (SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                  WHERE c.target_time=a.dateTime AND c.variable='outTemp');

-- 2) UTC-quarter training biases for the same eligible training pairs.
WITH eligible AS (
 SELECT a.dateTime,a.outTemp AS loucka,r.temperature_c AS ref
 FROM loucka_reconstruction.archive a
 JOIN loucka_reconstruction.reference_observations r
   ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
 WHERE a.dateTime>=1640995200 AND a.dateTime<1735689600
   AND a.outTemp IS NOT NULL AND r.temperature_c IS NOT NULL
   AND r.source_resolution='5min' AND r.quality_status='reference_only'
   AND NOT EXISTS (SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                   WHERE c.target_time=a.dateTime AND c.variable='outTemp')
)
SELECT CASE
 WHEN (dateTime>=1640995200 AND dateTime<1648771200) OR (dateTime>=1672531200 AND dateTime<1680307200) OR (dateTime>=1704067200 AND dateTime<1711929600) THEN 'Q1'
 WHEN (dateTime>=1648771200 AND dateTime<1656633600) OR (dateTime>=1680307200 AND dateTime<1688169600) OR (dateTime>=1711929600 AND dateTime<1719792000) THEN 'Q2'
 WHEN (dateTime>=1656633600 AND dateTime<1664582400) OR (dateTime>=1688169600 AND dateTime<1696118400) OR (dateTime>=1719792000 AND dateTime<1727740800) THEN 'Q3'
 ELSE 'Q4' END AS utc_quarter,
 COUNT(*) AS training_pairs,AVG(loucka-ref) AS bias_loucka_minus_luhamet
FROM eligible GROUP BY utc_quarter ORDER BY utc_quarter;

-- Training coefficients actually obtained on snapshot 2026-11-12 22:39 UTC:
-- global +0.4327640402293259 C; Q1 +0.1764673177451532;
-- Q2 +0.6530031582791965; Q3 +0.8341063715847581; Q4 +0.064150065820686.
-- 3) Holdout aggregate sums for later local calculation of MAE/RMSE/bias.
WITH eligible AS (
 SELECT a.dateTime,a.outTemp AS loucka,r.temperature_c AS ref,
        CASE WHEN a.dateTime<1743465600 THEN 'Q1'
             WHEN a.dateTime<1751328000 THEN 'Q2'
             WHEN a.dateTime<1759276800 THEN 'Q3' ELSE 'Q4' END AS qtr
 FROM loucka_reconstruction.archive a
 JOIN loucka_reconstruction.reference_observations r
   ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
 WHERE a.dateTime>=1735689600 AND a.dateTime<1767225600
   AND a.outTemp IS NOT NULL AND r.temperature_c IS NOT NULL
   AND r.source_resolution='5min' AND r.quality_status='reference_only'
   AND NOT EXISTS (SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                   WHERE c.target_time=a.dateTime AND c.variable='outTemp')
), scored AS (
 SELECT qtr,loucka,CASE WHEN loucka<0 THEN 'FREEZE' ELSE 'NONFREEZE' END AS temp_group,
        loucka-ref AS e0,
        loucka-(ref+0.4327640402293259) AS e1,
        loucka-(ref+CASE qtr WHEN 'Q1' THEN 0.1764673177451532
                             WHEN 'Q2' THEN 0.6530031582791965
                             WHEN 'Q3' THEN 0.8341063715847581
                             ELSE 0.064150065820686 END) AS e2
 FROM eligible
)
SELECT qtr,temp_group,COUNT(*) AS n,
 SUM(ABS(e0)) AS abs0,SUM(e0*e0) AS sq0,SUM(e0) AS bias0,MAX(ABS(e0)) AS maxabs0,
 SUM(ABS(e1)) AS abs1,SUM(e1*e1) AS sq1,SUM(e1) AS bias1,MAX(ABS(e1)) AS maxabs1,
 SUM(ABS(e2)) AS abs2,SUM(e2*e2) AS sq2,SUM(e2) AS bias2,MAX(ABS(e2)) AS maxabs2
FROM scored GROUP BY qtr,temp_group ORDER BY qtr,temp_group;
