-- READ-ONLY exact-time regional context for the frozen strict source-only 2011 cohort.
-- LuhaMet is regional reference, never local truth. This query tests availability only.
SELECT COUNT(*) AS source_candidates,
       COUNT(r.observed_at_utc) AS exact_LuhaMet_rows,
       SUM(r.temperature_c IS NOT NULL) AS exact_reference_T,
       MIN(r.temperature_c) AS reference_min_T,
       MAX(r.temperature_c) AS reference_max_T,
       SUM(ABS(o.outTemp-r.temperature_c)<=1) AS within_1C,
       SUM(ABS(o.outTemp-r.temperature_c)<=2) AS within_2C,
       SUM(ABS(o.outTemp-r.temperature_c)>5) AS over_5C,
       MIN(r.source_resolution) AS source_resolution,
       MIN(r.quality_status) AS quality_status
FROM old_weewx.archive o
JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.reference_observations r
 ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=o.dateTime
WHERE o.dateTime>=1293840000 AND o.dateTime<1325376000
 AND o.`interval`=5 AND o.usUnits=17 AND MOD(o.dateTime,300)=0
 AND w.`interval`=5 AND w.usUnits=17
 AND o.outTemp IS NOT NULL AND o.outHumidity IS NOT NULL
 AND o.rain IS NOT NULL AND o.rainRate IS NOT NULL AND o.windSpeed IS NOT NULL
 AND o.outTemp=w.outTemp AND o.outHumidity=w.outHumidity
 AND o.rain=w.rain AND o.rainRate=w.rainRate AND o.windSpeed=w.windSpeed
 AND t.dateTime IS NULL;
