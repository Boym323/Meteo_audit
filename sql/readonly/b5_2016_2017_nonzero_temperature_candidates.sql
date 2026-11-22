-- READ-ONLY SELECT; bounded to existing gaps with old_weewx nonzero outTemp candidates.
WITH gaps AS (
SELECT 1 AS gap_id,2016 AS year_utc,1454890200 AS left_time,1454895000 AS right_time
UNION ALL
SELECT 2 AS gap_id,2016 AS year_utc,1456298400 AS left_time,1456305300 AS right_time
UNION ALL
SELECT 3 AS gap_id,2016 AS year_utc,1456311900 AS left_time,1456315500 AS right_time
UNION ALL
SELECT 4 AS gap_id,2016 AS year_utc,1456356900 AS left_time,1456394100 AS right_time
UNION ALL
SELECT 5 AS gap_id,2016 AS year_utc,1456841100 AS left_time,1456847400 AS right_time
UNION ALL
SELECT 6 AS gap_id,2016 AS year_utc,1456847400 AS left_time,1456854000 AS right_time
UNION ALL
SELECT 7 AS gap_id,2016 AS year_utc,1456857000 AS left_time,1456860600 AS right_time
UNION ALL
SELECT 8 AS gap_id,2016 AS year_utc,1456863900 AS left_time,1456867800 AS right_time
UNION ALL
SELECT 9 AS gap_id,2016 AS year_utc,1456884600 AS left_time,1456888200 AS right_time
UNION ALL
SELECT 10 AS gap_id,2016 AS year_utc,1456892400 AS left_time,1456917300 AS right_time
UNION ALL
SELECT 11 AS gap_id,2016 AS year_utc,1458241800 AS left_time,1458247500 AS right_time
UNION ALL
SELECT 12 AS gap_id,2016 AS year_utc,1458248700 AS left_time,1458324600 AS right_time
UNION ALL
SELECT 13 AS gap_id,2016 AS year_utc,1458344400 AS left_time,1458357000 AS right_time
UNION ALL
SELECT 14 AS gap_id,2016 AS year_utc,1464894300 AS left_time,1464898200 AS right_time
UNION ALL
SELECT 15 AS gap_id,2016 AS year_utc,1464898500 AS left_time,1464902100 AS right_time
UNION ALL
SELECT 16 AS gap_id,2016 AS year_utc,1465141800 AS left_time,1465148400 AS right_time
UNION ALL
SELECT 17 AS gap_id,2016 AS year_utc,1465148700 AS left_time,1465173300 AS right_time
UNION ALL
SELECT 18 AS gap_id,2016 AS year_utc,1465187100 AS left_time,1465199700 AS right_time
UNION ALL
SELECT 19 AS gap_id,2016 AS year_utc,1465200900 AS left_time,1465214400 AS right_time
UNION ALL
SELECT 20 AS gap_id,2016 AS year_utc,1465214700 AS left_time,1465226400 AS right_time
UNION ALL
SELECT 21 AS gap_id,2016 AS year_utc,1465231500 AS left_time,1465236600 AS right_time
UNION ALL
SELECT 22 AS gap_id,2016 AS year_utc,1465347300 AS left_time,1465353000 AS right_time
UNION ALL
SELECT 23 AS gap_id,2016 AS year_utc,1465357800 AS left_time,1465368600 AS right_time
UNION ALL
SELECT 24 AS gap_id,2016 AS year_utc,1465397700 AS left_time,1465402500 AS right_time
UNION ALL
SELECT 25 AS gap_id,2016 AS year_utc,1466842500 AS left_time,1466847000 AS right_time
UNION ALL
SELECT 26 AS gap_id,2016 AS year_utc,1466847000 AS left_time,1466851200 AS right_time
UNION ALL
SELECT 27 AS gap_id,2016 AS year_utc,1466851500 AS left_time,1466860800 AS right_time
UNION ALL
SELECT 28 AS gap_id,2016 AS year_utc,1467665400 AS left_time,1467669000 AS right_time
UNION ALL
SELECT 29 AS gap_id,2016 AS year_utc,1467669300 AS left_time,1467674100 AS right_time
UNION ALL
SELECT 30 AS gap_id,2016 AS year_utc,1467677100 AS left_time,1467687000 AS right_time
UNION ALL
SELECT 31 AS gap_id,2016 AS year_utc,1468297200 AS left_time,1468305000 AS right_time
UNION ALL
SELECT 32 AS gap_id,2016 AS year_utc,1468307100 AS left_time,1468315200 AS right_time
UNION ALL
SELECT 33 AS gap_id,2016 AS year_utc,1468428900 AS left_time,1468448100 AS right_time
UNION ALL
SELECT 34 AS gap_id,2016 AS year_utc,1468464000 AS left_time,1468468200 AS right_time
UNION ALL
SELECT 35 AS gap_id,2016 AS year_utc,1468512000 AS left_time,1468517700 AS right_time
UNION ALL
SELECT 36 AS gap_id,2016 AS year_utc,1468521600 AS left_time,1468525200 AS right_time
UNION ALL
SELECT 37 AS gap_id,2016 AS year_utc,1468525800 AS left_time,1468532700 AS right_time
UNION ALL
SELECT 38 AS gap_id,2016 AS year_utc,1468539600 AS left_time,1468556400 AS right_time
UNION ALL
SELECT 39 AS gap_id,2016 AS year_utc,1468568100 AS left_time,1468574400 AS right_time
UNION ALL
SELECT 40 AS gap_id,2016 AS year_utc,1469289300 AS left_time,1469302800 AS right_time
UNION ALL
SELECT 41 AS gap_id,2016 AS year_utc,1469334600 AS left_time,1469339400 AS right_time
UNION ALL
SELECT 42 AS gap_id,2016 AS year_utc,1469341500 AS left_time,1469345100 AS right_time
UNION ALL
SELECT 43 AS gap_id,2016 AS year_utc,1469596800 AS left_time,1469605200 AS right_time
UNION ALL
SELECT 44 AS gap_id,2016 AS year_utc,1469646000 AS left_time,1469669100 AS right_time
UNION ALL
SELECT 45 AS gap_id,2016 AS year_utc,1469673900 AS left_time,1469682000 AS right_time
UNION ALL
SELECT 46 AS gap_id,2016 AS year_utc,1469686800 AS left_time,1469690400 AS right_time
UNION ALL
SELECT 47 AS gap_id,2016 AS year_utc,1469908500 AS left_time,1469915700 AS right_time
UNION ALL
SELECT 48 AS gap_id,2016 AS year_utc,1469916300 AS left_time,1469965800 AS right_time
UNION ALL
SELECT 49 AS gap_id,2016 AS year_utc,1469979900 AS left_time,1469983500 AS right_time
UNION ALL
SELECT 50 AS gap_id,2016 AS year_utc,1469986200 AS left_time,1470048300 AS right_time
UNION ALL
SELECT 51 AS gap_id,2016 AS year_utc,1470223500 AS left_time,1470227100 AS right_time
UNION ALL
SELECT 52 AS gap_id,2016 AS year_utc,1470270600 AS left_time,1470275700 AS right_time
UNION ALL
SELECT 53 AS gap_id,2016 AS year_utc,1471570500 AS left_time,1471576500 AS right_time
UNION ALL
SELECT 54 AS gap_id,2016 AS year_utc,1471785900 AS left_time,1471792800 AS right_time
UNION ALL
SELECT 55 AS gap_id,2016 AS year_utc,1471832100 AS left_time,1471836900 AS right_time
UNION ALL
SELECT 56 AS gap_id,2016 AS year_utc,1471916700 AS left_time,1471920300 AS right_time
UNION ALL
SELECT 57 AS gap_id,2016 AS year_utc,1471922700 AS left_time,1471926300 AS right_time
UNION ALL
SELECT 58 AS gap_id,2016 AS year_utc,1472239800 AS left_time,1472245800 AS right_time
UNION ALL
SELECT 59 AS gap_id,2016 AS year_utc,1472447100 AS left_time,1472483700 AS right_time
UNION ALL
SELECT 60 AS gap_id,2016 AS year_utc,1472540100 AS left_time,1472578800 AS right_time
UNION ALL
SELECT 61 AS gap_id,2016 AS year_utc,1472902500 AS left_time,1472907300 AS right_time
UNION ALL
SELECT 62 AS gap_id,2016 AS year_utc,1473528600 AS left_time,1473602100 AS right_time
UNION ALL
SELECT 63 AS gap_id,2016 AS year_utc,1473602400 AS left_time,1473607800 AS right_time
UNION ALL
SELECT 64 AS gap_id,2016 AS year_utc,1474274400 AS left_time,1474281600 AS right_time
UNION ALL
SELECT 65 AS gap_id,2016 AS year_utc,1474619100 AS left_time,1474622700 AS right_time
UNION ALL
SELECT 66 AS gap_id,2017 AS year_utc,1490142000 AS left_time,1490146500 AS right_time
UNION ALL
SELECT 67 AS gap_id,2017 AS year_utc,1490157900 AS left_time,1490164200 AS right_time
UNION ALL
SELECT 68 AS gap_id,2017 AS year_utc,1490256000 AS left_time,1490260500 AS right_time
UNION ALL
SELECT 69 AS gap_id,2017 AS year_utc,1490295600 AS left_time,1490299200 AS right_time
UNION ALL
SELECT 70 AS gap_id,2017 AS year_utc,1490318700 AS left_time,1490322300 AS right_time
UNION ALL
SELECT 71 AS gap_id,2017 AS year_utc,1490323800 AS left_time,1490328900 AS right_time
UNION ALL
SELECT 72 AS gap_id,2017 AS year_utc,1494090900 AS left_time,1494095700 AS right_time
UNION ALL
SELECT 73 AS gap_id,2017 AS year_utc,1494102000 AS left_time,1494107100 AS right_time
UNION ALL
SELECT 74 AS gap_id,2017 AS year_utc,1494125700 AS left_time,1494142500 AS right_time
UNION ALL
SELECT 75 AS gap_id,2017 AS year_utc,1494143400 AS left_time,1494153600 AS right_time
UNION ALL
SELECT 76 AS gap_id,2017 AS year_utc,1494168300 AS left_time,1494171900 AS right_time
UNION ALL
SELECT 77 AS gap_id,2017 AS year_utc,1494178800 AS left_time,1494188400 AS right_time
UNION ALL
SELECT 78 AS gap_id,2017 AS year_utc,1494440400 AS left_time,1494444000 AS right_time
UNION ALL
SELECT 79 AS gap_id,2017 AS year_utc,1496470200 AS left_time,1496479500 AS right_time
UNION ALL
SELECT 80 AS gap_id,2017 AS year_utc,1496502000 AS left_time,1496512800 AS right_time
UNION ALL
SELECT 81 AS gap_id,2017 AS year_utc,1496515200 AS left_time,1496526000 AS right_time
UNION ALL
SELECT 82 AS gap_id,2017 AS year_utc,1496533800 AS left_time,1496542500 AS right_time
UNION ALL
SELECT 83 AS gap_id,2017 AS year_utc,1496550600 AS left_time,1496554200 AS right_time
UNION ALL
SELECT 84 AS gap_id,2017 AS year_utc,1496561400 AS left_time,1496567700 AS right_time
UNION ALL
SELECT 85 AS gap_id,2017 AS year_utc,1496571000 AS left_time,1496594400 AS right_time
UNION ALL
SELECT 86 AS gap_id,2017 AS year_utc,1496653200 AS left_time,1496658300 AS right_time
UNION ALL
SELECT 87 AS gap_id,2017 AS year_utc,1496658300 AS left_time,1496687100 AS right_time
UNION ALL
SELECT 88 AS gap_id,2017 AS year_utc,1497515700 AS left_time,1497519900 AS right_time
UNION ALL
SELECT 89 AS gap_id,2017 AS year_utc,1497519900 AS left_time,1497524100 AS right_time
UNION ALL
SELECT 90 AS gap_id,2017 AS year_utc,1497524400 AS left_time,1497540300 AS right_time
UNION ALL
SELECT 91 AS gap_id,2017 AS year_utc,1497540600 AS left_time,1497558300 AS right_time
UNION ALL
SELECT 92 AS gap_id,2017 AS year_utc,1502088000 AS left_time,1502093400 AS right_time
UNION ALL
SELECT 93 AS gap_id,2017 AS year_utc,1502107500 AS left_time,1502112300 AS right_time
UNION ALL
SELECT 94 AS gap_id,2017 AS year_utc,1502131200 AS left_time,1502137200 AS right_time
UNION ALL
SELECT 95 AS gap_id,2017 AS year_utc,1502147100 AS left_time,1502154900 AS right_time
UNION ALL
SELECT 96 AS gap_id,2017 AS year_utc,1502155800 AS left_time,1502163600 AS right_time
UNION ALL
SELECT 97 AS gap_id,2017 AS year_utc,1502165700 AS left_time,1502172000 AS right_time
UNION ALL
SELECT 98 AS gap_id,2017 AS year_utc,1502188800 AS left_time,1502195700 AS right_time
UNION ALL
SELECT 99 AS gap_id,2017 AS year_utc,1508388300 AS left_time,1508396400 AS right_time
UNION ALL
SELECT 100 AS gap_id,2017 AS year_utc,1508396700 AS left_time,1508400900 AS right_time
UNION ALL
SELECT 101 AS gap_id,2017 AS year_utc,1512300000 AS left_time,1512305100 AS right_time
UNION ALL
SELECT 102 AS gap_id,2017 AS year_utc,1512392400 AS left_time,1512417300 AS right_time
UNION ALL
SELECT 103 AS gap_id,2017 AS year_utc,1512452100 AS left_time,1512489300 AS right_time
UNION ALL
SELECT 104 AS gap_id,2017 AS year_utc,1512545700 AS left_time,1512555300 AS right_time
UNION ALL
SELECT 105 AS gap_id,2017 AS year_utc,1512558300 AS left_time,1512562500 AS right_time
UNION ALL
SELECT 106 AS gap_id,2017 AS year_utc,1512719100 AS left_time,1512768900 AS right_time
UNION ALL
SELECT 107 AS gap_id,2017 AS year_utc,1512810600 AS left_time,1512860100 AS right_time
UNION ALL
SELECT 108 AS gap_id,2017 AS year_utc,1512956100 AS left_time,1513005900 AS right_time
UNION ALL
SELECT 109 AS gap_id,2017 AS year_utc,1513626000 AS left_time,1513689600 AS right_time
)
SELECT g.gap_id,
       g.year_utc,
       g.left_time,
       g.right_time,
       a.dateTime,
       a.usUnits AS old_usUnits,
       a.interval AS old_interval,
       w.usUnits AS wh_usUnits,
       w.interval AS wh_interval,
       a.`outTemp` AS old_outTemp,
       w.`outTemp` AS wh_outTemp,
       a.`outHumidity` AS old_outHumidity,
       w.`outHumidity` AS wh_outHumidity,
       a.`rain` AS old_rain,
       w.`rain` AS wh_rain,
       a.`rainRate` AS old_rainRate,
       w.`rainRate` AS wh_rainRate,
       a.`windSpeed` AS old_windSpeed,
       w.`windSpeed` AS wh_windSpeed,
       a.`windGust` AS old_windGust,
       w.`windGust` AS wh_windGust,
       a.`windDir` AS old_windDir,
       w.`windDir` AS wh_windDir,
       a.`barometer` AS old_barometer,
       w.`barometer` AS wh_barometer,
       a.`pressure` AS old_pressure,
       w.`pressure` AS wh_pressure,
       a.`altimeter` AS old_altimeter,
       w.`altimeter` AS wh_altimeter,
       e.dateTime AS euold_dateTime,
       e.usUnits AS euold_usUnits,
       e.interval AS euold_interval,
       e.outTemp AS euold_outTemp,
       l.outTemp AS left_target_outTemp,
       r.outTemp AS right_target_outTemp,
       ref.temperature_c AS luhamet_temperature_c,
       ref.quality_status AS luhamet_quality_status,
       ch.event_count AS outTemp_event_count
FROM gaps g
JOIN `old_weewx`.`archive` a ON a.dateTime>g.left_time AND a.dateTime<g.right_time
JOIN `weewx_WH1080`.`archive` w ON w.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.`archive` e ON e.dateTime=a.dateTime
LEFT JOIN `loucka_reconstruction`.`archive` l ON l.dateTime=g.left_time
LEFT JOIN `loucka_reconstruction`.`archive` r ON r.dateTime=g.right_time
LEFT JOIN `loucka_reconstruction`.`reference_observations` ref ON ref.observed_at_utc=a.dateTime AND ref.station_id='luhamet_sehradice'
LEFT JOIN (SELECT target_time,COUNT(*) AS event_count FROM `loucka_reconstruction`.`reconstruction_changes` WHERE variable='outTemp' GROUP BY target_time) ch ON ch.target_time=a.dateTime
WHERE a.outTemp IS NOT NULL AND a.outTemp<>0
ORDER BY g.year_utc,g.gap_id,a.dateTime;
