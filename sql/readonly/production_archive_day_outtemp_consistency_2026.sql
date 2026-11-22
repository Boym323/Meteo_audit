-- Read-only exact daily summary vs definitive archive check for local year 2026.
-- Europe/Prague local-day keys generated via zoneinfo; archive intervals assigned by
-- end timestamp: (local_midnight_start, next_local_midnight_start].
-- Current partial local day (2026-11-13) excluded; 2021 has separate diagnostic status.
WITH raw AS (
  SELECT DATE(FROM_UNIXTIME(dateTime-1)) AS local_date,
         COUNT(outTemp) AS r_count,
         MIN(outTemp) AS r_min, MAX(outTemp) AS r_max,
         SUM(outTemp) AS r_sum,
         SUM(outTemp*`interval`*60) AS r_wsum,
         SUM(CASE WHEN outTemp IS NOT NULL THEN `interval`*60 ELSE 0 END) AS r_sumtime
  FROM `pocasi-loucka.eu`.archive
  WHERE dateTime > 1767222000 AND dateTime <= 1794524400
  GROUP BY DATE(FROM_UNIXTIME(dateTime-1))
)
SELECT COUNT(*) AS summary_days,
       SUM(r.local_date IS NULL) AS no_raw_day,
       SUM(NOT (d.`count` <=> r.r_count)) AS count_mismatch,
       SUM(NOT (d.`sum` <=> r.r_sum)) AS sum_exact_mismatch,
       MAX(ABS(d.`sum`-r.r_sum)) AS max_sum_diff,
       SUM(NOT (d.wsum <=> r.r_wsum)) AS wsum_exact_mismatch,
       MAX(ABS(d.wsum-r.r_wsum)) AS max_wsum_diff,
       SUM(NOT (d.sumtime <=> r.r_sumtime)) AS sumtime_mismatch,
       SUM(NOT (d.`min` <=> r.r_min)) AS min_exact_mismatch,
       SUM(ABS(d.`min`-r.r_min)>0.1) AS min_diff_over_0_1,
       MAX(ABS(d.`min`-r.r_min)) AS max_min_diff,
       SUM(NOT (d.`max` <=> r.r_max)) AS max_exact_mismatch,
       SUM(ABS(d.`max`-r.r_max)>0.1) AS max_diff_over_0_1,
       SUM(d.`max`-r.r_max>0.1) AS summary_max_above_raw_over_0_1,
       SUM(d.`max`-r.r_max< -0.1) AS summary_max_below_raw_over_0_1,
       MAX(ABS(d.`max`-r.r_max)) AS max_max_diff,
       SUM(m.dateTime IS NULL) AS mintime_absent_in_archive,
       SUM(mx.dateTime IS NULL) AS maxtime_absent_in_archive
FROM `pocasi-loucka.eu`.archive_day_outTemp d
LEFT JOIN raw r ON r.local_date=DATE(FROM_UNIXTIME(d.dateTime))
LEFT JOIN `pocasi-loucka.eu`.archive m ON m.dateTime=d.mintime
LEFT JOIN `pocasi-loucka.eu`.archive mx ON mx.dateTime=d.maxtime
WHERE d.dateTime >= 1767222000 AND d.dateTime < 1794524400;

-- Monthly diagnostic split for 2026. Same bounded range and DST-safe local date mapping.
WITH raw AS (
  SELECT DATE(FROM_UNIXTIME(dateTime-1)) AS local_date,
         MIN(outTemp) AS r_min, MAX(outTemp) AS r_max
  FROM `pocasi-loucka.eu`.archive
  WHERE dateTime > 1767222000 AND dateTime <= 1794524400
  GROUP BY DATE(FROM_UNIXTIME(dateTime-1))
)
SELECT DATE_FORMAT(FROM_UNIXTIME(d.dateTime),'%Y-%m') AS local_month,
       COUNT(*) AS days,
       SUM(ABS(d.`min`-r.r_min)>0.1) AS min_gt_0_1,
       SUM(ABS(d.`max`-r.r_max)>0.1) AS max_gt_0_1,
       MAX(ABS(d.`min`-r.r_min)) AS max_min_diff,
       MAX(ABS(d.`max`-r.r_max)) AS max_max_diff,
       SUM(m.dateTime IS NULL) AS mintime_absent_in_archive,
       SUM(mx.dateTime IS NULL) AS maxtime_absent_in_archive
FROM `pocasi-loucka.eu`.archive_day_outTemp d
JOIN raw r ON r.local_date=DATE(FROM_UNIXTIME(d.dateTime))
LEFT JOIN `pocasi-loucka.eu`.archive m ON m.dateTime=d.mintime
LEFT JOIN `pocasi-loucka.eu`.archive mx ON mx.dateTime=d.maxtime
WHERE d.dateTime >= 1767222000 AND d.dateTime < 1794524400
GROUP BY DATE_FORMAT(FROM_UNIXTIME(d.dateTime),'%Y-%m')
ORDER BY local_month;
