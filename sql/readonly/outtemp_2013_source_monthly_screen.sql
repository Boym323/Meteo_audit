-- Read-only monthly screening of exact, agreeing outTemp source-copy candidates.
SELECT CASE
 WHEN o.dateTime>=1356998400 AND o.dateTime<1359676800 THEN 1
 WHEN o.dateTime>=1359676800 AND o.dateTime<1362096000 THEN 2
 WHEN o.dateTime>=1362096000 AND o.dateTime<1364774400 THEN 3
 WHEN o.dateTime>=1364774400 AND o.dateTime<1367366400 THEN 4
 WHEN o.dateTime>=1367366400 AND o.dateTime<1370044800 THEN 5
 WHEN o.dateTime>=1370044800 AND o.dateTime<1372636800 THEN 6
 WHEN o.dateTime>=1372636800 AND o.dateTime<1375315200 THEN 7
 WHEN o.dateTime>=1375315200 AND o.dateTime<1377993600 THEN 8
 WHEN o.dateTime>=1377993600 AND o.dateTime<1380585600 THEN 9
 WHEN o.dateTime>=1380585600 AND o.dateTime<1383264000 THEN 10
 WHEN o.dateTime>=1383264000 AND o.dateTime<1385856000 THEN 11
 WHEN o.dateTime>=1385856000 AND o.dateTime<1388534400 THEN 12 END AS utc_month,
 COUNT(*) AS candidate_count,MIN(o.outTemp) AS min_c,MAX(o.outTemp) AS max_c,
 SUM(o.outTemp<0) AS below_0,SUM(o.outTemp<=-5) AS at_or_below_minus5,SUM(o.outTemp>35) AS above_35
FROM old_weewx.archive o
JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
JOIN loucka_reconstruction.archive r ON r.dateTime=o.dateTime
WHERE o.dateTime>=1356998400 AND o.dateTime<1388534400
 AND o.outTemp IS NOT NULL AND w.outTemp=o.outTemp AND r.outTemp IS NULL
 AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                WHERE c.target_time=o.dateTime AND c.variable='outTemp')
GROUP BY utc_month ORDER BY utc_month;
