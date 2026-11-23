-- READ ONLY / 2026-11-23: anomaly discovery in original production
-- Schema: \`pocasi-loucka.eu\`.archive, all 80 columns, 2009-present.
-- Execute ONE SELECT at a time; high-cost gap/window queries off-peak.
-- NEVER UPDATE production, loucka_reconstruction or GW3000 sync.
-- "candidate" is not independent meteorological corroboration.
-- Snapshot anchor 2026-11-23 06:35 UTC: dateTime<=1795415700.
-- Note that data collection remains live. Group counts can grow after anchor.
--
-- A. Raw time identity and 5-min metadata.
SELECT COUNT(*) rows_total,MIN(dateTime) first_ts,MAX(dateTime) last_ts,
 COUNT(DISTINCT dateTime) distinct_timestamps,
 SUM(MOD(dateTime,300)<>0) off_grid,SUM(\`interval\`<>5) non5
FROM \`pocasi-loucka.eu\`.archive WHERE dateTime<=1795415700;

-- B. Year and field availability. A NULL does NOT prove a sensor was installed.
SELECT YEAR(DATE_ADD('1970-01-01',INTERVAL dateTime SECOND)) utc_year,
 COUNT(*) n,SUM(outTemp IS NULL) missing_temp,
 SUM(outHumidity IS NULL) missing_rh,
 SUM(pressure IS NULL) missing_pressure,SUM(rain IS NULL) missing_rain,
 SUM(windSpeed IS NULL) missing_wind,
 SUM(dewpoint IS NULL) missing_dewpoint,
 SUM(MOD(dateTime,300)<>0) offgrid,SUM(\`interval\`<>5) non5
FROM \`pocasi-loucka.eu\`.archive
WHERE dateTime<=1795415700
GROUP BY utc_year ORDER BY utc_year;

-- C. rainRate has no observed positive value through 2025, while rain can be positive.
SELECT MIN(CASE WHEN rainRate>0 THEN dateTime END) first_positive_rainRate,
 MAX(CASE WHEN dateTime<1767225600 THEN rainRate END) max_before_2026,
 SUM(dateTime<1767225600 AND rainRate=0) pre2026_zero_rainRate_rows,
 SUM(dateTime<1767225600 AND rain>0 AND rainRate=0) wet_with_zero_rate,
 SUM(dateTime>=1767225600 AND rainRate>0) positive_rate_in_2026
FROM \`pocasi-loucka.eu\`.archive WHERE dateTime<=1795415700;

-- D. Suspicious 5-min rain totals: review, never auto-delete on threshold alone.
SELECT YEAR(DATE_ADD('1970-01-01',INTERVAL p.dateTime SECOND)) utc_year,
 COUNT(*) gt5mm, SUM(p.rain>=1) ge10mm,
 SUM(r.rain IS NULL) recon_null, SUM(r.rain=0) recon_zero,
 SUM(r.rain>0) recon_positive
FROM \`pocasi-loucka.eu\`.archive p
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=p.dateTime
WHERE p.rain>0.5 AND p.dateTime<=1795415700
GROUP BY utc_year ORDER BY utc_year;

-- E. July 2021 source/reconstruction rain divergence: dateTime is UTC,
-- and 10*rain converts WeeWX METRIC centimetres into mm.
SELECT 'production' src,COUNT(*) n,ROUND(SUM(rain)*10,3) rain_mm
FROM \`pocasi-loucka.eu\`.archive
WHERE dateTime>1625090400 AND dateTime<=1627768800
UNION ALL
SELECT 'reconstruction',COUNT(*),ROUND(SUM(rain)*10,3)
FROM loucka_reconstruction.archive
WHERE dateTime>1625090400 AND dateTime<=1627768800;

-- F. 2015-18 RH exact 10% floor: source copies are not independent proof.
SELECT YEAR(DATE_ADD('1970-01-01',INTERVAL p.dateTime SECOND)) utc_year,
 COUNT(*) n,SUM(p.outTemp>=25) hot_25plus,
 SUM(r.outHumidity=10) remains_ten_in_reconstruction,
 SUM(w.outHumidity=10) wh_same_ten,
 SUM(w.outHumidity IS NOT NULL) wh_present
FROM \`pocasi-loucka.eu\`.archive p
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=p.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=p.dateTime
WHERE p.outHumidity=10 AND p.dateTime>=1420070400 AND p.dateTime<1546300800
GROUP BY utc_year ORDER BY utc_year;

-- G. 2020-22 4.25°C flatline candidate.
SELECT YEAR(DATE_ADD('1970-01-01',INTERVAL p.dateTime SECOND)) utc_year,
 COUNT(*) n,SUM(o.outTemp=4.25) old_copy_same,
 SUM(w.outTemp IS NOT NULL) wh_temp_present,
 SUM(w.outTemp IS NOT NULL AND ABS(w.outTemp-p.outTemp)>.5) wh_conflicts
FROM \`pocasi-loucka.eu\`.archive p
LEFT JOIN \`pocasi-loucka.eu_old\`.archive o ON o.dateTime=p.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=p.dateTime
WHERE p.dateTime>=1577836800 AND p.dateTime<1672531200
 AND p.outTemp=4.25
GROUP BY utc_year ORDER BY utc_year;

-- H. Exact-timestamp source comparisons; candidate presence is not approval.
SELECT COUNT(*) source_temp_missing,
 SUM(r.outTemp IS NOT NULL) reconstruction_filled,
 SUM(w.outTemp IS NOT NULL) wh_candidate_present,
 SUM(w.outTemp=0) wh_zero_placeholder,
 SUM(o.outTemp IS NOT NULL) old_copy_candidate_present
FROM \`pocasi-loucka.eu\`.archive p
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=p.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=p.dateTime
LEFT JOIN \`pocasi-loucka.eu_old\`.archive o ON o.dateTime=p.dateTime
WHERE p.dateTime>=1356998400 AND p.dateTime<1388534400
 AND p.outTemp IS NULL;

-- I. 2018/2019 historical RH candidates can contain 10% floor and >100% bad values.
SELECT YEAR(DATE_ADD('1970-01-01',INTERVAL p.dateTime SECOND)) utc_year,
 COUNT(*) original_rh_null,SUM(r.outHumidity IS NOT NULL) reconstruction_filled,
 SUM(w.outHumidity IS NOT NULL) wh_available,
 SUM(w.outHumidity=10) wh_at_floor_10,
 SUM(w.outHumidity>100) wh_over_100
FROM \`pocasi-loucka.eu\`.archive p
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=p.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=p.dateTime
WHERE p.dateTime>=1514764800 AND p.dateTime<1577836800
 AND p.outHumidity IS NULL GROUP BY utc_year ORDER BY utc_year;

-- J. RH 2022 missing before/after actual 2022-08-27 GW1000 installation epoch;
-- gw database may contain shared historical imports outside the real hardware epoch.
SELECT IF(p.dateTime<1661593200,'before_gw','after_gw') era,
 COUNT(*) rh_missing,SUM(r.outHumidity IS NOT NULL) recon_filled,
 SUM(g.outHumidity IS NOT NULL) gw_rh_available,
 SUM(p.pressure IS NULL) also_pressure_missing
FROM \`pocasi-loucka.eu\`.archive p
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=p.dateTime
LEFT JOIN \`pocasi-loucka.eu_GW1000\`.archive g ON g.dateTime=p.dateTime
WHERE p.dateTime>=1640995200 AND p.dateTime<1672531200
 AND p.outHumidity IS NULL GROUP BY era;

-- K. Phantom zeros in WH1080 archive *inside missing source intervals*.
-- These must NOT be imported as historical 0°C measurements.
SELECT '2011_aug_to_2012_mar' cohort,COUNT(*) n,
 SUM(outTemp=0) zero_temp,COUNT(DISTINCT outTemp) distinct_temp,
 SUM(outHumidity IS NOT NULL) with_rh,SUM(pressure IS NOT NULL) with_pressure
FROM weewx_WH1080.archive
WHERE dateTime>1313438700 AND dateTime<1330593900
UNION ALL SELECT '2016_jan_feb',COUNT(*),SUM(outTemp=0),
 COUNT(DISTINCT outTemp),SUM(outHumidity IS NOT NULL),SUM(pressure IS NOT NULL)
FROM weewx_WH1080.archive
WHERE dateTime>1453156500 AND dateTime<1454764200
UNION ALL SELECT '2017_jan',COUNT(*),SUM(outTemp=0),
 COUNT(DISTINCT outTemp),SUM(outHumidity IS NOT NULL),SUM(pressure IS NOT NULL)
FROM weewx_WH1080.archive
WHERE dateTime>1483966800 AND dateTime<1484645400
UNION ALL SELECT '2017_may',COUNT(*),SUM(outTemp=0),
 COUNT(DISTINCT outTemp),SUM(outHumidity IS NOT NULL),SUM(pressure IS NOT NULL)
FROM weewx_WH1080.archive
WHERE dateTime>1494564600 AND dateTime<1496007900;

-- L. Short-interval jumps on *adjacent exact 5-min* timestamps.
-- Threshold crossings are QC candidates, not proof of failure.
SELECT YEAR(DATE_ADD('1970-01-01',INTERVAL p.dateTime SECOND)) utc_year,
 SUM(ABS(p.outTemp-q.outTemp)>8) temp_jump_gt8C,
 SUM(ABS(p.outHumidity-q.outHumidity)>50) rh_jump_gt50pp,
 SUM(ABS(p.barometer-q.barometer)>8) barometer_jump_gt8hPa,
 SUM(ABS(p.windSpeed-q.windSpeed)>60) wind_jump_gt60kmh
FROM \`pocasi-loucka.eu\`.archive p
JOIN \`pocasi-loucka.eu\`.archive q ON q.dateTime=p.dateTime-300
WHERE p.dateTime<=1795415700
GROUP BY utc_year ORDER BY utc_year;

-- M. Solar, external-temperature and soil sentinels. Do not
-- pretend extraTemp2 2022 was always physically a temperature sensor.
SELECT SUM(radiation>1500) extreme_solar_gt1500,
 SUM(radiation>2*maxSolarRad AND radiation>100 AND maxSolarRad>0) double_model_solar,
 SUM(extraTemp1 NOT BETWEEN -50 AND 80
    OR extraTemp2 NOT BETWEEN -50 AND 80) extra_temp_outlier_rows,
 SUM(soilTemp1 NOT BETWEEN -50 AND 80
    OR soilTemp2 NOT BETWEEN -50 AND 80
    OR soilTemp3 NOT BETWEEN -50 AND 80
    OR soilTemp4 NOT BETWEEN -50 AND 80
    OR soilTemp5 NOT BETWEEN -50 AND 80
    OR soilTemp6 NOT BETWEEN -50 AND 80) soil_temp_outlier_rows,
 MIN(CASE WHEN extraTemp2>800 THEN dateTime END) extraTemp2_high_first
FROM \`pocasi-loucka.eu\`.archive WHERE dateTime<=1795415700;

-- N. Lightning source mapping: epoch-like "counter" and noise=strikes alias.
SELECT COUNT(*) disturber_present,
 SUM(lightning_disturber_count>1000000000) timestamp_like,
 SUM(lightning_noise_count IS NOT NULL) noise_present,
 SUM(lightning_noise_count IS NOT NULL
   AND lightning_noise_count<=>lightning_strike_count) noise_equals_strikes,
 MIN(dateTime) first_ts,MAX(dateTime) last_ts
FROM \`pocasi-loucka.eu\`.archive
WHERE lightning_disturber_count IS NOT NULL AND dateTime<=1795415700;

-- O. Production dewpoint consistency screen. Good consistency in original
-- means later *reconstruction* RH changes can stale the derived dewpoint.
SELECT COUNT(*) comparable,
 SUM(ABS(dewpoint-(243.04*
 (LN(outHumidity/100)+17.625*outTemp/(243.04+outTemp))/
 (17.625-(LN(outHumidity/100)+17.625*outTemp/(243.04+outTemp)))))>2)
   AS inconsistent_over_2C
FROM \`pocasi-loucka.eu\`.archive
WHERE outTemp IS NOT NULL AND dewpoint IS NOT NULL
 AND outHumidity BETWEEN 1 AND 100 AND usUnits=16 AND dateTime<=1795415700;

-- P. Exact comparison with current reconstruction in the four known fields.
-- Run at a SINGLE, fixed UTC watermark for reproducibility, as the live
-- producer and sync have slightly different latest-record timing.
SELECT COUNT(*) overlap,
 SUM(NOT (p.outTemp <=> r.outTemp)) temp_diffs,
 SUM(NOT (p.outHumidity <=> r.outHumidity)) rh_diffs,
 SUM(NOT (p.rain <=> r.rain)) rain_diffs,
 SUM(NOT (p.rainRate <=> r.rainRate)) rainRate_diffs
FROM \`pocasi-loucka.eu\`.archive p
JOIN loucka_reconstruction.archive r ON r.dateTime=p.dateTime
WHERE p.dateTime<=1795415700;

-- Q. Historical wind numeric scale changed across April 2013 outage:
-- does not prove original logger cutover or identify physical unit by itself.
SELECT q.period,COUNT(*) positive_speed_pairs,
 SUM(ABS(p.windSpeed-s.windSpeed)<0.1) numeric_factor1,
 SUM(ABS(p.windSpeed-3.6*s.windSpeed)<0.1) numeric_factor3_6
FROM (SELECT '2013_mar' period,1362096000 lo,1364774400 hi
 UNION ALL SELECT '2013_may_jul',1367366400,1375315200) q
JOIN old_weewx.archive s ON s.dateTime>=q.lo AND s.dateTime<q.hi
JOIN \`pocasi-loucka.eu\`.archive p
 ON p.dateTime=FLOOR((s.dateTime+150)/300)*300
WHERE s.windSpeed>0 AND p.windSpeed IS NOT NULL
GROUP BY q.period ORDER BY q.period;

-- R. Verify DAILY SUMMARY using exact WeeWX local-day boundaries via LEAD
-- for a SINGLE selected month; never naively group DATE(FROM_UNIXTIME).
-- 2021 July daily cache still matches the corrupted production rain series;
-- rebuilding it against validated reconstruction needs a separate process.
WITH days AS (
 SELECT d.dateTime day_start,LEAD(d.dateTime) OVER(ORDER BY d.dateTime) next_start,
 d.\`sum\` daily_source_rain
 FROM \`pocasi-loucka.eu\`.archive_day_rain d
), agg AS (
 SELECT d.day_start,d.daily_source_rain,COALESCE(SUM(a.rain),0) sum_intervals
 FROM days d LEFT JOIN \`pocasi-loucka.eu\`.archive a
 ON a.dateTime>d.day_start AND a.dateTime<=d.next_start
 WHERE d.day_start>=1625090400 AND d.day_start<1627768800
 AND d.next_start IS NOT NULL
 GROUP BY d.day_start,d.daily_source_rain
)
SELECT COUNT(*) days_checked,
 SUM(ABS(COALESCE(daily_source_rain,0)-sum_intervals)>.005) rain_mismatch_gt005_cm
FROM agg;
