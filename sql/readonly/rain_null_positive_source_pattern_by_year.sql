-- SELECT-only pattern screen. Replace :utc_year_start and :utc_year_end with
-- one year's Unix UTC bounds; run per year to keep archive work bounded.
-- Source rows with old rain>0, current reconstruction rain NULL, and no rain event.
WITH source_sequence AS (
  SELECT s.dateTime,s.rain,s.rainRate,s.interval,s.usUnits,
         LAG(s.dateTime) OVER(ORDER BY s.dateTime) AS prev_time,
         LAG(s.rain) OVER(ORDER BY s.dateTime) AS prev_rain,
         LEAD(s.dateTime) OVER(ORDER BY s.dateTime) AS next_time,
         LEAD(s.rain) OVER(ORDER BY s.dateTime) AS next_rain
  FROM old_weewx.archive s
  WHERE s.dateTime>=:utc_year_start AND s.dateTime<:utc_year_end
), rain_history AS (
  SELECT target_time,
         ROW_NUMBER() OVER(PARTITION BY target_time ORDER BY created_at DESC,id DESC) AS rn
  FROM loucka_reconstruction.reconstruction_changes
  WHERE variable='rain'
    AND target_time>=:utc_year_start AND target_time<:utc_year_end
), candidates AS (
  SELECT s.*,r.rainRate AS reconstruction_rainRate
  FROM source_sequence s
  JOIN loucka_reconstruction.archive r ON r.dateTime=s.dateTime
  LEFT JOIN rain_history h ON h.target_time=s.dateTime AND h.rn=1
  WHERE r.rain IS NULL AND s.rain>0 AND h.target_time IS NULL
)
SELECT UTC_TIMESTAMP() AS query_time_utc,
       COUNT(*) AS positive_nohistory_targets,
       MIN(rain) AS source_rain_min,MAX(rain) AS source_rain_max,
       SUM(usUnits=17) AS metricwx_rows,SUM(interval=5) AS five_minute_rows,
       SUM(prev_time=dateTime-300) AS prev_300s,
       SUM(next_time=dateTime+300) AS next_300s,
       SUM(prev_time=dateTime-300 AND prev_rain=0) AS prev_300s_zero,
       SUM(next_time=dateTime+300 AND next_rain=0) AS next_300s_zero,
       SUM(prev_time=dateTime-300 AND prev_rain=0 AND next_time=dateTime+300 AND next_rain=0) AS isolated_single_row_pulse,
       SUM(prev_time=dateTime-300 AND prev_rain>0) AS prev_300s_positive,
       SUM(next_time=dateTime+300 AND next_rain>0) AS next_300s_positive,
       SUM(reconstruction_rainRate IS NULL) AS reconstruction_rate_null,
       SUM(reconstruction_rainRate=0) AS reconstruction_rate_zero,
       SUM(reconstruction_rainRate>0) AS reconstruction_rate_positive,
       SUM(rainRate>0) AS source_rate_positive
FROM candidates;
