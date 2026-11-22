-- Issue #20 (with #18 and #19): read-only WH1080 source/staging rebaseline.
-- Execute EACH SELECT separately through single-statement Weather MCP.
-- Neither matching timestamps nor source copy agreement proves physical sensor truth.
-- Historical raw source times remain immutable. No DML/DDL or automatic imports.

-- A. Exact staged target presence by original QC cohort. All 49,796 are in scope.
SELECT c.status,COUNT(*) AS staged,
       SUM(a.dateTime IS NOT NULL) AS target_now_present,
       SUM(a.dateTime IS NULL) AS target_still_absent,
       SUM(w.dateTime IS NULL) AS source_now_missing,
       SUM(a.dateTime IS NOT NULL AND (a.outTemp <=> c.outTemp_C))
           AS target_temp_matches_staged,
       SUM(a.dateTime IS NOT NULL AND (a.pressure <=> c.pressure_hPa))
           AS target_pressure_matches_staged
FROM `loucka_reconstruction`.`wh1080_missing_5min_candidates_20261030` c
LEFT JOIN `loucka_reconstruction`.`archive` a ON a.dateTime=c.target_time
LEFT JOIN `weewx_WH1080`.`archive` w ON w.dateTime=c.source_time
GROUP BY c.status ORDER BY c.status;

-- B. WH1080 rows not staged AND without a snapped 5-minute target.
-- This is a *hypothetical slot screen*, not an approved timestamp mapping.
-- Source archive currently ends in 2020-09; interval 6 is not a 5-min sample.
SELECT w.interval,(w.dateTime MOD 300=0) AS on_grid,
       COUNT(*) AS n,SUM(o.dateTime IS NOT NULL) AS old_copy_same_timestamp
FROM `weewx_WH1080`.`archive` w
LEFT JOIN `loucka_reconstruction`.`archive` a
       ON a.dateTime=FLOOR((w.dateTime+150)/300)*300
LEFT JOIN `loucka_reconstruction`.`wh1080_missing_5min_candidates_20261030` c
       ON c.source_time=w.dateTime
LEFT JOIN `old_weewx`.`archive` o ON o.dateTime=w.dateTime
WHERE w.dateTime>=1238345160 AND w.dateTime<=1599055800
  AND a.dateTime IS NULL AND c.source_time IS NULL
GROUP BY w.interval,(w.dateTime MOD 300=0)
ORDER BY n DESC;

-- C. Year by UTC epoch, never by MySQL session's local FROM_UNIXTIME().
-- Years are ranges of original WH1080 source timestamps, not snapped slots.
SELECT CASE WHEN w.dateTime<1262304000 THEN '2009'
            WHEN w.dateTime<1293840000 THEN '2010'
            WHEN w.dateTime<1325376000 THEN '2011'
            WHEN w.dateTime<1356998400 THEN '2012'
            WHEN w.dateTime<1388534400 THEN '2013'
            WHEN w.dateTime<1420070400 THEN '2014'
            WHEN w.dateTime<1451606400 THEN '2015'
            WHEN w.dateTime<1483228800 THEN '2016'
            WHEN w.dateTime<1514764800 THEN '2017'
            WHEN w.dateTime<1546300800 THEN '2018'
            WHEN w.dateTime<1577836800 THEN '2019'
            ELSE '2020' END AS utc_year,
       COUNT(*) AS missing_unstaged
FROM `weewx_WH1080`.`archive` w
LEFT JOIN `loucka_reconstruction`.`archive` a
       ON a.dateTime=FLOOR((w.dateTime+150)/300)*300
LEFT JOIN `loucka_reconstruction`.`wh1080_missing_5min_candidates_20261030` c
       ON c.source_time=w.dateTime
WHERE w.dateTime>=1238345160 AND w.dateTime<=1599055800
  AND a.dateTime IS NULL AND c.source_time IS NULL
GROUP BY utc_year ORDER BY utc_year;
