-- READ-ONLY aggregate; fixed UTC gap episodes from the frozen interval-aware catalog.
WITH gaps AS (SELECT 1 AS gap_id, 1264189800 AS lo, 1264196700 AS hi UNION ALL SELECT 2 AS gap_id, 1265658600 AS lo, 1265665500 AS hi UNION ALL SELECT 3 AS gap_id, 1267117500 AS lo, 1267126200 AS hi UNION ALL SELECT 4 AS gap_id, 1267133100 AS lo, 1267140300 AS hi UNION ALL SELECT 5 AS gap_id, 1268089500 AS lo, 1268096100 AS hi UNION ALL SELECT 6 AS gap_id, 1268590500 AS lo, 1268599500 AS hi UNION ALL SELECT 7 AS gap_id, 1269203100 AS lo, 1269221700 AS hi UNION ALL SELECT 8 AS gap_id, 1271607600 AS lo, 1271614800 AS hi UNION ALL SELECT 9 AS gap_id, 1275230100 AS lo, 1275237600 AS hi UNION ALL SELECT 10 AS gap_id, 1275593400 AS lo, 1275605700 AS hi UNION ALL SELECT 11 AS gap_id, 1276377900 AS lo, 1276397100 AS hi UNION ALL SELECT 12 AS gap_id, 1276794900 AS lo, 1276801500 AS hi UNION ALL SELECT 13 AS gap_id, 1277986500 AS lo, 1277997900 AS hi UNION ALL SELECT 14 AS gap_id, 1278514500 AS lo, 1278541500 AS hi UNION ALL SELECT 15 AS gap_id, 1278852300 AS lo, 1278864000 AS hi UNION ALL SELECT 16 AS gap_id, 1280078100 AS lo, 1280085000 AS hi UNION ALL SELECT 17 AS gap_id, 1280091000 AS lo, 1280099100 AS hi UNION ALL SELECT 18 AS gap_id, 1281032100 AS lo, 1281043800 AS hi UNION ALL SELECT 19 AS gap_id, 1281292200 AS lo, 1281307800 AS hi UNION ALL SELECT 20 AS gap_id, 1281742800 AS lo, 1281752700 AS hi UNION ALL SELECT 21 AS gap_id, 1281785400 AS lo, 1281792900 AS hi UNION ALL SELECT 22 AS gap_id, 1281981600 AS lo, 1281987900 AS hi UNION ALL SELECT 23 AS gap_id, 1285695600 AS lo, 1285716900 AS hi UNION ALL SELECT 24 AS gap_id, 1286637600 AS lo, 1286642700 AS hi UNION ALL SELECT 25 AS gap_id, 1287438600 AS lo, 1287453600 AS hi UNION ALL SELECT 26 AS gap_id, 1288218600 AS lo, 1288225500 AS hi UNION ALL SELECT 27 AS gap_id, 1289602500 AS lo, 1289609100 AS hi UNION ALL SELECT 28 AS gap_id, 1292068800 AS lo, 1292075700 AS hi)
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
