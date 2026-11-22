-- READ-ONLY aggregate; fixed UTC gap episodes from the frozen interval-aware catalog.
WITH gaps AS (SELECT 1 AS gap_id, 1357466400 AS lo, 1357472100 AS hi UNION ALL SELECT 2 AS gap_id, 1359457200 AS lo, 1359529500 AS hi UNION ALL SELECT 3 AS gap_id, 1360676100 AS lo, 1360680300 AS hi UNION ALL SELECT 4 AS gap_id, 1360921500 AS lo, 1360927200 AS hi UNION ALL SELECT 5 AS gap_id, 1362166800 AS lo, 1362171600 AS hi UNION ALL SELECT 6 AS gap_id, 1362580800 AS lo, 1362644700 AS hi UNION ALL SELECT 7 AS gap_id, 1363401300 AS lo, 1363407300 AS hi UNION ALL SELECT 8 AS gap_id, 1363409100 AS lo, 1363413300 AS hi UNION ALL SELECT 9 AS gap_id, 1363415100 AS lo, 1363419300 AS hi UNION ALL SELECT 10 AS gap_id, 1363421100 AS lo, 1363425300 AS hi UNION ALL SELECT 11 AS gap_id, 1363427100 AS lo, 1363431300 AS hi UNION ALL SELECT 12 AS gap_id, 1363431300 AS lo, 1363435500 AS hi UNION ALL SELECT 13 AS gap_id, 1364238300 AS lo, 1364242200 AS hi UNION ALL SELECT 14 AS gap_id, 1364694900 AS lo, 1364698800 AS hi UNION ALL SELECT 15 AS gap_id, 1367210100 AS lo, 1367228400 AS hi UNION ALL SELECT 16 AS gap_id, 1367228400 AS lo, 1367251800 AS hi UNION ALL SELECT 17 AS gap_id, 1369740600 AS lo, 1369760100 AS hi UNION ALL SELECT 18 AS gap_id, 1371064200 AS lo, 1371070200 AS hi UNION ALL SELECT 19 AS gap_id, 1371070200 AS lo, 1371094500 AS hi UNION ALL SELECT 20 AS gap_id, 1372629000 AS lo, 1372635000 AS hi UNION ALL SELECT 21 AS gap_id, 1373500500 AS lo, 1373544300 AS hi UNION ALL SELECT 22 AS gap_id, 1382829900 AS lo, 1382856600 AS hi UNION ALL SELECT 23 AS gap_id, 1386043500 AS lo, 1386078300 AS hi UNION ALL SELECT 24 AS gap_id, 1388063700 AS lo, 1388088000 AS hi)
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
