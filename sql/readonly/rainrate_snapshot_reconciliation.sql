-- Reconstruct annual wet-rate-zero category immediately before the 2026-10-30 CSV snapshot.
-- DB timestamps use session-local time; 2026-10-30 10:30:10 is 09:30:10 UTC (CET).
-- 2021 is deliberately excluded from the output under the protected-year rule.
WITH rain_ranked AS (
    SELECT target_time, old_value,
           ROW_NUMBER() OVER (PARTITION BY target_time ORDER BY applied_at, id) AS rn
    FROM reconstruction_changes
    WHERE variable = 'rain' AND state = 'applied'
      AND applied_at >= '2026-10-30 10:30:10'
), rate_ranked AS (
    SELECT target_time, old_value,
           ROW_NUMBER() OVER (PARTITION BY target_time ORDER BY applied_at, id) AS rn
    FROM reconstruction_changes
    WHERE variable = 'rainRate' AND state = 'applied'
      AND applied_at >= '2026-10-30 10:30:10'
), rain_first AS (
    SELECT target_time, old_value FROM rain_ranked WHERE rn = 1
), rate_first AS (
    SELECT target_time, old_value FROM rate_ranked WHERE rn = 1
)
SELECT YEAR(FROM_UNIXTIME(a.dateTime)) AS local_year,
       COUNT(*) AS archive_rows,
       SUM((CASE WHEN r.target_time IS NULL THEN a.rain ELSE r.old_value END) > 0
           AND (CASE WHEN q.target_time IS NULL THEN a.rainRate ELSE q.old_value END) = 0)
           AS reconstructed_pre_export_wet_rate_zero,
       SUM(a.rain > 0 AND a.rainRate = 0) AS current_wet_rate_zero,
       SUM(r.target_time IS NOT NULL) AS rain_targets_changed_since_cutoff,
       SUM(q.target_time IS NOT NULL) AS rate_targets_changed_since_cutoff
FROM archive AS a
LEFT JOIN rain_first AS r ON r.target_time = a.dateTime
LEFT JOIN rate_first AS q ON q.target_time = a.dateTime
WHERE YEAR(FROM_UNIXTIME(a.dateTime)) <> 2021
GROUP BY YEAR(FROM_UNIXTIME(a.dateTime))
ORDER BY local_year;
