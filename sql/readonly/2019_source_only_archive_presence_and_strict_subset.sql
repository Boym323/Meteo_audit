-- READ-ONLY exact archive row-presence and five-primary strict-candidate summary.
SELECT COUNT(*) AS source_only_rows,
 SUM(z.dateTime IS NOT NULL) AS eu_old_exact_rows,
 SUM(e.dateTime IS NOT NULL) AS eu_exact_rows,
 SUM(g.dateTime IS NOT NULL) AS gw1000_exact_rows,
 SUM(z.outTemp IS NOT NULL AND z.outTemp=a0.outTemp) AS eu_old_outTemp_equal,
 SUM(z.outHumidity IS NOT NULL) AS eu_old_outHumidity_rows,
 SUM(MOD(a0.dateTime,300)<>0) AS off_grid_rows
FROM old_weewx.archive a0 JOIN weewx_WH1080.archive a1 ON a1.dateTime=a0.dateTime
LEFT JOIN loucka_reconstruction.archive x ON x.dateTime=a0.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive z ON z.dateTime=a0.dateTime
LEFT JOIN `pocasi-loucka.eu`.archive e ON e.dateTime=a0.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=a0.dateTime
WHERE a0.dateTime>=1546300800 AND a0.dateTime<1577836800 AND x.dateTime IS NULL;

-- Exact-grid strict subgroup. This matches the existing 233 timestamp REVIEW_REQUIRED screen.
SELECT COUNT(*) AS strict_exact_copy_timestamps,
 SUM(z.dateTime IS NOT NULL) AS eu_old_exact_rows
FROM old_weewx.archive a0 JOIN weewx_WH1080.archive a1 ON a1.dateTime=a0.dateTime
LEFT JOIN loucka_reconstruction.archive x ON x.dateTime=a0.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive z ON z.dateTime=a0.dateTime
WHERE a0.dateTime>=1546300800 AND a0.dateTime<1577836800 AND x.dateTime IS NULL
 AND MOD(a0.dateTime,300)=0 AND a0.usUnits=17 AND a1.usUnits=17 AND a0.interval=5 AND a1.interval=5
 AND a0.outTemp IS NOT NULL AND a0.outHumidity IS NOT NULL AND a0.rain IS NOT NULL AND a0.rainRate IS NOT NULL AND a0.windSpeed IS NOT NULL
 AND a0.outTemp=a1.outTemp AND a0.outHumidity=a1.outHumidity AND a0.rain=a1.rain AND a0.rainRate=a1.rainRate AND a0.windSpeed=a1.windSpeed;
