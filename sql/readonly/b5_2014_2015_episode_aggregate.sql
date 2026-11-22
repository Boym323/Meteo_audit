-- READ-ONLY SQL; bounded to frozen 65-gap cohort.
WITH gaps AS (
SELECT 1 AS gap_id,2014 AS year_utc,1389122400 AS left_time,1389131100 AS right_time
UNION ALL
SELECT 2 AS gap_id,2014 AS year_utc,1389261600 AS left_time,1389278400 AS right_time
UNION ALL
SELECT 3 AS gap_id,2014 AS year_utc,1389278400 AS left_time,1389291600 AS right_time
UNION ALL
SELECT 4 AS gap_id,2014 AS year_utc,1389351300 AS left_time,1389381900 AS right_time
UNION ALL
SELECT 5 AS gap_id,2014 AS year_utc,1390346400 AS left_time,1390353000 AS right_time
UNION ALL
SELECT 6 AS gap_id,2014 AS year_utc,1390353000 AS left_time,1390359000 AS right_time
UNION ALL
SELECT 7 AS gap_id,2014 AS year_utc,1390435500 AS left_time,1390441500 AS right_time
UNION ALL
SELECT 8 AS gap_id,2014 AS year_utc,1390523400 AS left_time,1390527000 AS right_time
UNION ALL
SELECT 9 AS gap_id,2014 AS year_utc,1394735100 AS left_time,1394765700 AS right_time
UNION ALL
SELECT 10 AS gap_id,2014 AS year_utc,1396144500 AS left_time,1396148400 AS right_time
UNION ALL
SELECT 11 AS gap_id,2014 AS year_utc,1397281500 AS left_time,1397314800 AS right_time
UNION ALL
SELECT 12 AS gap_id,2014 AS year_utc,1398266100 AS left_time,1398292800 AS right_time
UNION ALL
SELECT 13 AS gap_id,2014 AS year_utc,1401610800 AS left_time,1401642000 AS right_time
UNION ALL
SELECT 14 AS gap_id,2014 AS year_utc,1401643800 AS left_time,1401666600 AS right_time
UNION ALL
SELECT 15 AS gap_id,2014 AS year_utc,1401666600 AS left_time,1401674700 AS right_time
UNION ALL
SELECT 16 AS gap_id,2014 AS year_utc,1401884400 AS left_time,1401906600 AS right_time
UNION ALL
SELECT 17 AS gap_id,2014 AS year_utc,1401906600 AS left_time,1401915600 AS right_time
UNION ALL
SELECT 18 AS gap_id,2014 AS year_utc,1402757400 AS left_time,1402800000 AS right_time
UNION ALL
SELECT 19 AS gap_id,2014 AS year_utc,1402939800 AS left_time,1403012400 AS right_time
UNION ALL
SELECT 20 AS gap_id,2014 AS year_utc,1405856700 AS left_time,1405862700 AS right_time
UNION ALL
SELECT 21 AS gap_id,2014 AS year_utc,1405977300 AS left_time,1406001900 AS right_time
UNION ALL
SELECT 22 AS gap_id,2014 AS year_utc,1406014500 AS left_time,1406018100 AS right_time
UNION ALL
SELECT 23 AS gap_id,2014 AS year_utc,1406047800 AS left_time,1406052600 AS right_time
UNION ALL
SELECT 24 AS gap_id,2014 AS year_utc,1406060400 AS left_time,1406068200 AS right_time
UNION ALL
SELECT 25 AS gap_id,2014 AS year_utc,1406069700 AS left_time,1406073900 AS right_time
UNION ALL
SELECT 26 AS gap_id,2014 AS year_utc,1406108400 AS left_time,1406113500 AS right_time
UNION ALL
SELECT 27 AS gap_id,2014 AS year_utc,1406113800 AS left_time,1406126100 AS right_time
UNION ALL
SELECT 28 AS gap_id,2014 AS year_utc,1406126700 AS left_time,1406130900 AS right_time
UNION ALL
SELECT 29 AS gap_id,2014 AS year_utc,1406136900 AS left_time,1406140800 AS right_time
UNION ALL
SELECT 30 AS gap_id,2014 AS year_utc,1406231700 AS left_time,1406237100 AS right_time
UNION ALL
SELECT 31 AS gap_id,2014 AS year_utc,1406237400 AS left_time,1406313000 AS right_time
UNION ALL
SELECT 32 AS gap_id,2014 AS year_utc,1406363400 AS left_time,1406396700 AS right_time
UNION ALL
SELECT 33 AS gap_id,2014 AS year_utc,1406442000 AS left_time,1406445900 AS right_time
UNION ALL
SELECT 34 AS gap_id,2014 AS year_utc,1407588300 AS left_time,1407597300 AS right_time
UNION ALL
SELECT 35 AS gap_id,2014 AS year_utc,1410894600 AS left_time,1410898500 AS right_time
UNION ALL
SELECT 36 AS gap_id,2014 AS year_utc,1410900900 AS left_time,1410937800 AS right_time
UNION ALL
SELECT 37 AS gap_id,2015 AS year_utc,1422621600 AS left_time,1422627000 AS right_time
UNION ALL
SELECT 38 AS gap_id,2015 AS year_utc,1423554600 AS left_time,1423559700 AS right_time
UNION ALL
SELECT 39 AS gap_id,2015 AS year_utc,1428317700 AS left_time,1428325200 AS right_time
UNION ALL
SELECT 40 AS gap_id,2015 AS year_utc,1428325800 AS left_time,1428332100 AS right_time
UNION ALL
SELECT 41 AS gap_id,2015 AS year_utc,1428339600 AS left_time,1428344700 AS right_time
UNION ALL
SELECT 42 AS gap_id,2015 AS year_utc,1428345000 AS left_time,1428348600 AS right_time
UNION ALL
SELECT 43 AS gap_id,2015 AS year_utc,1428349800 AS left_time,1428356100 AS right_time
UNION ALL
SELECT 44 AS gap_id,2015 AS year_utc,1428364200 AS left_time,1428369900 AS right_time
UNION ALL
SELECT 45 AS gap_id,2015 AS year_utc,1428373800 AS left_time,1428384900 AS right_time
UNION ALL
SELECT 46 AS gap_id,2015 AS year_utc,1428389400 AS left_time,1428414000 AS right_time
UNION ALL
SELECT 47 AS gap_id,2015 AS year_utc,1428586500 AS left_time,1428592500 AS right_time
UNION ALL
SELECT 48 AS gap_id,2015 AS year_utc,1428594000 AS left_time,1428602700 AS right_time
UNION ALL
SELECT 49 AS gap_id,2015 AS year_utc,1429112400 AS left_time,1429125000 AS right_time
UNION ALL
SELECT 50 AS gap_id,2015 AS year_utc,1429187400 AS left_time,1429199700 AS right_time
UNION ALL
SELECT 51 AS gap_id,2015 AS year_utc,1432824300 AS left_time,1432830600 AS right_time
UNION ALL
SELECT 52 AS gap_id,2015 AS year_utc,1433324100 AS left_time,1433336400 AS right_time
UNION ALL
SELECT 53 AS gap_id,2015 AS year_utc,1436270400 AS left_time,1436295000 AS right_time
UNION ALL
SELECT 54 AS gap_id,2015 AS year_utc,1437067500 AS left_time,1437079800 AS right_time
UNION ALL
SELECT 55 AS gap_id,2015 AS year_utc,1437126600 AS left_time,1437139200 AS right_time
UNION ALL
SELECT 56 AS gap_id,2015 AS year_utc,1438527900 AS left_time,1438536300 AS right_time
UNION ALL
SELECT 57 AS gap_id,2015 AS year_utc,1438707900 AS left_time,1438711800 AS right_time
UNION ALL
SELECT 58 AS gap_id,2015 AS year_utc,1438749600 AS left_time,1438753800 AS right_time
UNION ALL
SELECT 59 AS gap_id,2015 AS year_utc,1438759500 AS left_time,1438763400 AS right_time
UNION ALL
SELECT 60 AS gap_id,2015 AS year_utc,1438803900 AS left_time,1438865700 AS right_time
UNION ALL
SELECT 61 AS gap_id,2015 AS year_utc,1440759900 AS left_time,1440763800 AS right_time
UNION ALL
SELECT 62 AS gap_id,2015 AS year_utc,1443606000 AS left_time,1443609600 AS right_time
UNION ALL
SELECT 63 AS gap_id,2015 AS year_utc,1447841400 AS left_time,1447845900 AS right_time
UNION ALL
SELECT 64 AS gap_id,2015 AS year_utc,1450864200 AS left_time,1450867800 AS right_time
UNION ALL
SELECT 65 AS gap_id,2015 AS year_utc,1451047800 AS left_time,1451085000 AS right_time
)
SELECT g.gap_id,
       g.year_utc,
       COUNT(*) AS paired_rows,
       SUM(a.`dateTime` % 300 <> 0) AS off_300s_grid,
       COUNT(DISTINCT CONCAT(a.`usUnits`,"/",a.`interval`)) AS old_unit_interval_codes,
       COUNT(DISTINCT CONCAT(w.`usUnits`,"/",w.`interval`)) AS wh_unit_interval_codes,
       COUNT(DISTINCT CONCAT(e.`usUnits`,"/",e.`interval`)) AS euold_unit_interval_codes,
       SUM(e.`dateTime` IS NOT NULL) AS euold_exact_rows,
       SUM(e.`outTemp` IS NOT NULL) AS euold_outTemp_nonnull,
       MIN(l.`outTemp`) AS left_reconstruction_outTemp,
       MAX(r.`outTemp`) AS right_reconstruction_outTemp,
       COUNT(DISTINCT ref.`observed_at_utc`) AS exact_luhamet_pairs,
       SUM(ref.`temperature_c` IS NOT NULL) AS luhamet_temp_nonnull,
       SUM(ch.`target_time` IS NOT NULL) AS any_outTemp_change_event,
       SUM(a.`outTemp` IS NOT NULL) AS old_outTemp_nonnull,
       SUM(w.`outTemp` IS NOT NULL) AS wh_outTemp_nonnull,
       SUM(a.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL AND a.`outTemp`=w.`outTemp`) AS outTemp_paired_equal,
       SUM(a.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL AND a.`outTemp`<>w.`outTemp`) AS outTemp_paired_conflict,
       SUM(a.`outHumidity` IS NOT NULL) AS old_outHumidity_nonnull,
       SUM(w.`outHumidity` IS NOT NULL) AS wh_outHumidity_nonnull,
       SUM(a.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL AND a.`outHumidity`=w.`outHumidity`) AS outHumidity_paired_equal,
       SUM(a.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL AND a.`outHumidity`<>w.`outHumidity`) AS outHumidity_paired_conflict,
       SUM(a.`rain` IS NOT NULL) AS old_rain_nonnull,
       SUM(w.`rain` IS NOT NULL) AS wh_rain_nonnull,
       SUM(a.`rain` IS NOT NULL AND w.`rain` IS NOT NULL AND a.`rain`=w.`rain`) AS rain_paired_equal,
       SUM(a.`rain` IS NOT NULL AND w.`rain` IS NOT NULL AND a.`rain`<>w.`rain`) AS rain_paired_conflict,
       SUM(a.`rainRate` IS NOT NULL) AS old_rainRate_nonnull,
       SUM(w.`rainRate` IS NOT NULL) AS wh_rainRate_nonnull,
       SUM(a.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL AND a.`rainRate`=w.`rainRate`) AS rainRate_paired_equal,
       SUM(a.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL AND a.`rainRate`<>w.`rainRate`) AS rainRate_paired_conflict,
       SUM(a.`windSpeed` IS NOT NULL) AS old_windSpeed_nonnull,
       SUM(w.`windSpeed` IS NOT NULL) AS wh_windSpeed_nonnull,
       SUM(a.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL AND a.`windSpeed`=w.`windSpeed`) AS windSpeed_paired_equal,
       SUM(a.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL AND a.`windSpeed`<>w.`windSpeed`) AS windSpeed_paired_conflict,
       SUM(a.`windGust` IS NOT NULL) AS old_windGust_nonnull,
       SUM(w.`windGust` IS NOT NULL) AS wh_windGust_nonnull,
       SUM(a.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL AND a.`windGust`=w.`windGust`) AS windGust_paired_equal,
       SUM(a.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL AND a.`windGust`<>w.`windGust`) AS windGust_paired_conflict,
       SUM(a.`windDir` IS NOT NULL) AS old_windDir_nonnull,
       SUM(w.`windDir` IS NOT NULL) AS wh_windDir_nonnull,
       SUM(a.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL AND a.`windDir`=w.`windDir`) AS windDir_paired_equal,
       SUM(a.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL AND a.`windDir`<>w.`windDir`) AS windDir_paired_conflict,
       SUM(a.`pressure` IS NOT NULL) AS old_pressure_nonnull,
       SUM(w.`pressure` IS NOT NULL) AS wh_pressure_nonnull,
       SUM(a.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL AND a.`pressure`=w.`pressure`) AS pressure_paired_equal,
       SUM(a.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL AND a.`pressure`<>w.`pressure`) AS pressure_paired_conflict,
       SUM(a.`barometer` IS NOT NULL) AS old_barometer_nonnull,
       SUM(w.`barometer` IS NOT NULL) AS wh_barometer_nonnull,
       SUM(a.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL AND a.`barometer`=w.`barometer`) AS barometer_paired_equal,
       SUM(a.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL AND a.`barometer`<>w.`barometer`) AS barometer_paired_conflict,
       SUM(a.`altimeter` IS NOT NULL) AS old_altimeter_nonnull,
       SUM(w.`altimeter` IS NOT NULL) AS wh_altimeter_nonnull,
       SUM(a.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL AND a.`altimeter`=w.`altimeter`) AS altimeter_paired_equal,
       SUM(a.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL AND a.`altimeter`<>w.`altimeter`) AS altimeter_paired_conflict,
       SUM(a.`outTemp`=0) AS old_outTemp_zero,
       SUM(w.`outTemp`=0) AS wh_outTemp_zero,
       SUM(e.`outTemp`=0) AS euold_outTemp_zero,
       MIN(a.`outTemp`) AS old_outTemp_min,
       MAX(a.`outTemp`) AS old_outTemp_max,
       MIN(w.`outTemp`) AS wh_outTemp_min,
       MAX(w.`outTemp`) AS wh_outTemp_max,
       COUNT(DISTINCT a.`outTemp`) AS old_outTemp_distinct,
       COUNT(DISTINCT w.`outTemp`) AS wh_outTemp_distinct,
       AVG(ABS(w.`outTemp`-ref.`temperature_c`)) AS wh_outTemp_LuhaMet_MAE,
       MAX(ABS(w.`outTemp`-ref.`temperature_c`)) AS wh_outTemp_LuhaMet_max_abs
FROM gaps g
JOIN `old_weewx`.`archive` a ON a.`dateTime`>g.left_time AND a.`dateTime`<g.right_time
JOIN `weewx_WH1080`.`archive` w ON w.`dateTime`=a.`dateTime`
LEFT JOIN `pocasi-loucka.eu_old`.`archive` e ON e.`dateTime`=a.`dateTime`
LEFT JOIN `loucka_reconstruction`.`archive` l ON l.`dateTime`=g.left_time
LEFT JOIN `loucka_reconstruction`.`archive` r ON r.`dateTime`=g.right_time
LEFT JOIN `loucka_reconstruction`.`reference_observations` ref ON ref.`observed_at_utc`=a.`dateTime` AND ref.`station_id`='luhamet_sehradice'
LEFT JOIN (SELECT DISTINCT `target_time` FROM `loucka_reconstruction`.`reconstruction_changes` WHERE `variable`='outTemp') ch ON ch.`target_time`=a.`dateTime`
WHERE (a.`dateTime`>1389122400 AND a.`dateTime`<1389131100) OR (a.`dateTime`>1389261600 AND a.`dateTime`<1389278400) OR (a.`dateTime`>1389278400 AND a.`dateTime`<1389291600) OR (a.`dateTime`>1389351300 AND a.`dateTime`<1389381900) OR (a.`dateTime`>1390346400 AND a.`dateTime`<1390353000) OR (a.`dateTime`>1390353000 AND a.`dateTime`<1390359000) OR (a.`dateTime`>1390435500 AND a.`dateTime`<1390441500) OR (a.`dateTime`>1390523400 AND a.`dateTime`<1390527000) OR (a.`dateTime`>1394735100 AND a.`dateTime`<1394765700) OR (a.`dateTime`>1396144500 AND a.`dateTime`<1396148400) OR (a.`dateTime`>1397281500 AND a.`dateTime`<1397314800) OR (a.`dateTime`>1398266100 AND a.`dateTime`<1398292800) OR (a.`dateTime`>1401610800 AND a.`dateTime`<1401642000) OR (a.`dateTime`>1401643800 AND a.`dateTime`<1401666600) OR (a.`dateTime`>1401666600 AND a.`dateTime`<1401674700) OR (a.`dateTime`>1401884400 AND a.`dateTime`<1401906600) OR (a.`dateTime`>1401906600 AND a.`dateTime`<1401915600) OR (a.`dateTime`>1402757400 AND a.`dateTime`<1402800000) OR (a.`dateTime`>1402939800 AND a.`dateTime`<1403012400) OR (a.`dateTime`>1405856700 AND a.`dateTime`<1405862700) OR (a.`dateTime`>1405977300 AND a.`dateTime`<1406001900) OR (a.`dateTime`>1406014500 AND a.`dateTime`<1406018100) OR (a.`dateTime`>1406047800 AND a.`dateTime`<1406052600) OR (a.`dateTime`>1406060400 AND a.`dateTime`<1406068200) OR (a.`dateTime`>1406069700 AND a.`dateTime`<1406073900) OR (a.`dateTime`>1406108400 AND a.`dateTime`<1406113500) OR (a.`dateTime`>1406113800 AND a.`dateTime`<1406126100) OR (a.`dateTime`>1406126700 AND a.`dateTime`<1406130900) OR (a.`dateTime`>1406136900 AND a.`dateTime`<1406140800) OR (a.`dateTime`>1406231700 AND a.`dateTime`<1406237100) OR (a.`dateTime`>1406237400 AND a.`dateTime`<1406313000) OR (a.`dateTime`>1406363400 AND a.`dateTime`<1406396700) OR (a.`dateTime`>1406442000 AND a.`dateTime`<1406445900) OR (a.`dateTime`>1407588300 AND a.`dateTime`<1407597300) OR (a.`dateTime`>1410894600 AND a.`dateTime`<1410898500) OR (a.`dateTime`>1410900900 AND a.`dateTime`<1410937800) OR (a.`dateTime`>1422621600 AND a.`dateTime`<1422627000) OR (a.`dateTime`>1423554600 AND a.`dateTime`<1423559700) OR (a.`dateTime`>1428317700 AND a.`dateTime`<1428325200) OR (a.`dateTime`>1428325800 AND a.`dateTime`<1428332100) OR (a.`dateTime`>1428339600 AND a.`dateTime`<1428344700) OR (a.`dateTime`>1428345000 AND a.`dateTime`<1428348600) OR (a.`dateTime`>1428349800 AND a.`dateTime`<1428356100) OR (a.`dateTime`>1428364200 AND a.`dateTime`<1428369900) OR (a.`dateTime`>1428373800 AND a.`dateTime`<1428384900) OR (a.`dateTime`>1428389400 AND a.`dateTime`<1428414000) OR (a.`dateTime`>1428586500 AND a.`dateTime`<1428592500) OR (a.`dateTime`>1428594000 AND a.`dateTime`<1428602700) OR (a.`dateTime`>1429112400 AND a.`dateTime`<1429125000) OR (a.`dateTime`>1429187400 AND a.`dateTime`<1429199700) OR (a.`dateTime`>1432824300 AND a.`dateTime`<1432830600) OR (a.`dateTime`>1433324100 AND a.`dateTime`<1433336400) OR (a.`dateTime`>1436270400 AND a.`dateTime`<1436295000) OR (a.`dateTime`>1437067500 AND a.`dateTime`<1437079800) OR (a.`dateTime`>1437126600 AND a.`dateTime`<1437139200) OR (a.`dateTime`>1438527900 AND a.`dateTime`<1438536300) OR (a.`dateTime`>1438707900 AND a.`dateTime`<1438711800) OR (a.`dateTime`>1438749600 AND a.`dateTime`<1438753800) OR (a.`dateTime`>1438759500 AND a.`dateTime`<1438763400) OR (a.`dateTime`>1438803900 AND a.`dateTime`<1438865700) OR (a.`dateTime`>1440759900 AND a.`dateTime`<1440763800) OR (a.`dateTime`>1443606000 AND a.`dateTime`<1443609600) OR (a.`dateTime`>1447841400 AND a.`dateTime`<1447845900) OR (a.`dateTime`>1450864200 AND a.`dateTime`<1450867800) OR (a.`dateTime`>1451047800 AND a.`dateTime`<1451085000)
GROUP BY g.gap_id,g.year_utc
ORDER BY g.year_utc,g.gap_id;
