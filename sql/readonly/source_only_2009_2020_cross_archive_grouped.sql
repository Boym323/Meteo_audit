-- READ-ONLY exact-source aggregate; interval/grid are screens, not cadence or correction evidence.
WITH o AS (
 SELECT a.dateTime ts,a.usUnits ou,a.interval oi,a.outTemp ot,a.outHumidity oh,a.rain ora,a.rainRate orr,a.windSpeed ows
 FROM old_weewx.archive a LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime
 WHERE a.dateTime>=UNIX_TIMESTAMP('2009-01-01') AND a.dateTime<UNIX_TIMESTAMP('2021-01-01') AND r.dateTime IS NULL
), w AS (
 SELECT a.dateTime ts,a.usUnits wu,a.interval wi,a.outTemp wt,a.outHumidity wh,a.rain wra,a.rainRate wrr,a.windSpeed wws
 FROM weewx_WH1080.archive a LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime
 WHERE a.dateTime>=UNIX_TIMESTAMP('2009-01-01') AND a.dateTime<UNIX_TIMESTAMP('2021-01-01') AND r.dateTime IS NULL
), u AS (
 SELECT COALESCE(o.ts,w.ts) ts,o.ts old_ts,w.ts wh_ts,o.ou,o.oi,o.ot,o.oh,o.ora,o.orr,o.ows,w.wu,w.wi,w.wt,w.wh,w.wra,w.wrr,w.wws FROM o LEFT JOIN w ON w.ts=o.ts
 UNION ALL
 SELECT w.ts,NULL,w.ts,NULL,NULL,NULL,NULL,NULL,NULL,NULL,w.wu,w.wi,w.wt,w.wh,w.wra,w.wrr,w.wws FROM w LEFT JOIN o ON o.ts=w.ts WHERE o.ts IS NULL
)
SELECT YEAR(FROM_UNIXTIME(u.ts)) utc_year,COALESCE(oi,wi) interval_min,COALESCE(ou,wu) usUnits,(u.ts%300=0) on_5m_grid,
 old_ts IS NOT NULL has_old,wh_ts IS NOT NULL has_wh1080,old_ts IS NOT NULL AND wh_ts IS NOT NULL both_copies,
 ot IS NOT NULL old_temp_present,wt IS NOT NULL wh_temp_present,oh IS NOT NULL old_rh_present,wh IS NOT NULL wh_rh_present,
 ora IS NOT NULL old_rain_present,wra IS NOT NULL wh_rain_present,orr IS NOT NULL old_rainrate_present,wrr IS NOT NULL wh_rainrate_present,
 ows IS NOT NULL old_wind_present,wws IS NOT NULL wh_wind_present,
 CASE WHEN old_ts IS NULL OR wh_ts IS NULL THEN 'SINGLE_COPY' WHEN ot<=>wt AND oh<=>wh AND ora<=>wra AND orr<=>wrr AND ows<=>wws THEN 'ALL_PRIMARY_EQUAL' WHEN ot<=>wt THEN 'TEMP_EQUAL_AUX_DIFF_OR_NULL' ELSE 'TEMP_CONFLICT' END concordance,
 p.dateTime IS NOT NULL has_pocasi_main,g.dateTime IS NOT NULL has_gw1000,e.dateTime IS NOT NULL has_pocasi_old,COUNT(*) timestamp_count
FROM u LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=u.ts LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=u.ts LEFT JOIN `pocasi-loucka.eu_old`.archive e ON e.dateTime=u.ts
GROUP BY utc_year,interval_min,usUnits,on_5m_grid,has_old,has_wh1080,both_copies,old_temp_present,wh_temp_present,old_rh_present,wh_rh_present,old_rain_present,wh_rain_present,old_rainrate_present,wh_rainrate_present,old_wind_present,wh_wind_present,concordance,has_pocasi_main,has_gw1000,has_pocasi_old
ORDER BY utc_year,interval_min,usUnits,on_5m_grid,concordance
