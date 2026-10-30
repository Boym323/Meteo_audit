-- Humidity audit: READ ONLY, never applies corrections.
-- Time boundaries are Unix UTC seconds. Archive month/day assignment follows
-- WeeWX interval END: dateTime > local_start_epoch AND dateTime <= local_end_epoch.
-- Year grouping via FROM_UNIXTIME uses DB session timezone and is illustrative;
-- use explicit Europe/Prague epoch month boundaries for report-grade output.

-- 1. Missing and suspect values across requested ranges.
SELECT YEAR(FROM_UNIXTIME(dateTime)) local_year, COUNT(*) rows_total,
       SUM(outHumidity IS NULL) humidity_missing,
       SUM(outHumidity BETWEEN 1 AND 15) humidity_suspect_low,
       SUM(outTemp IS NULL) temperature_missing
FROM `loucka_reconstruction`.archive
WHERE (dateTime >= 1420070400 AND dateTime < 1577836800)
   OR (dateTime >= 1640995200 AND dateTime < 1659312000)
GROUP BY YEAR(FROM_UNIXTIME(dateTime)) ORDER BY local_year;

-- 2. WH1080 looks like a source, but is not independent proof of valid RH.
SELECT YEAR(FROM_UNIXTIME(a.dateTime)) local_year,
       COUNT(*) timestamp_matches,
       ROUND(AVG(w.outHumidity), 2) historical_rh_mean,
       SUM(w.outHumidity BETWEEN 1 AND 15) very_dry_source,
       SUM(a.outTemp IS NOT NULL AND w.outTemp IS NOT NULL
           AND ABS(a.outTemp-w.outTemp) <= 0.2) same_temperature
FROM `loucka_reconstruction`.archive a
JOIN `weewx_WH1080`.archive w ON w.dateTime=a.dateTime
WHERE a.dateTime >= 1420070400 AND a.dateTime < 1577836800
  AND a.outHumidity IS NULL AND w.outHumidity BETWEEN 1 AND 100
GROUP BY YEAR(FROM_UNIXTIME(a.dateTime)) ORDER BY local_year;

-- 3. Reference data coverage and QC. Run with narrow UTC bounds for one year.
-- Time tolerance is bounded to +/-150s, but alignment is a proposal only;
-- audit possible same-slot collisions before using a returned observation.
SELECT r.station_id,
       DATE_FORMAT(FROM_UNIXTIME(a.dateTime), '%Y-%m') local_month,
       COUNT(*) paired_rows,
       SUM(a.outHumidity IS NULL AND a.outTemp BETWEEN -40 AND 45
           AND r.relative_humidity_pct BETWEEN 1 AND 100
           AND r.temperature_c BETWEEN -40 AND 45) estimated_candidate_inputs
FROM `loucka_reconstruction`.reference_observations r
JOIN `loucka_reconstruction`.archive a
  ON a.dateTime = FLOOR((r.observed_at_utc + 150) / 300) * 300
WHERE r.station_id IN ('luhamet_sehradice','wu_ilouka4')
  AND r.observed_at_utc >= 1640995200
  AND r.observed_at_utc < 1659312000
GROUP BY r.station_id,DATE_FORMAT(FROM_UNIXTIME(a.dateTime),'%Y-%m')
ORDER BY local_month,r.station_id;

-- 4. Candidate single five-minute null between close real RH anchors.
-- IMPORTANT: reject anchors present in reconstruction_changes, frozen/saturated
-- intervals and any targets that already have an applied correction.
SELECT a.dateTime, a.outHumidity old_rh,
       p.outHumidity previous_rh, n.outHumidity next_rh,
       (p.outHumidity+n.outHumidity)/2 proposed_rh
FROM `loucka_reconstruction`.archive a
JOIN `loucka_reconstruction`.archive p ON p.dateTime=a.dateTime-300
JOIN `loucka_reconstruction`.archive n ON n.dateTime=a.dateTime+300
LEFT JOIN `loucka_reconstruction`.reconstruction_changes pre
       ON pre.target_time=p.dateTime AND pre.variable='outHumidity' AND pre.state='applied'
LEFT JOIN `loucka_reconstruction`.reconstruction_changes nxt
       ON nxt.target_time=n.dateTime AND nxt.variable='outHumidity' AND nxt.state='applied'
LEFT JOIN `loucka_reconstruction`.reconstruction_changes old
       ON old.target_time=a.dateTime AND old.variable='outHumidity' AND old.state='applied'
WHERE a.dateTime>=1640995200 AND a.dateTime<1659312000
  AND a.outHumidity IS NULL
  AND p.outHumidity BETWEEN 50 AND 100
  AND n.outHumidity BETWEEN 50 AND 100
  AND ABS(p.outHumidity-n.outHumidity)<=3
  AND a.outTemp BETWEEN -40 AND 45 AND ABS(p.outTemp-n.outTemp)<=1.5
  AND pre.id IS NULL AND nxt.id IS NULL AND old.id IS NULL
ORDER BY a.dateTime LIMIT 100;

-- 5. Audit exact committed corrections; no re-apply.
SELECT batch_key, variable, state, COUNT(*) n
FROM `loucka_reconstruction`.reconstruction_changes
WHERE batch_key IN ('humidity-2019-short-gaps-v1','humidity-20220705-isolated-gap-v1')
GROUP BY batch_key,variable,state;
