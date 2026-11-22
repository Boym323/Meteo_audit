-- READ-ONLY aggregate; fixed UTC gap episodes from the frozen interval-aware catalog.
WITH gaps AS (SELECT 1 AS gap_id, 1297021500 AS lo, 1297028700 AS hi UNION ALL SELECT 2 AS gap_id, 1301452200 AS lo, 1301475000 AS hi UNION ALL SELECT 3 AS gap_id, 1304112900 AS lo, 1304121600 AS hi UNION ALL SELECT 4 AS gap_id, 1304121600 AS lo, 1304127600 AS hi UNION ALL SELECT 5 AS gap_id, 1304127600 AS lo, 1304133600 AS hi UNION ALL SELECT 6 AS gap_id, 1304133600 AS lo, 1304139600 AS hi UNION ALL SELECT 7 AS gap_id, 1304139600 AS lo, 1304160600 AS hi UNION ALL SELECT 8 AS gap_id, 1304160600 AS lo, 1304166600 AS hi UNION ALL SELECT 9 AS gap_id, 1304166600 AS lo, 1304172600 AS hi UNION ALL SELECT 10 AS gap_id, 1304172600 AS lo, 1304178600 AS hi UNION ALL SELECT 11 AS gap_id, 1304178600 AS lo, 1304184600 AS hi UNION ALL SELECT 12 AS gap_id, 1304184600 AS lo, 1304190600 AS hi UNION ALL SELECT 13 AS gap_id, 1304190600 AS lo, 1304196600 AS hi UNION ALL SELECT 14 AS gap_id, 1304196600 AS lo, 1304202600 AS hi UNION ALL SELECT 15 AS gap_id, 1304202600 AS lo, 1304212500 AS hi UNION ALL SELECT 16 AS gap_id, 1304212500 AS lo, 1304218500 AS hi UNION ALL SELECT 17 AS gap_id, 1304218500 AS lo, 1304230500 AS hi UNION ALL SELECT 18 AS gap_id, 1304230500 AS lo, 1304236500 AS hi UNION ALL SELECT 19 AS gap_id, 1304236500 AS lo, 1304242500 AS hi UNION ALL SELECT 20 AS gap_id, 1304242500 AS lo, 1304248500 AS hi UNION ALL SELECT 21 AS gap_id, 1304248500 AS lo, 1304254500 AS hi UNION ALL SELECT 22 AS gap_id, 1304254500 AS lo, 1304260500 AS hi UNION ALL SELECT 23 AS gap_id, 1304260500 AS lo, 1304266500 AS hi UNION ALL SELECT 24 AS gap_id, 1304266500 AS lo, 1304272500 AS hi UNION ALL SELECT 25 AS gap_id, 1304272500 AS lo, 1304278500 AS hi UNION ALL SELECT 26 AS gap_id, 1304278500 AS lo, 1304284500 AS hi UNION ALL SELECT 27 AS gap_id, 1304284500 AS lo, 1304290500 AS hi UNION ALL SELECT 28 AS gap_id, 1304290500 AS lo, 1304296500 AS hi UNION ALL SELECT 29 AS gap_id, 1304296500 AS lo, 1304302500 AS hi UNION ALL SELECT 30 AS gap_id, 1304302500 AS lo, 1304308500 AS hi UNION ALL SELECT 31 AS gap_id, 1304308500 AS lo, 1304314500 AS hi UNION ALL SELECT 32 AS gap_id, 1304314500 AS lo, 1304320500 AS hi UNION ALL SELECT 33 AS gap_id, 1304320500 AS lo, 1304326500 AS hi UNION ALL SELECT 34 AS gap_id, 1304326500 AS lo, 1304332500 AS hi UNION ALL SELECT 35 AS gap_id, 1304332500 AS lo, 1304338500 AS hi UNION ALL SELECT 36 AS gap_id, 1304338500 AS lo, 1304344500 AS hi UNION ALL SELECT 37 AS gap_id, 1304344500 AS lo, 1304350500 AS hi UNION ALL SELECT 38 AS gap_id, 1304350500 AS lo, 1304368500 AS hi UNION ALL SELECT 39 AS gap_id, 1304368500 AS lo, 1304374500 AS hi UNION ALL SELECT 40 AS gap_id, 1304374500 AS lo, 1304380500 AS hi UNION ALL SELECT 41 AS gap_id, 1304380500 AS lo, 1304386500 AS hi UNION ALL SELECT 42 AS gap_id, 1304386500 AS lo, 1304392500 AS hi UNION ALL SELECT 43 AS gap_id, 1304392500 AS lo, 1304398500 AS hi UNION ALL SELECT 44 AS gap_id, 1304398500 AS lo, 1304404500 AS hi UNION ALL SELECT 45 AS gap_id, 1304404500 AS lo, 1304413200 AS hi UNION ALL SELECT 46 AS gap_id, 1304413200 AS lo, 1304438700 AS hi UNION ALL SELECT 47 AS gap_id, 1305483600 AS lo, 1305490200 AS hi UNION ALL SELECT 48 AS gap_id, 1305490200 AS lo, 1305497100 AS hi UNION ALL SELECT 49 AS gap_id, 1305632100 AS lo, 1305638400 AS hi UNION ALL SELECT 50 AS gap_id, 1307442600 AS lo, 1307447400 AS hi UNION ALL SELECT 51 AS gap_id, 1308202500 AS lo, 1308261600 AS hi UNION ALL SELECT 52 AS gap_id, 1309323900 AS lo, 1309331700 AS hi UNION ALL SELECT 53 AS gap_id, 1309347300 AS lo, 1309353000 AS hi UNION ALL SELECT 54 AS gap_id, 1310120400 AS lo, 1310127300 AS hi UNION ALL SELECT 55 AS gap_id, 1310852700 AS lo, 1310858700 AS hi UNION ALL SELECT 56 AS gap_id, 1313091000 AS lo, 1313098200 AS hi)
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
