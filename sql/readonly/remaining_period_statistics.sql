-- Read-only pattern used for daily_core_valid_statistics_YYYY.csv exports.
-- Run one year at a time; pad UTC bounds by one day to retain full Prague local
-- New Year's days, then retain only DATE(FROM_UNIXTIME(dateTime)) in that year.
-- `dateTime` is UTC epoch. The live Weather MCP session was verified SYSTEM/CET.
WITH raw AS (
 SELECT DATE(FROM_UNIXTIME(dateTime)) local_day,'outTemp' variable,dateTime,
        outTemp value,`interval` interval_min,HOUR(FROM_UNIXTIME(dateTime)) local_hour
 FROM archive
 WHERE dateTime>=UNIX_TIMESTAMP('2022-12-31') AND dateTime<UNIX_TIMESTAMP('2024-01-02')
   AND outTemp IS NOT NULL AND dateTime<>1725016800 -- applied estimated outTemp, excluded from stats
 UNION ALL
 SELECT DATE(FROM_UNIXTIME(dateTime)),'outHumidity',dateTime,outHumidity,`interval`,HOUR(FROM_UNIXTIME(dateTime)) FROM archive
 WHERE dateTime>=UNIX_TIMESTAMP('2022-12-31') AND dateTime<UNIX_TIMESTAMP('2024-01-02') AND outHumidity IS NOT NULL
 UNION ALL
 SELECT DATE(FROM_UNIXTIME(dateTime)),'windSpeed',dateTime,windSpeed,`interval`,HOUR(FROM_UNIXTIME(dateTime)) FROM archive
 WHERE dateTime>=UNIX_TIMESTAMP('2022-12-31') AND dateTime<UNIX_TIMESTAMP('2024-01-02') AND windSpeed IS NOT NULL
 UNION ALL
 SELECT DATE(FROM_UNIXTIME(dateTime)),'windGust',dateTime,windGust,`interval`,HOUR(FROM_UNIXTIME(dateTime)) FROM archive
 WHERE dateTime>=UNIX_TIMESTAMP('2022-12-31') AND dateTime<UNIX_TIMESTAMP('2024-01-02') AND windGust IS NOT NULL
 UNION ALL
 SELECT DATE(FROM_UNIXTIME(dateTime)),'barometer',dateTime,barometer,`interval`,HOUR(FROM_UNIXTIME(dateTime)) FROM archive
 WHERE dateTime>=UNIX_TIMESTAMP('2022-12-31') AND dateTime<UNIX_TIMESTAMP('2024-01-02') AND barometer IS NOT NULL
), stepped AS (
 SELECT *,LAG(dateTime) OVER (PARTITION BY local_day,variable ORDER BY dateTime) previous_valid
 FROM raw
)
SELECT local_day,variable,COUNT(*) measured_rows,AVG(value) mean_value,
       MIN(value) min_value,MAX(value) max_value,
       SUM(local_hour>=6 AND local_hour<18) daytime_measured,
       SUM(local_hour<6 OR local_hour>=18) nighttime_measured,
       MIN(dateTime) first_valid_epoch_utc,MAX(dateTime) last_valid_epoch_utc,
       MIN(interval_min) min_interval_minutes,MAX(interval_min) max_interval_minutes,
       MAX(dateTime-previous_valid) max_valid_value_step_seconds
FROM stepped
GROUP BY local_day,variable ORDER BY local_day,variable;

-- Applied-event counts are joined by exact local day + field in the offline builder.
-- This query reports audit classes without treating unclassified rows as original.
SELECT DATE(FROM_UNIXTIME(target_time)) local_day,variable,
       SUM(LOWER(batch_key) LIKE '%estimated%' OR LOWER(batch_key) LIKE 'p3-v2%' OR LOWER(reason) LIKE '%estimated%') estimated_events,
       SUM(LOWER(batch_key) LIKE 'restored-%' OR LOWER(reason) LIKE '%restored%') restored_events,
       SUM(LOWER(batch_key) LIKE '%corrected%' OR LOWER(reason) LIKE '%corrected%') corrected_events,
       COUNT(*) audit_events
FROM reconstruction_changes
WHERE state='applied'
  AND variable IN ('outTemp','outHumidity','windSpeed','windGust','barometer')
  AND target_time>=UNIX_TIMESTAMP('2022-12-31') AND target_time<UNIX_TIMESTAMP('2026-11-15')
GROUP BY local_day,variable ORDER BY local_day,variable;

-- Archive-row and NULL denominator export corresponding to daily_core_statistics_YYYY.csv.
-- Retain only local_day in the requested local calendar year after the padded scan.
SELECT DATE(FROM_UNIXTIME(dateTime)) local_day,COUNT(*) archive_rows,
       SUM(outTemp IS NOT NULL) outTemp_raw_nonnull,
       SUM(outHumidity IS NOT NULL) outHumidity_raw_nonnull,
       SUM(windSpeed IS NOT NULL) windSpeed_raw_nonnull,
       SUM(windGust IS NOT NULL) windGust_raw_nonnull,
       SUM(barometer IS NOT NULL) barometer_raw_nonnull,
       MIN(`interval`) min_interval_minutes,MAX(`interval`) max_interval_minutes,
       MIN(dateTime) first_archive_epoch_utc,MAX(dateTime) last_archive_epoch_utc
FROM archive
WHERE dateTime>=UNIX_TIMESTAMP('2022-12-31') AND dateTime<UNIX_TIMESTAMP('2024-01-02')
GROUP BY local_day ORDER BY local_day;
