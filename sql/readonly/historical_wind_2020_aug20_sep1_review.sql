-- READ-ONLY exact timestamp review; UTC window [2020-08-20, 2020-09-01).
-- Run with database_name=weewx_WH1080. No raw rows are exported; daily aggregates only.
SELECT
  FLOOR((a0.dateTime-1597881600)/86400) AS utc_day_index,
  COUNT(*) AS WH1080_rows,
  SUM(a2.dateTime IS NOT NULL) AS eu_old_rows,
  SUM(a0.windSpeed IS NOT NULL AND a2.windSpeed IS NOT NULL AND a0.windSpeed<>0) AS windSpeed_nonzero_pairs,
  SUM(a0.windSpeed IS NOT NULL AND a2.windSpeed IS NOT NULL AND a0.windSpeed<>0 AND ABS(a2.windSpeed/a0.windSpeed-3.6)<0.001) AS windSpeed_ratio_3_6,
  SUM(a0.windSpeed IS NOT NULL AND a2.windSpeed IS NOT NULL AND a0.windSpeed<>0 AND ABS(a2.windSpeed/a0.windSpeed-1)<0.001) AS windSpeed_ratio_1,
  SUM(a0.windSpeed IS NOT NULL AND a2.windSpeed IS NOT NULL AND a0.windSpeed<>0 AND ABS(a2.windSpeed/a0.windSpeed-3.6)>=0.001 AND ABS(a2.windSpeed/a0.windSpeed-1)>=0.001) AS windSpeed_other,
  SUM(a0.windGust IS NOT NULL AND a2.windGust IS NOT NULL AND a0.windGust<>0) AS windGust_nonzero_pairs,
  SUM(a0.windGust IS NOT NULL AND a2.windGust IS NOT NULL AND a0.windGust<>0 AND ABS(a2.windGust/a0.windGust-3.6)<0.001) AS windGust_ratio_3_6,
  SUM(a0.windGust IS NOT NULL AND a2.windGust IS NOT NULL AND a0.windGust<>0 AND ABS(a2.windGust/a0.windGust-1)<0.001) AS windGust_ratio_1,
  SUM(a0.windGust IS NOT NULL AND a2.windGust IS NOT NULL AND a0.windGust<>0 AND ABS(a2.windGust/a0.windGust-3.6)>=0.001 AND ABS(a2.windGust/a0.windGust-1)>=0.001) AS windGust_other,
  SUM(a3.dateTime IS NOT NULL) AS current_eu_rows,
  SUM(a4.dateTime IS NOT NULL) AS GW1000_rows,
  SUM(a5.dateTime IS NOT NULL) AS reconstruction_rows,
  SUM(a2.dateTime IS NOT NULL AND (a3.windSpeed <=> a2.windSpeed)) AS eu_vs_euold_windSpeed_equal,
  SUM(a2.dateTime IS NOT NULL AND (a4.windSpeed <=> a2.windSpeed)) AS GW1000_vs_euold_windSpeed_equal,
  SUM(a2.dateTime IS NOT NULL AND (a5.windSpeed <=> a2.windSpeed)) AS reconstruction_vs_euold_windSpeed_equal,
  SUM(a2.dateTime IS NOT NULL AND (a3.windGust <=> a2.windGust)) AS eu_vs_euold_windGust_equal,
  SUM(a2.dateTime IS NOT NULL AND (a4.windGust <=> a2.windGust)) AS GW1000_vs_euold_windGust_equal,
  SUM(a2.dateTime IS NOT NULL AND (a5.windGust <=> a2.windGust)) AS reconstruction_vs_euold_windGust_equal
FROM archive a0
LEFT JOIN `pocasi-loucka.eu_old`.archive a2 ON a2.dateTime=a0.dateTime
LEFT JOIN `pocasi-loucka.eu`.archive a3 ON a3.dateTime=a0.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive a4 ON a4.dateTime=a0.dateTime
LEFT JOIN loucka_reconstruction.archive a5 ON a5.dateTime=a0.dateTime
WHERE a0.dateTime>=1597881600 AND a0.dateTime<1598918400
GROUP BY FLOOR((a0.dateTime-1597881600)/86400)
ORDER BY utc_day_index;

-- Separate exact-absence check; run with database_name=old_weewx:
-- SELECT dateTime FROM archive WHERE dateTime>=1597881600 AND dateTime<1598918400 LIMIT 1;
