-- Read-only comparison of exact-time outTemp source-copy candidates.
-- Scope: 2009-2020; reconstruction is NULL; no target-variable change event.
SELECT CASE
    WHEN o.dateTime>=1230768000 AND o.dateTime<1262304000 THEN 2009
    WHEN o.dateTime>=1262304000 AND o.dateTime<1293840000 THEN 2010
    WHEN o.dateTime>=1293840000 AND o.dateTime<1325376000 THEN 2011
    WHEN o.dateTime>=1325376000 AND o.dateTime<1356998400 THEN 2012
    WHEN o.dateTime>=1356998400 AND o.dateTime<1388534400 THEN 2013
    WHEN o.dateTime>=1388534400 AND o.dateTime<1420070400 THEN 2014
    WHEN o.dateTime>=1420070400 AND o.dateTime<1451606400 THEN 2015
    WHEN o.dateTime>=1451606400 AND o.dateTime<1483228800 THEN 2016
    WHEN o.dateTime>=1483228800 AND o.dateTime<1514764800 THEN 2017
    WHEN o.dateTime>=1514764800 AND o.dateTime<1546300800 THEN 2018
    WHEN o.dateTime>=1546300800 AND o.dateTime<1577836800 THEN 2019
    WHEN o.dateTime>=1577836800 AND o.dateTime<1609459200 THEN 2020
  END AS utc_year,
  COUNT(*) AS paired_targets,
  SUM(o.outTemp=w.outTemp) AS exact_equal,
  SUM(ABS(o.outTemp-w.outTemp)>0.01) AS differs_over_0_01,
  MIN(o.outTemp) AS min_outTemp,
  MAX(o.outTemp) AS max_outTemp,
  SUM(o.outTemp < -40 OR o.outTemp > 50) AS outside_screen_range
FROM old_weewx.archive o
JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
JOIN loucka_reconstruction.archive r ON r.dateTime=o.dateTime
WHERE o.dateTime>=1230768000 AND o.dateTime<1609459200
  AND o.outTemp IS NOT NULL AND w.outTemp IS NOT NULL AND r.outTemp IS NULL
  AND NOT EXISTS (
    SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
    WHERE c.target_time=o.dateTime AND c.variable='outTemp'
  )
GROUP BY utc_year
ORDER BY utc_year;
