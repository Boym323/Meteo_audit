-- Read-only U1 current snapshot. Query through Weather MCP against loucka_reconstruction.
-- UTC year is selected by explicit epoch boundaries because MariaDB is SYSTEM/CET.
SELECT CASE
  WHEN dateTime >= 1230768000 AND dateTime < 1262304000 THEN 2009
  WHEN dateTime >= 1262304000 AND dateTime < 1293840000 THEN 2010
  WHEN dateTime >= 1293840000 AND dateTime < 1325376000 THEN 2011
  WHEN dateTime >= 1325376000 AND dateTime < 1356998400 THEN 2012
  WHEN dateTime >= 1356998400 AND dateTime < 1388534400 THEN 2013
  WHEN dateTime >= 1388534400 AND dateTime < 1420070400 THEN 2014
  WHEN dateTime >= 1420070400 AND dateTime < 1451606400 THEN 2015
  WHEN dateTime >= 1451606400 AND dateTime < 1483228800 THEN 2016
  WHEN dateTime >= 1483228800 AND dateTime < 1514764800 THEN 2017
  WHEN dateTime >= 1514764800 AND dateTime < 1546300800 THEN 2018
  WHEN dateTime >= 1546300800 AND dateTime < 1577836800 THEN 2019
  WHEN dateTime >= 1577836800 AND dateTime < 1609459200 THEN 2020
  WHEN dateTime >= 1609459200 AND dateTime < 1640995200 THEN 2021
  WHEN dateTime >= 1640995200 AND dateTime < 1672531200 THEN 2022
  WHEN dateTime >= 1672531200 AND dateTime < 1704067200 THEN 2023
  WHEN dateTime >= 1704067200 AND dateTime < 1735689600 THEN 2024
  WHEN dateTime >= 1735689600 AND dateTime < 1767225600 THEN 2025
  WHEN dateTime >= 1767225600 AND dateTime < 1798761600 THEN 2026
  ELSE NULL END AS utc_year, COUNT(*) AS row_count, MIN(dateTime) AS first_epoch,
       MAX(dateTime) AS last_epoch,
       SUM(outTemp IS NULL) AS null_outTemp,
       SUM(outHumidity IS NULL) AS null_outHumidity,
       SUM(rain IS NULL) AS null_rain,
       SUM(rainRate IS NULL) AS null_rainRate,
       SUM(windSpeed IS NULL) AS null_windSpeed,
       SUM(windGust IS NULL) AS null_windGust,
       SUM(windDir IS NULL) AS null_windDir,
       SUM(barometer IS NULL) AS null_barometer,
       SUM(pressure IS NULL) AS null_pressure,
       SUM(radiation IS NULL) AS null_radiation,
       SUM(UV IS NULL) AS null_UV,
       SUM(dewpoint IS NULL) AS null_dewpoint,
       SUM(inTemp IS NULL) AS null_inTemp,
       SUM(inHumidity IS NULL) AS null_inHumidity,
       SUM(altimeter IS NULL) AS null_altimeter,
       SUM(windrun IS NULL) AS null_windrun,
       SUM(sunshineDur IS NULL) AS null_sunshineDur,
       SUM(lightning_distance IS NULL) AS null_lightning_distance
FROM archive GROUP BY utc_year ORDER BY utc_year;

-- Interval/unit epoch profile (does not assert observed cadence).
SELECT CASE
  WHEN dateTime >= 1230768000 AND dateTime < 1262304000 THEN 2009
  WHEN dateTime >= 1262304000 AND dateTime < 1293840000 THEN 2010
  WHEN dateTime >= 1293840000 AND dateTime < 1325376000 THEN 2011
  WHEN dateTime >= 1325376000 AND dateTime < 1356998400 THEN 2012
  WHEN dateTime >= 1356998400 AND dateTime < 1388534400 THEN 2013
  WHEN dateTime >= 1388534400 AND dateTime < 1420070400 THEN 2014
  WHEN dateTime >= 1420070400 AND dateTime < 1451606400 THEN 2015
  WHEN dateTime >= 1451606400 AND dateTime < 1483228800 THEN 2016
  WHEN dateTime >= 1483228800 AND dateTime < 1514764800 THEN 2017
  WHEN dateTime >= 1514764800 AND dateTime < 1546300800 THEN 2018
  WHEN dateTime >= 1546300800 AND dateTime < 1577836800 THEN 2019
  WHEN dateTime >= 1577836800 AND dateTime < 1609459200 THEN 2020
  WHEN dateTime >= 1609459200 AND dateTime < 1640995200 THEN 2021
  WHEN dateTime >= 1640995200 AND dateTime < 1672531200 THEN 2022
  WHEN dateTime >= 1672531200 AND dateTime < 1704067200 THEN 2023
  WHEN dateTime >= 1704067200 AND dateTime < 1735689600 THEN 2024
  WHEN dateTime >= 1735689600 AND dateTime < 1767225600 THEN 2025
  WHEN dateTime >= 1767225600 AND dateTime < 1798761600 THEN 2026
  ELSE NULL END AS utc_year, `interval` AS interval_minutes, usUnits, COUNT(*) AS row_count,
       MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch
FROM archive GROUP BY utc_year, `interval`, usUnits ORDER BY utc_year, interval_minutes, usUnits;

-- Candidate discontinuity edges: variable interval-aware screen, not an inferred number of lost observations.
WITH a AS (SELECT dateTime, `interval` AS step_min,
                  LAG(dateTime) OVER (ORDER BY dateTime) AS prev_ts,
                  LAG(`interval`) OVER (ORDER BY dateTime) AS prev_step
           FROM archive),
g AS (SELECT dateTime, dateTime-prev_ts AS delta_seconds, step_min, prev_step FROM a
      WHERE prev_ts IS NOT NULL AND dateTime-prev_ts > LEAST(step_min,prev_step)*60)
SELECT CASE
  WHEN dateTime >= 1230768000 AND dateTime < 1262304000 THEN 2009
  WHEN dateTime >= 1262304000 AND dateTime < 1293840000 THEN 2010
  WHEN dateTime >= 1293840000 AND dateTime < 1325376000 THEN 2011
  WHEN dateTime >= 1325376000 AND dateTime < 1356998400 THEN 2012
  WHEN dateTime >= 1356998400 AND dateTime < 1388534400 THEN 2013
  WHEN dateTime >= 1388534400 AND dateTime < 1420070400 THEN 2014
  WHEN dateTime >= 1420070400 AND dateTime < 1451606400 THEN 2015
  WHEN dateTime >= 1451606400 AND dateTime < 1483228800 THEN 2016
  WHEN dateTime >= 1483228800 AND dateTime < 1514764800 THEN 2017
  WHEN dateTime >= 1514764800 AND dateTime < 1546300800 THEN 2018
  WHEN dateTime >= 1546300800 AND dateTime < 1577836800 THEN 2019
  WHEN dateTime >= 1577836800 AND dateTime < 1609459200 THEN 2020
  WHEN dateTime >= 1609459200 AND dateTime < 1640995200 THEN 2021
  WHEN dateTime >= 1640995200 AND dateTime < 1672531200 THEN 2022
  WHEN dateTime >= 1672531200 AND dateTime < 1704067200 THEN 2023
  WHEN dateTime >= 1704067200 AND dateTime < 1735689600 THEN 2024
  WHEN dateTime >= 1735689600 AND dateTime < 1767225600 THEN 2025
  WHEN dateTime >= 1767225600 AND dateTime < 1798761600 THEN 2026
  ELSE NULL END AS utc_year, COUNT(*) AS gap_edges,
       SUM(delta_seconds>3600) AS gaps_over_1h, SUM(delta_seconds>86400) AS gaps_over_24h,
       MAX(delta_seconds) AS max_gap_seconds,
       SUM(delta_seconds>prev_step*60 AND delta_seconds>step_min*60) AS exceeds_both_metadata_steps
FROM g GROUP BY utc_year ORDER BY utc_year;

-- Audit event state totals; reason/source labels are claims and require source-level checks.
SELECT state, variable, COUNT(*) AS field_events, COUNT(DISTINCT target_time) AS target_timestamps,
       MIN(id) AS first_id, MAX(id) AS last_id
FROM reconstruction_changes GROUP BY state, variable ORDER BY state, variable;
