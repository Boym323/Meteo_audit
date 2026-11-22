-- Exact-time LuhaMet reference-only context for the 2016-03-17 RH candidate.
-- This does not treat the other station as local truth.
SELECT observed_at_utc, relative_humidity_pct, temperature_c
FROM loucka_reconstruction.reference_observations
WHERE station_id='luhamet_sehradice'
  AND observed_at_utc BETWEEN 1458238500 AND 1458240000
  AND relative_humidity_pct IS NOT NULL
ORDER BY observed_at_utc;
