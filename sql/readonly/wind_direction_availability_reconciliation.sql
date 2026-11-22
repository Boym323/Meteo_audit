-- Positive wind speed with missing windDir, by UTC year and speed band.
SELECT YEAR(DATE_ADD('1970-01-01',INTERVAL a.dateTime SECOND)) AS utc_year,
  COUNT(*) AS archive_rows,
  SUM(a.windSpeed IS NOT NULL) AS speed_n,
  SUM(a.windDir IS NOT NULL) AS direction_n,
  SUM(a.windSpeed>0) AS positive_speed_n,
  SUM(a.windSpeed>0 AND a.windDir IS NULL) AS positive_speed_missing_dir,
  SUM(a.windSpeed>10 AND a.windDir IS NULL) AS speed_gt10_missing_dir,
  SUM(a.windGustDir IS NOT NULL) AS gust_direction_n
FROM `loucka_reconstruction`.archive a
GROUP BY utc_year ORDER BY utc_year;

-- Exploratory speed bands; not normative sensor thresholds.
SELECT CASE
    WHEN a.dateTime>=1514764800 AND a.dateTime<1522540800 THEN '2018_Q1_INTERIM'
    WHEN a.dateTime>=1609459200 AND a.dateTime<1640995200 THEN '2021_DIAGNOSTIC_ONLY'
    ELSE 'other'
  END AS scope,
  CASE WHEN a.windSpeed=0 THEN 'zero'
       WHEN a.windSpeed<=1 THEN '(0,1]'
       WHEN a.windSpeed<=3 THEN '(1,3]'
       WHEN a.windSpeed<=5 THEN '(3,5]'
       WHEN a.windSpeed<=10 THEN '(5,10]'
       ELSE '>10' END AS speed_band_kmh,
  COUNT(*) AS windSpeed_rows,
  SUM(a.windDir IS NOT NULL) AS direction_present,
  SUM(a.windDir IS NULL) AS direction_missing,
  SUM(a.windGust IS NOT NULL) AS gust_present,
  SUM(a.windGustDir IS NOT NULL) AS gust_direction_present
FROM `loucka_reconstruction`.archive a
WHERE a.windSpeed IS NOT NULL
GROUP BY scope,speed_band_kmh
ORDER BY scope,FIELD(speed_band_kmh,'zero','(0,1]','(1,3]','(3,5]','(5,10]','>10');

-- Exact-time legacy source reconciliation for positive-speed/missing-direction targets.
WITH c AS (
  SELECT a.dateTime,a.windSpeed,a.windDir
  FROM `loucka_reconstruction`.archive a
  WHERE a.dateTime>=1235865600 AND a.dateTime<1793286601
    AND a.windSpeed>0 AND a.windDir IS NULL
)
SELECT CASE
    WHEN YEAR(DATE_ADD('1970-01-01',INTERVAL c.dateTime SECOND))<=2013 THEN '2009_2013'
    WHEN YEAR(DATE_ADD('1970-01-01',INTERVAL c.dateTime SECOND))<=2019 THEN '2014_2019'
    WHEN YEAR(DATE_ADD('1970-01-01',INTERVAL c.dateTime SECOND))<=2022 THEN '2020_2022'
    ELSE '2023_2026' END AS period,
  COUNT(*) AS candidates,
  SUM(o.windDir BETWEEN 0 AND 360 AND w.windDir BETWEEN 0 AND 360 AND o.windDir=w.windDir) AS both_legacy_dirs_valid_equal,
  SUM(o.windDir BETWEEN 0 AND 360 AND (w.windDir<0 OR w.windDir>=360)) AS old_valid_wh_invalid,
  SUM(o.windDir IS NULL AND w.windDir BETWEEN 0 AND 360) AS old_null_wh_valid,
  SUM(o.windDir IS NULL AND w.windDir IS NULL) AS both_legacy_null,
  SUM(po.windDir IS NOT NULL) AS pocasi_old_dir_present,
  SUM(g.windDir IS NOT NULL) AS GW1000_dir_present,
  SUM(p.windDir IS NOT NULL) AS main_production_dir_present,
  SUM(h.target_time IS NOT NULL) AS windDir_change_history
FROM c
LEFT JOIN `old_weewx`.archive o ON o.dateTime=c.dateTime
LEFT JOIN `weewx_WH1080`.archive w ON w.dateTime=c.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive po ON po.dateTime=c.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=c.dateTime
LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=c.dateTime
LEFT JOIN (SELECT DISTINCT target_time FROM `loucka_reconstruction`.reconstruction_changes WHERE variable='windDir') h
  ON h.target_time=c.dateTime
GROUP BY period ORDER BY period;

-- Bounded problematic cases 2014-2019 and rare 2020 legacy-only direction samples.
SELECT a.dateTime AS epoch,a.windSpeed AS reconstruction_speed,o.windDir AS old_dir,w.windDir AS wh1080_dir,
       o.windSpeed AS old_speed,w.windSpeed AS wh1080_speed,o.usUnits AS old_units,w.usUnits AS wh1080_units,
       o.`interval` AS old_interval,w.`interval` AS wh1080_interval
FROM `loucka_reconstruction`.archive a
LEFT JOIN `old_weewx`.archive o ON o.dateTime=a.dateTime
LEFT JOIN `weewx_WH1080`.archive w ON w.dateTime=a.dateTime
WHERE a.dateTime>=1391212800 AND a.dateTime<1672531200
  AND a.windSpeed>0 AND a.windDir IS NULL
  AND (o.windDir IS NOT NULL OR w.windDir IS NOT NULL)
ORDER BY a.dateTime;
