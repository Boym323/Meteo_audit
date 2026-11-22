-- Read-only daily core-variable export query template.
-- Set local year bounds and scan one UTC day beyond each Prague-local year.
-- Session SYSTEM/CET was checked when these frozen exports were made.
-- Replace the illustrative timestamps for one requested local calendar year.
WITH base AS (
  SELECT DATE(FROM_UNIXTIME(dateTime)) local_day,dateTime,`interval` interval_min,
         HOUR(FROM_UNIXTIME(dateTime)) local_hour,
         COUNT(*) OVER (PARTITION BY DATE(FROM_UNIXTIME(dateTime))) archive_rows,
         SUM(outTemp IS NOT NULL) OVER (PARTITION BY DATE(FROM_UNIXTIME(dateTime))) outTemp_raw_nonnull,
         SUM(outHumidity IS NOT NULL) OVER (PARTITION BY DATE(FROM_UNIXTIME(dateTime))) outHumidity_raw_nonnull,
         SUM(windSpeed IS NOT NULL) OVER (PARTITION BY DATE(FROM_UNIXTIME(dateTime))) windSpeed_raw_nonnull,
         SUM(windGust IS NOT NULL) OVER (PARTITION BY DATE(FROM_UNIXTIME(dateTime))) windGust_raw_nonnull,
         SUM(barometer IS NOT NULL) OVER (PARTITION BY DATE(FROM_UNIXTIME(dateTime))) barometer_raw_nonnull,
         MIN(`interval`) OVER (PARTITION BY DATE(FROM_UNIXTIME(dateTime))) min_interval,
         MAX(`interval`) OVER (PARTITION BY DATE(FROM_UNIXTIME(dateTime))) max_interval,
         MIN(dateTime) OVER (PARTITION BY DATE(FROM_UNIXTIME(dateTime))) first_archive_epoch_utc,
         MAX(dateTime) OVER (PARTITION BY DATE(FROM_UNIXTIME(dateTime))) last_archive_epoch_utc,
         outTemp,outHumidity,windSpeed,windGust,barometer
  FROM loucka_reconstruction.archive
  WHERE usUnits=16 AND dateTime>=1514678400 AND dateTime<1546473600
), vals AS (
  SELECT local_day,dateTime,interval_min,local_hour,archive_rows,outTemp_raw_nonnull,outHumidity_raw_nonnull,windSpeed_raw_nonnull,windGust_raw_nonnull,barometer_raw_nonnull,min_interval,max_interval,first_archive_epoch_utc,last_archive_epoch_utc,'outTemp' variable,outTemp value FROM base
  UNION ALL SELECT local_day,dateTime,interval_min,local_hour,archive_rows,outTemp_raw_nonnull,outHumidity_raw_nonnull,windSpeed_raw_nonnull,windGust_raw_nonnull,barometer_raw_nonnull,min_interval,max_interval,first_archive_epoch_utc,last_archive_epoch_utc,'outHumidity',outHumidity FROM base
  UNION ALL SELECT local_day,dateTime,interval_min,local_hour,archive_rows,outTemp_raw_nonnull,outHumidity_raw_nonnull,windSpeed_raw_nonnull,windGust_raw_nonnull,barometer_raw_nonnull,min_interval,max_interval,first_archive_epoch_utc,last_archive_epoch_utc,'windSpeed',windSpeed FROM base
  UNION ALL SELECT local_day,dateTime,interval_min,local_hour,archive_rows,outTemp_raw_nonnull,outHumidity_raw_nonnull,windSpeed_raw_nonnull,windGust_raw_nonnull,barometer_raw_nonnull,min_interval,max_interval,first_archive_epoch_utc,last_archive_epoch_utc,'windGust',windGust FROM base
  UNION ALL SELECT local_day,dateTime,interval_min,local_hour,archive_rows,outTemp_raw_nonnull,outHumidity_raw_nonnull,windSpeed_raw_nonnull,windGust_raw_nonnull,barometer_raw_nonnull,min_interval,max_interval,first_archive_epoch_utc,last_archive_epoch_utc,'barometer',barometer FROM base
), stepped AS (
  SELECT *,LAG(dateTime) OVER(PARTITION BY local_day,variable ORDER BY dateTime) previous_valid
  FROM vals WHERE value IS NOT NULL
)
SELECT local_day,archive_rows,outTemp_raw_nonnull,outHumidity_raw_nonnull,windSpeed_raw_nonnull,windGust_raw_nonnull,barometer_raw_nonnull,
       min_interval,max_interval,first_archive_epoch_utc,last_archive_epoch_utc,variable,
       COUNT(*) measured_rows,AVG(value) mean_value,
       SUM(value*interval_min)/NULLIF(SUM(interval_min),0) weighted_mean_value,
       SUM(interval_min) valid_interval_minutes,MIN(value) min_value,MAX(value) max_value,
       SUM(local_hour>=6 AND local_hour<18) daytime_measured,
       SUM(local_hour<6 OR local_hour>=18) nighttime_measured,
       MIN(dateTime) first_valid_epoch_utc,MAX(dateTime) last_valid_epoch_utc,
       MIN(interval_min) min_valid_interval,MAX(interval_min) max_valid_interval,
       MAX(COALESCE(dateTime-previous_valid,interval_min*60)) max_valid_step_seconds
FROM stepped
GROUP BY local_day,variable ORDER BY local_day,variable;

-- These are current archive values, including known estimated target values.
-- The offline builder counts affected keys and marks those periods REVIEW_REQUIRED;
-- do not publish them as measurements until recomputed with estimate keys excluded.

-- Wind direction is circular: this separate read-only query computes a time-weighted
-- circular daily mean and resultant length. Do not use arithmetic min/max for degrees.
WITH raw_direction AS (
 SELECT DATE(FROM_UNIXTIME(dateTime)) local_day,dateTime,`interval` interval_min,
        HOUR(FROM_UNIXTIME(dateTime)) local_hour,windDir
 FROM loucka_reconstruction.archive
 WHERE usUnits=16 AND dateTime>=UNIX_TIMESTAMP('2009-01-01')
   AND dateTime<UNIX_TIMESTAMP('2026-10-30') AND windDir IS NOT NULL
), direction AS (
 SELECT *,LAG(dateTime) OVER(PARTITION BY local_day ORDER BY dateTime) previous_valid
 FROM raw_direction
)
SELECT local_day,COUNT(*) measured_rows,SUM(interval_min) valid_interval_minutes,
       MOD(DEGREES(ATAN2(SUM(interval_min*SIN(RADIANS(windDir))),
                         SUM(interval_min*COS(RADIANS(windDir)))))+360,360) circular_mean_direction_deg,
       SQRT(POW(SUM(interval_min*SIN(RADIANS(windDir))),2)+
            POW(SUM(interval_min*COS(RADIANS(windDir))),2))/NULLIF(SUM(interval_min),0) direction_resultant_length,
       SUM(local_hour>=6 AND local_hour<18) daytime_measured,
       SUM(local_hour<6 OR local_hour>=18) nighttime_measured,
       MAX(COALESCE(dateTime-previous_valid,interval_min*60)) max_valid_step_seconds,
       SUM(interval_min*SIN(RADIANS(windDir))) weighted_sin_component,
       SUM(interval_min*COS(RADIANS(windDir))) weighted_cos_component
FROM direction GROUP BY local_day ORDER BY local_day;

-- A single applied windDir restoration was verified against current target and exact
-- source value: target_time 1546297200 (local 2019-01-01), value 22.5 degrees.

-- Pressure and altimeter daily aggregates. Set the two UTC bounds to the padded
-- requested local-year range. The time-window (LAG) max step is per local day.
WITH raw AS (
 SELECT DATE(FROM_UNIXTIME(dateTime)) local_day,dateTime,`interval` interval_min,
        HOUR(FROM_UNIXTIME(dateTime)) local_hour,'pressure' variable,pressure value
 FROM loucka_reconstruction.archive
 WHERE usUnits=16 AND dateTime>=UNIX_TIMESTAMP('2009-01-01')
   AND dateTime<UNIX_TIMESTAMP('2026-10-30')
 UNION ALL
 SELECT DATE(FROM_UNIXTIME(dateTime)),dateTime,`interval`,
        HOUR(FROM_UNIXTIME(dateTime)),'altimeter',altimeter
 FROM loucka_reconstruction.archive
 WHERE usUnits=16 AND dateTime>=UNIX_TIMESTAMP('2009-01-01')
   AND dateTime<UNIX_TIMESTAMP('2026-10-30')
), valid AS (SELECT * FROM raw WHERE value IS NOT NULL),
stepped AS (
 SELECT *,LAG(dateTime) OVER(PARTITION BY local_day,variable ORDER BY dateTime) previous_valid
 FROM valid
)
SELECT local_day,variable,COUNT(*) measured_rows,
       SUM(value*interval_min)/NULLIF(SUM(interval_min),0) weighted_mean_value,
       SUM(interval_min) valid_interval_minutes,AVG(value) mean_value,MIN(value) min_value,MAX(value) max_value,
       SUM(local_hour>=6 AND local_hour<18) daytime_measured,
       SUM(local_hour<6 OR local_hour>=18) nighttime_measured,
       MIN(dateTime) first_valid_epoch_utc,MAX(dateTime) last_valid_epoch_utc,
       MAX(COALESCE(dateTime-previous_valid,interval_min*60)) max_valid_step_seconds
FROM stepped GROUP BY local_day,variable ORDER BY local_day,variable;

-- Read-only audit history for added variables; exact restored windDir is annotated above.
SELECT DATE(FROM_UNIXTIME(target_time)) local_day,variable,
       SUM(state='applied') applied_events,SUM(state='reverted') reverted_events,
       SUM(state='applied' AND (LOWER(batch_key) LIKE '%estimated%' OR LOWER(reason) LIKE '%estimated%')) estimated_events,
       SUM(state='applied' AND (LOWER(batch_key) LIKE 'restored-%' OR LOWER(reason) LIKE '%restored%')) restored_events,
       SUM(state='applied' AND (LOWER(batch_key) LIKE '%corrected%' OR LOWER(reason) LIKE '%corrected%')) corrected_events,
       COUNT(*) history_events
FROM loucka_reconstruction.reconstruction_changes
WHERE target_time>=1230768000 AND target_time<1793286601
  AND variable IN ('windDir','pressure','altimeter')
GROUP BY local_day,variable ORDER BY local_day,variable;
