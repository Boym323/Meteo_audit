-- Aggregate source RH candidates with live reconstruction RH at both +/-300s,
-- exact old_weewx/WH1080 pair, and no outHumidity change event.
-- Q1 2018 excluded from this review because it is protected.
WITH p AS (
 SELECT o.dateTime,o.outHumidity rh,o.outTemp old_temp,w.outTemp wh_temp,
        e.outHumidity euold_rh,r.outTemp target_temp,
        rp.outHumidity target_prev_rh,rn.outHumidity target_next_rh,
        o.usUnits old_units,o.interval old_interval,
        w.usUnits wh_units,w.interval wh_interval,
        CASE
         WHEN o.dateTime<1262304000 THEN 2009
         WHEN o.dateTime<1293840000 THEN 2010
         WHEN o.dateTime<1325376000 THEN 2011
         WHEN o.dateTime<1356998400 THEN 2012
         WHEN o.dateTime<1388534400 THEN 2013
         WHEN o.dateTime<1420070400 THEN 2014
         WHEN o.dateTime<1451606400 THEN 2015
         WHEN o.dateTime<1483228800 THEN 2016
         WHEN o.dateTime<1514764800 THEN 2017
         WHEN o.dateTime<1546300800 THEN 2018
         WHEN o.dateTime<1577836800 THEN 2019
         ELSE 2020 END utc_year
 FROM old_weewx.archive o
 JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
 JOIN loucka_reconstruction.archive r ON r.dateTime=o.dateTime
 LEFT JOIN `pocasi-loucka.eu_old`.archive e ON e.dateTime=o.dateTime
 JOIN loucka_reconstruction.archive rp ON rp.dateTime=o.dateTime-300
 JOIN loucka_reconstruction.archive rn ON rn.dateTime=o.dateTime+300
 WHERE o.dateTime>=1230768000 AND o.dateTime<1609459200
   AND o.outHumidity IS NOT NULL AND w.outHumidity IS NOT NULL
   AND o.outHumidity=w.outHumidity AND r.outHumidity IS NULL
   AND rp.outHumidity IS NOT NULL AND rn.outHumidity IS NOT NULL
   AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                  WHERE c.target_time=o.dateTime AND c.variable='outHumidity')
   AND NOT (o.dateTime>=1514764800 AND o.dateTime<1522540800)
)
SELECT utc_year,COUNT(*) paired_and_bracketed,
 SUM(euold_rh IS NOT NULL) euold_retains_rh,
 SUM(euold_rh=rh) euold_agrees_when_nonnull,
 SUM(rh BETWEEN LEAST(target_prev_rh,target_next_rh) AND GREATEST(target_prev_rh,target_next_rh)) source_rh_within_neighbor_range,
 SUM(ABS(rh-(target_prev_rh+target_next_rh)/2)<=1) within_1pct_midpoint,
 SUM(old_units=17 AND wh_units=17 AND old_interval=5 AND wh_interval=5) units_interval_17_5,
 SUM(old_temp=wh_temp) exact_source_temperature_copy,
 SUM(target_temp IS NOT NULL AND target_temp=old_temp) exact_source_target_temperature
FROM p GROUP BY utc_year ORDER BY utc_year;
