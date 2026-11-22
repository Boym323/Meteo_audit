/* READ ONLY: exact-pair rainRate ratio profile; 2009-2020 UTC; no writes. */
SELECT
 CASE
 WHEN a.dateTime >= 1230768000 AND a.dateTime < 1262304000 THEN 2009
 WHEN a.dateTime >= 1262304000 AND a.dateTime < 1293840000 THEN 2010
 WHEN a.dateTime >= 1293840000 AND a.dateTime < 1325376000 THEN 2011
 WHEN a.dateTime >= 1325376000 AND a.dateTime < 1356998400 THEN 2012
 WHEN a.dateTime >= 1356998400 AND a.dateTime < 1388534400 THEN 2013
 WHEN a.dateTime >= 1388534400 AND a.dateTime < 1420070400 THEN 2014
 WHEN a.dateTime >= 1420070400 AND a.dateTime < 1451606400 THEN 2015
 WHEN a.dateTime >= 1451606400 AND a.dateTime < 1483228800 THEN 2016
 WHEN a.dateTime >= 1483228800 AND a.dateTime < 1514764800 THEN 2017
 WHEN a.dateTime >= 1514764800 AND a.dateTime < 1546300800 THEN 2018
 WHEN a.dateTime >= 1546300800 AND a.dateTime < 1577836800 THEN 2019
 WHEN a.dateTime >= 1577836800 AND a.dateTime < 1609459200 THEN 2020
 ELSE NULL END AS year_utc,
 a.usUnits AS gw1000_usUnits, b.usUnits AS gw3000_usUnits,
 a.interval AS gw1000_interval, b.interval AS gw3000_interval,
 ROUND(b.rainRate / a.rainRate, 4) AS gw3000_over_gw1000_ratio,
 COUNT(*) AS paired_nonzero_rows,
 MIN(a.rainRate) AS gw1000_min,
 MAX(a.rainRate) AS gw1000_max,
 MIN(b.rainRate) AS gw3000_min,
 MAX(b.rainRate) AS gw3000_max,
 MIN(ABS(b.rainRate-a.rainRate)) AS min_abs_difference,
 MAX(ABS(b.rainRate-a.rainRate)) AS max_abs_difference,
 AVG(ABS(b.rainRate-a.rainRate)) AS mean_abs_difference
FROM `pocasi-loucka.eu_GW1000`.archive a
JOIN `pocasi-loucka.eu`.archive b ON b.dateTime=a.dateTime
WHERE a.dateTime >= 1230768000 AND a.dateTime < 1609459200
 AND a.rainRate IS NOT NULL AND b.rainRate IS NOT NULL
 AND a.rainRate <> 0 AND b.rainRate <> 0
GROUP BY year_utc,a.usUnits,b.usUnits,a.interval,b.interval,gw3000_over_gw1000_ratio
ORDER BY year_utc,paired_nonzero_rows DESC,gw3000_over_gw1000_ratio
