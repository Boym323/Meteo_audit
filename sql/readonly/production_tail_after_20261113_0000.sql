-- Bounded read-only aggregate for production rows after the 00:00 UTC anchor.
-- The database connector is scoped to loucka_reconstruction; use the confirmed
-- fully qualified production schema/table.
SELECT COUNT(*) AS rows_n,
       MIN(dateTime) AS first_epoch,
       MAX(dateTime) AS latest_epoch,
       MIN(`interval`) AS interval_min,
       MAX(`interval`) AS interval_max,
       MIN(usUnits) AS usUnits_min,
       MAX(usUnits) AS usUnits_max,
       SUM(outTemp IS NOT NULL) AS outTemp_n,
       SUM(outHumidity IS NOT NULL) AS outHumidity_n,
       SUM(rain IS NOT NULL) AS rain_n,
       SUM(rainRate IS NOT NULL) AS rainRate_n,
       SUM(inTemp IS NOT NULL) AS inTemp_n,
       SUM(extraTemp1 IS NOT NULL) AS extraTemp1_n,
       SUM(extraTemp2 IS NOT NULL) AS extraTemp2_n,
       SUM(soilTemp1 IS NOT NULL) AS soilTemp1_n,
       SUM(soilMoist1 IS NOT NULL) AS soilMoist1_n,
       SUM(soilad1 IS NOT NULL) AS soilad1_n,
       SUM(radiation IS NOT NULL) AS radiation_n,
       SUM(UV IS NOT NULL) AS UV_n,
       SUM(windSpeed IS NOT NULL) AS windSpeed_n,
       SUM(windDir IS NOT NULL) AS windDir_n,
       SUM(windGust IS NOT NULL) AS windGust_n,
       SUM(windGustDir IS NOT NULL) AS windGustDir_n
FROM `pocasi-loucka.eu`.archive
WHERE dateTime > 1794528000;
