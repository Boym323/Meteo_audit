-- Temporary/export-only exact-UTC-hour source rows for independent validation.
-- Join result locally to SHA-256-verified ČHMÚ hourly P files, quality=0.
-- Execute with the existing read-only Weather MCP connection. No DML/DDL.
SELECT r.dateTime AS dateTime_utc,
       r.pressure AS target_pressure_hpa,
       r.barometer AS target_barometer_hpa,
       r.outTemp AS target_outTemp_c,
       w.usUnits AS source_usUnits,
       w.`interval` AS source_interval_minutes,
       w.pressure AS source_pressure_hpa
FROM loucka_reconstruction.archive AS r
JOIN weewx_WH1080.archive AS w ON w.dateTime = r.dateTime
WHERE r.dateTime >= 1514764800 AND r.dateTime < 1546300800
  AND MOD(r.dateTime, 3600) = 0
  AND w.pressure IS NOT NULL
ORDER BY r.dateTime;
