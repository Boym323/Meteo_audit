-- READ-ONLY aggregate; fixed UTC gap episodes from the frozen interval-aware catalog.
WITH gaps AS (SELECT 1 AS gap_id, 1330952700 AS lo, 1330965900 AS hi UNION ALL SELECT 2 AS gap_id, 1331404500 AS lo, 1331412300 AS hi UNION ALL SELECT 3 AS gap_id, 1331412300 AS lo, 1331417700 AS hi UNION ALL SELECT 4 AS gap_id, 1331418900 AS lo, 1331426700 AS hi UNION ALL SELECT 5 AS gap_id, 1333907100 AS lo, 1333922700 AS hi UNION ALL SELECT 6 AS gap_id, 1338749700 AS lo, 1338759000 AS hi UNION ALL SELECT 7 AS gap_id, 1340367900 AS lo, 1340374200 AS hi UNION ALL SELECT 8 AS gap_id, 1341100500 AS lo, 1341106500 AS hi UNION ALL SELECT 9 AS gap_id, 1342207800 AS lo, 1342213200 AS hi UNION ALL SELECT 10 AS gap_id, 1344996600 AS lo, 1345019400 AS hi UNION ALL SELECT 11 AS gap_id, 1346451900 AS lo, 1346457600 AS hi UNION ALL SELECT 12 AS gap_id, 1347913200 AS lo, 1347921900 AS hi UNION ALL SELECT 13 AS gap_id, 1348474200 AS lo, 1348480200 AS hi UNION ALL SELECT 14 AS gap_id, 1348480200 AS lo, 1348485000 AS hi UNION ALL SELECT 15 AS gap_id, 1348485000 AS lo, 1348492200 AS hi UNION ALL SELECT 16 AS gap_id, 1348494000 AS lo, 1348520400 AS hi UNION ALL SELECT 17 AS gap_id, 1348576200 AS lo, 1348581600 AS hi UNION ALL SELECT 18 AS gap_id, 1348789800 AS lo, 1348794000 AS hi UNION ALL SELECT 19 AS gap_id, 1349437500 AS lo, 1349442300 AS hi UNION ALL SELECT 20 AS gap_id, 1350296400 AS lo, 1350301200 AS hi UNION ALL SELECT 21 AS gap_id, 1350758700 AS lo, 1350765000 AS hi UNION ALL SELECT 22 AS gap_id, 1352101500 AS lo, 1352108400 AS hi UNION ALL SELECT 23 AS gap_id, 1354703400 AS lo, 1354711200 AS hi UNION ALL SELECT 24 AS gap_id, 1354735200 AS lo, 1354740000 AS hi UNION ALL SELECT 25 AS gap_id, 1354808400 AS lo, 1354813200 AS hi UNION ALL SELECT 26 AS gap_id, 1355184900 AS lo, 1355189700 AS hi UNION ALL SELECT 27 AS gap_id, 1355189700 AS lo, 1355205300 AS hi UNION ALL SELECT 28 AS gap_id, 1355205300 AS lo, 1355230500 AS hi UNION ALL SELECT 29 AS gap_id, 1356963900 AS lo, 1356969900 AS hi)
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
