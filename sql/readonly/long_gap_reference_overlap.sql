-- READ-ONLY bounded reference coverage check for the 2011-08-15 to 2012-03-01 long gap.
-- Epoch bounds are inclusive endpoints from the audited target archive.
SELECT station_id, COUNT(*) AS rows_n,
       SUM(temperature_c IS NOT NULL) AS temperature_rows,
       SUM(relative_humidity_pct IS NOT NULL) AS humidity_rows,
       MIN(observed_at_utc) AS first_utc, MAX(observed_at_utc) AS last_utc
FROM reference_observations
WHERE observed_at_utc BETWEEN 1313438700 AND 1330593900
GROUP BY station_id;
