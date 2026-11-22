-- Execute against information_schema through Weather MCP. SELECT-only.
-- Fully qualified quoting permits read-only archive access despite punctuation
-- in schema names rejected as database_name by the connector.
SELECT COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch,
       MIN(`interval`) AS min_interval, MAX(`interval`) AS max_interval
FROM `pocasi-loucka.eu`.archive;
SELECT COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch,
       MIN(`interval`) AS min_interval, MAX(`interval`) AS max_interval
FROM `pocasi-loucka.eu_GW1000`.archive;
SELECT COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch,
       MIN(`interval`) AS min_interval, MAX(`interval`) AS max_interval
FROM `pocasi-loucka.eu_old`.archive;
SELECT COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch,
       MIN(`interval`) AS min_interval, MAX(`interval`) AS max_interval
FROM `loucka_reconstruction`.archive;
SELECT COUNT(*) AS rows_after_reconstruction, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch,
       COUNT(outTemp) AS outTemp_n, COUNT(outHumidity) AS outHumidity_n,
       COUNT(rain) AS rain_n, COUNT(rainRate) AS rainRate_n,
       COUNT(windSpeed) AS windSpeed_n, COUNT(radiation) AS radiation_n,
       COUNT(pm25_1) AS pm25_1_n
FROM `pocasi-loucka.eu`.archive
WHERE dateTime > 1793286600;
SELECT TABLE_SCHEMA, COUNT(*) AS table_count,
       SUM(TABLE_NAME='archive') AS has_archive,
       SUM(TABLE_NAME LIKE 'archive_day_%') AS archive_day_table_count
FROM information_schema.TABLES
WHERE TABLE_SCHEMA IN ('loucka_reconstruction','old_weewx','weewx_WH1080',
                       'pocasi-loucka.eu','pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old')
GROUP BY TABLE_SCHEMA ORDER BY TABLE_SCHEMA;
-- Bounded cadence audit of main production observations newer than reconstruction.
SELECT `interval`, usUnits, COUNT(*) AS rows_n, MIN(dateTime) AS first_epoch,
       MAX(dateTime) AS last_epoch
FROM `pocasi-loucka.eu`.archive WHERE dateTime > 1793286600
GROUP BY `interval`, usUnits ORDER BY `interval`, usUnits;
SELECT COUNT(*) AS adjacent_pairs,
       SUM(dateTime-prev_time=300) AS five_min_steps,
       SUM(dateTime-prev_time>300) AS longer_steps,
       SUM((dateTime-prev_time)/300-1) AS absent_300s_slots,
       MIN(dateTime-prev_time) AS min_delta_seconds,
       MAX(dateTime-prev_time) AS max_delta_seconds
FROM (SELECT dateTime,LAG(dateTime) OVER (ORDER BY dateTime) AS prev_time
      FROM `pocasi-loucka.eu`.archive WHERE dateTime > 1793286600) x
WHERE prev_time IS NOT NULL;
SELECT prev_time+300 AS candidate_missing_epoch, prev_time AS prior_epoch,
       dateTime AS next_epoch, dateTime-prev_time AS delta_seconds
FROM (SELECT dateTime,LAG(dateTime) OVER (ORDER BY dateTime) AS prev_time
      FROM `pocasi-loucka.eu`.archive WHERE dateTime > 1793286600) x
WHERE prev_time IS NOT NULL AND dateTime-prev_time>300 ORDER BY prev_time;
-- Exact-time cross-check of the three cadence candidates against all accessible archives.
SELECT t.dt,p.dateTime IS NOT NULL AS exact_prod_row,
       g.dateTime IS NOT NULL AS exact_GW_row,r.dateTime IS NOT NULL AS exact_reconstruction_row
FROM (SELECT 1793289600 AS dt UNION ALL SELECT 1793717700 UNION ALL SELECT 1794141000) t
LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=t.dt
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=t.dt
LEFT JOIN `loucka_reconstruction`.archive r ON r.dateTime=t.dt ORDER BY t.dt;
-- Bounded three-row boundary comparison; not a full-period provenance check.
SELECT p.dateTime,p.usUnits AS prod_units,p.`interval` AS prod_interval,
       p.outTemp AS prod_outTemp,p.outHumidity AS prod_outHumidity,
       p.rain AS prod_rain,p.rainRate AS prod_rainRate,
       r.usUnits AS recon_units,r.`interval` AS recon_interval,
       r.outTemp AS recon_outTemp,r.outHumidity AS recon_outHumidity,
       r.rain AS recon_rain,r.rainRate AS recon_rainRate
FROM `pocasi-loucka.eu`.archive p
LEFT JOIN `loucka_reconstruction`.archive r ON r.dateTime=p.dateTime
WHERE p.dateTime BETWEEN 1793286000 AND 1793288100 ORDER BY p.dateTime;
-- Exact key-variable non-NULL counts, reported as coverage counts (not quality).
SELECT COUNT(*) AS rows_n,COUNT(outTemp) AS outTemp_n,COUNT(outHumidity) AS outHumidity_n,
       COUNT(rain) AS rain_n,COUNT(rainRate) AS rainRate_n,COUNT(windSpeed) AS windSpeed_n,
       COUNT(windGust) AS windGust_n,COUNT(windDir) AS windDir_n,
       COUNT(pressure) AS pressure_n,COUNT(barometer) AS barometer_n
FROM `pocasi-loucka.eu`.archive;
SELECT COUNT(*) AS rows_n,COUNT(outTemp) AS outTemp_n,COUNT(outHumidity) AS outHumidity_n,
       COUNT(rain) AS rain_n,COUNT(rainRate) AS rainRate_n,COUNT(windSpeed) AS windSpeed_n,
       COUNT(windGust) AS windGust_n,COUNT(windDir) AS windDir_n,
       COUNT(pressure) AS pressure_n,COUNT(barometer) AS barometer_n
FROM `pocasi-loucka.eu_GW1000`.archive;
SELECT COUNT(*) AS rows_n,COUNT(outTemp) AS outTemp_n,COUNT(outHumidity) AS outHumidity_n,
       COUNT(rain) AS rain_n,COUNT(rainRate) AS rainRate_n,COUNT(windSpeed) AS windSpeed_n,
       COUNT(windGust) AS windGust_n,COUNT(windDir) AS windDir_n,
       COUNT(pressure) AS pressure_n,COUNT(barometer) AS barometer_n
FROM `pocasi-loucka.eu_old`.archive;
-- Exact interval/unit distribution, execute once for each of the three schemas.
SELECT usUnits,`interval`,COUNT(*) AS rows_n,MIN(dateTime) AS first_epoch,MAX(dateTime) AS last_epoch
FROM `pocasi-loucka.eu`.archive GROUP BY usUnits,`interval` ORDER BY usUnits,`interval`;
SELECT usUnits,`interval`,COUNT(*) AS rows_n,MIN(dateTime) AS first_epoch,MAX(dateTime) AS last_epoch
FROM `pocasi-loucka.eu_GW1000`.archive GROUP BY usUnits,`interval` ORDER BY usUnits,`interval`;
SELECT usUnits,`interval`,COUNT(*) AS rows_n,MIN(dateTime) AS first_epoch,MAX(dateTime) AS last_epoch
FROM `pocasi-loucka.eu_old`.archive GROUP BY usUnits,`interval` ORDER BY usUnits,`interval`;
-- Schema/table/index metadata from information_schema (no data-row scan).
SELECT TABLE_SCHEMA,COUNT(*) AS table_count,
       SUM(TABLE_NAME='archive') AS has_archive,
       SUM(TABLE_NAME LIKE 'archive_day_%') AS archive_day_table_count
FROM information_schema.TABLES
WHERE TABLE_SCHEMA IN ('loucka_reconstruction','old_weewx','weewx_WH1080',
                       'pocasi-loucka.eu','pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old')
GROUP BY TABLE_SCHEMA ORDER BY TABLE_SCHEMA;
SELECT c.TABLE_SCHEMA,COUNT(*) AS archive_column_count,
       GROUP_CONCAT(DISTINCT CONCAT(s.INDEX_NAME,':',s.COLUMN_NAME)
                    ORDER BY s.INDEX_NAME,s.SEQ_IN_INDEX SEPARATOR ', ') AS indexes
FROM information_schema.COLUMNS c
LEFT JOIN information_schema.STATISTICS s
  ON s.TABLE_SCHEMA=c.TABLE_SCHEMA AND s.TABLE_NAME=c.TABLE_NAME
WHERE c.TABLE_SCHEMA IN ('pocasi-loucka.eu','pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old')
  AND c.TABLE_NAME='archive'
GROUP BY c.TABLE_SCHEMA ORDER BY c.TABLE_SCHEMA;
-- Broad range screen for all rows beyond the reconstruction cutoff; triage only.
SELECT COUNT(*) AS n,MIN(outTemp) AS min_outTemp,MAX(outTemp) AS max_outTemp,
       SUM(outTemp < -50 OR outTemp > 60) AS outTemp_outside_broad_range,
       MIN(outHumidity) AS min_RH,MAX(outHumidity) AS max_RH,
       SUM(outHumidity < 0 OR outHumidity > 100) AS RH_outside_0_100,
       MIN(rain) AS min_rain,MAX(rain) AS max_rain,SUM(rain < 0) AS negative_rain,
       MIN(rainRate) AS min_rainRate,MAX(rainRate) AS max_rainRate,SUM(rainRate < 0) AS negative_rainRate,
       MIN(windSpeed) AS min_windSpeed,MAX(windSpeed) AS max_windSpeed,SUM(windSpeed < 0) AS negative_windSpeed,
       MIN(windGust) AS min_windGust,MAX(windGust) AS max_windGust,SUM(windGust < 0) AS negative_windGust,
       MIN(windDir) AS min_windDir,MAX(windDir) AS max_windDir,
       SUM(windDir < 0 OR windDir >= 360) AS windDir_outside_0_360,
       MIN(radiation) AS min_radiation,MAX(radiation) AS max_radiation,SUM(radiation < 0) AS negative_radiation,
       MIN(pm25_1) AS min_pm25_1,MAX(pm25_1) AS max_pm25_1,SUM(pm25_1 >= 999.8) AS pm25_at_or_above_999_8,
       MIN(pressure) AS min_pressure,MAX(pressure) AS max_pressure,
       MIN(barometer) AS min_barometer,MAX(barometer) AS max_barometer
FROM `pocasi-loucka.eu`.archive WHERE dateTime>1793286600;
