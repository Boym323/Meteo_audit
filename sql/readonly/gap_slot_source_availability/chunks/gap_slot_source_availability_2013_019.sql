-- READ-ONLY source-first overlay: exact source records on conditional interior 5-minute slots.
-- Historical snapshot basis: reports/2026-11-12-gap-event-catalog.csv.
-- This query does not assert those slots were expected; source matches are review candidates only.
WITH targets AS (SELECT 1388532600 AS left_time, 1388533200 AS right_time, '2013:1388532600:1388533200' AS gap_id, 600 AS gap_seconds, 'lt_1h' AS gap_band UNION ALL SELECT 1388533200, 1388533800, '2013:1388533200:1388533800', 600, 'lt_1h'), matches AS (SELECT 'loucka_reconstruction' AS source_database, t.gap_band, CASE WHEN a.dateTime >= 1514764800 AND a.dateTime < 1522540800 THEN 'PROTECTED_Q1_2018_DIAGNOSTIC' ELSE 'NORMAL' END AS protection_scope, t.gap_id, a.dateTime AS target_time, a.`usUnits`, a.`interval`, a.`outTemp`, a.`outHumidity`, a.`rain`, a.`rainRate`, a.`barometer`, a.`pressure`, a.`altimeter`, a.`inTemp`, a.`inHumidity`, a.`windSpeed`, a.`windDir`, a.`windGust`, a.`windGustDir`, a.`dewpoint`, a.`windchill`, a.`heatindex`, a.`ET`, a.`radiation`, a.`UV`, a.`extraTemp1`, a.`extraTemp2`, a.`soilTemp1`, a.`soilTemp2`, a.`soilTemp3`, a.`soilTemp4`, a.`soilMoist1` FROM targets t JOIN `loucka_reconstruction`.archive a ON a.dateTime>t.left_time AND a.dateTime<t.right_time AND MOD(a.dateTime-t.left_time,300)=0 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime WHERE r.dateTime IS NULL
UNION ALL
SELECT 'pocasi-loucka.eu' AS source_database, t.gap_band, CASE WHEN a.dateTime >= 1514764800 AND a.dateTime < 1522540800 THEN 'PROTECTED_Q1_2018_DIAGNOSTIC' ELSE 'NORMAL' END AS protection_scope, t.gap_id, a.dateTime AS target_time, a.`usUnits`, a.`interval`, a.`outTemp`, a.`outHumidity`, a.`rain`, a.`rainRate`, a.`barometer`, a.`pressure`, a.`altimeter`, a.`inTemp`, a.`inHumidity`, a.`windSpeed`, a.`windDir`, a.`windGust`, a.`windGustDir`, a.`dewpoint`, a.`windchill`, a.`heatindex`, a.`ET`, a.`radiation`, a.`UV`, a.`extraTemp1`, a.`extraTemp2`, a.`soilTemp1`, a.`soilTemp2`, a.`soilTemp3`, a.`soilTemp4`, a.`soilMoist1` FROM targets t JOIN `pocasi-loucka.eu`.archive a ON a.dateTime>t.left_time AND a.dateTime<t.right_time AND MOD(a.dateTime-t.left_time,300)=0 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime WHERE r.dateTime IS NULL
UNION ALL
SELECT 'pocasi-loucka.eu_GW1000' AS source_database, t.gap_band, CASE WHEN a.dateTime >= 1514764800 AND a.dateTime < 1522540800 THEN 'PROTECTED_Q1_2018_DIAGNOSTIC' ELSE 'NORMAL' END AS protection_scope, t.gap_id, a.dateTime AS target_time, a.`usUnits`, a.`interval`, a.`outTemp`, a.`outHumidity`, a.`rain`, a.`rainRate`, a.`barometer`, a.`pressure`, a.`altimeter`, a.`inTemp`, a.`inHumidity`, a.`windSpeed`, a.`windDir`, a.`windGust`, a.`windGustDir`, a.`dewpoint`, a.`windchill`, a.`heatindex`, a.`ET`, a.`radiation`, a.`UV`, a.`extraTemp1`, a.`extraTemp2`, a.`soilTemp1`, a.`soilTemp2`, a.`soilTemp3`, a.`soilTemp4`, a.`soilMoist1` FROM targets t JOIN `pocasi-loucka.eu_GW1000`.archive a ON a.dateTime>t.left_time AND a.dateTime<t.right_time AND MOD(a.dateTime-t.left_time,300)=0 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime WHERE r.dateTime IS NULL
UNION ALL
SELECT 'pocasi-loucka.eu_old' AS source_database, t.gap_band, CASE WHEN a.dateTime >= 1514764800 AND a.dateTime < 1522540800 THEN 'PROTECTED_Q1_2018_DIAGNOSTIC' ELSE 'NORMAL' END AS protection_scope, t.gap_id, a.dateTime AS target_time, a.`usUnits`, a.`interval`, a.`outTemp`, a.`outHumidity`, a.`rain`, a.`rainRate`, a.`barometer`, a.`pressure`, a.`altimeter`, a.`inTemp`, a.`inHumidity`, a.`windSpeed`, a.`windDir`, a.`windGust`, a.`windGustDir`, a.`dewpoint`, a.`windchill`, a.`heatindex`, a.`ET`, a.`radiation`, a.`UV`, a.`extraTemp1`, a.`extraTemp2`, a.`soilTemp1`, a.`soilTemp2`, a.`soilTemp3`, a.`soilTemp4`, a.`soilMoist1` FROM targets t JOIN `pocasi-loucka.eu_old`.archive a ON a.dateTime>t.left_time AND a.dateTime<t.right_time AND MOD(a.dateTime-t.left_time,300)=0 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime WHERE r.dateTime IS NULL
UNION ALL
SELECT 'old_weewx' AS source_database, t.gap_band, CASE WHEN a.dateTime >= 1514764800 AND a.dateTime < 1522540800 THEN 'PROTECTED_Q1_2018_DIAGNOSTIC' ELSE 'NORMAL' END AS protection_scope, t.gap_id, a.dateTime AS target_time, a.`usUnits`, a.`interval`, a.`outTemp`, a.`outHumidity`, a.`rain`, a.`rainRate`, a.`barometer`, a.`pressure`, a.`altimeter`, a.`inTemp`, a.`inHumidity`, a.`windSpeed`, a.`windDir`, a.`windGust`, a.`windGustDir`, a.`dewpoint`, a.`windchill`, a.`heatindex`, a.`ET`, a.`radiation`, a.`UV`, a.`extraTemp1`, a.`extraTemp2`, a.`soilTemp1`, a.`soilTemp2`, a.`soilTemp3`, a.`soilTemp4`, a.`soilMoist1` FROM targets t JOIN `old_weewx`.archive a ON a.dateTime>t.left_time AND a.dateTime<t.right_time AND MOD(a.dateTime-t.left_time,300)=0 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime WHERE r.dateTime IS NULL
UNION ALL
SELECT 'weewx_WH1080' AS source_database, t.gap_band, CASE WHEN a.dateTime >= 1514764800 AND a.dateTime < 1522540800 THEN 'PROTECTED_Q1_2018_DIAGNOSTIC' ELSE 'NORMAL' END AS protection_scope, t.gap_id, a.dateTime AS target_time, a.`usUnits`, a.`interval`, a.`outTemp`, a.`outHumidity`, a.`rain`, a.`rainRate`, a.`barometer`, a.`pressure`, a.`altimeter`, a.`inTemp`, a.`inHumidity`, a.`windSpeed`, a.`windDir`, a.`windGust`, a.`windGustDir`, a.`dewpoint`, a.`windchill`, a.`heatindex`, a.`ET`, a.`radiation`, a.`UV`, a.`extraTemp1`, a.`extraTemp2`, a.`soilTemp1`, a.`soilTemp2`, a.`soilTemp3`, a.`soilTemp4`, a.`soilMoist1` FROM targets t JOIN `weewx_WH1080`.archive a ON a.dateTime>t.left_time AND a.dateTime<t.right_time AND MOD(a.dateTime-t.left_time,300)=0 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime WHERE r.dateTime IS NULL)
SELECT source_database, gap_band, protection_scope, COUNT(*) AS source_archive_rows,
 COUNT(DISTINCT target_time) AS unique_target_timestamps, COUNT(DISTINCT gap_id) AS gaps_with_source,
 SUM(`usUnits` IS NOT NULL) AS `usUnits_nonnull`,
 SUM(`interval` IS NOT NULL) AS `interval_nonnull`,
 SUM(`outTemp` IS NOT NULL) AS `outTemp_nonnull`,
 SUM(`outHumidity` IS NOT NULL) AS `outHumidity_nonnull`,
 SUM(`rain` IS NOT NULL) AS `rain_nonnull`,
 SUM(`rainRate` IS NOT NULL) AS `rainRate_nonnull`,
 SUM(`barometer` IS NOT NULL) AS `barometer_nonnull`,
 SUM(`pressure` IS NOT NULL) AS `pressure_nonnull`,
 SUM(`altimeter` IS NOT NULL) AS `altimeter_nonnull`,
 SUM(`inTemp` IS NOT NULL) AS `inTemp_nonnull`,
 SUM(`inHumidity` IS NOT NULL) AS `inHumidity_nonnull`,
 SUM(`windSpeed` IS NOT NULL) AS `windSpeed_nonnull`,
 SUM(`windDir` IS NOT NULL) AS `windDir_nonnull`,
 SUM(`windGust` IS NOT NULL) AS `windGust_nonnull`,
 SUM(`windGustDir` IS NOT NULL) AS `windGustDir_nonnull`,
 SUM(`dewpoint` IS NOT NULL) AS `dewpoint_nonnull`,
 SUM(`windchill` IS NOT NULL) AS `windchill_nonnull`,
 SUM(`heatindex` IS NOT NULL) AS `heatindex_nonnull`,
 SUM(`ET` IS NOT NULL) AS `ET_nonnull`,
 SUM(`radiation` IS NOT NULL) AS `radiation_nonnull`,
 SUM(`UV` IS NOT NULL) AS `UV_nonnull`,
 SUM(`extraTemp1` IS NOT NULL) AS `extraTemp1_nonnull`,
 SUM(`extraTemp2` IS NOT NULL) AS `extraTemp2_nonnull`,
 SUM(`soilTemp1` IS NOT NULL) AS `soilTemp1_nonnull`,
 SUM(`soilTemp2` IS NOT NULL) AS `soilTemp2_nonnull`,
 SUM(`soilTemp3` IS NOT NULL) AS `soilTemp3_nonnull`,
 SUM(`soilTemp4` IS NOT NULL) AS `soilTemp4_nonnull`,
 SUM(`soilMoist1` IS NOT NULL) AS `soilMoist1_nonnull`
FROM matches GROUP BY source_database, gap_band, protection_scope ORDER BY source_database, gap_band, protection_scope;
