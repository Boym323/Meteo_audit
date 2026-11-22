/* READ ONLY: exact-time GW1000/GW3000 rainRate mismatch pattern by year/unit/interval and rain. 2009-2020 UTC. */
SELECT
 CASE WHEN a.dateTime < 1262304000 THEN 2009 WHEN a.dateTime < 1293840000 THEN 2010 WHEN a.dateTime < 1325376000 THEN 2011 WHEN a.dateTime < 1356998400 THEN 2012 WHEN a.dateTime < 1388534400 THEN 2013 WHEN a.dateTime < 1420070400 THEN 2014 WHEN a.dateTime < 1451606400 THEN 2015 WHEN a.dateTime < 1483228800 THEN 2016 WHEN a.dateTime < 1514764800 THEN 2017 WHEN a.dateTime < 1546300800 THEN 2018 WHEN a.dateTime < 1577836800 THEN 2019 ELSE 2020 END AS year_utc,
 a.usUnits AS gw1000_usUnits,b.usUnits AS gw3000_usUnits,a.interval AS gw1000_interval,b.interval AS gw3000_interval,
 CASE WHEN a.rain=0 THEN 'RAIN_FIELD_ZERO' WHEN a.rain>0 THEN 'RAIN_FIELD_POSITIVE' WHEN a.rain<0 THEN 'RAIN_FIELD_NEGATIVE' ELSE 'RAIN_FIELD_NULL' END AS rain_bucket,
 COUNT(*) AS mismatch_rows, MIN(a.rain) AS rain_min,MAX(a.rain) AS rain_max,
 MIN(a.rainRate) AS gw1000_rate_min,MAX(a.rainRate) AS gw1000_rate_max,
 MIN(b.rainRate) AS gw3000_rate_min,MAX(b.rainRate) AS gw3000_rate_max
FROM `pocasi-loucka.eu_GW1000`.archive a
JOIN `pocasi-loucka.eu`.archive b ON b.dateTime=a.dateTime
WHERE a.dateTime>=1230768000 AND a.dateTime<1609459200 AND a.rainRate IS NOT NULL AND b.rainRate IS NOT NULL AND a.rainRate<>b.rainRate
GROUP BY year_utc,a.usUnits,b.usUnits,a.interval,b.interval,rain_bucket ORDER BY year_utc,rain_bucket,a.interval
