-- Complete reconstruction QA, read-only, 22 Nov 2026.
-- Execute ONE SELECT at a time. All times are UTC Unix seconds. Avoid
-- YEAR(FROM_UNIXTIME(dateTime)) if the server session timezone is not UTC.
-- NO DML/DDL, no automatic historical correction or production cutover.
-- Fixed cutoff: 2026-11-22 20:20:00 UTC = 1795378800.
-- See reconstruction_v1_all_80_columns_parity.sql for exhaustive 79-field
-- NULL-safe comparisons; that file already exists in the repository.

-- 1. Consistent source/target row identity at a fixed checkpoint.
SELECT
 (SELECT COUNT(*) FROM `pocasi-loucka.eu`.archive
  WHERE dateTime<=1795378800) AS source_rows,
 (SELECT COUNT(*) FROM loucka_reconstruction.archive
  WHERE dateTime<=1795378800) AS reconstruction_rows,
 (SELECT COUNT(*) FROM `pocasi-loucka.eu`.archive p
  LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=p.dateTime
  WHERE p.dateTime<=1795378800 AND r.dateTime IS NULL) AS missing_source_rows,
 (SELECT COUNT(*) FROM loucka_reconstruction.archive r
  LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=r.dateTime
  WHERE r.dateTime<=1795378800 AND p.dateTime IS NULL) AS target_only_rows;

-- 2. Total four known differences. Remaining 75 value columns and dateTime
-- are verified exhaustively in the separately referenced 80-column SQL.
SELECT COUNT(*) AS common_rows,
 SUM(NOT(p.outTemp <=> r.outTemp)) AS outtemp_diff,
 SUM(NOT(p.outHumidity <=> r.outHumidity)) AS outhumidity_diff,
 SUM(NOT(p.rain <=> r.rain)) AS rain_diff,
 SUM(NOT(p.rainRate <=> r.rainRate)) AS rainrate_diff
FROM `pocasi-loucka.eu`.archive p
JOIN loucka_reconstruction.archive r ON r.dateTime=p.dateTime
WHERE p.dateTime<=1795378800;

-- 3. Yearly time/field coverage; count alone is not a coverage guarantee
-- for 2026 because multiple original timestamps may map to one 5-min slot.
SELECT YEAR(DATE_ADD('1970-01-01 00:00:00',
 INTERVAL dateTime SECOND)) AS utc_year,
 COUNT(*) AS rows_present,
 SUM(outTemp IS NULL) AS missing_outtemp_in_existing_rows,
 SUM(outHumidity IS NULL) AS missing_outhumidity_in_existing_rows,
 SUM(rain IS NULL) AS missing_rain_in_existing_rows,
 SUM(MOD(dateTime,300)<>0) AS offgrid_rows,
 SUM(`interval`<>5) AS non5_intervals
FROM loucka_reconstruction.archive
WHERE dateTime<=1795378800
GROUP BY utc_year ORDER BY utc_year;

-- 4. Longest actual gaps (needs scan and window sort; schedule off-peak).
WITH gaps AS (
 SELECT dateTime,LAG(dateTime) OVER (ORDER BY dateTime) AS prev_ts
 FROM loucka_reconstruction.archive WHERE dateTime<=1795378800
)
SELECT prev_ts,dateTime AS next_ts,(dateTime-prev_ts) AS gap_seconds,
 FLOOR((dateTime-prev_ts)/300)-1 AS nominal_missing_5min_slots
FROM gaps
WHERE dateTime-prev_ts>=86400
ORDER BY gap_seconds DESC LIMIT 50;

-- 5. Original legacy data inside missing time ranges:
-- 2016/2017 old source provides pressure/indoor values but almost no outdoor.
SELECT '2016_gap' AS cohort,COUNT(*) AS legacy_rows,
 SUM(outTemp IS NOT NULL) AS outdoor_temp,
 SUM(outHumidity IS NOT NULL) AS outdoor_rh,
 SUM(pressure BETWEEN 800 AND 1100) AS plausible_pressure,
 SUM(inTemp IS NOT NULL) AS indoor_temp,
 SUM(MOD(dateTime,300)=0) AS on_exact_five_min_grid
FROM old_weewx.archive
WHERE dateTime>1453156500 AND dateTime<1454764200
UNION ALL
SELECT '2017_jan',COUNT(*),SUM(outTemp IS NOT NULL),
 SUM(outHumidity IS NOT NULL),SUM(pressure BETWEEN 800 AND 1100),
 SUM(inTemp IS NOT NULL),SUM(MOD(dateTime,300)=0)
FROM old_weewx.archive
WHERE dateTime>1483966800 AND dateTime<1484645400
UNION ALL
SELECT '2017_may',COUNT(*),SUM(outTemp IS NOT NULL),
 SUM(outHumidity IS NOT NULL),SUM(pressure BETWEEN 800 AND 1100),
 SUM(inTemp IS NOT NULL),SUM(MOD(dateTime,300)=0)
FROM old_weewx.archive
WHERE dateTime>1494564600 AND dateTime<1496007900;

-- 6. Lightning mapper: Unix epoch values in *_disturber_count,
-- noise_count repeating strike_count. Do not treat as valid counts.
SELECT COUNT(*) AS disturber_nonnull,
 SUM(r.lightning_disturber_count>1000000000) AS timestamp_like_disturbers,
 SUM(p.lightning_disturber_count <=> r.lightning_disturber_count)
  AS unchanged_from_production,
 SUM(r.lightning_noise_count IS NOT NULL) AS noise_nonnull,
 SUM(r.lightning_noise_count IS NOT NULL AND
  r.lightning_noise_count <=> r.lightning_strike_count)
  AS noise_identical_to_strike
FROM loucka_reconstruction.archive r
JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=r.dateTime
WHERE r.dateTime>=1767225600 AND r.dateTime<=1795378800;

-- 7. 2026 nominal five-minute slot collisions; do not mutate timestamps.
WITH slots AS (
 SELECT FLOOR((dateTime+150)/300) AS nominal_slot,COUNT(*) AS n
 FROM loucka_reconstruction.archive
 WHERE dateTime>=1767225600 AND dateTime<=1795378800
 GROUP BY FLOOR((dateTime+150)/300)
)
SELECT COUNT(*) AS occupied_slots,
 SUM(n>1) AS slots_with_collision,
 SUM(IF(n>1,n-1,0)) AS duplicate_nominal_members,
 (FLOOR(1795378800/300)-FLOOR(1767225600/300)+1)
 - COUNT(*) AS empty_nominal_slots
FROM slots;

-- 8. July 2021 source and reconstruction interval rainfall sums.
-- NOT an independent validation of 42.567mm; 146 audit NULL vs actual zero.
SELECT 'production' AS dataset,COUNT(*) AS n,
 ROUND(10*SUM(rain),3) AS july_rain_mm
FROM `pocasi-loucka.eu`.archive
WHERE dateTime>1625090400 AND dateTime<=1627768800
UNION ALL
SELECT 'reconstruction',COUNT(*),ROUND(10*SUM(rain),3)
FROM loucka_reconstruction.archive
WHERE dateTime>1625090400 AND dateTime<=1627768800;

-- 9. Audit/actual mismatch by rain: history.state='reverted' is NOT
-- an active proposed postimage; inspect only latest applied event.
WITH last_event AS (
 SELECT h.target_time,h.new_value,h.state,h.reason,
 ROW_NUMBER() OVER (PARTITION BY h.target_time
  ORDER BY COALESCE(h.applied_at,h.created_at) DESC,h.id DESC) AS rn
 FROM loucka_reconstruction.reconstruction_changes h
 WHERE BINARY h.variable=BINARY 'rain'
)
SELECT COUNT(*) AS applied_mismatch,
 SUM(l.new_value IS NULL AND r.rain=0) AS expected_null_actual_zero,
 MIN(l.target_time) AS first_ts,MAX(l.target_time) AS last_ts
FROM last_event l
JOIN loucka_reconstruction.archive r ON r.dateTime=l.target_time
WHERE l.rn=1 AND l.state='applied'
 AND NOT(r.rain <=> l.new_value);

-- 10. April 2022 diagnostic-only dewpoint screening.
-- Magnus constants below are a screening approximation, NOT verified
-- historical WeeWX configuration. Never automatically overwrite dewpoint.
WITH latest AS (
 SELECT target_time,old_value,new_value,
 ROW_NUMBER() OVER (PARTITION BY target_time
 ORDER BY applied_at DESC,id DESC) rn
 FROM loucka_reconstruction.reconstruction_changes
 WHERE variable='outHumidity' AND state='applied'
 AND target_time>=1648771200 AND target_time<1651363200
),basis AS (
 SELECT a.dateTime,a.outTemp AS t,a.outHumidity AS rh,
 a.dewpoint AS dp,l.old_value AS old_rh,l.new_value AS new_rh
 FROM latest l JOIN loucka_reconstruction.archive a ON a.dateTime=l.target_time
 WHERE l.rn=1 AND a.usUnits=16 AND a.outTemp IS NOT NULL
 AND a.outHumidity BETWEEN 1 AND 100 AND l.old_value BETWEEN 1 AND 100
 AND a.dewpoint IS NOT NULL
),calc AS (
 SELECT *,
 243.04*(LN(rh/100)+17.625*t/(243.04+t))/
 (17.625-(LN(rh/100)+17.625*t/(243.04+t))) AS expected_current,
 243.04*(LN(old_rh/100)+17.625*t/(243.04+t))/
 (17.625-(LN(old_rh/100)+17.625*t/(243.04+t))) AS expected_old
 FROM basis
)
SELECT COUNT(*) AS comparable,
 SUM(rh <=> new_rh) AS rh_matches_latest_applied,
 SUM(ABS(dp-expected_current)>2) AS discrepancy_over_2_c,
 SUM(ABS(dp-expected_current)>2 AND ABS(dp-expected_old)<=0.1)
  AS stored_dewpoint_matches_old_rh,
 MAX(ABS(dp-expected_current)) AS max_delta_c
FROM calc;

-- 11. Batch-level hashes: row-level verified postimage hash is NULL by
-- schema/use; hashes are compared at verification batch level only.
SELECT COUNT(*) AS batches,SUM(row_count) AS verified_rows,
 SUM(source_payload_sha256=verified_target_postimage_sha256)
  AS batches_with_equal_hashes,
 SUM(source_payload_sha256<>verified_target_postimage_sha256)
  AS batches_with_nonmatching_hashes
FROM loucka_reconstruction.archive_sync_verification;

-- 12. Physical high-threshold anomalies (not automatic deletions).
SELECT SUM(rainRate>10) AS rate_over_10_cm_per_h,
 SUM(radiation>1500) AS radiation_over_1500_w_per_m2,
 SUM(outTemp NOT BETWEEN -50 AND 60) AS temp_outside_screen,
 SUM(outHumidity NOT BETWEEN 0 AND 100) AS rh_outside_screen,
 SUM(rain<0) AS negative_rain
FROM loucka_reconstruction.archive WHERE dateTime<=1795378800;

-- 13. Reconstruction lacks finalized per-field WeeWX archive_day_* materializations.
SELECT TABLE_SCHEMA,COUNT(*) AS archive_day_tables
FROM information_schema.TABLES
WHERE TABLE_SCHEMA IN ('loucka_reconstruction','pocasi-loucka.eu')
 AND TABLE_NAME LIKE 'archive_day\\_%'
GROUP BY TABLE_SCHEMA;
