-- SELECT-only cadence summary: run separately per station_id to bound window work.
SELECT station_id, COUNT(*) AS observations, MIN(observed_at_utc) AS first_epoch,
       MAX(observed_at_utc) AS last_epoch, COUNT(delta) AS pairs,
       SUM(delta = 300) AS exact_5m, SUM(delta = 360) AS exact_6m,
       SUM(delta <> 300) AS non_5m, SUM(delta > 600) AS gaps_gt_10m,
       MAX(delta) AS max_delta_seconds
FROM (
  SELECT station_id, observed_at_utc,
         observed_at_utc - LAG(observed_at_utc) OVER (ORDER BY observed_at_utc) AS delta
  FROM loucka_reconstruction.reference_observations
  WHERE station_id = :station_id
) AS adjacent
GROUP BY station_id;

-- Epoch phase distribution; aggregate only, no observations returned.
SELECT MOD(observed_at_utc, 300) AS epoch_mod_300, COUNT(*) AS n
FROM loucka_reconstruction.reference_observations
WHERE station_id = :station_id
GROUP BY epoch_mod_300
ORDER BY n DESC
LIMIT 6;

-- Most common adjacent intervals (diagnostic).
SELECT delta, COUNT(*) AS n
FROM (
  SELECT observed_at_utc - LAG(observed_at_utc) OVER (ORDER BY observed_at_utc) AS delta
  FROM loucka_reconstruction.reference_observations
  WHERE station_id = :station_id
) AS adjacent
WHERE delta IS NOT NULL
GROUP BY delta ORDER BY n DESC, delta LIMIT 12;
