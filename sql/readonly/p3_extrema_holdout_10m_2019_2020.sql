-- SELECT-only Weather MCP READ-ONLY query. Hidden interior extrema against endpoints.
WITH episodes AS (
 SELECT CASE WHEN a.dateTime<1577836800 THEN 2019 ELSE 2020 END utc_year,
        a.dateTime left_t,a.outTemp left_y,b.outTemp right_y
 FROM loucka_reconstruction.archive a
 JOIN loucka_reconstruction.archive b ON b.dateTime=a.dateTime+600
 WHERE a.dateTime>=1546300800 AND a.dateTime<1609459200
  AND MOD(a.dateTime-1546300800,3600)=0 AND a.interval=5 AND b.interval=5
  AND a.usUnits=16 AND b.usUnits=16
  AND a.outTemp>0 AND a.outTemp<=35 AND b.outTemp>0 AND b.outTemp<=35
  AND a.outHumidity BETWEEN 20 AND 95 AND b.outHumidity BETWEEN 20 AND 95
  AND a.rain=0 AND b.rain=0 AND a.rainRate=0 AND b.rainRate=0
  AND a.windSpeed>=5 AND b.windSpeed>=5 AND ABS(b.outTemp-a.outTemp)<=2
  AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=a.dateTime AND c.variable='outTemp')
  AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=b.dateTime AND c.variable='outTemp')
), complete AS (
 SELECT e.*,t1.outTemp y1
 FROM episodes e JOIN loucka_reconstruction.archive t1 ON t1.dateTime=e.left_t+300 AND t1.interval=5 AND t1.usUnits=16 AND t1.outTemp IS NOT NULL AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=t1.dateTime AND c.variable='outTemp')
)
SELECT 10 gap_minutes,utc_year,COUNT(*) episode_n,
 SUM(y1>GREATEST(left_y,right_y)) episodes_hidden_max,
 SUM(y1<LEAST(left_y,right_y)) episodes_hidden_min,
 MAX(GREATEST(y1-GREATEST(left_y,right_y),0)) max_hidden_max_error_c,
 MAX(GREATEST(LEAST(left_y,right_y)-y1,0)) max_hidden_min_error_c
FROM complete GROUP BY utc_year ORDER BY utc_year;
