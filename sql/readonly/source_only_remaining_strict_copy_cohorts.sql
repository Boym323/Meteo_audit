-- READ ONLY: residual exact-copy, on-grid, interval=5/usUnits=17, all-five
-- primary-value-equal source-only rows in the UTC years not yet row-screened.
SELECT a.dateTime ts,CASE WHEN a.dateTime<1388534400 THEN 2013 WHEN a.dateTime<1483228800 THEN 2016 ELSE 2020 END utc_year,
 a.usUnits old_units,a.`interval` old_interval,a.outTemp old_temp,a.outHumidity old_rh,
 a.rain old_rain,a.rainRate old_rainRate,a.windSpeed old_wind,
 b.usUnits wh_units,b.`interval` wh_interval,b.outTemp wh_temp,b.outHumidity wh_rh,
 b.rain wh_rain,b.rainRate wh_rainRate,b.windSpeed wh_wind,
 p.dateTime IS NOT NULL has_pocasi_main,g.dateTime IS NOT NULL has_gw1000,e.dateTime IS NOT NULL has_pocasi_old,
 (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes x WHERE x.target_time=a.dateTime) change_events
FROM old_weewx.archive a
JOIN weewx_WH1080.archive b ON b.dateTime=a.dateTime
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive e ON e.dateTime=a.dateTime
WHERE ((a.dateTime>=1356998400 AND a.dateTime<1388534400)
    OR (a.dateTime>=1451606400 AND a.dateTime<1483228800)
    OR (a.dateTime>=1577836800 AND a.dateTime<1609459200))
 AND a.`interval`=5 AND b.`interval`=5 AND a.usUnits=17 AND b.usUnits=17 AND MOD(a.dateTime,300)=0
 AND r.dateTime IS NULL
 AND a.outTemp<=>b.outTemp AND a.outHumidity<=>b.outHumidity AND a.rain<=>b.rain
 AND a.rainRate<=>b.rainRate AND a.windSpeed<=>b.windSpeed
ORDER BY a.dateTime;

-- Source context for those target timestamps, bounded to ±10 minutes.
WITH cohort AS (
 SELECT a.dateTime ts
 FROM old_weewx.archive a JOIN weewx_WH1080.archive b ON b.dateTime=a.dateTime
 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime
 WHERE ((a.dateTime>=1356998400 AND a.dateTime<1388534400)
    OR (a.dateTime>=1451606400 AND a.dateTime<1483228800)
    OR (a.dateTime>=1577836800 AND a.dateTime<1609459200))
  AND a.`interval`=5 AND b.`interval`=5 AND a.usUnits=17 AND b.usUnits=17 AND MOD(a.dateTime,300)=0
  AND r.dateTime IS NULL AND a.outTemp<=>b.outTemp AND a.outHumidity<=>b.outHumidity
  AND a.rain<=>b.rain AND a.rainRate<=>b.rainRate AND a.windSpeed<=>b.windSpeed
)
SELECT c.ts target_time,'old_weewx' source_database,s.dateTime neighbor_time,s.outTemp,s.outHumidity,s.rain,s.rainRate,s.windSpeed
FROM cohort c JOIN old_weewx.archive s ON s.dateTime BETWEEN c.ts-600 AND c.ts+600
UNION ALL
SELECT c.ts,'weewx_WH1080',s.dateTime,s.outTemp,s.outHumidity,s.rain,s.rainRate,s.windSpeed
FROM cohort c JOIN weewx_WH1080.archive s ON s.dateTime BETWEEN c.ts-600 AND c.ts+600
ORDER BY target_time,source_database,neighbor_time;
