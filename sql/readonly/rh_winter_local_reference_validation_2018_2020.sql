-- SELECT-only independent historical winter check for P4; Q1 2018 and 2021 are excluded.
-- Winter scopes: 2018-12-01..2019-03-01 and 2019-12-01..2020-03-01 UTC.
WITH p AS (
 SELECT a.dateTime,a.outHumidity local_rh,a.outTemp local_t,a.windSpeed local_wind,
        r.relative_humidity_pct ref_rh,
        CASE WHEN a.dateTime<1551398400 THEN '2018-19' ELSE '2019-20' END winter
 FROM archive a JOIN reference_observations r
   ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
 WHERE ((a.dateTime>=1543622400 AND a.dateTime<1551398400)
     OR (a.dateTime>=1575158400 AND a.dateTime<1583020800))
   AND a.`interval`=5 AND a.usUnits=16 AND a.outHumidity BETWEEN 0 AND 100
   AND a.outTemp BETWEEN -30 AND 40 AND r.relative_humidity_pct BETWEEN 1 AND 100
   AND r.quality_status='reference_only' AND r.source_resolution='5min'
   AND NOT EXISTS (SELECT 1 FROM reconstruction_changes c
                   WHERE c.target_time=a.dateTime AND c.variable IN ('outHumidity','outTemp'))
), scopes AS (
 SELECT winter,'all_exact_pairs' scope,* FROM p
 UNION ALL SELECT winter,'exclude_local_rh_ge_99',* FROM p WHERE local_rh<99
 UNION ALL SELECT winter,'freeze_local_temp_le_0',* FROM p WHERE local_t<=0
 UNION ALL SELECT winter,'near_saturation_rh_ge_95_lt_99',* FROM p WHERE local_rh>=95 AND local_rh<99
 UNION ALL SELECT winter,'calm_wind_lt_5_kmh',* FROM p WHERE local_wind<5
 UNION ALL SELECT winter,'local_rh_exactly_100',* FROM p WHERE local_rh=100
)
SELECT winter,scope,COUNT(*) n,AVG(local_rh-ref_rh) bias_pp,AVG(ABS(local_rh-ref_rh)) mae_pp,
       SQRT(AVG(POW(local_rh-ref_rh,2))) rmse_pp,MIN(local_rh-ref_rh) min_error_pp,
       MAX(local_rh-ref_rh) max_error_pp,AVG(local_rh) mean_local_rh,AVG(ref_rh) mean_ref_rh,
       AVG(local_t) mean_local_temp_c,AVG(local_wind) mean_local_wind_kmh
FROM scopes GROUP BY winter,scope ORDER BY winter,scope;

-- UTC monthly profile in 2019 uses explicit epoch boundaries, not session timezone.
WITH p AS (
 SELECT a.dateTime,a.outHumidity local_rh,a.outTemp local_t,a.windSpeed local_wind,
        r.relative_humidity_pct ref_rh,
        CASE WHEN a.dateTime<1548979200 THEN '2019-01'
             WHEN a.dateTime<1551398400 THEN '2019-02'
             WHEN a.dateTime<1554076800 THEN '2019-03'
             WHEN a.dateTime<1556668800 THEN '2019-04'
             WHEN a.dateTime<1559347200 THEN '2019-05'
             WHEN a.dateTime<1561939200 THEN '2019-06'
             WHEN a.dateTime<1564617600 THEN '2019-07'
             WHEN a.dateTime<1567296000 THEN '2019-08'
             WHEN a.dateTime<1569888000 THEN '2019-09'
             WHEN a.dateTime<1572566400 THEN '2019-10'
             WHEN a.dateTime<1575158400 THEN '2019-11' ELSE '2019-12' END month_utc
 FROM archive a JOIN reference_observations r
   ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
 WHERE a.dateTime>=1546300800 AND a.dateTime<1577836800 AND a.`interval`=5 AND a.usUnits=16
   AND a.outHumidity BETWEEN 0 AND 100 AND a.outTemp BETWEEN -30 AND 40
   AND r.relative_humidity_pct BETWEEN 1 AND 100 AND r.quality_status='reference_only'
   AND r.source_resolution='5min'
   AND NOT EXISTS (SELECT 1 FROM reconstruction_changes c
                   WHERE c.target_time=a.dateTime AND c.variable IN ('outHumidity','outTemp'))
)
SELECT month_utc,COUNT(*) n,AVG(local_rh-ref_rh) bias_pp,AVG(ABS(local_rh-ref_rh)) mae_pp,
       SQRT(AVG(POW(local_rh-ref_rh,2))) rmse_pp,AVG(local_rh) mean_local_rh,
       AVG(ref_rh) mean_ref_rh,SUM(local_t<=0) freeze_n,
       SUM(local_rh>=95 AND local_rh<99) near_saturation_n,SUM(local_rh=100) exact100_n,
       SUM(local_wind<5) calm_n
FROM p GROUP BY month_utc ORDER BY month_utc;

-- Source-copy context for winter 2018/19: copies may share lineage; this is not independent truth.
SELECT CASE WHEN a.dateTime<1548979200 THEN '2019-01'
            WHEN a.dateTime<1551398400 THEN '2019-02' ELSE '2019-03' END month_utc,
       COUNT(*) current_local_rows,SUM(o.outHumidity IS NOT NULL) old_rh_available,
       SUM(w.outHumidity IS NOT NULL) wh_rh_available,
       SUM(o.outHumidity IS NOT NULL AND w.outHumidity IS NOT NULL) both_available,
       SUM(o.outHumidity IS NOT NULL AND w.outHumidity IS NOT NULL
           AND ABS(o.outHumidity-w.outHumidity)<=0.1) copies_agree_0_1,
       SUM(o.outHumidity IS NOT NULL AND w.outHumidity IS NOT NULL
           AND ABS(o.outHumidity-w.outHumidity)>0.1) copies_conflict,
       SUM(o.outHumidity IS NOT NULL AND ABS(a.outHumidity-o.outHumidity)<=0.1) current_matches_old,
       SUM(w.outHumidity IS NOT NULL AND ABS(a.outHumidity-w.outHumidity)<=0.1) current_matches_wh
FROM archive a LEFT JOIN old_weewx.archive o ON o.dateTime=a.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=a.dateTime
WHERE a.dateTime>=1546300800 AND a.dateTime<1554076800 AND a.`interval`=5 AND a.usUnits=16
  AND a.outHumidity BETWEEN 0 AND 100
  AND NOT EXISTS (SELECT 1 FROM reconstruction_changes c
                  WHERE c.target_time=a.dateTime AND c.variable='outHumidity')
GROUP BY month_utc ORDER BY month_utc;
