-- READ-ONLY aggregate; fixed UTC gap episodes from the frozen interval-aware catalog.
WITH gaps AS (SELECT 1 AS gap_id, 1238346600 AS lo, 1238353200 AS hi UNION ALL SELECT 2 AS gap_id, 1238841000 AS lo, 1238851500 AS hi UNION ALL SELECT 3 AS gap_id, 1239094200 AS lo, 1239100200 AS hi UNION ALL SELECT 4 AS gap_id, 1239736800 AS lo, 1239742800 AS hi UNION ALL SELECT 5 AS gap_id, 1239798600 AS lo, 1239805500 AS hi UNION ALL SELECT 6 AS gap_id, 1240390500 AS lo, 1240397400 AS hi UNION ALL SELECT 7 AS gap_id, 1244473500 AS lo, 1244479800 AS hi UNION ALL SELECT 8 AS gap_id, 1245931200 AS lo, 1245942300 AS hi UNION ALL SELECT 9 AS gap_id, 1246052100 AS lo, 1246064700 AS hi UNION ALL SELECT 10 AS gap_id, 1246365300 AS lo, 1246373700 AS hi UNION ALL SELECT 11 AS gap_id, 1246542000 AS lo, 1246555200 AS hi UNION ALL SELECT 12 AS gap_id, 1246561200 AS lo, 1246569300 AS hi UNION ALL SELECT 13 AS gap_id, 1246987200 AS lo, 1246999500 AS hi UNION ALL SELECT 14 AS gap_id, 1247921400 AS lo, 1247932500 AS hi UNION ALL SELECT 15 AS gap_id, 1250055900 AS lo, 1250082000 AS hi UNION ALL SELECT 16 AS gap_id, 1251234900 AS lo, 1251254400 AS hi UNION ALL SELECT 17 AS gap_id, 1251483300 AS lo, 1251487800 AS hi UNION ALL SELECT 18 AS gap_id, 1252502700 AS lo, 1252509300 AS hi UNION ALL SELECT 19 AS gap_id, 1256155500 AS lo, 1256167500 AS hi UNION ALL SELECT 20 AS gap_id, 1256167500 AS lo, 1256183700 AS hi UNION ALL SELECT 21 AS gap_id, 1256308800 AS lo, 1256315700 AS hi UNION ALL SELECT 22 AS gap_id, 1256999700 AS lo, 1257006600 AS hi UNION ALL SELECT 23 AS gap_id, 1257944700 AS lo, 1257952500 AS hi UNION ALL SELECT 24 AS gap_id, 1260950700 AS lo, 1260960600 AS hi UNION ALL SELECT 25 AS gap_id, 1261086600 AS lo, 1261092900 AS hi UNION ALL SELECT 26 AS gap_id, 1261992300 AS lo, 1262015700 AS hi)
SELECT 'reconstruction' AS archive, COUNT(*) AS gap_count, SUM(row_count>0) AS gaps_with_any_rows, SUM(row_count=0) AS gaps_without_rows, SUM(row_count) AS source_rows, SUM(n_outTemp>0) AS gaps_with_outTemp, SUM(n_outTemp) AS values_outTemp,
SUM(n_outHumidity>0) AS gaps_with_outHumidity, SUM(n_outHumidity) AS values_outHumidity,
SUM(n_rain>0) AS gaps_with_rain, SUM(n_rain) AS values_rain,
SUM(n_rainRate>0) AS gaps_with_rainRate, SUM(n_rainRate) AS values_rainRate,
SUM(n_windSpeed>0) AS gaps_with_windSpeed, SUM(n_windSpeed) AS values_windSpeed,
SUM(n_windGust>0) AS gaps_with_windGust, SUM(n_windGust) AS values_windGust,
SUM(n_barometer>0) AS gaps_with_barometer, SUM(n_barometer) AS values_barometer
FROM (SELECT g.gap_id, COUNT(a.`dateTime`) AS row_count, SUM(a.`outTemp` IS NOT NULL) AS n_outTemp, SUM(a.`outHumidity` IS NOT NULL) AS n_outHumidity, SUM(a.`rain` IS NOT NULL) AS n_rain, SUM(a.`rainRate` IS NOT NULL) AS n_rainRate, SUM(a.`windSpeed` IS NOT NULL) AS n_windSpeed, SUM(a.`windGust` IS NOT NULL) AS n_windGust, SUM(a.`barometer` IS NOT NULL) AS n_barometer
 FROM gaps g LEFT JOIN `loucka_reconstruction`.`archive` a ON a.`dateTime`>g.lo AND a.`dateTime`<g.hi GROUP BY g.gap_id) q
UNION ALL
SELECT 'eu' AS archive, COUNT(*) AS gap_count, SUM(row_count>0) AS gaps_with_any_rows, SUM(row_count=0) AS gaps_without_rows, SUM(row_count) AS source_rows, SUM(n_outTemp>0) AS gaps_with_outTemp, SUM(n_outTemp) AS values_outTemp,
SUM(n_outHumidity>0) AS gaps_with_outHumidity, SUM(n_outHumidity) AS values_outHumidity,
SUM(n_rain>0) AS gaps_with_rain, SUM(n_rain) AS values_rain,
SUM(n_rainRate>0) AS gaps_with_rainRate, SUM(n_rainRate) AS values_rainRate,
SUM(n_windSpeed>0) AS gaps_with_windSpeed, SUM(n_windSpeed) AS values_windSpeed,
SUM(n_windGust>0) AS gaps_with_windGust, SUM(n_windGust) AS values_windGust,
SUM(n_barometer>0) AS gaps_with_barometer, SUM(n_barometer) AS values_barometer
FROM (SELECT g.gap_id, COUNT(a.`dateTime`) AS row_count, SUM(a.`outTemp` IS NOT NULL) AS n_outTemp, SUM(a.`outHumidity` IS NOT NULL) AS n_outHumidity, SUM(a.`rain` IS NOT NULL) AS n_rain, SUM(a.`rainRate` IS NOT NULL) AS n_rainRate, SUM(a.`windSpeed` IS NOT NULL) AS n_windSpeed, SUM(a.`windGust` IS NOT NULL) AS n_windGust, SUM(a.`barometer` IS NOT NULL) AS n_barometer
 FROM gaps g LEFT JOIN `pocasi-loucka.eu`.`archive` a ON a.`dateTime`>g.lo AND a.`dateTime`<g.hi GROUP BY g.gap_id) q
UNION ALL
SELECT 'gw1000' AS archive, COUNT(*) AS gap_count, SUM(row_count>0) AS gaps_with_any_rows, SUM(row_count=0) AS gaps_without_rows, SUM(row_count) AS source_rows, SUM(n_outTemp>0) AS gaps_with_outTemp, SUM(n_outTemp) AS values_outTemp,
SUM(n_outHumidity>0) AS gaps_with_outHumidity, SUM(n_outHumidity) AS values_outHumidity,
SUM(n_rain>0) AS gaps_with_rain, SUM(n_rain) AS values_rain,
SUM(n_rainRate>0) AS gaps_with_rainRate, SUM(n_rainRate) AS values_rainRate,
SUM(n_windSpeed>0) AS gaps_with_windSpeed, SUM(n_windSpeed) AS values_windSpeed,
SUM(n_windGust>0) AS gaps_with_windGust, SUM(n_windGust) AS values_windGust,
SUM(n_barometer>0) AS gaps_with_barometer, SUM(n_barometer) AS values_barometer
FROM (SELECT g.gap_id, COUNT(a.`dateTime`) AS row_count, SUM(a.`outTemp` IS NOT NULL) AS n_outTemp, SUM(a.`outHumidity` IS NOT NULL) AS n_outHumidity, SUM(a.`rain` IS NOT NULL) AS n_rain, SUM(a.`rainRate` IS NOT NULL) AS n_rainRate, SUM(a.`windSpeed` IS NOT NULL) AS n_windSpeed, SUM(a.`windGust` IS NOT NULL) AS n_windGust, SUM(a.`barometer` IS NOT NULL) AS n_barometer
 FROM gaps g LEFT JOIN `pocasi-loucka.eu_GW1000`.`archive` a ON a.`dateTime`>g.lo AND a.`dateTime`<g.hi GROUP BY g.gap_id) q
UNION ALL
SELECT 'eu_old' AS archive, COUNT(*) AS gap_count, SUM(row_count>0) AS gaps_with_any_rows, SUM(row_count=0) AS gaps_without_rows, SUM(row_count) AS source_rows, SUM(n_outTemp>0) AS gaps_with_outTemp, SUM(n_outTemp) AS values_outTemp,
SUM(n_outHumidity>0) AS gaps_with_outHumidity, SUM(n_outHumidity) AS values_outHumidity,
SUM(n_rain>0) AS gaps_with_rain, SUM(n_rain) AS values_rain,
SUM(n_rainRate>0) AS gaps_with_rainRate, SUM(n_rainRate) AS values_rainRate,
SUM(n_windSpeed>0) AS gaps_with_windSpeed, SUM(n_windSpeed) AS values_windSpeed,
SUM(n_windGust>0) AS gaps_with_windGust, SUM(n_windGust) AS values_windGust,
SUM(n_barometer>0) AS gaps_with_barometer, SUM(n_barometer) AS values_barometer
FROM (SELECT g.gap_id, COUNT(a.`dateTime`) AS row_count, SUM(a.`outTemp` IS NOT NULL) AS n_outTemp, SUM(a.`outHumidity` IS NOT NULL) AS n_outHumidity, SUM(a.`rain` IS NOT NULL) AS n_rain, SUM(a.`rainRate` IS NOT NULL) AS n_rainRate, SUM(a.`windSpeed` IS NOT NULL) AS n_windSpeed, SUM(a.`windGust` IS NOT NULL) AS n_windGust, SUM(a.`barometer` IS NOT NULL) AS n_barometer
 FROM gaps g LEFT JOIN `pocasi-loucka.eu_old`.`archive` a ON a.`dateTime`>g.lo AND a.`dateTime`<g.hi GROUP BY g.gap_id) q
UNION ALL
SELECT 'old_weewx' AS archive, COUNT(*) AS gap_count, SUM(row_count>0) AS gaps_with_any_rows, SUM(row_count=0) AS gaps_without_rows, SUM(row_count) AS source_rows, SUM(n_outTemp>0) AS gaps_with_outTemp, SUM(n_outTemp) AS values_outTemp,
SUM(n_outHumidity>0) AS gaps_with_outHumidity, SUM(n_outHumidity) AS values_outHumidity,
SUM(n_rain>0) AS gaps_with_rain, SUM(n_rain) AS values_rain,
SUM(n_rainRate>0) AS gaps_with_rainRate, SUM(n_rainRate) AS values_rainRate,
SUM(n_windSpeed>0) AS gaps_with_windSpeed, SUM(n_windSpeed) AS values_windSpeed,
SUM(n_windGust>0) AS gaps_with_windGust, SUM(n_windGust) AS values_windGust,
SUM(n_barometer>0) AS gaps_with_barometer, SUM(n_barometer) AS values_barometer
FROM (SELECT g.gap_id, COUNT(a.`dateTime`) AS row_count, SUM(a.`outTemp` IS NOT NULL) AS n_outTemp, SUM(a.`outHumidity` IS NOT NULL) AS n_outHumidity, SUM(a.`rain` IS NOT NULL) AS n_rain, SUM(a.`rainRate` IS NOT NULL) AS n_rainRate, SUM(a.`windSpeed` IS NOT NULL) AS n_windSpeed, SUM(a.`windGust` IS NOT NULL) AS n_windGust, SUM(a.`barometer` IS NOT NULL) AS n_barometer
 FROM gaps g LEFT JOIN `old_weewx`.`archive` a ON a.`dateTime`>g.lo AND a.`dateTime`<g.hi GROUP BY g.gap_id) q
UNION ALL
SELECT 'wh1080' AS archive, COUNT(*) AS gap_count, SUM(row_count>0) AS gaps_with_any_rows, SUM(row_count=0) AS gaps_without_rows, SUM(row_count) AS source_rows, SUM(n_outTemp>0) AS gaps_with_outTemp, SUM(n_outTemp) AS values_outTemp,
SUM(n_outHumidity>0) AS gaps_with_outHumidity, SUM(n_outHumidity) AS values_outHumidity,
SUM(n_rain>0) AS gaps_with_rain, SUM(n_rain) AS values_rain,
SUM(n_rainRate>0) AS gaps_with_rainRate, SUM(n_rainRate) AS values_rainRate,
SUM(n_windSpeed>0) AS gaps_with_windSpeed, SUM(n_windSpeed) AS values_windSpeed,
SUM(n_windGust>0) AS gaps_with_windGust, SUM(n_windGust) AS values_windGust,
SUM(n_barometer>0) AS gaps_with_barometer, SUM(n_barometer) AS values_barometer
FROM (SELECT g.gap_id, COUNT(a.`dateTime`) AS row_count, SUM(a.`outTemp` IS NOT NULL) AS n_outTemp, SUM(a.`outHumidity` IS NOT NULL) AS n_outHumidity, SUM(a.`rain` IS NOT NULL) AS n_rain, SUM(a.`rainRate` IS NOT NULL) AS n_rainRate, SUM(a.`windSpeed` IS NOT NULL) AS n_windSpeed, SUM(a.`windGust` IS NOT NULL) AS n_windGust, SUM(a.`barometer` IS NOT NULL) AS n_barometer
 FROM gaps g LEFT JOIN `weewx_WH1080`.`archive` a ON a.`dateTime`>g.lo AND a.`dateTime`<g.hi GROUP BY g.gap_id) q;
