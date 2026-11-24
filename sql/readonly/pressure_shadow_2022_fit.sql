-- READ-ONLY diagnostic fit; no data writes.
-- Frozen training: 2020 only; 2021 selection; 2022 prospective local test.
WITH base AS (
 SELECT dateTime, YEAR(DATE_ADD('1970-01-01',INTERVAL dateTime SECOND)) AS yr,
 outTemp AS t,
 pressure-barometer*EXP(-9.80665*425/(287.05*(outTemp+273.15))) AS residual
 FROM loucka_reconstruction.archive
 WHERE dateTime>=1577836800 AND dateTime<1660953600
 AND usUnits=16 AND pressure BETWEEN 900 AND 1050
 AND barometer BETWEEN 930 AND 1080 AND outTemp BETWEEN -40 AND 45
), model AS (
 SELECT COUNT(*) AS training_n, AVG(residual) AS offset_hpa, AVG(t) AS mean_t,
 (AVG(t*residual)-AVG(t)*AVG(residual))/NULLIF(AVG(t*t)-AVG(t)*AVG(t),0) AS slope
 FROM base WHERE yr=2020
), errors AS (
 SELECT yr,residual,residual-offset_hpa AS constant_error,
 residual-offset_hpa-slope*(t-mean_t) AS temp_error,
 training_n,offset_hpa,mean_t,slope FROM base CROSS JOIN model WHERE yr>=2021
)
SELECT yr,COUNT(*) AS n,MAX(training_n) AS training_n,
 MAX(offset_hpa) AS offset_hpa,MAX(mean_t) AS mean_t,MAX(slope) AS slope,
 AVG(ABS(residual)) AS physical_mae,AVG(ABS(constant_error)) AS constant_mae,
 AVG(ABS(temp_error)) AS temp_mae
FROM errors GROUP BY yr ORDER BY yr;
