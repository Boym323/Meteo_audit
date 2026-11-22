-- SELECT-only aggregate through Weather MCP read-only executor.
-- Deterministic hourly anchors; exact 10-minute gaps; endpoint gates match P3.
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
), scores AS (
 SELECT e.utc_year,FLOOR(ABS((e.left_y+e.right_y)/2-t.outTemp)*10)/10 err_bucket
 FROM episodes e JOIN loucka_reconstruction.archive t ON t.dateTime=e.left_t+300
 WHERE t.interval=5 AND t.usUnits=16 AND t.outTemp IS NOT NULL
  AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=t.dateTime AND c.variable='outTemp')
)
SELECT utc_year,err_bucket,COUNT(*) n FROM scores GROUP BY utc_year,err_bucket ORDER BY utc_year,err_bucket;
