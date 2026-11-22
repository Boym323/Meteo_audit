-- READ-ONLY bounded 2014-2015 B5 nonzero source-temperature candidates.
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
SELECT g.gap_id,g.year_utc,g.left_time,g.right_time,a.dateTime,a.usUnits,a.interval,a.outTemp AS source_outTemp,w.outTemp AS wh_outTemp,e.outTemp AS euold_outTemp,e.dateTime AS euold_row_ts,
       a.outHumidity AS old_RH,w.outHumidity AS wh_RH,a.rain AS old_rain,w.rain AS wh_rain,
       a.windSpeed AS old_windSpeed,w.windSpeed AS wh_windSpeed,
       l.outTemp AS left_target_outTemp,r.outTemp AS right_target_outTemp
FROM gaps g
JOIN `old_weewx`.`archive` a ON a.dateTime>g.left_time AND a.dateTime<g.right_time
JOIN `weewx_WH1080`.`archive` w ON w.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.`archive` e ON e.dateTime=a.dateTime
LEFT JOIN `loucka_reconstruction`.`archive` l ON l.dateTime=g.left_time
LEFT JOIN `loucka_reconstruction`.`archive` r ON r.dateTime=g.right_time
WHERE a.outTemp IS NOT NULL AND a.outTemp<>0
ORDER BY g.year_utc,g.gap_id,a.dateTime;
