-- Exploratory, exact-time LuhaMet->Loučka temperature transfer holdout.
-- All epochs UTC. Run SELECTs separately. 2021 and 2018 Q1 are excluded.
-- Eligibility: both temperatures present; LuhaMet 5min/reference_only;
-- no outTemp event at target in reconstruction_changes.
-- Train: 2015-2017. Test: 2019-2020. 2018 excluded between periods.
-- qtr CASE enumerates the UTC quarter boundaries for each training year.
-- 1) Train coefficients, base and sensitivity (flag reference=0 with Loucka>=20).
WITH eligible AS (
 SELECT a.dateTime,a.outTemp-r.temperature_c AS diff,
        CASE
          WHEN (a.dateTime>=1420070400 AND a.dateTime<1427846400)
            OR (a.dateTime>=1451606400 AND a.dateTime<1459468800)
            OR (a.dateTime>=1483228800 AND a.dateTime<1491004800) THEN 'Q1'
          WHEN (a.dateTime>=1427846400 AND a.dateTime<1435708800)
            OR (a.dateTime>=1459468800 AND a.dateTime<1467331200)
            OR (a.dateTime>=1491004800 AND a.dateTime<1498867200) THEN 'Q2'
          WHEN (a.dateTime>=1435708800 AND a.dateTime<1443657600)
            OR (a.dateTime>=1467331200 AND a.dateTime<1475280000)
            OR (a.dateTime>=1498867200 AND a.dateTime<1506816000) THEN 'Q3'
          ELSE 'Q4' END AS quarter_utc,
        CASE WHEN r.temperature_c=0 AND a.outTemp>=20 THEN 1 ELSE 0 END AS suspect_zero_hot
 FROM loucka_reconstruction.archive a
 JOIN loucka_reconstruction.reference_observations r
   ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
 WHERE a.dateTime>=1420070400 AND a.dateTime<1514764800
   AND a.outTemp IS NOT NULL AND r.temperature_c IS NOT NULL
   AND r.source_resolution='5min' AND r.quality_status='reference_only'
   AND NOT EXISTS (SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                   WHERE c.target_time=a.dateTime AND c.variable='outTemp')
)
SELECT quarter_utc,COUNT(*) AS all_pairs,AVG(diff) AS base_bias_loucka_minus_luhamet,
       SUM(suspect_zero_hot) AS zero_reference_loucka_ge20,
       COUNT(*)-SUM(suspect_zero_hot) AS sensitivity_pairs,
       AVG(CASE WHEN suspect_zero_hot=0 THEN diff END) AS sensitivity_bias
FROM eligible GROUP BY quarter_utc ORDER BY quarter_utc;

-- 2) Test sufficient statistics by UTC year/quarter/freeze group. Coefficients
-- are locked to the training output above and must not be re-fit on test:
-- base global +0.2558004621458543; base Q1/Q2/Q3/Q4
-- -0.2995033595113402 / +0.48883041676520056 /
-- +0.9490444122580227 / -0.29549082370010477.
-- sensitivity global +0.24191684220231197; quarter
-- -0.2995033595113402 / +0.4718600189323519 /
-- +0.9164187414330053 / -0.29549082370010477.
WITH eligible AS (
 SELECT a.dateTime,a.outTemp AS loucka,r.temperature_c AS ref,
        CASE WHEN a.dateTime<1577836800 THEN '2019' ELSE '2020' END AS utc_year,
        CASE WHEN a.dateTime<1554076800 OR (a.dateTime>=1577836800 AND a.dateTime<1585699200) THEN 'Q1'
             WHEN a.dateTime<1561939200 OR (a.dateTime>=1585699200 AND a.dateTime<1593561600) THEN 'Q2'
             WHEN a.dateTime<1569888000 OR (a.dateTime>=1593561600 AND a.dateTime<1601510400) THEN 'Q3'
             ELSE 'Q4' END AS utc_quarter,
        CASE WHEN a.outTemp<0 THEN 'FREEZE' ELSE 'NONFREEZE' END AS temp_group,
        CASE WHEN r.temperature_c=0 AND a.outTemp>=20 THEN 1 ELSE 0 END AS suspect_zero_hot
 FROM loucka_reconstruction.archive a
 JOIN loucka_reconstruction.reference_observations r
   ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
 WHERE a.dateTime>=1546300800 AND a.dateTime<1609459200
   AND a.outTemp IS NOT NULL AND r.temperature_c IS NOT NULL
   AND r.source_resolution='5min' AND r.quality_status='reference_only'
   AND NOT EXISTS (SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                   WHERE c.target_time=a.dateTime AND c.variable='outTemp')
), scored AS (
 SELECT utc_year,utc_quarter,temp_group,suspect_zero_hot,
        loucka-ref AS e0,
        loucka-(ref+0.2558004621458543) AS e1,
        loucka-(ref+CASE utc_quarter WHEN 'Q1' THEN -0.2995033595113402
             WHEN 'Q2' THEN 0.48883041676520056 WHEN 'Q3' THEN 0.9490444122580227
             ELSE -0.29549082370010477 END) AS e2,
        loucka-(ref+0.24191684220231197) AS e1_sensitivity,
        loucka-(ref+CASE utc_quarter WHEN 'Q1' THEN -0.2995033595113402
             WHEN 'Q2' THEN 0.4718600189323519 WHEN 'Q3' THEN 0.9164187414330053
             ELSE -0.29549082370010477 END) AS e2_sensitivity
 FROM eligible
)
SELECT utc_year,utc_quarter,temp_group,COUNT(*) AS all_pairs,
       SUM(suspect_zero_hot) AS suspect_reference_zero_hot_pairs,
       COUNT(*)-SUM(suspect_zero_hot) AS sensitivity_pairs,
       SUM(ABS(e0)) AS abs0,SUM(e0*e0) AS sq0,SUM(e0) AS bias0,MAX(ABS(e0)) AS maxabs0,
       SUM(ABS(e1)) AS abs1,SUM(e1*e1) AS sq1,SUM(e1) AS bias1,MAX(ABS(e1)) AS maxabs1,
       SUM(ABS(e2)) AS abs2,SUM(e2*e2) AS sq2,SUM(e2) AS bias2,MAX(ABS(e2)) AS maxabs2,
       SUM(CASE WHEN suspect_zero_hot=0 THEN ABS(e0) ELSE 0 END) AS sens_abs0,
       SUM(CASE WHEN suspect_zero_hot=0 THEN e0*e0 ELSE 0 END) AS sens_sq0,
       SUM(CASE WHEN suspect_zero_hot=0 THEN e0 ELSE 0 END) AS sens_bias0,
       SUM(CASE WHEN suspect_zero_hot=0 THEN ABS(e1_sensitivity) ELSE 0 END) AS sens_abs1,
       SUM(CASE WHEN suspect_zero_hot=0 THEN e1_sensitivity*e1_sensitivity ELSE 0 END) AS sens_sq1,
       SUM(CASE WHEN suspect_zero_hot=0 THEN e1_sensitivity ELSE 0 END) AS sens_bias1,
       SUM(CASE WHEN suspect_zero_hot=0 THEN ABS(e2_sensitivity) ELSE 0 END) AS sens_abs2,
       SUM(CASE WHEN suspect_zero_hot=0 THEN e2_sensitivity*e2_sensitivity ELSE 0 END) AS sens_sq2,
       SUM(CASE WHEN suspect_zero_hot=0 THEN e2_sensitivity ELSE 0 END) AS sens_bias2
FROM scored GROUP BY utc_year,utc_quarter,temp_group
ORDER BY utc_year,utc_quarter,temp_group;

-- 3) Bounded concrete top discrepancies for review. This is a reference
-- conflict sample, not proof that either station is wrong.
SELECT a.dateTime,a.outTemp,r.temperature_c,a.outTemp-r.temperature_c,
       a.outHumidity,a.windSpeed,r.source_resolution,r.quality_status
FROM loucka_reconstruction.archive a
JOIN loucka_reconstruction.reference_observations r
  ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
WHERE a.dateTime>=1546300800 AND a.dateTime<1609459200
  AND a.outTemp IS NOT NULL AND r.temperature_c IS NOT NULL
  AND r.source_resolution='5min' AND r.quality_status='reference_only'
  AND NOT EXISTS (SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                  WHERE c.target_time=a.dateTime AND c.variable='outTemp')
ORDER BY ABS(a.outTemp-r.temperature_c) DESC LIMIT 12;
