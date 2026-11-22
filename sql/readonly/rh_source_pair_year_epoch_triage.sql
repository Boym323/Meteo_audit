-- Bounded read-only Weather MCP query: exact-time common RH source-copy candidates,
-- current RH NULL, no target-variable history; UTC year boundaries use Unix seconds.
-- The Weather MCP SQL executor enforces read-only access. Returns aggregates only.
WITH paired AS (
 SELECT a.dateTime, o.outHumidity old_rh, w.outHumidity wh_rh,
        o.interval old_interval, w.interval wh_interval,
        o.usUnits old_units, w.usUnits wh_units, a.outHumidity target_rh,
        CASE
          WHEN a.dateTime < 1230768000 THEN 2008
          WHEN a.dateTime < 1262304000 THEN 2009
          WHEN a.dateTime < 1293840000 THEN 2010
          WHEN a.dateTime < 1325376000 THEN 2011
          WHEN a.dateTime < 1356998400 THEN 2012
          WHEN a.dateTime < 1388534400 THEN 2013
          WHEN a.dateTime < 1420070400 THEN 2014
          WHEN a.dateTime < 1451606400 THEN 2015
          WHEN a.dateTime < 1483228800 THEN 2016
          WHEN a.dateTime < 1514764800 THEN 2017
          WHEN a.dateTime < 1546300800 THEN 2018
          WHEN a.dateTime < 1577836800 THEN 2019
          WHEN a.dateTime < 1609459200 THEN 2020
          ELSE 2021 END utc_year
 FROM old_weewx.archive o
 JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
 JOIN loucka_reconstruction.archive a ON a.dateTime=o.dateTime
 WHERE o.outHumidity IS NOT NULL AND w.outHumidity IS NOT NULL
   AND a.outHumidity IS NULL
   AND NOT EXISTS (SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                   WHERE c.target_time=a.dateTime AND c.variable='outHumidity')
)
SELECT utc_year, COUNT(*) paired_candidates,
       SUM(old_rh=wh_rh) exact_copy_agreement,
       SUM(old_rh<>wh_rh) conflict_count,
       SUM(CASE WHEN old_interval=5 AND wh_interval=5 THEN 1 ELSE 0 END) both_interval_5,
       SUM(CASE WHEN old_interval=6 AND wh_interval=6 THEN 1 ELSE 0 END) both_interval_6,
       SUM(old_units=17 AND wh_units=17) both_units_17,
       SUM(target_rh IS NULL) target_null,
       MIN(dateTime) first_epoch_utc, MAX(dateTime) last_epoch_utc
FROM paired WHERE utc_year BETWEEN 2009 AND 2020
GROUP BY utc_year ORDER BY utc_year;
