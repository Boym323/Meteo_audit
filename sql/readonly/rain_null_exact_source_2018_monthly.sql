-- SELECT-only, exact source timestamp match; Q1 2018 remains interim.
WITH src AS (
 SELECT s.dateTime,'old_weewx' source_name,s.rain source_rain,s.rainRate source_rate FROM old_weewx.archive s WHERE s.dateTime>=1514764800 AND s.dateTime<1546300800
 UNION ALL
 SELECT s.dateTime,'weewx_WH1080',s.rain,s.rainRate FROM weewx_WH1080.archive s WHERE s.dateTime>=1514764800 AND s.dateTime<1546300800
), c AS (
 SELECT src.dateTime target_time,
 MAX(src.source_name='old_weewx' AND src.source_rain IS NOT NULL) old_available,
 MAX(src.source_name='weewx_WH1080' AND src.source_rain IS NOT NULL) wh_available,
 MAX(CASE WHEN src.source_name='old_weewx' THEN src.source_rain END) old_rain,
 MAX(CASE WHEN src.source_name='weewx_WH1080' THEN src.source_rain END) wh_rain,
 MAX(CASE WHEN src.source_name='old_weewx' THEN src.source_rate END) old_rate,
 MAX(CASE WHEN src.source_name='weewx_WH1080' THEN src.source_rate END) wh_rate
 FROM src JOIN loucka_reconstruction.archive r ON r.dateTime=src.dateTime
 WHERE r.rain IS NULL AND src.source_rain IS NOT NULL GROUP BY src.dateTime
)
SELECT MAX(UTC_TIMESTAMP()) query_time_utc,
CASE
WHEN c.target_time < 1517443200 THEN '2018-01'
WHEN c.target_time < 1519862400 THEN '2018-02'
WHEN c.target_time < 1522540800 THEN '2018-03'
WHEN c.target_time < 1525132800 THEN '2018-04'
WHEN c.target_time < 1527811200 THEN '2018-05'
WHEN c.target_time < 1530403200 THEN '2018-06'
WHEN c.target_time < 1533081600 THEN '2018-07'
WHEN c.target_time < 1535760000 THEN '2018-08'
WHEN c.target_time < 1538352000 THEN '2018-09'
WHEN c.target_time < 1541030400 THEN '2018-10'
WHEN c.target_time < 1543622400 THEN '2018-11'
WHEN c.target_time < 1546300800 THEN '2018-12'
ELSE '2018-12' END AS utc_month,
COUNT(*) source_null_targets,
SUM(old_available) old_available,SUM(wh_available) wh_available,
SUM(old_available AND wh_available AND old_rain=wh_rain) both_rain_equal,
SUM(old_available AND wh_available AND old_rain<>wh_rain) both_rain_differ,
SUM(old_available AND old_rain=0) old_rain_zero,SUM(old_available AND old_rain>0) old_rain_positive,
SUM(wh_available AND wh_rain=0) wh_rain_zero,SUM(wh_available AND wh_rain>0) wh_rain_positive,
SUM(r.rainRate IS NULL) current_rate_null,SUM(r.rainRate=0) current_rate_zero,SUM(r.rainRate>0) current_rate_positive,
SUM(old_rate IS NOT NULL AND wh_rate IS NOT NULL AND old_rate=wh_rate) both_rate_equal,
SUM(old_rate>0) old_rate_positive,SUM(wh_rate>0) wh_rate_positive,
SUM(old_rain>0 AND old_rate>0) source_both_positive,
SUM(old_rain>0 AND (old_rate=0 OR old_rate IS NULL)) source_rain_only,
SUM((old_rain=0 OR old_rain IS NULL) AND old_rate>0) source_rate_only,
SUM(old_rain=0 AND old_rate=0) source_both_zero,
SUM(old_rate>0 AND r.rainRate=0) source_rate_current_rate_zero,
SUM(old_rate>0 AND r.rainRate IS NULL) source_rate_current_rate_null,
SUM(old_rain>0 AND r.rainRate=0) source_rain_current_rate_zero,
SUM(old_rain>0 AND r.rainRate IS NULL) source_rain_current_rate_null
FROM c JOIN loucka_reconstruction.archive r ON r.dateTime=c.target_time
GROUP BY utc_month ORDER BY utc_month
