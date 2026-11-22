-- SELECT-only Weather MCP READ-ONLY query. Synthetic complete rows are masked.
-- Deterministic hourly anchors; same P3 endpoint filters; 0.1 C error bins.
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
), scores AS (
 SELECT utc_year,FLOOR(ABS((left_y+(right_y-left_y)*300/600)-y1)*10)/10 err_bucket FROM complete
), hist AS (
 SELECT utc_year,err_bucket,COUNT(*) point_n FROM scores GROUP BY utc_year,err_bucket
), counts AS (
 SELECT utc_year,COUNT(*) episode_n,COUNT(*)*1 total_points FROM complete GROUP BY utc_year
)
SELECT 10 gap_minutes,h.utc_year,h.err_bucket,h.point_n,c.episode_n,c.total_points
FROM hist h JOIN counts c ON c.utc_year=h.utc_year ORDER BY h.utc_year,h.err_bucket;
