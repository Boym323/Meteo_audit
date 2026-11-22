-- Cumulus -> WeeWX transition forensic screen, 2026-11-22.
-- All SELECTs are read-only; run ONE statement at a time in Weather MCP.
-- UTC Unix seconds; original WeeWX interval end timestamps are unchanged.
-- This is a data-pipeline fingerprint, NOT proof of original recording software.
--
-- A: first technical markers. 'pressure' missing until 2014-07-03 in old_weewx
-- even though weewx_WH1080 has pressure from 2009: different archive schemas/
-- import paths do not establish which software originally logged the sample.
SELECT 'old_weewx' AS source_archive,
  MIN(CASE WHEN pressure IS NOT NULL THEN dateTime END) AS first_pressure_utc,
  MIN(CASE WHEN MOD(dateTime,60)<>0 THEN dateTime END) AS first_subminute_utc,
  MIN(CASE WHEN MOD(dateTime,300)=1 THEN dateTime END) AS first_slot_plus_1sec_utc,
  MIN(CASE WHEN `interval`<>5 THEN dateTime END) AS first_nonfive_interval_utc
FROM `old_weewx`.`archive` WHERE dateTime<1514764800
UNION ALL
SELECT 'weewx_WH1080',
  MIN(CASE WHEN pressure IS NOT NULL THEN dateTime END),
  MIN(CASE WHEN MOD(dateTime,60)<>0 THEN dateTime END),
  MIN(CASE WHEN MOD(dateTime,300)=1 THEN dateTime END),
  MIN(CASE WHEN `interval`<>5 THEN dateTime END)
FROM `weewx_WH1080`.`archive` WHERE dateTime<1514764800;

-- B: same gap visible independently in imported/source and live target epochs.
-- The ~12.76-day gap is not proof of a specific program switch.
SELECT 'old_weewx' AS source_archive,
  MAX(CASE WHEN dateTime<1404406800 THEN dateTime END) AS last_before_utc,
  MIN(CASE WHEN dateTime>=1404406800 THEN dateTime END) AS first_after_utc,
  COUNT(CASE WHEN dateTime>=1403222400 AND dateTime<1404406800 THEN 1 END) AS may_june_tail_rows
FROM `old_weewx`.`archive`
WHERE dateTime>=1403222400 AND dateTime<1405296000
UNION ALL
SELECT 'weewx_WH1080',
  MAX(CASE WHEN dateTime<1404406800 THEN dateTime END),
  MIN(CASE WHEN dateTime>=1404406800 THEN dateTime END),
  COUNT(CASE WHEN dateTime>=1403222400 AND dateTime<1404406800 THEN 1 END)
FROM `weewx_WH1080`.`archive`
WHERE dateTime>=1403222400 AND dateTime<1405296000
UNION ALL
SELECT 'pocasi-loucka.eu',
  MAX(CASE WHEN dateTime<1404406800 THEN dateTime END),
  MIN(CASE WHEN dateTime>=1404406800 THEN dateTime END),
  COUNT(CASE WHEN dateTime>=1403222400 AND dateTime<1404406800 THEN 1 END)
FROM `pocasi-loucka.eu`.`archive`
WHERE dateTime>=1403222400 AND dateTime<1405296000;

-- C: wind numeric scale. Nearest 5-minute slot is a bounded diagnostic,
-- not proof of identical physical observation or permission to rewrite it.
WITH periods AS (
  SELECT '2013_MAR' AS window_name,1362096000 AS start_utc,1364774400 AS end_utc
  UNION ALL SELECT '2013_MAY_JUL',1367366400,1375315200
  UNION ALL SELECT '2014_MAY_JUN20',1398902400,1403304600
  UNION ALL SELECT '2014_JUL3_JUL31',1404406800,1406851200
)
SELECT k.window_name,COUNT(*) AS source_rows,
  SUM(p.dateTime IS NOT NULL) AS joined_snapped_target,
  SUM(s.windSpeed>0 AND p.windSpeed IS NOT NULL) AS positive_speed_pairs,
  SUM(s.windSpeed>0 AND ABS(p.windSpeed-s.windSpeed)<0.1) AS numeric_equal,
  SUM(s.windSpeed>0 AND ABS(p.windSpeed-3.6*s.windSpeed)<0.1) AS numeric_factor_3_6,
  SUM(s.pressure IS NOT NULL) AS source_pressure_present,
  SUM(MOD(s.dateTime,60)<>0) AS source_subminute_rows
FROM periods k
JOIN `old_weewx`.`archive` s ON s.dateTime>=k.start_utc AND s.dateTime<k.end_utc
LEFT JOIN `pocasi-loucka.eu`.`archive` p
  ON p.dateTime=FLOOR((s.dateTime+150)/300)*300
GROUP BY k.window_name ORDER BY k.window_name;

-- D: April 2013 wind ratio changed across the Apr 6–12 archive gap.
-- This is a numeric-unit epoch boundary, not evidence of WeeWX installation.
SELECT
  MAX(CASE WHEN ABS(p.windSpeed-s.windSpeed)<0.1 THEN s.dateTime END)
     AS last_numeric_1_to_1_utc,
  MIN(CASE WHEN ABS(p.windSpeed-3.6*s.windSpeed)<0.1 THEN s.dateTime END)
     AS first_numeric_factor_3_6_utc,
  SUM(ABS(p.windSpeed-s.windSpeed)<0.1) AS same_numeric_rows,
  SUM(ABS(p.windSpeed-3.6*s.windSpeed)<0.1) AS factor_3_6_rows
FROM `old_weewx`.`archive` s
JOIN `pocasi-loucka.eu`.`archive` p
  ON p.dateTime=FLOOR((s.dateTime+150)/300)*300
WHERE s.dateTime>=1364774400 AND s.dateTime<1367366400
  AND s.windSpeed>0 AND p.windSpeed IS NOT NULL;

-- E: transition day profiles without reliance on server local timezone.
SELECT FLOOR(dateTime/86400) AS utc_day_index,COUNT(*) AS rows,
  SUM(pressure IS NOT NULL) AS source_pressure_present,
  SUM(MOD(dateTime,60)<>0) AS with_second_offset,
  SUM(`interval`<>5) AS source_nonfive,
  MIN(dateTime) AS min_epoch,MAX(dateTime) AS max_epoch
FROM `old_weewx`.`archive`
WHERE dateTime>=1403827200 AND dateTime<1405382400
GROUP BY FLOOR(dateTime/86400) ORDER BY utc_day_index;
