-- READ ONLY. Strict 2011 source-only cohort: both source archives agree on all
-- five primary values; exact target archive row absent. Summary plus repeated-value
-- groups are separate queries. Database connection is old_weewx.
SELECT COUNT(*) AS timestamps,
       SUM(a.outTemp = 0) AS zero_outTemp,
       SUM(a.outTemp < 0) AS negative_outTemp,
       SUM(a.outTemp > 0) AS positive_outTemp,
       SUM(a.outHumidity = 0) AS zero_outHumidity,
       SUM(a.rain > 0) AS positive_rain,
       SUM(a.rainRate > 0) AS positive_rainRate,
       MIN(a.outTemp) AS min_outTemp,
       MAX(a.outTemp) AS max_outTemp,
       AVG(a.outTemp) AS mean_outTemp,
       COUNT(DISTINCT a.outTemp) AS distinct_outTemp,
       MIN(a.outHumidity) AS min_outHumidity,
       MAX(a.outHumidity) AS max_outHumidity,
       COUNT(DISTINCT a.outHumidity) AS distinct_outHumidity,
       MIN(a.rain) AS min_rain,
       MAX(a.rain) AS max_rain,
       COUNT(DISTINCT a.rain) AS distinct_rain,
       MIN(a.dateTime) AS first_timestamp,
       MAX(a.dateTime) AS last_timestamp
FROM archive a
JOIN weewx_WH1080.archive b ON b.dateTime = a.dateTime
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime = a.dateTime
WHERE a.dateTime >= 1293840000 AND a.dateTime < 1325376000
  AND a.`interval` = 5 AND a.usUnits = 17 AND MOD(a.dateTime,300) = 0
  AND b.`interval` = 5 AND b.usUnits = 17
  AND a.outTemp IS NOT NULL AND a.outHumidity IS NOT NULL
  AND a.rain IS NOT NULL AND a.rainRate IS NOT NULL AND a.windSpeed IS NOT NULL
  AND a.outTemp = b.outTemp AND a.outHumidity = b.outHumidity
  AND a.rain = b.rain AND a.rainRate = b.rainRate AND a.windSpeed = b.windSpeed
  AND t.dateTime IS NULL;

-- Exact repeated triples reveal long stationary runs, without claiming whether
-- the cause is a frozen sensor, export transform, or valid weather plateau.
SELECT a.outTemp, a.outHumidity, a.rain, COUNT(*) AS rows,
       MIN(a.dateTime) AS first_timestamp, MAX(a.dateTime) AS last_timestamp
FROM archive a
JOIN weewx_WH1080.archive b ON b.dateTime = a.dateTime
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime = a.dateTime
WHERE a.dateTime >= 1293840000 AND a.dateTime < 1325376000
  AND a.`interval` = 5 AND a.usUnits = 17 AND MOD(a.dateTime,300) = 0
  AND b.`interval` = 5 AND b.usUnits = 17
  AND a.outTemp IS NOT NULL AND a.outHumidity IS NOT NULL
  AND a.rain IS NOT NULL AND a.rainRate IS NOT NULL AND a.windSpeed IS NOT NULL
  AND a.outTemp = b.outTemp AND a.outHumidity = b.outHumidity
  AND a.rain = b.rain AND a.rainRate = b.rainRate AND a.windSpeed = b.windSpeed
  AND t.dateTime IS NULL
GROUP BY a.outTemp, a.outHumidity, a.rain
ORDER BY rows DESC;
