-- Read-only template; replace each :utc_year_* token with the epoch for ONE UTC year.
-- Run one year per request (2009 through 2020) to stay below the connector's
-- statement time limit. This is exact timestamp source availability, not a fill.
WITH src AS (
  SELECT s.dateTime,'old_weewx' AS source_name,s.rain AS source_rain
  FROM old_weewx.archive s
  WHERE s.dateTime>=:utc_year_start AND s.dateTime<:utc_year_end AND s.rain IS NOT NULL
  UNION ALL
  SELECT s.dateTime,'weewx_WH1080',s.rain
  FROM weewx_WH1080.archive s
  WHERE s.dateTime>=:utc_year_start AND s.dateTime<:utc_year_end AND s.rain IS NOT NULL
), candidates AS (
  SELECT src.dateTime AS target_time,
         MAX(src.source_name='old_weewx') AS old_available,
         MAX(src.source_name='weewx_WH1080') AS wh_available,
         MAX(CASE WHEN src.source_name='old_weewx' THEN src.source_rain END) AS old_rain,
         MAX(CASE WHEN src.source_name='weewx_WH1080' THEN src.source_rain END) AS wh_rain
  FROM src
  JOIN loucka_reconstruction.archive r ON r.dateTime=src.dateTime
  WHERE r.rain IS NULL
  GROUP BY src.dateTime
), latest_rain_history AS (
  SELECT rc.target_time,rc.state,rc.new_value,
         ROW_NUMBER() OVER(PARTITION BY rc.target_time ORDER BY rc.created_at DESC,rc.id DESC) AS rn
  FROM loucka_reconstruction.reconstruction_changes rc
  WHERE rc.variable='rain'
    AND rc.target_time>=:utc_year_start AND rc.target_time<:utc_year_end
)
SELECT MAX(UTC_TIMESTAMP()) AS query_time_utc,
       :utc_year AS utc_year,
       COUNT(*) AS unique_null_targets_with_exact_source,
       COALESCE(SUM(c.old_available),0) AS old_source_available,
       COALESCE(SUM(c.wh_available),0) AS wh_source_available,
       COALESCE(SUM(c.old_available AND c.wh_available),0) AS both_sources_available,
       COALESCE(SUM(c.old_available AND c.wh_available AND c.old_rain=c.wh_rain),0) AS both_raw_equal,
       COALESCE(SUM(c.old_available AND c.wh_available AND c.old_rain<>c.wh_rain),0) AS both_raw_differ,
       COALESCE(SUM(c.old_available AND c.old_rain=0),0) AS old_zero,
       COALESCE(SUM(c.old_available AND c.old_rain>0),0) AS old_positive,
       COALESCE(SUM(c.wh_available AND c.wh_rain=0),0) AS wh_zero,
       COALESCE(SUM(c.wh_available AND c.wh_rain>0),0) AS wh_positive,
       COALESCE(SUM(h.rn=1 AND h.state='applied' AND h.new_value IS NULL),0) AS latest_applied_null,
       COALESCE(SUM(h.rn=1 AND h.state='applied' AND h.new_value IS NOT NULL),0) AS latest_applied_nonnull,
       COALESCE(SUM(h.rn=1 AND h.state='reverted'),0) AS latest_reverted,
       COALESCE(SUM(h.target_time IS NULL),0) AS no_history
FROM candidates c
LEFT JOIN latest_rain_history h ON h.target_time=c.target_time AND h.rn=1;
