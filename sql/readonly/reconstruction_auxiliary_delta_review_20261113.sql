-- Targeted auxiliary-table inventory delta checks. READ-ONLY SELECT only.
SELECT r.dateTime,r.rain_cm,r.rainRate_cm_h,r.station_count,r.method,o.target_time AS original_match
FROM loucka_reconstruction.rain_reconstruction_202107_chmi_v1 r
LEFT JOIN loucka_reconstruction.rain_archive_original_202107 o ON o.target_time=r.dateTime
WHERE o.target_time IS NULL ORDER BY r.dateTime;
SELECT o.target_time,o.original_rain_cm,o.original_rainrate_cm_h,r.dateTime AS reconstruction_match
FROM loucka_reconstruction.rain_archive_original_202107 o
LEFT JOIN loucka_reconstruction.rain_reconstruction_202107_chmi_v1 r ON r.dateTime=o.target_time
WHERE r.dateTime IS NULL ORDER BY o.target_time;
SELECT dateTime,rain_before,rainRate_before,usUnits_before,interval_before,saved_at
FROM loucka_reconstruction.rain_phase_a_backup_20261030_v1 ORDER BY dateTime;

-- Current field completeness for the seven exact affected timestamps (diagnostic only).
SELECT COUNT(*) AS exact_rows, MIN(dateTime) AS min_time, MAX(dateTime) AS max_time,
       COUNT(DISTINCT usUnits) AS unit_values, COUNT(DISTINCT `interval`) AS interval_values,
       SUM(outTemp IS NOT NULL) AS outTemp_nonnull, SUM(outHumidity IS NOT NULL) AS outHumidity_nonnull,
       SUM(rain IS NOT NULL) AS rain_nonnull, SUM(rainRate IS NOT NULL) AS rainRate_nonnull,
       SUM(barometer IS NOT NULL) AS barometer_nonnull, SUM(pressure IS NOT NULL) AS pressure_nonnull,
       SUM(windSpeed IS NOT NULL) AS windSpeed_nonnull, SUM(windDir IS NOT NULL) AS windDir_nonnull,
       SUM(windGust IS NOT NULL) AS windGust_nonnull
FROM loucka_reconstruction.archive
WHERE dateTime IN (1625319000,1625324100,1625324400,1625324700,1625325000,1625325300,1625325600);
-- Full event detail for the seven exact targets.
SELECT target_time,variable,batch_key,old_value,new_value,source_database,source_time,source_value,reason,state,created_at,applied_at
FROM loucka_reconstruction.reconstruction_changes
WHERE target_time IN (1625319000,1625324100,1625324400,1625324700,1625325000,1625325300,1625325600)
  AND variable IN ('rain','rainRate') ORDER BY target_time,created_at,id;
