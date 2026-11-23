-- Follow-up to the 26-cohort full-production audit. PINNED cutoff 2026-11-23 06:35 UTC.
-- Every statement is SELECT-only. Execute ONE query at a time on a read replica
-- or off peak. NEVER do INSERT/UPDATE/DELETE/DDL, cutover or auto-approve.
-- The GW1000 archive is a related source, not independent corroboration.
-- Column name equality (soilTemp1 vs soilTemp1) is NOT sensor identity.
-- A. PM2.5 September/October 2024 is NOT a handful of isolated peaks.
SELECT DATE_FORMAT(DATE_ADD('1970-01-01 00:00:00',INTERVAL dateTime SECOND),'%Y-%m') utc_month,
 COUNT(pm25_1) nonnull,ROUND(AVG(pm25_1),1) mean_value,
 SUM(pm25_1>=250) ge250,SUM(pm25_1>=500) ge500,
 SUM(pm25_1>=990) ge990,SUM(ABS(pm25_1-999.9)<0.001) near_999_9
FROM `pocasi-loucka.eu`.archive
WHERE dateTime>=1704067200 AND dateTime<1735689600
GROUP BY utc_month ORDER BY utc_month;

-- B. Same exact GW1000 PM values are NOT independent validation.
SELECT COUNT(*) pm_pairs,SUM(ABS(p.pm25_1-g.pm2_5)<0.001) identical_pairs,
 SUM(p.pm25_1>=500) ge500, SUM(p.pm25_1>=990) ge990,
 SUM(ABS(p.pm25_1-999.9)<0.001) near_999_9
FROM `pocasi-loucka.eu`.archive p
JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=p.dateTime
WHERE p.dateTime>=1704067200 AND p.dateTime<1735689600
 AND p.pm25_1 IS NOT NULL AND g.pm2_5 IS NOT NULL;

-- C. PM >500, grouped only for strict, exact five-minute adjacency.
WITH high AS (
 SELECT dateTime,pm25_1,LAG(dateTime) OVER (ORDER BY dateTime) prev_t
 FROM `pocasi-loucka.eu`.archive
 WHERE dateTime>=1725148800 AND dateTime<1730419200 AND pm25_1>=500
), seg AS (
 SELECT dateTime,pm25_1,
 SUM(CASE WHEN prev_t=dateTime-300 THEN 0 ELSE 1 END) OVER (ORDER BY dateTime) run_id
 FROM high
)
SELECT MIN(dateTime) start_utc,MAX(dateTime) end_utc,COUNT(*) rows_in_run,
 ROUND(AVG(pm25_1),1) mean_pm,ROUND(MAX(pm25_1),1) peak_pm
FROM seg GROUP BY run_id ORDER BY rows_in_run DESC LIMIT 12;

-- D. Black globe temperature constant source placeholder, not proof of sensor activity.
SELECT COUNT(*) n,COUNT(DISTINCT bgt) distinct_bgt,
 MIN(bgt) min_bgt,MAX(bgt) max_bgt,MIN(dateTime) first_ts,MAX(dateTime) last_ts,
 COUNT(DISTINCT outTemp) distinct_outTemp,MIN(outTemp) outdoor_min,MAX(outTemp) outdoor_max
FROM `pocasi-loucka.eu`.archive
WHERE bgt IS NOT NULL AND dateTime<=1795415700;

-- E. GW source soilTemp1-4 -> production soilTemp3-6, NOT same-numbered.
-- Exact copy matched for all comparable samples during 2022-2025.
SELECT YEAR(DATE_ADD('1970-01-01 00:00:00',INTERVAL p.dateTime SECOND)) utc_year,
 SUM(p.soilTemp3 IS NOT NULL AND g.soilTemp1 IS NOT NULL) comparable_g1_p3,
 SUM(p.soilTemp3 IS NOT NULL AND g.soilTemp1 IS NOT NULL AND ABS(p.soilTemp3-g.soilTemp1)<0.15) near_g1_p3,
 SUM(p.soilTemp4 IS NOT NULL AND g.soilTemp2 IS NOT NULL) comparable_g2_p4,
 SUM(p.soilTemp4 IS NOT NULL AND g.soilTemp2 IS NOT NULL AND ABS(p.soilTemp4-g.soilTemp2)<0.15) near_g2_p4,
 SUM(p.soilTemp5 IS NOT NULL AND g.soilTemp3 IS NOT NULL) comparable_g3_p5,
 SUM(p.soilTemp5 IS NOT NULL AND g.soilTemp3 IS NOT NULL AND ABS(p.soilTemp5-g.soilTemp3)<0.15) near_g3_p5,
 SUM(p.soilTemp6 IS NOT NULL AND g.soilTemp4 IS NOT NULL) comparable_g4_p6,
 SUM(p.soilTemp6 IS NOT NULL AND g.soilTemp4 IS NOT NULL AND ABS(p.soilTemp6-g.soilTemp4)<0.15) near_g4_p6
FROM `pocasi-loucka.eu`.archive p
JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=p.dateTime
WHERE p.dateTime>=1661593200 AND p.dateTime<=1795415700
GROUP BY utc_year ORDER BY utc_year;

-- F. 2026 summer soilTemp1 <-20C, but GW1000.soilTemp1 maps to p.soilTemp3;
-- the GW channel must NOT be copied into p.soilTemp1 automatically.
SELECT p.dateTime,p.soilTemp1 as original_soil1,g.soilTemp1 as gw_soil1,
 p.soilTemp3 as original_soil3,p.outTemp
FROM `pocasi-loucka.eu`.archive p
JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=p.dateTime
WHERE p.dateTime>=1767225600 AND p.dateTime<=1795415700
 AND p.soilTemp1 < -20 ORDER BY p.dateTime LIMIT 50;

-- G. Soil flags below -20/-40 are separate from the older -50 threshold.
SELECT YEAR(DATE_ADD('1970-01-01 00:00:00',INTERVAL dateTime SECOND)) utc_year,
 SUM(soilTemp1 < -20) soil1_below_neg20,
 SUM(soilTemp5 < -40) soil5_below_neg40,
 SUM(soilTemp6 < -40) soil6_below_neg40,
 SUM(soilTemp5 < -50 OR soilTemp6 < -50) soil56_below_neg50
FROM `pocasi-loucka.eu`.archive
WHERE dateTime>=1556289900 AND dateTime<=1795415700
GROUP BY utc_year ORDER BY utc_year;

-- H. ExtraTemp2 in 2022 can be humidity-like; its unit/meaning may be
-- different from 2023-2025, and 14 extreme 2024 values are 822.4.
SELECT YEAR(DATE_ADD('1970-01-01 00:00:00',INTERVAL dateTime SECOND)) utc_year,
 COUNT(extraTemp2) available,MIN(dateTime) first_time,MAX(dateTime) last_time,
 ROUND(MIN(extraTemp2),2) min_extra2,ROUND(MAX(extraTemp2),2) max_extra2,
 SUM(extraTemp2>60) over60,SUM(extraTemp2>100) over100
FROM `pocasi-loucka.eu`.archive
WHERE dateTime>=1661990400 AND dateTime<=1795415700
GROUP BY utc_year ORDER BY utc_year;

-- I. Sunshine fields have unclear units/aggregation; NEVER mark as
-- invalid simply because values exceed 300, before driver/skin review.
SELECT COUNT(sunshineDur) sunshineDur_nonnull,
 SUM(sunshineDur>60*`interval`) sunshineDur_over_interval_seconds,
 COUNT(sunshine_time) sunshine_time_nonnull,
 SUM(sunshine_time>60*`interval`) sunshine_time_over_interval_seconds,
 SUM(rainDur>60*`interval`) rainDur_over_interval_seconds
FROM `pocasi-loucka.eu`.archive
WHERE dateTime>=1767225600 AND dateTime<=1795415700;

-- J. March 8 2026 alternate data processing began. Field differences
-- are NOT sufficient to decide which calibration is physically correct.
SELECT COUNT(*) paired,
 MIN(CASE WHEN ABS(p.barometer-g.barometer)>0.5 THEN p.dateTime END) baro_first_gt05,
 MIN(CASE WHEN ABS(p.windSpeed-g.windSpeed)>1 THEN p.dateTime END) wind_first_gt1,
 MIN(CASE WHEN ABS(p.soilTemp5-g.soilTemp3)>0.15 THEN p.dateTime END) soil5_first_gt015,
 MIN(CASE WHEN ABS(p.pm25_1-g.pm2_5)>1 THEN p.dateTime END) pm_first_gt1
FROM `pocasi-loucka.eu`.archive p
JOIN `pocasi-loucka.eu_GW1000`.archive g ON p.dateTime=g.dateTime
WHERE p.dateTime>=1772323200 AND p.dateTime<=1795415700;

-- K. GW historical mirror ends before current production; do not mistake
-- an absent independent mirror for loss of the production measurements.
SELECT 'production' as source,COUNT(*) n,MIN(dateTime) first_ts,MAX(dateTime) last_ts
FROM `pocasi-loucka.eu`.archive WHERE dateTime<=1795415700
UNION ALL
SELECT 'GW1000 historical mirror',COUNT(*),MIN(dateTime),MAX(dateTime)
FROM `pocasi-loucka.eu_GW1000`.archive;

-- L. 2026 lightning_distance remains 34 km in a narrow subset with
-- no coincident positive strikes; may legitimately represent *last* event.
SELECT COUNT(*) nonnull,COUNT(DISTINCT lightning_distance) distinct_distance,
 MIN(lightning_distance) min_distance,MAX(lightning_distance) max_distance,
 SUM(lightning_strike_count>0) coincident_strikes,
 MIN(dateTime) first_ts,MAX(dateTime) last_ts
FROM `pocasi-loucka.eu`.archive
WHERE dateTime>=1767225600 AND dateTime<=1795415700
 AND lightning_distance IS NOT NULL;
