-- READ ONLY. UTC epoch window for 2017; exact source-only archive rows with
-- 5-minute grid, units=17 and exact agreement on all five primary fields.
-- Report source context and all-archive target presence; do not infer lineage.
WITH cohort AS (
 SELECT a.dateTime ts
 FROM old_weewx.archive a
 JOIN weewx_WH1080.archive b ON b.dateTime=a.dateTime
 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime
 WHERE a.dateTime>=1483228800 AND a.dateTime<1514764800
   AND a.`interval`=5 AND b.`interval`=5 AND a.usUnits=17 AND b.usUnits=17
   AND MOD(a.dateTime,300)=0 AND r.dateTime IS NULL
   AND a.outTemp IS NOT NULL AND a.rain IS NOT NULL
   AND a.rainRate IS NOT NULL AND a.windSpeed IS NOT NULL
   AND a.outTemp<=>b.outTemp AND a.outHumidity<=>b.outHumidity
   AND a.rain<=>b.rain AND a.rainRate<=>b.rainRate AND a.windSpeed<=>b.windSpeed
)
SELECT c.ts,
 a.usUnits old_usUnits,a.`interval` old_interval,a.outTemp old_outTemp,a.outHumidity old_outHumidity,
 a.rain old_rain,a.rainRate old_rainRate,a.windSpeed old_windSpeed,
 b.usUnits wh_usUnits,b.`interval` wh_interval,b.outTemp wh_outTemp,b.outHumidity wh_outHumidity,
 b.rain wh_rain,b.rainRate wh_rainRate,b.windSpeed wh_windSpeed,
 p.dateTime IS NOT NULL has_pocasi_main,g.dateTime IS NOT NULL has_gw1000,
 e.dateTime IS NOT NULL has_pocasi_old,
 (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes x WHERE x.target_time=c.ts) change_events
FROM cohort c
JOIN old_weewx.archive a ON a.dateTime=c.ts
JOIN weewx_WH1080.archive b ON b.dateTime=c.ts
LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=c.ts
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=c.ts
LEFT JOIN `pocasi-loucka.eu_old`.archive e ON e.dateTime=c.ts
ORDER BY c.ts;

-- Neighbor context in each source copy; rows are independently selected, not
-- assumed to be authentic or independent observations.
WITH cohort AS (
 SELECT a.dateTime ts FROM old_weewx.archive a
 JOIN weewx_WH1080.archive b ON b.dateTime=a.dateTime
 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime
 WHERE a.dateTime>=1483228800 AND a.dateTime<1514764800
   AND a.`interval`=5 AND b.`interval`=5 AND a.usUnits=17 AND b.usUnits=17
   AND MOD(a.dateTime,300)=0 AND r.dateTime IS NULL
   AND a.outTemp IS NOT NULL AND a.rain IS NOT NULL
   AND a.rainRate IS NOT NULL AND a.windSpeed IS NOT NULL
   AND a.outTemp<=>b.outTemp AND a.outHumidity<=>b.outHumidity
   AND a.rain<=>b.rain AND a.rainRate<=>b.rainRate AND a.windSpeed<=>b.windSpeed
)
SELECT c.ts target_time,'old_weewx' source_database,s.dateTime neighbor_time,
 s.usUnits,s.`interval`,s.outTemp,s.outHumidity,s.rain,s.rainRate,s.windSpeed
FROM cohort c JOIN old_weewx.archive s ON s.dateTime BETWEEN c.ts-600 AND c.ts+600
UNION ALL
SELECT c.ts,'weewx_WH1080',s.dateTime,s.usUnits,s.`interval`,s.outTemp,s.outHumidity,s.rain,s.rainRate,s.windSpeed
FROM cohort c JOIN weewx_WH1080.archive s ON s.dateTime BETWEEN c.ts-600 AND c.ts+600
ORDER BY target_time,source_database,neighbor_time;
