-- READ-ONLY cross-copy quality screen; source agreement is not provenance.
WITH targets AS (SELECT 1482866700 AS left_time, 1482867300 AS right_time, '2016:1482866700:1482867300' AS gap_id, 600 AS gap_seconds, 'lt_1h' AS gap_band UNION ALL SELECT 1482867600, 1482869700, '2016:1482867600:1482869700', 2100, 'lt_1h' UNION ALL SELECT 1482871200, 1482871800, '2016:1482871200:1482871800', 600, 'lt_1h' UNION ALL SELECT 1482872100, 1482873300, '2016:1482872100:1482873300', 1200, 'lt_1h' UNION ALL SELECT 1483117200, 1483118100, '2016:1483117200:1483118100', 900, 'lt_1h' UNION ALL SELECT 1483127700, 1483134000, '2016:1483127700:1483134000', 6300, '1h_to_lt_1d' UNION ALL SELECT 1483134600, 1483196400, '2016:1483134600:1483196400', 61800, '1h_to_lt_1d' UNION ALL SELECT 1483208400, 1483210200, '2016:1483208400:1483210200', 1800, 'lt_1h' UNION ALL SELECT 1483212600, 1483213800, '2016:1483212600:1483213800', 1200, 'lt_1h'), wh_hits AS (
 SELECT t.gap_id,t.gap_band,t.left_time,t.right_time,a.dateTime ts,
        a.usUnits wh_units,a.`interval` wh_interval,a.outTemp wh_temp,a.outHumidity wh_rh,
        a.rain wh_rain,a.rainRate wh_rainRate,a.windSpeed wh_wind
 FROM targets t JOIN weewx_WH1080.archive a
   ON a.dateTime>t.left_time AND a.dateTime<t.right_time AND MOD(a.dateTime-t.left_time,300)=0
 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime
 WHERE r.dateTime IS NULL
)
SELECT CAST(SUBSTRING_INDEX(h.gap_id,':',1) AS UNSIGNED) utc_year,h.gap_band,
 CASE WHEN h.ts>=1514764800 AND h.ts<1522540800 THEN 'PROTECTED_Q1_2018_DIAGNOSTIC' ELSE 'NORMAL' END protection_scope,
 COUNT(*) wh1080_rows,SUM(o.dateTime IS NOT NULL) old_weewx_rows,
 SUM(o.dateTime IS NULL) old_weewx_missing,
 SUM(h.wh_units=17) wh_units17,SUM(h.wh_interval=5) wh_interval5,
 SUM(o.usUnits<=>h.wh_units) units_equal,SUM(o.`interval`<=>h.wh_interval) intervals_equal,
 SUM(o.outTemp<=>h.wh_temp) outTemp_equal,SUM(o.outTemp IS NOT NULL AND h.wh_temp IS NOT NULL) outTemp_both_present,
 SUM(o.outTemp IS NOT NULL AND h.wh_temp IS NOT NULL AND o.outTemp<>h.wh_temp) outTemp_conflict,
 SUM(h.wh_temp=0) wh_outTemp_zero,SUM(h.wh_temp IS NULL) wh_outTemp_null,
 SUM(o.outHumidity<=>h.wh_rh) outHumidity_equal,SUM(o.outHumidity IS NOT NULL AND h.wh_rh IS NOT NULL) outHumidity_both_present,
 SUM(o.outHumidity IS NOT NULL AND h.wh_rh IS NOT NULL AND o.outHumidity<>h.wh_rh) outHumidity_conflict,
 SUM(h.wh_rh IS NULL) wh_outHumidity_null,
 SUM(o.rain<=>h.wh_rain) rain_equal,SUM(o.rain IS NOT NULL AND h.wh_rain IS NOT NULL) rain_both_present,
 SUM(o.rain IS NOT NULL AND h.wh_rain IS NOT NULL AND o.rain<>h.wh_rain) rain_conflict,
 SUM(h.wh_rain IS NULL) wh_rain_null,
 SUM(o.rainRate<=>h.wh_rainRate) rainRate_equal,SUM(o.rainRate IS NOT NULL AND h.wh_rainRate IS NOT NULL) rainRate_both_present,
 SUM(o.rainRate IS NOT NULL AND h.wh_rainRate IS NOT NULL AND o.rainRate<>h.wh_rainRate) rainRate_conflict,
 SUM(h.wh_rainRate IS NULL) wh_rainRate_null,
 SUM(o.windSpeed<=>h.wh_wind) windSpeed_equal,SUM(o.windSpeed IS NOT NULL AND h.wh_wind IS NOT NULL) windSpeed_both_present,
 SUM(o.windSpeed IS NOT NULL AND h.wh_wind IS NOT NULL AND o.windSpeed<>h.wh_wind) windSpeed_conflict,
 SUM(h.wh_wind IS NULL) wh_windSpeed_null
FROM wh_hits h LEFT JOIN old_weewx.archive o ON o.dateTime=h.ts
GROUP BY utc_year,h.gap_band,protection_scope
