-- READ-ONLY episode-level zero outTemp run-length screen.
WITH targets AS (SELECT 1482866700 AS left_time, 1482867300 AS right_time, '2016:1482866700:1482867300' AS gap_id, 600 AS gap_seconds, 'lt_1h' AS gap_band UNION ALL SELECT 1482867600, 1482869700, '2016:1482867600:1482869700', 2100, 'lt_1h' UNION ALL SELECT 1482871200, 1482871800, '2016:1482871200:1482871800', 600, 'lt_1h' UNION ALL SELECT 1482872100, 1482873300, '2016:1482872100:1482873300', 1200, 'lt_1h' UNION ALL SELECT 1483117200, 1483118100, '2016:1483117200:1483118100', 900, 'lt_1h' UNION ALL SELECT 1483127700, 1483134000, '2016:1483127700:1483134000', 6300, '1h_to_lt_1d' UNION ALL SELECT 1483134600, 1483196400, '2016:1483134600:1483196400', 61800, '1h_to_lt_1d' UNION ALL SELECT 1483208400, 1483210200, '2016:1483208400:1483210200', 1800, 'lt_1h' UNION ALL SELECT 1483212600, 1483213800, '2016:1483212600:1483213800', 1200, 'lt_1h'), wh_rows AS (
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
