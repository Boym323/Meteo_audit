-- READ-ONLY cross-copy quality screen; source agreement is not provenance.
WITH targets AS (SELECT 1548076500 AS left_time, 1548077100 AS right_time, '2019:1548076500:1548077100' AS gap_id, 600 AS gap_seconds, 'lt_1h' AS gap_band UNION ALL SELECT 1556184300, 1556185500, '2019:1556184300:1556185500', 1200, 'lt_1h' UNION ALL SELECT 1557825600, 1557826200, '2019:1557825600:1557826200', 600, 'lt_1h' UNION ALL SELECT 1557828300, 1557828900, '2019:1557828300:1557828900', 600, 'lt_1h' UNION ALL SELECT 1557840000, 1557840600, '2019:1557840000:1557840600', 600, 'lt_1h' UNION ALL SELECT 1558259700, 1558341000, '2019:1558259700:1558341000', 81300, '1h_to_lt_1d' UNION ALL SELECT 1559203200, 1559208900, '2019:1559203200:1559208900', 5700, '1h_to_lt_1d' UNION ALL SELECT 1559209500, 1559213700, '2019:1559209500:1559213700', 4200, '1h_to_lt_1d' UNION ALL SELECT 1559214300, 1559216400, '2019:1559214300:1559216400', 2100, 'lt_1h' UNION ALL SELECT 1559217600, 1559218500, '2019:1559217600:1559218500', 900, 'lt_1h' UNION ALL SELECT 1559219100, 1559223300, '2019:1559219100:1559223300', 4200, '1h_to_lt_1d' UNION ALL SELECT 1559223900, 1559224800, '2019:1559223900:1559224800', 900, 'lt_1h' UNION ALL SELECT 1559239500, 1559240100, '2019:1559239500:1559240100', 600, 'lt_1h' UNION ALL SELECT 1559293500, 1559294100, '2019:1559293500:1559294100', 600, 'lt_1h' UNION ALL SELECT 1559295300, 1559295900, '2019:1559295300:1559295900', 600, 'lt_1h' UNION ALL SELECT 1559295900, 1559296500, '2019:1559295900:1559296500', 600, 'lt_1h' UNION ALL SELECT 1559296800, 1559297400, '2019:1559296800:1559297400', 600, 'lt_1h' UNION ALL SELECT 1559297400, 1559298000, '2019:1559297400:1559298000', 600, 'lt_1h' UNION ALL SELECT 1559298600, 1559299500, '2019:1559298600:1559299500', 900, 'lt_1h' UNION ALL SELECT 1559299500, 1559300100, '2019:1559299500:1559300100', 600, 'lt_1h' UNION ALL SELECT 1559300100, 1559300700, '2019:1559300100:1559300700', 600, 'lt_1h' UNION ALL SELECT 1559301300, 1559301900, '2019:1559301300:1559301900', 600, 'lt_1h' UNION ALL SELECT 1559733900, 1559734500, '2019:1559733900:1559734500', 600, 'lt_1h' UNION ALL SELECT 1559847000, 1559847600, '2019:1559847000:1559847600', 600, 'lt_1h' UNION ALL SELECT 1560932700, 1560933300, '2019:1560932700:1560933300', 600, 'lt_1h' UNION ALL SELECT 1561405800, 1561408500, '2019:1561405800:1561408500', 2700, 'lt_1h' UNION ALL SELECT 1561907400, 1561908000, '2019:1561907400:1561908000', 600, 'lt_1h' UNION ALL SELECT 1562587200, 1562587800, '2019:1562587200:1562587800', 600, 'lt_1h' UNION ALL SELECT 1563292200, 1563292800, '2019:1563292200:1563292800', 600, 'lt_1h' UNION ALL SELECT 1564775700, 1564776300, '2019:1564775700:1564776300', 600, 'lt_1h' UNION ALL SELECT 1568361900, 1568362500, '2019:1568361900:1568362500', 600, 'lt_1h' UNION ALL SELECT 1572134100, 1572138000, '2019:1572134100:1572138000', 3900, '1h_to_lt_1d'), wh_hits AS (
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
