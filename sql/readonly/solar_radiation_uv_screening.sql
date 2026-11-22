-- Read-only archive coverage/range totals for solar channels.
SELECT
  CASE
    WHEN a.dateTime >= 1514764800 AND a.dateTime < 1522540800 THEN '2018_Q1_INTERIM'
    WHEN a.dateTime >= 1609459200 AND a.dateTime < 1640995200 THEN '2021_DIAGNOSTIC_ONLY'
    ELSE 'other'
  END AS scope,
  a.usUnits,
  COUNT(*) AS rows_n,
  SUM(a.radiation IS NOT NULL) AS radiation_n,
  SUM(a.UV IS NOT NULL) AS UV_n,
  SUM(a.radiation < 0) AS negative_radiation,
  SUM(a.UV < 0) AS negative_UV,
  SUM(a.radiation = 0) AS radiation_zero,
  SUM(a.UV = 0) AS UV_zero,
  MAX(a.radiation) AS max_radiation,
  MAX(a.UV) AS max_UV,
  SUM(a.radiation > 1000) AS radiation_gt1000,
  SUM(a.radiation > 1500) AS radiation_gt1500,
  SUM(a.radiation > 2000) AS radiation_gt2000,
  SUM(a.UV > 10) AS UV_gt10,
  SUM(a.UV > 12) AS UV_gt12
FROM `loucka_reconstruction`.archive a
WHERE a.dateTime >= 1235865600 AND a.dateTime < 1793328000
GROUP BY scope, a.usUnits
ORDER BY scope, a.usUnits;

-- Solar elevation screening. The coarse UTC month/hour mask is deliberately broad
-- and only prefilters possible night records. Elevation uses the hour midpoint,
-- approximate village coordinates 49.13 N / 17.75 E, and NOAA fractional-year
-- declination/equation-of-time approximations. Results are triage, not QC rules.
WITH candidates AS (
  SELECT a.dateTime,a.usUnits,a.radiation,a.UV,
    CASE
      WHEN a.dateTime >= 1514764800 AND a.dateTime < 1522540800 THEN '2018_Q1_INTERIM'
      WHEN a.dateTime >= 1609459200 AND a.dateTime < 1640995200 THEN '2021_DIAGNOSTIC_ONLY'
      ELSE 'other'
    END AS scope,
    DAYOFYEAR(DATE_ADD('1970-01-01', INTERVAL a.dateTime SECOND)) AS doy,
    MOD(FLOOR(a.dateTime/3600),24) AS utc_hour,
    2*PI()/365.2422*(DAYOFYEAR(DATE_ADD('1970-01-01', INTERVAL a.dateTime SECOND))-1+(MOD(FLOOR(a.dateTime/3600),24)-12)/24) AS gamma
  FROM `loucka_reconstruction`.archive a
  WHERE a.dateTime >= 1235865600 AND a.dateTime < 1793328000
    AND (a.radiation > 0 OR a.UV > 0)
    AND (
      (MONTH(DATE_ADD('1970-01-01', INTERVAL a.dateTime SECOND)) IN (11,12,1,2)
       AND (MOD(FLOOR(a.dateTime/3600),24) >= 15 OR MOD(FLOOR(a.dateTime/3600),24) <= 8))
      OR (MONTH(DATE_ADD('1970-01-01', INTERVAL a.dateTime SECOND)) IN (3,4,9,10)
       AND (MOD(FLOOR(a.dateTime/3600),24) >= 17 OR MOD(FLOOR(a.dateTime/3600),24) <= 6))
      OR (MONTH(DATE_ADD('1970-01-01', INTERVAL a.dateTime SECOND)) IN (5,6,7,8)
       AND (MOD(FLOOR(a.dateTime/3600),24) >= 19 OR MOD(FLOOR(a.dateTime/3600),24) <= 4))
    )
), solar_terms AS (
  SELECT candidates.*,
    (0.006918-0.399912*COS(gamma)+0.070257*SIN(gamma)-0.006758*COS(2*gamma)
      +0.000907*SIN(2*gamma)-0.002697*COS(3*gamma)+0.00148*SIN(3*gamma)) AS declination,
    229.18*(0.000075+0.001868*COS(gamma)-0.032077*SIN(gamma)
      -0.014615*COS(2*gamma)-0.040849*SIN(2*gamma)) AS equation_minutes
  FROM candidates
), elevations AS (
  SELECT solar_terms.*,
    DEGREES(ASIN(
      SIN(RADIANS(49.13))*SIN(declination)
      + COS(RADIANS(49.13))*COS(declination)*COS(RADIANS(
        (utc_hour*60+30+equation_minutes+4*17.75-720)/4
      ))
    )) AS solar_elevation_deg
  FROM solar_terms
)
SELECT scope,COUNT(*) AS coarse_night_candidates,
  SUM(radiation > 0 AND solar_elevation_deg < -6) AS radiation_positive_below_civil_twilight,
  SUM(radiation > 10 AND solar_elevation_deg < -6) AS radiation_gt10_below_twilight,
  MAX(CASE WHEN radiation > 0 AND solar_elevation_deg < -6 THEN radiation END) AS max_radiation_below_twilight,
  SUM(UV > 0 AND solar_elevation_deg < -6) AS UV_positive_below_civil_twilight,
  SUM(UV > 0.1 AND solar_elevation_deg < -6) AS UV_gt0_1_below_twilight,
  MIN(CASE WHEN radiation > 0 AND solar_elevation_deg < -6 THEN solar_elevation_deg END) AS min_elevation_of_positive_radiation
FROM elevations
GROUP BY scope
ORDER BY scope;

-- High daytime values are listed as specific cases, not labeled errors.
SELECT a.dateTime,a.radiation,a.UV,a.maxSolarRad,a.interval,a.usUnits,
       p.radiation AS production_radiation,p.UV AS production_UV,
       g.radiation AS gw1000_radiation,g.UV AS gw1000_UV
FROM `loucka_reconstruction`.archive a
LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=a.dateTime
WHERE a.dateTime IN (1718531100,1753857300,1787465400,1787465700)
ORDER BY a.dateTime;
