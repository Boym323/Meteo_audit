-- Read-only current archive timestamp discontinuities. dateTime is UTC epoch.
-- This returns every adjacent pair whose delta exceeds the smaller stored
-- interval at either endpoint. It is a candidate interval list, not a count of
-- lost measurements or an assertion that a sensor was operating.
WITH adjacent AS (
  SELECT dateTime,
         `interval` AS current_interval_minutes,
         LAG(dateTime) OVER (ORDER BY dateTime) AS previous_epoch,
         LAG(`interval`) OVER (ORDER BY dateTime) AS previous_interval_minutes
  FROM loucka_reconstruction.archive
), gaps AS (
  SELECT dateTime AS target_epoch,
         previous_epoch,
         dateTime - previous_epoch AS delta_seconds,
         previous_interval_minutes,
         current_interval_minutes
  FROM adjacent
  WHERE previous_epoch IS NOT NULL
    AND dateTime - previous_epoch > LEAST(previous_interval_minutes, current_interval_minutes) * 60
)
SELECT target_epoch, previous_epoch, delta_seconds,
       previous_interval_minutes, current_interval_minutes
FROM gaps ORDER BY target_epoch;

-- Empirical UTC-month cadence modes, using TIMESTAMPADD to avoid the session
-- SYSTEM/CET timezone conversion of FROM_UNIXTIME(). The 30-minute bound is
-- only a cadence screen; longer gaps are listed in the query above.
WITH adjacent AS (
  SELECT dateTime,
         `interval` AS current_interval_minutes,
         LAG(dateTime) OVER (ORDER BY dateTime) AS previous_epoch,
         LAG(`interval`) OVER (ORDER BY dateTime) AS previous_interval_minutes
  FROM loucka_reconstruction.archive
)
SELECT DATE_FORMAT(TIMESTAMPADD(SECOND, dateTime, '1970-01-01 00:00:00'), '%Y-%m') AS utc_month,
       dateTime - previous_epoch AS delta_seconds,
       previous_interval_minutes,
       current_interval_minutes,
       COUNT(*) AS transitions
FROM adjacent
WHERE previous_epoch IS NOT NULL
  AND dateTime - previous_epoch <= 1800
GROUP BY utc_month, delta_seconds, previous_interval_minutes, current_interval_minutes
ORDER BY utc_month, transitions DESC;
