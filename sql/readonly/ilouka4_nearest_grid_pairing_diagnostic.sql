-- SELECT-only diagnostic. Reference epochs map to nearest 5-minute UTC grid.
-- This does NOT authorize pairing for calibration/reconstruction.
-- Bind :tolerance_seconds from a declared sensitivity set (e.g. 5/10/15/30).
SELECT COUNT(*) AS nearest_grid_cells,
       SUM(n_eligible) AS reference_epochs_within_tolerance,
       SUM(n_eligible > 1) AS collision_cells,
       SUM(n_eligible = 1 AND n_temperature_eligible = 1
           AND archive_outTemp IS NOT NULL) AS unique_temperature_pairs,
       SUM(n_eligible = 1 AND n_temperature_eligible = 1
           AND archive_outTemp IS NOT NULL AND n_exact_timestamp = 1) AS exact_time_pairs
FROM (
  SELECT g.nearest_epoch, g.n_eligible, g.n_temperature_eligible,
         g.n_exact_timestamp, a.outTemp AS archive_outTemp
  FROM (
    SELECT nearest_epoch,
           SUM(ABS(nearest_epoch-observed_at_utc) <= :tolerance_seconds) AS n_eligible,
           SUM(ABS(nearest_epoch-observed_at_utc) <= :tolerance_seconds
               AND temperature_c IS NOT NULL) AS n_temperature_eligible,
           SUM(observed_at_utc = nearest_epoch
               AND ABS(nearest_epoch-observed_at_utc) <= :tolerance_seconds) AS n_exact_timestamp
    FROM (
      SELECT observed_at_utc, temperature_c,
             FLOOR((observed_at_utc+150)/300)*300 AS nearest_epoch
      FROM loucka_reconstruction.reference_observations
      WHERE station_id = 'wu_ilouka4'
    ) AS mapped
    GROUP BY nearest_epoch
  ) AS g
  LEFT JOIN loucka_reconstruction.archive AS a ON a.dateTime=g.nearest_epoch
) AS candidates;

-- Annual counts must use explicit UTC epoch bounds or integer epoch CASE ranges;
-- do not use FROM_UNIXTIME without confirming the SQL session timezone.

-- Annual variant: bind explicit UTC epoch bounds for the rounded grid target.
SELECT COUNT(*) AS nearest_grid_cells,
       SUM(g.n_eligible) AS reference_epochs_within_tolerance,
       SUM(g.n_eligible = 1) AS single_reference_cells,
       SUM(g.n_eligible > 1) AS collision_cells,
       SUM(g.n_eligible = 1 AND g.n_temperature_eligible = 1
           AND a.outTemp IS NOT NULL) AS unique_temperature_pairs,
       SUM(a.dateTime IS NOT NULL) AS cells_with_archive
FROM (
  SELECT nearest_epoch,
         SUM(ABS(nearest_epoch-observed_at_utc) <= :tolerance_seconds) AS n_eligible,
         SUM(ABS(nearest_epoch-observed_at_utc) <= :tolerance_seconds
             AND temperature_c IS NOT NULL) AS n_temperature_eligible
  FROM (
    SELECT observed_at_utc,temperature_c,
           FLOOR((observed_at_utc+150)/300)*300 AS nearest_epoch
    FROM loucka_reconstruction.reference_observations
    WHERE station_id = 'wu_ilouka4'
  ) AS mapped
  GROUP BY nearest_epoch
) AS g
LEFT JOIN loucka_reconstruction.archive AS a ON a.dateTime=g.nearest_epoch
WHERE g.nearest_epoch >= :utc_year_start
  AND g.nearest_epoch < :utc_year_end;
