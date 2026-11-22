-- READ-ONLY aggregate: source rows without a reconstruction timestamp, 2009–2020 only.
-- Results are screening counts, not approved restoration targets.
SELECT YEAR(FROM_UNIXTIME(a.dateTime)) year, COUNT(*) source_only_rows,
 SUM(a.outTemp IS NOT NULL) outTemp_n, SUM(a.outHumidity IS NOT NULL) outHumidity_n,
 SUM(a.rain IS NOT NULL) rain_n, SUM(a.rainRate IS NOT NULL) rainRate_n,
 SUM(a.barometer IS NOT NULL) barometer_n, SUM(a.windSpeed IS NOT NULL) windSpeed_n,
 SUM(a.windDir IS NOT NULL) windDir_n, SUM(a.dateTime % 300 = 0) on_5m_grid
FROM archive a LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime
WHERE a.dateTime >= UNIX_TIMESTAMP('2009-01-01') AND a.dateTime < UNIX_TIMESTAMP('2021-01-01')
 AND r.dateTime IS NULL GROUP BY YEAR(FROM_UNIXTIME(a.dateTime)) ORDER BY year;
