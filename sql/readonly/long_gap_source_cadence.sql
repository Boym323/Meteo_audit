-- SELECT-only cadence summary for historical source rows inside the longest gap.
SELECT COUNT(*) AS source_rows,
       SUM(MOD(dateTime,300)=0) AS on_300s_grid,
       SUM(MOD(dateTime,300)<>0) AS off_300s_grid,
       MIN(usUnits) AS usUnits,
       MAX(usUnits) AS max_usUnits,
       MIN(`interval`) AS min_interval,
       MAX(`interval`) AS max_interval,
       MIN(dateTime) AS first_source_ts,
       MAX(dateTime) AS last_source_ts,
       MIN(outTemp) AS min_outTemp,
       MAX(outTemp) AS max_outTemp
FROM `old_weewx`.`archive`
WHERE dateTime BETWEEN 1313438700 AND 1330593900;

-- Aggregate neighboring source timestamp deltas within the bounded window.
SELECT COUNT(*) AS adjacent_pairs,
       SUM(delta<300) AS delta_lt_300s,
       SUM(delta=300) AS delta_300s,
       SUM(delta BETWEEN 301 AND 359) AS delta_301_359s,
       SUM(delta=360) AS delta_360s,
       SUM(delta BETWEEN 361 AND 600) AS delta_361_600s,
       SUM(delta>600) AS delta_gt_600s,
       COUNT(DISTINCT delta) AS distinct_deltas,
       MIN(delta) AS min_delta_s,
       MAX(delta) AS max_delta_s
FROM (
  SELECT dateTime-LAG(dateTime) OVER (ORDER BY dateTime) AS delta
  FROM `old_weewx`.`archive`
  WHERE dateTime BETWEEN 1313438700 AND 1330593900
) q
WHERE delta IS NOT NULL;

-- Specific source discontinuities >600 seconds in the same window.
SELECT prev_ts, dateTime AS target_ts, delta AS delta_seconds
FROM (
  SELECT dateTime,
         LAG(dateTime) OVER (ORDER BY dateTime) AS prev_ts,
         dateTime-LAG(dateTime) OVER (ORDER BY dateTime) AS delta
  FROM `old_weewx`.`archive`
  WHERE dateTime BETWEEN 1313438700 AND 1330593900
) q
WHERE delta>600
ORDER BY delta DESC;
