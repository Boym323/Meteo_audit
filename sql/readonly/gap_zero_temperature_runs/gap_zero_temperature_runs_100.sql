-- READ-ONLY episode-level zero outTemp run-length screen.
WITH targets AS (SELECT 1513626000 AS left_time, 1513689600 AS right_time, '2017:1513626000:1513689600' AS gap_id, 63600 AS gap_seconds, '1h_to_lt_1d' AS gap_band UNION ALL SELECT 1514002800, 1514003400, '2017:1514002800:1514003400', 600, 'lt_1h' UNION ALL SELECT 1514007600, 1514008200, '2017:1514007600:1514008200', 600, 'lt_1h' UNION ALL SELECT 1514012400, 1514013000, '2017:1514012400:1514013000', 600, 'lt_1h' UNION ALL SELECT 1514017200, 1514017800, '2017:1514017200:1514017800', 600, 'lt_1h' UNION ALL SELECT 1514126700, 1514127300, '2017:1514126700:1514127300', 600, 'lt_1h' UNION ALL SELECT 1514320800, 1514322600, '2017:1514320800:1514322600', 1800, 'lt_1h' UNION ALL SELECT 1514343000, 1514344200, '2017:1514343000:1514344200', 1200, 'lt_1h' UNION ALL SELECT 1514344500, 1514345100, '2017:1514344500:1514345100', 600, 'lt_1h' UNION ALL SELECT 1514345400, 1514346000, '2017:1514345400:1514346000', 600, 'lt_1h' UNION ALL SELECT 1514347200, 1514350200, '2017:1514347200:1514350200', 3000, 'lt_1h' UNION ALL SELECT 1514352300, 1514352900, '2017:1514352300:1514352900', 600, 'lt_1h' UNION ALL SELECT 1514356500, 1514357400, '2017:1514356500:1514357400', 900, 'lt_1h' UNION ALL SELECT 1514462400, 1514463000, '2017:1514462400:1514463000', 600, 'lt_1h' UNION ALL SELECT 1514497500, 1514499900, '2017:1514497500:1514499900', 2400, 'lt_1h' UNION ALL SELECT 1514514900, 1514517600, '2017:1514514900:1514517600', 2700, 'lt_1h' UNION ALL SELECT 1514517900, 1514518500, '2017:1514517900:1514518500', 600, 'lt_1h' UNION ALL SELECT 1514533500, 1514534100, '2017:1514533500:1514534100', 600, 'lt_1h'), wh_rows AS (
 SELECT t.gap_id,t.gap_band,t.left_time,t.right_time,a.dateTime ts,a.outTemp,
        CASE WHEN a.dateTime>=1514764800 AND a.dateTime<1522540800 THEN 'PROTECTED_Q1_2018_DIAGNOSTIC' ELSE 'NORMAL' END protection_scope
 FROM targets t JOIN weewx_WH1080.archive a
   ON a.dateTime>t.left_time AND a.dateTime<t.right_time AND MOD(a.dateTime-t.left_time,300)=0
 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime
 WHERE r.dateTime IS NULL
), lagged AS (
 SELECT *,LAG(ts) OVER(PARTITION BY gap_id ORDER BY ts) prev_ts,
          LAG(outTemp) OVER(PARTITION BY gap_id ORDER BY ts) prev_temp,
          LEAD(ts) OVER(PARTITION BY gap_id ORDER BY ts) next_ts,
          LEAD(outTemp) OVER(PARTITION BY gap_id ORDER BY ts) next_temp
 FROM wh_rows
), marked AS (
 SELECT *,CASE WHEN outTemp=0 AND COALESCE(prev_ts=ts-300 AND prev_temp=0,0)=0 THEN 1 ELSE 0 END zero_run_start
 FROM lagged
), segmented AS (
 SELECT *,SUM(zero_run_start) OVER(PARTITION BY gap_id ORDER BY ts ROWS UNBOUNDED PRECEDING) zero_run_id
 FROM marked
), runs AS (
 SELECT CAST(SUBSTRING_INDEX(gap_id,':',1) AS UNSIGNED) utc_year,gap_band,protection_scope,
        gap_id,zero_run_id,COUNT(*) sample_count,MIN(ts) first_ts,MAX(ts) last_ts,
        MAX(CASE WHEN zero_run_start=1 AND prev_ts=ts-300 THEN prev_temp END) left_neighbor_temp,
        MAX(CASE WHEN next_ts=ts+300 AND next_temp<>0 THEN next_temp END) right_neighbor_temp
 FROM segmented WHERE outTemp=0
 GROUP BY utc_year,gap_band,protection_scope,gap_id,zero_run_id
)
SELECT utc_year,gap_band,protection_scope,COUNT(*) zero_run_count,
       SUM(sample_count) zero_samples,SUM(sample_count=1) singleton_runs,
       SUM(sample_count BETWEEN 2 AND 5) runs_2_to_5,
       SUM(sample_count BETWEEN 6 AND 11) runs_6_to_11,
       SUM(sample_count>=12) runs_12_plus,MAX(sample_count) max_run_samples,
       COUNT(DISTINCT gap_id) gaps_with_zero_run,
       SUM(left_neighbor_temp IS NOT NULL AND right_neighbor_temp IS NOT NULL) runs_bracketed_by_nonzero,
       SUM(left_neighbor_temp IS NOT NULL AND right_neighbor_temp IS NOT NULL AND left_neighbor_temp<>right_neighbor_temp) bracketed_with_change
FROM runs GROUP BY utc_year,gap_band,protection_scope ORDER BY utc_year,gap_band,protection_scope
