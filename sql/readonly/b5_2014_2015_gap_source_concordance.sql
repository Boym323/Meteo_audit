-- READ-ONLY exact source-copy key/value concordance for 2014-2015 source rows inside the frozen 263 1h-to-<24h target gaps. No inference of omission cause or restoration eligibility.
WITH gaps AS (
SELECT 1 AS gap_no, 1389122400 AS left_time, 1389131100 AS right_time UNION ALL
SELECT 2 AS gap_no, 1389261600 AS left_time, 1389278400 AS right_time UNION ALL
SELECT 3 AS gap_no, 1389278400 AS left_time, 1389291600 AS right_time UNION ALL
SELECT 4 AS gap_no, 1389351300 AS left_time, 1389381900 AS right_time UNION ALL
SELECT 5 AS gap_no, 1390346400 AS left_time, 1390353000 AS right_time UNION ALL
SELECT 6 AS gap_no, 1390353000 AS left_time, 1390359000 AS right_time UNION ALL
SELECT 7 AS gap_no, 1390435500 AS left_time, 1390441500 AS right_time UNION ALL
SELECT 8 AS gap_no, 1390523400 AS left_time, 1390527000 AS right_time UNION ALL
SELECT 9 AS gap_no, 1394735100 AS left_time, 1394765700 AS right_time UNION ALL
SELECT 10 AS gap_no, 1396144500 AS left_time, 1396148400 AS right_time UNION ALL
SELECT 11 AS gap_no, 1397281500 AS left_time, 1397314800 AS right_time UNION ALL
SELECT 12 AS gap_no, 1398266100 AS left_time, 1398292800 AS right_time UNION ALL
SELECT 13 AS gap_no, 1401610800 AS left_time, 1401642000 AS right_time UNION ALL
SELECT 14 AS gap_no, 1401643800 AS left_time, 1401666600 AS right_time UNION ALL
SELECT 15 AS gap_no, 1401666600 AS left_time, 1401674700 AS right_time UNION ALL
SELECT 16 AS gap_no, 1401884400 AS left_time, 1401906600 AS right_time UNION ALL
SELECT 17 AS gap_no, 1401906600 AS left_time, 1401915600 AS right_time UNION ALL
SELECT 18 AS gap_no, 1402757400 AS left_time, 1402800000 AS right_time UNION ALL
SELECT 19 AS gap_no, 1402939800 AS left_time, 1403012400 AS right_time UNION ALL
SELECT 20 AS gap_no, 1405856700 AS left_time, 1405862700 AS right_time UNION ALL
SELECT 21 AS gap_no, 1405977300 AS left_time, 1406001900 AS right_time UNION ALL
SELECT 22 AS gap_no, 1406014500 AS left_time, 1406018100 AS right_time UNION ALL
SELECT 23 AS gap_no, 1406047800 AS left_time, 1406052600 AS right_time UNION ALL
SELECT 24 AS gap_no, 1406060400 AS left_time, 1406068200 AS right_time UNION ALL
SELECT 25 AS gap_no, 1406069700 AS left_time, 1406073900 AS right_time UNION ALL
SELECT 26 AS gap_no, 1406108400 AS left_time, 1406113500 AS right_time UNION ALL
SELECT 27 AS gap_no, 1406113800 AS left_time, 1406126100 AS right_time UNION ALL
SELECT 28 AS gap_no, 1406126700 AS left_time, 1406130900 AS right_time UNION ALL
SELECT 29 AS gap_no, 1406136900 AS left_time, 1406140800 AS right_time UNION ALL
SELECT 30 AS gap_no, 1406231700 AS left_time, 1406237100 AS right_time UNION ALL
SELECT 31 AS gap_no, 1406237400 AS left_time, 1406313000 AS right_time UNION ALL
SELECT 32 AS gap_no, 1406363400 AS left_time, 1406396700 AS right_time UNION ALL
SELECT 33 AS gap_no, 1406442000 AS left_time, 1406445900 AS right_time UNION ALL
SELECT 34 AS gap_no, 1407588300 AS left_time, 1407597300 AS right_time UNION ALL
SELECT 35 AS gap_no, 1410894600 AS left_time, 1410898500 AS right_time UNION ALL
SELECT 36 AS gap_no, 1410900900 AS left_time, 1410937800 AS right_time UNION ALL
SELECT 37 AS gap_no, 1422621600 AS left_time, 1422627000 AS right_time UNION ALL
SELECT 38 AS gap_no, 1423554600 AS left_time, 1423559700 AS right_time UNION ALL
SELECT 39 AS gap_no, 1428317700 AS left_time, 1428325200 AS right_time UNION ALL
SELECT 40 AS gap_no, 1428325800 AS left_time, 1428332100 AS right_time UNION ALL
SELECT 41 AS gap_no, 1428339600 AS left_time, 1428344700 AS right_time UNION ALL
SELECT 42 AS gap_no, 1428345000 AS left_time, 1428348600 AS right_time UNION ALL
SELECT 43 AS gap_no, 1428349800 AS left_time, 1428356100 AS right_time UNION ALL
SELECT 44 AS gap_no, 1428364200 AS left_time, 1428369900 AS right_time UNION ALL
SELECT 45 AS gap_no, 1428373800 AS left_time, 1428384900 AS right_time UNION ALL
SELECT 46 AS gap_no, 1428389400 AS left_time, 1428414000 AS right_time UNION ALL
SELECT 47 AS gap_no, 1428586500 AS left_time, 1428592500 AS right_time UNION ALL
SELECT 48 AS gap_no, 1428594000 AS left_time, 1428602700 AS right_time UNION ALL
SELECT 49 AS gap_no, 1429112400 AS left_time, 1429125000 AS right_time UNION ALL
SELECT 50 AS gap_no, 1429187400 AS left_time, 1429199700 AS right_time UNION ALL
SELECT 51 AS gap_no, 1432824300 AS left_time, 1432830600 AS right_time UNION ALL
SELECT 52 AS gap_no, 1433324100 AS left_time, 1433336400 AS right_time UNION ALL
SELECT 53 AS gap_no, 1436270400 AS left_time, 1436295000 AS right_time UNION ALL
SELECT 54 AS gap_no, 1437067500 AS left_time, 1437079800 AS right_time UNION ALL
SELECT 55 AS gap_no, 1437126600 AS left_time, 1437139200 AS right_time UNION ALL
SELECT 56 AS gap_no, 1438527900 AS left_time, 1438536300 AS right_time UNION ALL
SELECT 57 AS gap_no, 1438707900 AS left_time, 1438711800 AS right_time UNION ALL
SELECT 58 AS gap_no, 1438749600 AS left_time, 1438753800 AS right_time UNION ALL
SELECT 59 AS gap_no, 1438759500 AS left_time, 1438763400 AS right_time UNION ALL
SELECT 60 AS gap_no, 1438803900 AS left_time, 1438865700 AS right_time UNION ALL
SELECT 61 AS gap_no, 1440759900 AS left_time, 1440763800 AS right_time UNION ALL
SELECT 62 AS gap_no, 1443606000 AS left_time, 1443609600 AS right_time UNION ALL
SELECT 63 AS gap_no, 1447841400 AS left_time, 1447845900 AS right_time UNION ALL
SELECT 64 AS gap_no, 1450864200 AS left_time, 1450867800 AS right_time UNION ALL
SELECT 65 AS gap_no, 1451047800 AS left_time, 1451085000 AS right_time
), source_keys AS (
 SELECT g.gap_no,a.dateTime FROM gaps g JOIN old_weewx.archive a ON a.dateTime>g.left_time AND a.dateTime<g.right_time
 UNION
 SELECT g.gap_no,a.dateTime FROM gaps g JOIN weewx_WH1080.archive a ON a.dateTime>g.left_time AND a.dateTime<g.right_time
)
SELECT
 g.gap_no,
 g.left_time,
 g.right_time,
 COUNT(k.dateTime) AS source_union_timestamps,
 SUM(o.dateTime IS NOT NULL) AS old_rows,
 SUM(w.dateTime IS NOT NULL) AS wh1080_rows,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL) AS exact_timestamp_pairs,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NULL) AS old_only_timestamps,
 SUM(o.dateTime IS NULL AND w.dateTime IS NOT NULL) AS wh1080_only_timestamps,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND (o.usUnits<>w.usUnits OR o.interval<>w.interval)) AS unit_interval_conflicts,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL) AS `outTemp_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL AND o.`outTemp`=w.`outTemp`) AS `outTemp_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL AND o.`outTemp`<>w.`outTemp`) AS `outTemp_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`outTemp` IS NULL)<>(w.`outTemp` IS NULL))) AS `outTemp_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL) AS `outHumidity_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL AND o.`outHumidity`=w.`outHumidity`) AS `outHumidity_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL AND o.`outHumidity`<>w.`outHumidity`) AS `outHumidity_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`outHumidity` IS NULL)<>(w.`outHumidity` IS NULL))) AS `outHumidity_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`rain` IS NOT NULL AND w.`rain` IS NOT NULL) AS `rain_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`rain` IS NOT NULL AND w.`rain` IS NOT NULL AND o.`rain`=w.`rain`) AS `rain_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`rain` IS NOT NULL AND w.`rain` IS NOT NULL AND o.`rain`<>w.`rain`) AS `rain_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`rain` IS NULL)<>(w.`rain` IS NULL))) AS `rain_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL) AS `rainRate_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL AND o.`rainRate`=w.`rainRate`) AS `rainRate_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL AND o.`rainRate`<>w.`rainRate`) AS `rainRate_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`rainRate` IS NULL)<>(w.`rainRate` IS NULL))) AS `rainRate_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL) AS `windSpeed_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL AND o.`windSpeed`=w.`windSpeed`) AS `windSpeed_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL AND o.`windSpeed`<>w.`windSpeed`) AS `windSpeed_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`windSpeed` IS NULL)<>(w.`windSpeed` IS NULL))) AS `windSpeed_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL) AS `windGust_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL AND o.`windGust`=w.`windGust`) AS `windGust_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL AND o.`windGust`<>w.`windGust`) AS `windGust_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`windGust` IS NULL)<>(w.`windGust` IS NULL))) AS `windGust_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL) AS `windDir_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL AND o.`windDir`=w.`windDir`) AS `windDir_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL AND o.`windDir`<>w.`windDir`) AS `windDir_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`windDir` IS NULL)<>(w.`windDir` IS NULL))) AS `windDir_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL) AS `pressure_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL AND o.`pressure`=w.`pressure`) AS `pressure_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL AND o.`pressure`<>w.`pressure`) AS `pressure_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`pressure` IS NULL)<>(w.`pressure` IS NULL))) AS `pressure_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL) AS `barometer_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL AND o.`barometer`=w.`barometer`) AS `barometer_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL AND o.`barometer`<>w.`barometer`) AS `barometer_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`barometer` IS NULL)<>(w.`barometer` IS NULL))) AS `barometer_null_asymmetry`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL) AS `altimeter_paired_nonnull`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL AND o.`altimeter`=w.`altimeter`) AS `altimeter_equal`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL AND o.`altimeter`<>w.`altimeter`) AS `altimeter_conflict`,
 SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`altimeter` IS NULL)<>(w.`altimeter` IS NULL))) AS `altimeter_null_asymmetry`
FROM gaps g LEFT JOIN source_keys k ON k.gap_no=g.gap_no
LEFT JOIN old_weewx.archive o ON o.dateTime=k.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=k.dateTime
GROUP BY g.gap_no,g.left_time,g.right_time ORDER BY g.gap_no;
