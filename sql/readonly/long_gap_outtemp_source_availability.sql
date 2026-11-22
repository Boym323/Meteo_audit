-- Read-only source availability and zero-value triage for the five >=7-day gaps.
-- Values of zero are counted as a signature only; they are not auto-classified invalid.
SELECT 1 AS gap_id, COUNT(*) AS shared_timestamps,
       SUM(a.outTemp IS NOT NULL) AS old_outTemp_n,
       SUM(b.outTemp IS NOT NULL) AS wh1080_outTemp_n,
       SUM(a.outTemp IS NULL AND b.outTemp IS NOT NULL) AS old_null_wh_value,
       SUM(a.outTemp IS NOT NULL AND b.outTemp IS NULL) AS old_value_wh_null,
       SUM(a.outTemp IS NOT NULL AND b.outTemp IS NOT NULL AND a.outTemp=b.outTemp) AS both_value_equal,
       SUM(a.outTemp IS NOT NULL AND b.outTemp IS NOT NULL AND a.outTemp<>b.outTemp) AS both_value_different,
       SUM(b.outTemp=0) AS wh_zero_n,
       SUM(b.outTemp<0) AS wh_negative_n,
       SUM(b.outTemp>0) AS wh_positive_n,
       COUNT(DISTINCT b.outTemp) AS wh_distinct,
       MIN(b.outTemp) AS wh_min, MAX(b.outTemp) AS wh_max
FROM `old_weewx`.`archive` a JOIN `weewx_WH1080`.`archive` b USING(dateTime)
WHERE a.dateTime BETWEEN 1313438700 AND 1330593900
UNION ALL
SELECT 2, COUNT(*), SUM(a.outTemp IS NOT NULL), SUM(b.outTemp IS NOT NULL),
       SUM(a.outTemp IS NULL AND b.outTemp IS NOT NULL), SUM(a.outTemp IS NOT NULL AND b.outTemp IS NULL),
       SUM(a.outTemp IS NOT NULL AND b.outTemp IS NOT NULL AND a.outTemp=b.outTemp),
       SUM(a.outTemp IS NOT NULL AND b.outTemp IS NOT NULL AND a.outTemp<>b.outTemp),
       SUM(b.outTemp=0), SUM(b.outTemp<0), SUM(b.outTemp>0), COUNT(DISTINCT b.outTemp), MIN(b.outTemp), MAX(b.outTemp)
FROM `old_weewx`.`archive` a JOIN `weewx_WH1080`.`archive` b USING(dateTime)
WHERE a.dateTime BETWEEN 1453156500 AND 1454764200
UNION ALL
SELECT 3, COUNT(*), SUM(a.outTemp IS NOT NULL), SUM(b.outTemp IS NOT NULL),
       SUM(a.outTemp IS NULL AND b.outTemp IS NOT NULL), SUM(a.outTemp IS NOT NULL AND b.outTemp IS NULL),
       SUM(a.outTemp IS NOT NULL AND b.outTemp IS NOT NULL AND a.outTemp=b.outTemp),
       SUM(a.outTemp IS NOT NULL AND b.outTemp IS NOT NULL AND a.outTemp<>b.outTemp),
       SUM(b.outTemp=0), SUM(b.outTemp<0), SUM(b.outTemp>0), COUNT(DISTINCT b.outTemp), MIN(b.outTemp), MAX(b.outTemp)
FROM `old_weewx`.`archive` a JOIN `weewx_WH1080`.`archive` b USING(dateTime)
WHERE a.dateTime BETWEEN 1494564600 AND 1496007900
UNION ALL
SELECT 4, COUNT(*), SUM(a.outTemp IS NOT NULL), SUM(b.outTemp IS NOT NULL),
       SUM(a.outTemp IS NULL AND b.outTemp IS NOT NULL), SUM(a.outTemp IS NOT NULL AND b.outTemp IS NULL),
       SUM(a.outTemp IS NOT NULL AND b.outTemp IS NOT NULL AND a.outTemp=b.outTemp),
       SUM(a.outTemp IS NOT NULL AND b.outTemp IS NOT NULL AND a.outTemp<>b.outTemp),
       SUM(b.outTemp=0), SUM(b.outTemp<0), SUM(b.outTemp>0), COUNT(DISTINCT b.outTemp), MIN(b.outTemp), MAX(b.outTemp)
FROM `old_weewx`.`archive` a JOIN `weewx_WH1080`.`archive` b USING(dateTime)
WHERE a.dateTime BETWEEN 1403304600 AND 1404406800
UNION ALL
SELECT 5, COUNT(*), SUM(a.outTemp IS NOT NULL), SUM(b.outTemp IS NOT NULL),
       SUM(a.outTemp IS NULL AND b.outTemp IS NOT NULL), SUM(a.outTemp IS NOT NULL AND b.outTemp IS NULL),
       SUM(a.outTemp IS NOT NULL AND b.outTemp IS NOT NULL AND a.outTemp=b.outTemp),
       SUM(a.outTemp IS NOT NULL AND b.outTemp IS NOT NULL AND a.outTemp<>b.outTemp),
       SUM(b.outTemp=0), SUM(b.outTemp<0), SUM(b.outTemp>0), COUNT(DISTINCT b.outTemp), MIN(b.outTemp), MAX(b.outTemp)
FROM `old_weewx`.`archive` a JOIN `weewx_WH1080`.`archive` b USING(dateTime)
WHERE a.dateTime BETWEEN 1483966800 AND 1484645400;

-- Other-channel context for the three zero-heavy windows. Distinct counts show
-- whether the archive rows carry variation in channels while outTemp is zero;
-- this is still not proof that outTemp=0 is invalid.
SELECT 2 AS gap_id, COUNT(*) AS rows_in_window,
       SUM(outHumidity IS NOT NULL) AS rh_nonnull, COUNT(DISTINCT outHumidity) AS rh_distinct,
       SUM(rain IS NOT NULL) AS rain_nonnull, COUNT(DISTINCT rain) AS rain_distinct,
       SUM(rainRate IS NOT NULL) AS rainRate_nonnull, COUNT(DISTINCT rainRate) AS rainRate_distinct,
       SUM(windSpeed IS NOT NULL) AS wind_nonnull, COUNT(DISTINCT windSpeed) AS wind_distinct,
       SUM(barometer IS NOT NULL) AS pressure_nonnull, COUNT(DISTINCT barometer) AS pressure_distinct
FROM `weewx_WH1080`.`archive` WHERE dateTime BETWEEN 1453156500 AND 1454764200
UNION ALL
SELECT 3, COUNT(*), SUM(outHumidity IS NOT NULL), COUNT(DISTINCT outHumidity),
       SUM(rain IS NOT NULL), COUNT(DISTINCT rain), SUM(rainRate IS NOT NULL), COUNT(DISTINCT rainRate),
       SUM(windSpeed IS NOT NULL), COUNT(DISTINCT windSpeed), SUM(barometer IS NOT NULL), COUNT(DISTINCT barometer)
FROM `weewx_WH1080`.`archive` WHERE dateTime BETWEEN 1494564600 AND 1496007900
UNION ALL
SELECT 5, COUNT(*), SUM(outHumidity IS NOT NULL), COUNT(DISTINCT outHumidity),
       SUM(rain IS NOT NULL), COUNT(DISTINCT rain), SUM(rainRate IS NOT NULL), COUNT(DISTINCT rainRate),
       SUM(windSpeed IS NOT NULL), COUNT(DISTINCT windSpeed), SUM(barometer IS NOT NULL), COUNT(DISTINCT barometer)
FROM `weewx_WH1080`.`archive` WHERE dateTime BETWEEN 1483966800 AND 1484645400;
