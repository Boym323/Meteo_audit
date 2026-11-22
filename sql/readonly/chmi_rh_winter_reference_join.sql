-- Exact-hour read-only extraction for CHMI 10-minute winter validation.
-- The external CHMI files are locally joined by Unix UTC epoch in scripts/analyze_chmi_rh_winter_validation.py.
-- Includes local measured fields and LuhaMet reference context. 2021 is diagnostic only.
SELECT a.dateTime,a.outTemp,a.outHumidity,a.rain,a.rainRate,a.windSpeed,
       r.temperature_c AS luhamet_temp,
       r.relative_humidity_pct AS luhamet_rh,
       r.quality_status,r.source_resolution,
       EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
              WHERE c.target_time=a.dateTime AND c.variable='outHumidity') AS rh_has_history
FROM loucka_reconstruction.archive a
LEFT JOIN loucka_reconstruction.reference_observations r
  ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
WHERE ((a.dateTime>=1546300800 AND a.dateTime<1551484800) -- 2019 Jan-Feb
    OR (a.dateTime>=1577836800 AND a.dateTime<1583020800) -- 2020 Jan-Feb
    OR (a.dateTime>=1609459200 AND a.dateTime<1614556800) -- 2021 Jan-Feb, diagnostic only
    OR (a.dateTime>=1640995200 AND a.dateTime<1646092800)) -- 2022 Jan-Feb
  AND MOD(a.dateTime,3600)=0
ORDER BY a.dateTime;
