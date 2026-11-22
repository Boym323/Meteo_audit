-- SELECT-only sensitivity query: deliberately omit only endpoint RH 20-95 screen; all other P3 filters are retained. Synthetic complete rows are masked.
-- Deterministic hourly anchors; same P3 endpoint filters; 0.1 C error bins.
WITH episodes AS (
 SELECT CASE WHEN a.dateTime<1577836800 THEN 2019 ELSE 2020 END utc_year,
        a.dateTime left_t,a.outTemp left_y,b.outTemp right_y
 FROM loucka_reconstruction.archive a
 JOIN loucka_reconstruction.archive b ON b.dateTime=a.dateTime+1200
 WHERE a.dateTime>=1546300800 AND a.dateTime<1609459200
  AND MOD(a.dateTime-1546300800,3600)=0 AND a.interval=5 AND b.interval=5
  AND a.usUnits=16 AND b.usUnits=16
  AND a.outTemp>0 AND a.outTemp<=35 AND b.outTemp>0 AND b.outTemp<=35
  AND a.rain=0 AND b.rain=0 AND a.rainRate=0 AND b.rainRate=0
  AND a.windSpeed>=5 AND b.windSpeed>=5 AND ABS(b.outTemp-a.outTemp)<=2
  AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=a.dateTime AND c.variable='outTemp')
  AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=b.dateTime AND c.variable='outTemp')
), complete AS (
 SELECT e.*,t1.outTemp y1, t2.outTemp y2, t3.outTemp y3
 FROM episodes e JOIN loucka_reconstruction.archive t1 ON t1.dateTime=e.left_t+300 AND t1.interval=5 AND t1.usUnits=16 AND t1.outTemp IS NOT NULL AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=t1.dateTime AND c.variable='outTemp') JOIN loucka_reconstruction.archive t2 ON t2.dateTime=e.left_t+600 AND t2.interval=5 AND t2.usUnits=16 AND t2.outTemp IS NOT NULL AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=t2.dateTime AND c.variable='outTemp') JOIN loucka_reconstruction.archive t3 ON t3.dateTime=e.left_t+900 AND t3.interval=5 AND t3.usUnits=16 AND t3.outTemp IS NOT NULL AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=t3.dateTime AND c.variable='outTemp')
), scores AS (
 SELECT utc_year,FLOOR(ABS((left_y+(right_y-left_y)*300/1200)-y1)*10)/10 err_bucket FROM complete UNION ALL SELECT utc_year,FLOOR(ABS((left_y+(right_y-left_y)*600/1200)-y2)*10)/10 err_bucket FROM complete UNION ALL SELECT utc_year,FLOOR(ABS((left_y+(right_y-left_y)*900/1200)-y3)*10)/10 err_bucket FROM complete
), hist AS (
 SELECT utc_year,err_bucket,COUNT(*) point_n FROM scores GROUP BY utc_year,err_bucket
), counts AS (
 SELECT utc_year,COUNT(*) episode_n,COUNT(*)*3 total_points FROM complete GROUP BY utc_year
)
SELECT 20 gap_minutes,h.utc_year,h.err_bucket,h.point_n,c.episode_n,c.total_points
FROM hist h JOIN counts c ON c.utc_year=h.utc_year ORDER BY h.utc_year,h.err_bucket;
