-- B5 bounded 2014 per-gap source availability; exact open intervals, six archives, READ ONLY.
WITH gaps AS (
 SELECT '2014:1389122400:1389131100' AS gap_id, 1389122400 AS left_time, 1389131100 AS right_time, 8700 AS gap_seconds
UNION ALL
 SELECT '2014:1389261600:1389278400' AS gap_id, 1389261600 AS left_time, 1389278400 AS right_time, 16800 AS gap_seconds
UNION ALL
 SELECT '2014:1389278400:1389291600' AS gap_id, 1389278400 AS left_time, 1389291600 AS right_time, 13200 AS gap_seconds
UNION ALL
 SELECT '2014:1389351300:1389381900' AS gap_id, 1389351300 AS left_time, 1389381900 AS right_time, 30600 AS gap_seconds
UNION ALL
 SELECT '2014:1390346400:1390353000' AS gap_id, 1390346400 AS left_time, 1390353000 AS right_time, 6600 AS gap_seconds
UNION ALL
 SELECT '2014:1390353000:1390359000' AS gap_id, 1390353000 AS left_time, 1390359000 AS right_time, 6000 AS gap_seconds
UNION ALL
 SELECT '2014:1390435500:1390441500' AS gap_id, 1390435500 AS left_time, 1390441500 AS right_time, 6000 AS gap_seconds
UNION ALL
 SELECT '2014:1390523400:1390527000' AS gap_id, 1390523400 AS left_time, 1390527000 AS right_time, 3600 AS gap_seconds
UNION ALL
 SELECT '2014:1394735100:1394765700' AS gap_id, 1394735100 AS left_time, 1394765700 AS right_time, 30600 AS gap_seconds
UNION ALL
 SELECT '2014:1396144500:1396148400' AS gap_id, 1396144500 AS left_time, 1396148400 AS right_time, 3900 AS gap_seconds
UNION ALL
 SELECT '2014:1397281500:1397314800' AS gap_id, 1397281500 AS left_time, 1397314800 AS right_time, 33300 AS gap_seconds
UNION ALL
 SELECT '2014:1398266100:1398292800' AS gap_id, 1398266100 AS left_time, 1398292800 AS right_time, 26700 AS gap_seconds
UNION ALL
 SELECT '2014:1401610800:1401642000' AS gap_id, 1401610800 AS left_time, 1401642000 AS right_time, 31200 AS gap_seconds
UNION ALL
 SELECT '2014:1401643800:1401666600' AS gap_id, 1401643800 AS left_time, 1401666600 AS right_time, 22800 AS gap_seconds
UNION ALL
 SELECT '2014:1401666600:1401674700' AS gap_id, 1401666600 AS left_time, 1401674700 AS right_time, 8100 AS gap_seconds
UNION ALL
 SELECT '2014:1401884400:1401906600' AS gap_id, 1401884400 AS left_time, 1401906600 AS right_time, 22200 AS gap_seconds
UNION ALL
 SELECT '2014:1401906600:1401915600' AS gap_id, 1401906600 AS left_time, 1401915600 AS right_time, 9000 AS gap_seconds
UNION ALL
 SELECT '2014:1402757400:1402800000' AS gap_id, 1402757400 AS left_time, 1402800000 AS right_time, 42600 AS gap_seconds
UNION ALL
 SELECT '2014:1402939800:1403012400' AS gap_id, 1402939800 AS left_time, 1403012400 AS right_time, 72600 AS gap_seconds
UNION ALL
 SELECT '2014:1403304600:1404406800' AS gap_id, 1403304600 AS left_time, 1404406800 AS right_time, 1102200 AS gap_seconds
UNION ALL
 SELECT '2014:1405856700:1405862700' AS gap_id, 1405856700 AS left_time, 1405862700 AS right_time, 6000 AS gap_seconds
UNION ALL
 SELECT '2014:1405977300:1406001900' AS gap_id, 1405977300 AS left_time, 1406001900 AS right_time, 24600 AS gap_seconds
UNION ALL
 SELECT '2014:1406014500:1406018100' AS gap_id, 1406014500 AS left_time, 1406018100 AS right_time, 3600 AS gap_seconds
UNION ALL
 SELECT '2014:1406047800:1406052600' AS gap_id, 1406047800 AS left_time, 1406052600 AS right_time, 4800 AS gap_seconds
UNION ALL
 SELECT '2014:1406060400:1406068200' AS gap_id, 1406060400 AS left_time, 1406068200 AS right_time, 7800 AS gap_seconds
UNION ALL
 SELECT '2014:1406069700:1406073900' AS gap_id, 1406069700 AS left_time, 1406073900 AS right_time, 4200 AS gap_seconds
UNION ALL
 SELECT '2014:1406108400:1406113500' AS gap_id, 1406108400 AS left_time, 1406113500 AS right_time, 5100 AS gap_seconds
UNION ALL
 SELECT '2014:1406113800:1406126100' AS gap_id, 1406113800 AS left_time, 1406126100 AS right_time, 12300 AS gap_seconds
UNION ALL
 SELECT '2014:1406126700:1406130900' AS gap_id, 1406126700 AS left_time, 1406130900 AS right_time, 4200 AS gap_seconds
UNION ALL
 SELECT '2014:1406136900:1406140800' AS gap_id, 1406136900 AS left_time, 1406140800 AS right_time, 3900 AS gap_seconds
UNION ALL
 SELECT '2014:1406231700:1406237100' AS gap_id, 1406231700 AS left_time, 1406237100 AS right_time, 5400 AS gap_seconds
UNION ALL
 SELECT '2014:1406237400:1406313000' AS gap_id, 1406237400 AS left_time, 1406313000 AS right_time, 75600 AS gap_seconds
UNION ALL
 SELECT '2014:1406363400:1406396700' AS gap_id, 1406363400 AS left_time, 1406396700 AS right_time, 33300 AS gap_seconds
UNION ALL
 SELECT '2014:1406442000:1406445900' AS gap_id, 1406442000 AS left_time, 1406445900 AS right_time, 3900 AS gap_seconds
UNION ALL
 SELECT '2014:1407588300:1407597300' AS gap_id, 1407588300 AS left_time, 1407597300 AS right_time, 9000 AS gap_seconds
UNION ALL
 SELECT '2014:1410894600:1410898500' AS gap_id, 1410894600 AS left_time, 1410898500 AS right_time, 3900 AS gap_seconds
UNION ALL
 SELECT '2014:1410900900:1410937800' AS gap_id, 1410900900 AS left_time, 1410937800 AS right_time, 36900 AS gap_seconds
),
reconstruction AS (SELECT g.gap_id, COUNT(a.dateTime) AS row_count, SUM(a.outTemp IS NOT NULL) AS outTemp_nonnull, SUM(a.outTemp=0) AS outTemp_zero, SUM(a.outHumidity IS NOT NULL) AS outHumidity_nonnull, SUM(a.rain IS NOT NULL) AS rain_nonnull, SUM(a.rainRate IS NOT NULL) AS rainRate_nonnull, SUM(a.windSpeed IS NOT NULL) AS windSpeed_nonnull, SUM(a.windGust IS NOT NULL) AS windGust_nonnull, SUM(a.windDir IS NOT NULL) AS windDir_nonnull, SUM(a.barometer IS NOT NULL) AS barometer_nonnull, COUNT(DISTINCT a.usUnits) AS distinct_usUnits, COUNT(DISTINCT a.`interval`) AS distinct_interval FROM gaps g LEFT JOIN `loucka_reconstruction`.archive a ON a.dateTime>g.left_time AND a.dateTime<g.right_time GROUP BY g.gap_id),
eu AS (SELECT g.gap_id, COUNT(a.dateTime) AS row_count, SUM(a.outTemp IS NOT NULL) AS outTemp_nonnull, SUM(a.outTemp=0) AS outTemp_zero, SUM(a.outHumidity IS NOT NULL) AS outHumidity_nonnull, SUM(a.rain IS NOT NULL) AS rain_nonnull, SUM(a.rainRate IS NOT NULL) AS rainRate_nonnull, SUM(a.windSpeed IS NOT NULL) AS windSpeed_nonnull, SUM(a.windGust IS NOT NULL) AS windGust_nonnull, SUM(a.windDir IS NOT NULL) AS windDir_nonnull, SUM(a.barometer IS NOT NULL) AS barometer_nonnull, COUNT(DISTINCT a.usUnits) AS distinct_usUnits, COUNT(DISTINCT a.`interval`) AS distinct_interval FROM gaps g LEFT JOIN `pocasi-loucka.eu`.archive a ON a.dateTime>g.left_time AND a.dateTime<g.right_time GROUP BY g.gap_id),
gw1000 AS (SELECT g.gap_id, COUNT(a.dateTime) AS row_count, SUM(a.outTemp IS NOT NULL) AS outTemp_nonnull, SUM(a.outTemp=0) AS outTemp_zero, SUM(a.outHumidity IS NOT NULL) AS outHumidity_nonnull, SUM(a.rain IS NOT NULL) AS rain_nonnull, SUM(a.rainRate IS NOT NULL) AS rainRate_nonnull, SUM(a.windSpeed IS NOT NULL) AS windSpeed_nonnull, SUM(a.windGust IS NOT NULL) AS windGust_nonnull, SUM(a.windDir IS NOT NULL) AS windDir_nonnull, SUM(a.barometer IS NOT NULL) AS barometer_nonnull, COUNT(DISTINCT a.usUnits) AS distinct_usUnits, COUNT(DISTINCT a.`interval`) AS distinct_interval FROM gaps g LEFT JOIN `pocasi-loucka.eu_GW1000`.archive a ON a.dateTime>g.left_time AND a.dateTime<g.right_time GROUP BY g.gap_id),
eu_old AS (SELECT g.gap_id, COUNT(a.dateTime) AS row_count, SUM(a.outTemp IS NOT NULL) AS outTemp_nonnull, SUM(a.outTemp=0) AS outTemp_zero, SUM(a.outHumidity IS NOT NULL) AS outHumidity_nonnull, SUM(a.rain IS NOT NULL) AS rain_nonnull, SUM(a.rainRate IS NOT NULL) AS rainRate_nonnull, SUM(a.windSpeed IS NOT NULL) AS windSpeed_nonnull, SUM(a.windGust IS NOT NULL) AS windGust_nonnull, SUM(a.windDir IS NOT NULL) AS windDir_nonnull, SUM(a.barometer IS NOT NULL) AS barometer_nonnull, COUNT(DISTINCT a.usUnits) AS distinct_usUnits, COUNT(DISTINCT a.`interval`) AS distinct_interval FROM gaps g LEFT JOIN `pocasi-loucka.eu_old`.archive a ON a.dateTime>g.left_time AND a.dateTime<g.right_time GROUP BY g.gap_id),
old_weewx AS (SELECT g.gap_id, COUNT(a.dateTime) AS row_count, SUM(a.outTemp IS NOT NULL) AS outTemp_nonnull, SUM(a.outTemp=0) AS outTemp_zero, SUM(a.outHumidity IS NOT NULL) AS outHumidity_nonnull, SUM(a.rain IS NOT NULL) AS rain_nonnull, SUM(a.rainRate IS NOT NULL) AS rainRate_nonnull, SUM(a.windSpeed IS NOT NULL) AS windSpeed_nonnull, SUM(a.windGust IS NOT NULL) AS windGust_nonnull, SUM(a.windDir IS NOT NULL) AS windDir_nonnull, SUM(a.barometer IS NOT NULL) AS barometer_nonnull, COUNT(DISTINCT a.usUnits) AS distinct_usUnits, COUNT(DISTINCT a.`interval`) AS distinct_interval FROM gaps g LEFT JOIN `old_weewx`.archive a ON a.dateTime>g.left_time AND a.dateTime<g.right_time GROUP BY g.gap_id),
wh1080 AS (SELECT g.gap_id, COUNT(a.dateTime) AS row_count, SUM(a.outTemp IS NOT NULL) AS outTemp_nonnull, SUM(a.outTemp=0) AS outTemp_zero, SUM(a.outHumidity IS NOT NULL) AS outHumidity_nonnull, SUM(a.rain IS NOT NULL) AS rain_nonnull, SUM(a.rainRate IS NOT NULL) AS rainRate_nonnull, SUM(a.windSpeed IS NOT NULL) AS windSpeed_nonnull, SUM(a.windGust IS NOT NULL) AS windGust_nonnull, SUM(a.windDir IS NOT NULL) AS windDir_nonnull, SUM(a.barometer IS NOT NULL) AS barometer_nonnull, COUNT(DISTINCT a.usUnits) AS distinct_usUnits, COUNT(DISTINCT a.`interval`) AS distinct_interval FROM gaps g LEFT JOIN `weewx_WH1080`.archive a ON a.dateTime>g.left_time AND a.dateTime<g.right_time GROUP BY g.gap_id)
SELECT g.gap_id, g.left_time, g.right_time, g.gap_seconds, COALESCE(reconstruction.row_count,0) AS reconstruction_rows, COALESCE(reconstruction.outTemp_nonnull,0) AS reconstruction_outTemp_nonnull, COALESCE(reconstruction.outTemp_zero,0) AS reconstruction_outTemp_zero, COALESCE(reconstruction.outHumidity_nonnull,0) AS reconstruction_outHumidity_nonnull, COALESCE(reconstruction.rain_nonnull,0) AS reconstruction_rain_nonnull, COALESCE(reconstruction.rainRate_nonnull,0) AS reconstruction_rainRate_nonnull, COALESCE(reconstruction.windSpeed_nonnull,0) AS reconstruction_windSpeed_nonnull, COALESCE(reconstruction.windGust_nonnull,0) AS reconstruction_windGust_nonnull, COALESCE(reconstruction.windDir_nonnull,0) AS reconstruction_windDir_nonnull, COALESCE(reconstruction.barometer_nonnull,0) AS reconstruction_barometer_nonnull, COALESCE(reconstruction.distinct_usUnits,0) AS reconstruction_unit_count, COALESCE(reconstruction.distinct_interval,0) AS reconstruction_interval_count, COALESCE(eu.row_count,0) AS eu_rows, COALESCE(eu.outTemp_nonnull,0) AS eu_outTemp_nonnull, COALESCE(eu.outTemp_zero,0) AS eu_outTemp_zero, COALESCE(eu.outHumidity_nonnull,0) AS eu_outHumidity_nonnull, COALESCE(eu.rain_nonnull,0) AS eu_rain_nonnull, COALESCE(eu.rainRate_nonnull,0) AS eu_rainRate_nonnull, COALESCE(eu.windSpeed_nonnull,0) AS eu_windSpeed_nonnull, COALESCE(eu.windGust_nonnull,0) AS eu_windGust_nonnull, COALESCE(eu.windDir_nonnull,0) AS eu_windDir_nonnull, COALESCE(eu.barometer_nonnull,0) AS eu_barometer_nonnull, COALESCE(eu.distinct_usUnits,0) AS eu_unit_count, COALESCE(eu.distinct_interval,0) AS eu_interval_count, COALESCE(gw1000.row_count,0) AS gw1000_rows, COALESCE(gw1000.outTemp_nonnull,0) AS gw1000_outTemp_nonnull, COALESCE(gw1000.outTemp_zero,0) AS gw1000_outTemp_zero, COALESCE(gw1000.outHumidity_nonnull,0) AS gw1000_outHumidity_nonnull, COALESCE(gw1000.rain_nonnull,0) AS gw1000_rain_nonnull, COALESCE(gw1000.rainRate_nonnull,0) AS gw1000_rainRate_nonnull, COALESCE(gw1000.windSpeed_nonnull,0) AS gw1000_windSpeed_nonnull, COALESCE(gw1000.windGust_nonnull,0) AS gw1000_windGust_nonnull, COALESCE(gw1000.windDir_nonnull,0) AS gw1000_windDir_nonnull, COALESCE(gw1000.barometer_nonnull,0) AS gw1000_barometer_nonnull, COALESCE(gw1000.distinct_usUnits,0) AS gw1000_unit_count, COALESCE(gw1000.distinct_interval,0) AS gw1000_interval_count, COALESCE(eu_old.row_count,0) AS eu_old_rows, COALESCE(eu_old.outTemp_nonnull,0) AS eu_old_outTemp_nonnull, COALESCE(eu_old.outTemp_zero,0) AS eu_old_outTemp_zero, COALESCE(eu_old.outHumidity_nonnull,0) AS eu_old_outHumidity_nonnull, COALESCE(eu_old.rain_nonnull,0) AS eu_old_rain_nonnull, COALESCE(eu_old.rainRate_nonnull,0) AS eu_old_rainRate_nonnull, COALESCE(eu_old.windSpeed_nonnull,0) AS eu_old_windSpeed_nonnull, COALESCE(eu_old.windGust_nonnull,0) AS eu_old_windGust_nonnull, COALESCE(eu_old.windDir_nonnull,0) AS eu_old_windDir_nonnull, COALESCE(eu_old.barometer_nonnull,0) AS eu_old_barometer_nonnull, COALESCE(eu_old.distinct_usUnits,0) AS eu_old_unit_count, COALESCE(eu_old.distinct_interval,0) AS eu_old_interval_count, COALESCE(old_weewx.row_count,0) AS old_weewx_rows, COALESCE(old_weewx.outTemp_nonnull,0) AS old_weewx_outTemp_nonnull, COALESCE(old_weewx.outTemp_zero,0) AS old_weewx_outTemp_zero, COALESCE(old_weewx.outHumidity_nonnull,0) AS old_weewx_outHumidity_nonnull, COALESCE(old_weewx.rain_nonnull,0) AS old_weewx_rain_nonnull, COALESCE(old_weewx.rainRate_nonnull,0) AS old_weewx_rainRate_nonnull, COALESCE(old_weewx.windSpeed_nonnull,0) AS old_weewx_windSpeed_nonnull, COALESCE(old_weewx.windGust_nonnull,0) AS old_weewx_windGust_nonnull, COALESCE(old_weewx.windDir_nonnull,0) AS old_weewx_windDir_nonnull, COALESCE(old_weewx.barometer_nonnull,0) AS old_weewx_barometer_nonnull, COALESCE(old_weewx.distinct_usUnits,0) AS old_weewx_unit_count, COALESCE(old_weewx.distinct_interval,0) AS old_weewx_interval_count, COALESCE(wh1080.row_count,0) AS wh1080_rows, COALESCE(wh1080.outTemp_nonnull,0) AS wh1080_outTemp_nonnull, COALESCE(wh1080.outTemp_zero,0) AS wh1080_outTemp_zero, COALESCE(wh1080.outHumidity_nonnull,0) AS wh1080_outHumidity_nonnull, COALESCE(wh1080.rain_nonnull,0) AS wh1080_rain_nonnull, COALESCE(wh1080.rainRate_nonnull,0) AS wh1080_rainRate_nonnull, COALESCE(wh1080.windSpeed_nonnull,0) AS wh1080_windSpeed_nonnull, COALESCE(wh1080.windGust_nonnull,0) AS wh1080_windGust_nonnull, COALESCE(wh1080.windDir_nonnull,0) AS wh1080_windDir_nonnull, COALESCE(wh1080.barometer_nonnull,0) AS wh1080_barometer_nonnull, COALESCE(wh1080.distinct_usUnits,0) AS wh1080_unit_count, COALESCE(wh1080.distinct_interval,0) AS wh1080_interval_count FROM gaps g LEFT JOIN reconstruction USING(gap_id) LEFT JOIN eu USING(gap_id) LEFT JOIN gw1000 USING(gap_id) LEFT JOIN eu_old USING(gap_id) LEFT JOIN old_weewx USING(gap_id) LEFT JOIN wh1080 USING(gap_id) ORDER BY g.left_time;
