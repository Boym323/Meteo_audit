-- READ-ONLY: precise observed boundaries of 2013 field ratio groups.
-- UTC scope [2013-01-01, 2014-01-01); a gap between ratio groups is not interpolated.
START TRANSACTION READ ONLY;
SELECT field_name,ratio_class,COUNT(*) AS value_pairs,MIN(dateTime) AS first_epoch,MAX(dateTime) AS last_epoch
FROM (
 SELECT 'windSpeed' AS field_name,w.dateTime,
  CASE WHEN w.windSpeed IS NULL OR s.windSpeed IS NULL THEN 'NULL_EXCLUDED'
       WHEN w.windSpeed=0 OR s.windSpeed=0 THEN 'ZERO_EXCLUDED'
       WHEN ABS(s.windSpeed/w.windSpeed-1)<0.001 THEN 'RATIO_1'
       WHEN ABS(s.windSpeed/w.windSpeed-3.6)<0.001 THEN 'RATIO_3_6' ELSE 'OTHER' END AS ratio_class
 FROM `weewx_WH1080`.archive w JOIN `pocasi-loucka.eu_old`.archive s ON s.dateTime=w.dateTime
 WHERE w.dateTime>=1356998400 AND w.dateTime<1388534400
 UNION ALL
 SELECT 'windGust',w.dateTime,
  CASE WHEN w.windGust IS NULL OR s.windGust IS NULL THEN 'NULL_EXCLUDED'
       WHEN w.windGust=0 OR s.windGust=0 THEN 'ZERO_EXCLUDED'
       WHEN ABS(s.windGust/w.windGust-1)<0.001 THEN 'RATIO_1'
       WHEN ABS(s.windGust/w.windGust-3.6)<0.001 THEN 'RATIO_3_6' ELSE 'OTHER' END
 FROM `weewx_WH1080`.archive w JOIN `pocasi-loucka.eu_old`.archive s ON s.dateTime=w.dateTime
 WHERE w.dateTime>=1356998400 AND w.dateTime<1388534400
 UNION ALL
 SELECT 'windrun',w.dateTime,
  CASE WHEN w.windrun IS NULL OR s.windrun IS NULL THEN 'NULL_EXCLUDED'
       WHEN w.windrun=0 OR s.windrun=0 THEN 'ZERO_EXCLUDED'
       WHEN ABS(s.windrun/w.windrun-1)<0.001 THEN 'RATIO_1'
       WHEN ABS(s.windrun/w.windrun-1/3.6)<0.001 THEN 'RATIO_1_OVER_3_6' ELSE 'OTHER' END
 FROM `weewx_WH1080`.archive w JOIN `pocasi-loucka.eu_old`.archive s ON s.dateTime=w.dateTime
 WHERE w.dateTime>=1356998400 AND w.dateTime<1388534400
) ratios GROUP BY field_name,ratio_class ORDER BY field_name,ratio_class;
