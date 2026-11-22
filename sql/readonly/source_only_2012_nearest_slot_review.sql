-- READ-ONLY 2012 reconstruction source-only alignment and conflict screen.
-- Run with database_name=old_weewx. Nearest 300s target is diagnostic only.
SELECT MOD(o.dateTime,300) AS grid_remainder,o.usUnits,o.`interval`,COUNT(*) AS source_only_rows,
       SUM(w.dateTime IS NOT NULL) AS wh1080_rows,
       SUM(w.outTemp<=>o.outTemp) AS wh_outTemp_equal,
       SUM(r.dateTime IS NOT NULL) AS nearest_reconstruction_rows,
       SUM(r.usUnits=16 AND r.`interval`=5) AS nearest_metric_interval5_rows,
       SUM(r.outTemp<=>o.outTemp) AS nearest_outTemp_equal
FROM archive o
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive r
  ON r.dateTime=CASE WHEN MOD(o.dateTime,300)<=150
                     THEN o.dateTime-MOD(o.dateTime,300)
                     ELSE o.dateTime+(300-MOD(o.dateTime,300)) END
WHERE o.dateTime>=1325376000 AND o.dateTime<1356998400 AND t.dateTime IS NULL
GROUP BY MOD(o.dateTime,300),o.usUnits,o.`interval`
ORDER BY grid_remainder,o.usUnits,o.`interval`;

-- Per-field source lineage and exact availability in the merged/current archives.
SELECT COUNT(*) AS source_rows,
       SUM(w.dateTime IS NOT NULL) AS wh_rows,
       SUM(eo.dateTime IS NOT NULL) AS eu_old_rows,
       SUM(eu.dateTime IS NOT NULL) AS current_eu_rows,
       SUM(gw.dateTime IS NOT NULL) AS GW1000_rows,
       SUM(w.outTemp<=>o.outTemp) AS old_wh_T_equal,
       SUM(eo.outTemp<=>o.outTemp) AS old_euOld_T_equal,
       SUM(w.outHumidity<=>o.outHumidity) AS old_wh_RH_equal,
       SUM(eo.outHumidity<=>o.outHumidity) AS old_euOld_RH_equal,
       SUM(w.windSpeed<=>o.windSpeed) AS old_wh_speed_equal,
       SUM(eo.windSpeed<=>o.windSpeed) AS old_euOld_speed_equal,
       SUM(w.windGust<=>o.windGust) AS old_wh_gust_equal,
       SUM(eo.windGust<=>o.windGust) AS old_euOld_gust_equal,
       MIN(o.usUnits) AS old_units,MAX(o.usUnits) AS old_units_max,
       MIN(eo.usUnits) AS euold_units,MAX(eo.usUnits) AS euold_units_max
FROM archive o
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive eo ON eo.dateTime=o.dateTime
LEFT JOIN `pocasi-loucka.eu`.archive eu ON eu.dateTime=o.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive gw ON gw.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=o.dateTime
WHERE o.dateTime>=1325376000 AND o.dateTime<1356998400 AND t.dateTime IS NULL;

-- Three many-to-one projections that must not become duplicate inserts.
SELECT r.dateTime AS projected_target_time,COUNT(*) AS source_rows,
       GROUP_CONCAT(o.dateTime ORDER BY o.dateTime) AS source_timestamps,
       GROUP_CONCAT(o.outTemp ORDER BY o.dateTime) AS source_temperatures,
       GROUP_CONCAT(MOD(o.dateTime,300) ORDER BY o.dateTime) AS source_moduli,
       GROUP_CONCAT(ABS(o.dateTime-r.dateTime) ORDER BY o.dateTime) AS offsets_seconds
FROM archive o
JOIN loucka_reconstruction.archive r
  ON r.dateTime=CASE WHEN MOD(o.dateTime,300)<=150
                     THEN o.dateTime-MOD(o.dateTime,300)
                     ELSE o.dateTime+(300-MOD(o.dateTime,300)) END
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=o.dateTime
WHERE o.dateTime>=1325376000 AND o.dateTime<1356998400 AND t.dateTime IS NULL
GROUP BY r.dateTime HAVING COUNT(*)>1 ORDER BY r.dateTime;

-- Specific source-vs-merged outTemp conflicts, surrounding source/target values,
-- exact LuhaMet availability. No source or target row is modified.
SELECT o.dateTime,o.outTemp AS old_T,w.outTemp AS wh_T,eo.outTemp AS euOld_T,
       o.outHumidity AS old_RH,w.outHumidity AS wh_RH,eo.outHumidity AS euOld_RH,
       o.rain AS old_rain,eo.rain AS euOld_rain,
       o.windSpeed AS old_windSpeed,eo.windSpeed AS euOld_windSpeed,
       o.windGust AS old_windGust,eo.windGust AS euOld_windGust,
       r.dateTime AS nearest_target_time,r.outTemp AS nearest_target_T,
       r.outHumidity AS nearest_target_RH,l.temperature_c AS luhamet_T,
       l.quality_status AS luhamet_status,l.source_resolution AS luhamet_resolution
FROM archive o
JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
JOIN `pocasi-loucka.eu_old`.archive eo ON eo.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive r
  ON r.dateTime=CASE WHEN MOD(o.dateTime,300)<=150
                     THEN o.dateTime-MOD(o.dateTime,300)
                     ELSE o.dateTime+(300-MOD(o.dateTime,300)) END
LEFT JOIN loucka_reconstruction.reference_observations l
  ON l.station_id='luhamet_sehradice' AND l.observed_at_utc=o.dateTime
WHERE o.dateTime>=1325376000 AND o.dateTime<1356998400 AND t.dateTime IS NULL
  AND NOT (eo.outTemp<=>o.outTemp)
ORDER BY o.dateTime;
