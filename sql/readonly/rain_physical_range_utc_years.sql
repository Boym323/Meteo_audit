-- Read-only Weather MCP query; UTC year keys use explicit Unix epochs, not session timezone.
-- 2021 is excluded (diagnostic-only protected year).
SELECT UTC_TIMESTAMP() AS query_time_utc,
       CASE
    WHEN dateTime < 1262304000 THEN 2009
    WHEN dateTime < 1293840000 THEN 2010
    WHEN dateTime < 1325376000 THEN 2011
    WHEN dateTime < 1356998400 THEN 2012
    WHEN dateTime < 1388534400 THEN 2013
    WHEN dateTime < 1420070400 THEN 2014
    WHEN dateTime < 1451606400 THEN 2015
    WHEN dateTime < 1483228800 THEN 2016
    WHEN dateTime < 1514764800 THEN 2017
    WHEN dateTime < 1546300800 THEN 2018
    WHEN dateTime < 1577836800 THEN 2019
    WHEN dateTime < 1609459200 THEN 2020
    WHEN dateTime < 1640995200 THEN 2021
    WHEN dateTime < 1672531200 THEN 2022
    WHEN dateTime < 1704067200 THEN 2023
    WHEN dateTime < 1735689600 THEN 2024
    WHEN dateTime < 1767225600 THEN 2025
    WHEN dateTime < 1798761600 THEN 2026
       ELSE 2027 END AS utc_year,
       usUnits,COUNT(*) AS n_rows,
       SUM(rain IS NULL) AS rain_null,SUM(rain < 0) AS rain_negative,
       SUM(rain > 0.5) AS rain_gt_0_5_cm,SUM(rain > 1.0) AS rain_gt_1_cm,
       MIN(rain) AS rain_min,MAX(rain) AS rain_max,
       SUM(rainRate IS NULL) AS rainRate_null,SUM(rainRate < 0) AS rainRate_negative,
       SUM(rainRate >= 5) AS rainRate_ge_5_cm_h,SUM(rainRate >= 10) AS rainRate_ge_10_cm_h,
       MIN(rainRate) AS rainRate_min,MAX(rainRate) AS rainRate_max
FROM archive
WHERE dateTime >= 1230768000 AND dateTime < 1798761600
  AND (dateTime < 1609459200 OR dateTime >= 1640995200)
GROUP BY utc_year,usUnits
ORDER BY utc_year,usUnits;
