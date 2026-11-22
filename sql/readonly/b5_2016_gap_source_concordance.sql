-- READ-ONLY exact source-copy key/value concordance for 2016 source rows inside the frozen 263 1h-to-<24h target gaps. No inference of omission cause or restoration eligibility.
WITH gaps AS (
SELECT 1 AS gap_no, 1454890200 AS left_time, 1454895000 AS right_time UNION ALL
SELECT 2 AS gap_no, 1456298400 AS left_time, 1456305300 AS right_time UNION ALL
SELECT 3 AS gap_no, 1456311900 AS left_time, 1456315500 AS right_time UNION ALL
SELECT 4 AS gap_no, 1456356900 AS left_time, 1456394100 AS right_time UNION ALL
SELECT 5 AS gap_no, 1456841100 AS left_time, 1456847400 AS right_time UNION ALL
SELECT 6 AS gap_no, 1456847400 AS left_time, 1456854000 AS right_time UNION ALL
SELECT 7 AS gap_no, 1456857000 AS left_time, 1456860600 AS right_time UNION ALL
SELECT 8 AS gap_no, 1456863900 AS left_time, 1456867800 AS right_time UNION ALL
SELECT 9 AS gap_no, 1456884600 AS left_time, 1456888200 AS right_time UNION ALL
SELECT 10 AS gap_no, 1456892400 AS left_time, 1456917300 AS right_time UNION ALL
SELECT 11 AS gap_no, 1458241800 AS left_time, 1458247500 AS right_time UNION ALL
SELECT 12 AS gap_no, 1458248700 AS left_time, 1458324600 AS right_time UNION ALL
SELECT 13 AS gap_no, 1458344400 AS left_time, 1458357000 AS right_time UNION ALL
SELECT 14 AS gap_no, 1464894300 AS left_time, 1464898200 AS right_time UNION ALL
SELECT 15 AS gap_no, 1464898500 AS left_time, 1464902100 AS right_time UNION ALL
SELECT 16 AS gap_no, 1465141800 AS left_time, 1465148400 AS right_time UNION ALL
SELECT 17 AS gap_no, 1465148700 AS left_time, 1465173300 AS right_time UNION ALL
SELECT 18 AS gap_no, 1465187100 AS left_time, 1465199700 AS right_time UNION ALL
SELECT 19 AS gap_no, 1465200900 AS left_time, 1465214400 AS right_time UNION ALL
SELECT 20 AS gap_no, 1465214700 AS left_time, 1465226400 AS right_time UNION ALL
SELECT 21 AS gap_no, 1465226400 AS left_time, 1465231200 AS right_time UNION ALL
SELECT 22 AS gap_no, 1465231500 AS left_time, 1465236600 AS right_time UNION ALL
SELECT 23 AS gap_no, 1465331100 AS left_time, 1465338300 AS right_time UNION ALL
SELECT 24 AS gap_no, 1465347300 AS left_time, 1465353000 AS right_time UNION ALL
SELECT 25 AS gap_no, 1465357800 AS left_time, 1465368600 AS right_time UNION ALL
SELECT 26 AS gap_no, 1465397700 AS left_time, 1465402500 AS right_time UNION ALL
SELECT 27 AS gap_no, 1466842500 AS left_time, 1466847000 AS right_time UNION ALL
SELECT 28 AS gap_no, 1466847000 AS left_time, 1466851200 AS right_time UNION ALL
SELECT 29 AS gap_no, 1466851500 AS left_time, 1466860800 AS right_time UNION ALL
SELECT 30 AS gap_no, 1467665400 AS left_time, 1467669000 AS right_time UNION ALL
SELECT 31 AS gap_no, 1467669300 AS left_time, 1467674100 AS right_time UNION ALL
SELECT 32 AS gap_no, 1467677100 AS left_time, 1467687000 AS right_time UNION ALL
SELECT 33 AS gap_no, 1468297200 AS left_time, 1468305000 AS right_time UNION ALL
SELECT 34 AS gap_no, 1468307100 AS left_time, 1468315200 AS right_time UNION ALL
SELECT 35 AS gap_no, 1468346100 AS left_time, 1468395300 AS right_time UNION ALL
SELECT 36 AS gap_no, 1468428900 AS left_time, 1468448100 AS right_time UNION ALL
SELECT 37 AS gap_no, 1468464000 AS left_time, 1468468200 AS right_time UNION ALL
SELECT 38 AS gap_no, 1468512000 AS left_time, 1468517700 AS right_time UNION ALL
SELECT 39 AS gap_no, 1468521600 AS left_time, 1468525200 AS right_time UNION ALL
SELECT 40 AS gap_no, 1468525800 AS left_time, 1468532700 AS right_time UNION ALL
SELECT 41 AS gap_no, 1468539600 AS left_time, 1468556400 AS right_time UNION ALL
SELECT 42 AS gap_no, 1468568100 AS left_time, 1468574400 AS right_time UNION ALL
SELECT 43 AS gap_no, 1469289300 AS left_time, 1469302800 AS right_time UNION ALL
SELECT 44 AS gap_no, 1469334600 AS left_time, 1469339400 AS right_time UNION ALL
SELECT 45 AS gap_no, 1469341500 AS left_time, 1469345100 AS right_time UNION ALL
SELECT 46 AS gap_no, 1469422500 AS left_time, 1469429100 AS right_time UNION ALL
SELECT 47 AS gap_no, 1469596800 AS left_time, 1469605200 AS right_time UNION ALL
SELECT 48 AS gap_no, 1469612400 AS left_time, 1469616300 AS right_time UNION ALL
SELECT 49 AS gap_no, 1469646000 AS left_time, 1469669100 AS right_time UNION ALL
SELECT 50 AS gap_no, 1469673900 AS left_time, 1469682000 AS right_time UNION ALL
SELECT 51 AS gap_no, 1469686800 AS left_time, 1469690400 AS right_time UNION ALL
SELECT 52 AS gap_no, 1469908500 AS left_time, 1469915700 AS right_time UNION ALL
SELECT 53 AS gap_no, 1469916300 AS left_time, 1469965800 AS right_time UNION ALL
SELECT 54 AS gap_no, 1469979900 AS left_time, 1469983500 AS right_time UNION ALL
SELECT 55 AS gap_no, 1469986200 AS left_time, 1470048300 AS right_time UNION ALL
SELECT 56 AS gap_no, 1470223500 AS left_time, 1470227100 AS right_time UNION ALL
SELECT 57 AS gap_no, 1470270600 AS left_time, 1470275700 AS right_time UNION ALL
SELECT 58 AS gap_no, 1471570500 AS left_time, 1471576500 AS right_time UNION ALL
SELECT 59 AS gap_no, 1471785900 AS left_time, 1471792800 AS right_time UNION ALL
SELECT 60 AS gap_no, 1471832100 AS left_time, 1471836900 AS right_time UNION ALL
SELECT 61 AS gap_no, 1471916700 AS left_time, 1471920300 AS right_time UNION ALL
SELECT 62 AS gap_no, 1471922700 AS left_time, 1471926300 AS right_time UNION ALL
SELECT 63 AS gap_no, 1472239800 AS left_time, 1472245800 AS right_time UNION ALL
SELECT 64 AS gap_no, 1472447100 AS left_time, 1472483700 AS right_time UNION ALL
SELECT 65 AS gap_no, 1472540100 AS left_time, 1472578800 AS right_time UNION ALL
SELECT 66 AS gap_no, 1472902500 AS left_time, 1472907300 AS right_time UNION ALL
SELECT 67 AS gap_no, 1472992200 AS left_time, 1472999100 AS right_time UNION ALL
SELECT 68 AS gap_no, 1473006900 AS left_time, 1473017400 AS right_time UNION ALL
SELECT 69 AS gap_no, 1473020700 AS left_time, 1473025800 AS right_time UNION ALL
SELECT 70 AS gap_no, 1473096900 AS left_time, 1473133800 AS right_time UNION ALL
SELECT 71 AS gap_no, 1473186600 AS left_time, 1473198600 AS right_time UNION ALL
SELECT 72 AS gap_no, 1473198900 AS left_time, 1473205500 AS right_time UNION ALL
SELECT 73 AS gap_no, 1473205800 AS left_time, 1473210600 AS right_time UNION ALL
SELECT 74 AS gap_no, 1473211200 AS left_time, 1473219300 AS right_time UNION ALL
SELECT 75 AS gap_no, 1473220800 AS left_time, 1473225300 AS right_time UNION ALL
SELECT 76 AS gap_no, 1473384000 AS left_time, 1473396300 AS right_time UNION ALL
SELECT 77 AS gap_no, 1473447000 AS left_time, 1473526800 AS right_time UNION ALL
SELECT 78 AS gap_no, 1473528600 AS left_time, 1473602100 AS right_time UNION ALL
SELECT 79 AS gap_no, 1473602400 AS left_time, 1473607800 AS right_time UNION ALL
SELECT 80 AS gap_no, 1473648000 AS left_time, 1473652800 AS right_time UNION ALL
SELECT 81 AS gap_no, 1473663300 AS left_time, 1473669000 AS right_time UNION ALL
SELECT 82 AS gap_no, 1474085400 AS left_time, 1474090800 AS right_time UNION ALL
SELECT 83 AS gap_no, 1474096800 AS left_time, 1474116000 AS right_time UNION ALL
SELECT 84 AS gap_no, 1474119000 AS left_time, 1474125900 AS right_time UNION ALL
SELECT 85 AS gap_no, 1474126800 AS left_time, 1474148100 AS right_time UNION ALL
SELECT 86 AS gap_no, 1474148400 AS left_time, 1474155600 AS right_time UNION ALL
SELECT 87 AS gap_no, 1474156500 AS left_time, 1474166100 AS right_time UNION ALL
SELECT 88 AS gap_no, 1474167600 AS left_time, 1474196400 AS right_time UNION ALL
SELECT 89 AS gap_no, 1474197000 AS left_time, 1474205100 AS right_time UNION ALL
SELECT 90 AS gap_no, 1474206900 AS left_time, 1474211400 AS right_time UNION ALL
SELECT 91 AS gap_no, 1474211700 AS left_time, 1474217700 AS right_time UNION ALL
SELECT 92 AS gap_no, 1474218300 AS left_time, 1474228200 AS right_time UNION ALL
SELECT 93 AS gap_no, 1474268100 AS left_time, 1474274100 AS right_time UNION ALL
SELECT 94 AS gap_no, 1474274400 AS left_time, 1474281600 AS right_time UNION ALL
SELECT 95 AS gap_no, 1474282800 AS left_time, 1474291500 AS right_time UNION ALL
SELECT 96 AS gap_no, 1474292400 AS left_time, 1474298400 AS right_time UNION ALL
SELECT 97 AS gap_no, 1474298700 AS left_time, 1474305300 AS right_time UNION ALL
SELECT 98 AS gap_no, 1474309200 AS left_time, 1474325700 AS right_time UNION ALL
SELECT 99 AS gap_no, 1474326000 AS left_time, 1474331100 AS right_time UNION ALL
SELECT 100 AS gap_no, 1474331700 AS left_time, 1474335300 AS right_time UNION ALL
SELECT 101 AS gap_no, 1474335600 AS left_time, 1474339800 AS right_time UNION ALL
SELECT 102 AS gap_no, 1474341000 AS left_time, 1474353300 AS right_time UNION ALL
SELECT 103 AS gap_no, 1474356600 AS left_time, 1474361700 AS right_time UNION ALL
SELECT 104 AS gap_no, 1474619100 AS left_time, 1474622700 AS right_time UNION ALL
SELECT 105 AS gap_no, 1474765200 AS left_time, 1474772400 AS right_time UNION ALL
SELECT 106 AS gap_no, 1474774800 AS left_time, 1474784700 AS right_time UNION ALL
SELECT 107 AS gap_no, 1474806600 AS left_time, 1474812600 AS right_time UNION ALL
SELECT 108 AS gap_no, 1474812900 AS left_time, 1474817400 AS right_time UNION ALL
SELECT 109 AS gap_no, 1475158200 AS left_time, 1475162100 AS right_time UNION ALL
SELECT 110 AS gap_no, 1475242500 AS left_time, 1475253300 AS right_time UNION ALL
SELECT 111 AS gap_no, 1475253600 AS left_time, 1475258700 AS right_time UNION ALL
SELECT 112 AS gap_no, 1476189300 AS left_time, 1476195900 AS right_time UNION ALL
SELECT 113 AS gap_no, 1477720200 AS left_time, 1477723800 AS right_time UNION ALL
SELECT 114 AS gap_no, 1478259600 AS left_time, 1478266500 AS right_time UNION ALL
SELECT 115 AS gap_no, 1478299500 AS left_time, 1478305200 AS right_time UNION ALL
SELECT 116 AS gap_no, 1478342100 AS left_time, 1478346300 AS right_time UNION ALL
SELECT 117 AS gap_no, 1478346900 AS left_time, 1478351400 AS right_time UNION ALL
SELECT 118 AS gap_no, 1478393100 AS left_time, 1478397300 AS right_time UNION ALL
SELECT 119 AS gap_no, 1478400300 AS left_time, 1478403900 AS right_time UNION ALL
SELECT 120 AS gap_no, 1478431500 AS left_time, 1478438100 AS right_time UNION ALL
SELECT 121 AS gap_no, 1478503500 AS left_time, 1478511300 AS right_time UNION ALL
SELECT 122 AS gap_no, 1478520000 AS left_time, 1478524200 AS right_time UNION ALL
SELECT 123 AS gap_no, 1478803500 AS left_time, 1478809200 AS right_time UNION ALL
SELECT 124 AS gap_no, 1479318600 AS left_time, 1479380100 AS right_time UNION ALL
SELECT 125 AS gap_no, 1481123400 AS left_time, 1481197500 AS right_time UNION ALL
SELECT 126 AS gap_no, 1481866500 AS left_time, 1481871300 AS right_time UNION ALL
SELECT 127 AS gap_no, 1481871600 AS left_time, 1481896500 AS right_time UNION ALL
SELECT 128 AS gap_no, 1482094500 AS left_time, 1482156300 AS right_time UNION ALL
SELECT 129 AS gap_no, 1482535200 AS left_time, 1482539100 AS right_time UNION ALL
SELECT 130 AS gap_no, 1482721200 AS left_time, 1482727200 AS right_time UNION ALL
SELECT 131 AS gap_no, 1482739800 AS left_time, 1482743400 AS right_time UNION ALL
SELECT 132 AS gap_no, 1482765300 AS left_time, 1482768900 AS right_time UNION ALL
SELECT 133 AS gap_no, 1482840600 AS left_time, 1482852600 AS right_time UNION ALL
SELECT 134 AS gap_no, 1483127700 AS left_time, 1483134000 AS right_time UNION ALL
SELECT 135 AS gap_no, 1483134600 AS left_time, 1483196400 AS right_time
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
