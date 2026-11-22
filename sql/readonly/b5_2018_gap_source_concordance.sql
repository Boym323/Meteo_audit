-- READ-ONLY exact source-copy key/value concordance for 2018 source rows inside the frozen 263 1h-to-<24h target gaps. No inference of omission cause or restoration eligibility.
WITH gaps AS (
SELECT 1 AS gap_no, 1516295100 AS left_time, 1516317300 AS right_time UNION ALL
SELECT 2 AS gap_no, 1516595400 AS left_time, 1516613100 AS right_time UNION ALL
SELECT 3 AS gap_no, 1516766400 AS left_time, 1516773600 AS right_time UNION ALL
SELECT 4 AS gap_no, 1516903200 AS left_time, 1516928100 AS right_time UNION ALL
SELECT 5 AS gap_no, 1517124900 AS left_time, 1517131200 AS right_time UNION ALL
SELECT 6 AS gap_no, 1517260800 AS left_time, 1517264700 AS right_time UNION ALL
SELECT 7 AS gap_no, 1517331300 AS left_time, 1517338200 AS right_time UNION ALL
SELECT 8 AS gap_no, 1517386800 AS left_time, 1517393400 AS right_time UNION ALL
SELECT 9 AS gap_no, 1517612400 AS left_time, 1517618100 AS right_time UNION ALL
SELECT 10 AS gap_no, 1517628600 AS left_time, 1517644500 AS right_time UNION ALL
SELECT 11 AS gap_no, 1517722500 AS left_time, 1517728800 AS right_time UNION ALL
SELECT 12 AS gap_no, 1517730000 AS left_time, 1517734500 AS right_time UNION ALL
SELECT 13 AS gap_no, 1517760900 AS left_time, 1517778900 AS right_time UNION ALL
SELECT 14 AS gap_no, 1517782800 AS left_time, 1517799600 AS right_time UNION ALL
SELECT 15 AS gap_no, 1517804400 AS left_time, 1517817000 AS right_time UNION ALL
SELECT 16 AS gap_no, 1517847000 AS left_time, 1517916900 AS right_time UNION ALL
SELECT 17 AS gap_no, 1517960400 AS left_time, 1517979600 AS right_time UNION ALL
SELECT 18 AS gap_no, 1518102600 AS left_time, 1518166200 AS right_time UNION ALL
SELECT 19 AS gap_no, 1518238500 AS left_time, 1518258300 AS right_time UNION ALL
SELECT 20 AS gap_no, 1518278100 AS left_time, 1518336900 AS right_time UNION ALL
SELECT 21 AS gap_no, 1518367500 AS left_time, 1518378900 AS right_time UNION ALL
SELECT 22 AS gap_no, 1518469800 AS left_time, 1518505800 AS right_time UNION ALL
SELECT 23 AS gap_no, 1518568200 AS left_time, 1518594000 AS right_time UNION ALL
SELECT 24 AS gap_no, 1518641700 AS left_time, 1518645600 AS right_time UNION ALL
SELECT 25 AS gap_no, 1518710400 AS left_time, 1518729300 AS right_time UNION ALL
SELECT 26 AS gap_no, 1518820500 AS left_time, 1518858300 AS right_time UNION ALL
SELECT 27 AS gap_no, 1518926700 AS left_time, 1518936600 AS right_time UNION ALL
SELECT 28 AS gap_no, 1518985800 AS left_time, 1519031400 AS right_time UNION ALL
SELECT 29 AS gap_no, 1519054500 AS left_time, 1519116300 AS right_time UNION ALL
SELECT 30 AS gap_no, 1519163100 AS left_time, 1519203000 AS right_time UNION ALL
SELECT 31 AS gap_no, 1519224900 AS left_time, 1519287000 AS right_time UNION ALL
SELECT 32 AS gap_no, 1519301400 AS left_time, 1519305600 AS right_time UNION ALL
SELECT 33 AS gap_no, 1519315500 AS left_time, 1519375500 AS right_time UNION ALL
SELECT 34 AS gap_no, 1519386000 AS left_time, 1519390800 AS right_time UNION ALL
SELECT 35 AS gap_no, 1519392000 AS left_time, 1519395600 AS right_time UNION ALL
SELECT 36 AS gap_no, 1520083800 AS left_time, 1520087400 AS right_time UNION ALL
SELECT 37 AS gap_no, 1520088300 AS left_time, 1520094300 AS right_time UNION ALL
SELECT 38 AS gap_no, 1520094300 AS left_time, 1520152800 AS right_time UNION ALL
SELECT 39 AS gap_no, 1520213700 AS left_time, 1520223300 AS right_time UNION ALL
SELECT 40 AS gap_no, 1520396400 AS left_time, 1520400000 AS right_time UNION ALL
SELECT 41 AS gap_no, 1520436600 AS left_time, 1520442300 AS right_time UNION ALL
SELECT 42 AS gap_no, 1520551200 AS left_time, 1520576400 AS right_time UNION ALL
SELECT 43 AS gap_no, 1520581500 AS left_time, 1520588700 AS right_time UNION ALL
SELECT 44 AS gap_no, 1520678100 AS left_time, 1520693700 AS right_time UNION ALL
SELECT 45 AS gap_no, 1520708400 AS left_time, 1520753100 AS right_time UNION ALL
SELECT 46 AS gap_no, 1520760600 AS left_time, 1520781000 AS right_time UNION ALL
SELECT 47 AS gap_no, 1520814000 AS left_time, 1520822100 AS right_time UNION ALL
SELECT 48 AS gap_no, 1520843400 AS left_time, 1520854800 AS right_time UNION ALL
SELECT 49 AS gap_no, 1520875200 AS left_time, 1520897400 AS right_time UNION ALL
SELECT 50 AS gap_no, 1520922600 AS left_time, 1520927400 AS right_time UNION ALL
SELECT 51 AS gap_no, 1521152400 AS left_time, 1521158400 AS right_time UNION ALL
SELECT 52 AS gap_no, 1521221400 AS left_time, 1521225300 AS right_time UNION ALL
SELECT 53 AS gap_no, 1521277200 AS left_time, 1521282600 AS right_time UNION ALL
SELECT 54 AS gap_no, 1521282600 AS left_time, 1521287700 AS right_time UNION ALL
SELECT 55 AS gap_no, 1521288000 AS left_time, 1521292800 AS right_time UNION ALL
SELECT 56 AS gap_no, 1521311400 AS left_time, 1521375600 AS right_time UNION ALL
SELECT 57 AS gap_no, 1521379500 AS left_time, 1521387600 AS right_time UNION ALL
SELECT 58 AS gap_no, 1521390300 AS left_time, 1521453000 AS right_time UNION ALL
SELECT 59 AS gap_no, 1521476400 AS left_time, 1521536100 AS right_time UNION ALL
SELECT 60 AS gap_no, 1521581100 AS left_time, 1521614100 AS right_time UNION ALL
SELECT 61 AS gap_no, 1521658500 AS left_time, 1521702600 AS right_time UNION ALL
SELECT 62 AS gap_no, 1521751500 AS left_time, 1521785400 AS right_time UNION ALL
SELECT 63 AS gap_no, 1521847200 AS left_time, 1521871200 AS right_time
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
