-- READ-ONLY cross-copy quality screen; source agreement is not provenance.
WITH targets AS (SELECT 1513626000 AS left_time, 1513689600 AS right_time, '2017:1513626000:1513689600' AS gap_id, 63600 AS gap_seconds, '1h_to_lt_1d' AS gap_band UNION ALL SELECT 1514002800, 1514003400, '2017:1514002800:1514003400', 600, 'lt_1h' UNION ALL SELECT 1514007600, 1514008200, '2017:1514007600:1514008200', 600, 'lt_1h' UNION ALL SELECT 1514012400, 1514013000, '2017:1514012400:1514013000', 600, 'lt_1h' UNION ALL SELECT 1514017200, 1514017800, '2017:1514017200:1514017800', 600, 'lt_1h' UNION ALL SELECT 1514126700, 1514127300, '2017:1514126700:1514127300', 600, 'lt_1h' UNION ALL SELECT 1514320800, 1514322600, '2017:1514320800:1514322600', 1800, 'lt_1h' UNION ALL SELECT 1514343000, 1514344200, '2017:1514343000:1514344200', 1200, 'lt_1h' UNION ALL SELECT 1514344500, 1514345100, '2017:1514344500:1514345100', 600, 'lt_1h' UNION ALL SELECT 1514345400, 1514346000, '2017:1514345400:1514346000', 600, 'lt_1h' UNION ALL SELECT 1514347200, 1514350200, '2017:1514347200:1514350200', 3000, 'lt_1h' UNION ALL SELECT 1514352300, 1514352900, '2017:1514352300:1514352900', 600, 'lt_1h' UNION ALL SELECT 1514356500, 1514357400, '2017:1514356500:1514357400', 900, 'lt_1h' UNION ALL SELECT 1514462400, 1514463000, '2017:1514462400:1514463000', 600, 'lt_1h' UNION ALL SELECT 1514497500, 1514499900, '2017:1514497500:1514499900', 2400, 'lt_1h' UNION ALL SELECT 1514514900, 1514517600, '2017:1514514900:1514517600', 2700, 'lt_1h' UNION ALL SELECT 1514517900, 1514518500, '2017:1514517900:1514518500', 600, 'lt_1h' UNION ALL SELECT 1514533500, 1514534100, '2017:1514533500:1514534100', 600, 'lt_1h'), wh_hits AS (
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
