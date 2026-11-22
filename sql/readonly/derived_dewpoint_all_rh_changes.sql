-- SELECT-only, UTC-bounded by exclusion of 2021. Reproduces the RH-change
-- follow-up using current and immediately prior (old_value) RH. Magnus is a
-- diagnostic approximation; no historical formula is asserted.
WITH ranked AS (
    SELECT target_time, old_value, new_value, created_at, id,
           ROW_NUMBER() OVER (
               PARTITION BY target_time ORDER BY created_at DESC, id DESC
           ) AS rn
    FROM `loucka_reconstruction`.reconstruction_changes
    WHERE variable = 'outHumidity' AND state = 'applied'
      AND (target_time < 1609459200 OR target_time >= 1640995200)
), latest AS (
    SELECT * FROM ranked WHERE rn = 1
), derived_history AS (
    SELECT DISTINCT target_time
    FROM `loucka_reconstruction`.reconstruction_changes
    WHERE variable = 'dewpoint'
), calc AS (
    SELECT a.dateTime, a.outHumidity, a.dewpoint,
           l.old_value AS old_rh, l.new_value AS latest_new_rh,
           d.target_time AS has_dewpoint_history,
           CASE
             WHEN a.dateTime >= 1514764800 AND a.dateTime < 1522540800 THEN '2018_Q1_INTERIM'
             WHEN a.dateTime >= 1648771200 AND a.dateTime < 1651363200 THEN '2022_04_TARGET'
             WHEN a.dateTime >= 1230768000 AND a.dateTime < 1262304000 THEN '2009'
             WHEN a.dateTime >= 1262304000 AND a.dateTime < 1293840000 THEN '2010'
             WHEN a.dateTime >= 1293840000 AND a.dateTime < 1325376000 THEN '2011'
             WHEN a.dateTime >= 1325376000 AND a.dateTime < 1356998400 THEN '2012'
             WHEN a.dateTime >= 1356998400 AND a.dateTime < 1388534400 THEN '2013'
             WHEN a.dateTime >= 1388534400 AND a.dateTime < 1420070400 THEN '2014'
             WHEN a.dateTime >= 1420070400 AND a.dateTime < 1451606400 THEN '2015'
             WHEN a.dateTime >= 1451606400 AND a.dateTime < 1483228800 THEN '2016'
             WHEN a.dateTime >= 1483228800 AND a.dateTime < 1514764800 THEN '2017'
             WHEN a.dateTime >= 1514764800 AND a.dateTime < 1546300800 THEN '2018'
             WHEN a.dateTime >= 1546300800 AND a.dateTime < 1577836800 THEN '2019'
             WHEN a.dateTime >= 1577836800 AND a.dateTime < 1609459200 THEN '2020'
             WHEN a.dateTime >= 1609459200 AND a.dateTime < 1640995200 THEN '2021'
             WHEN a.dateTime >= 1640995200 AND a.dateTime < 1672531200 THEN '2022'
             WHEN a.dateTime >= 1672531200 AND a.dateTime < 1704067200 THEN '2023'
             WHEN a.dateTime >= 1704067200 AND a.dateTime < 1735689600 THEN '2024'
             WHEN a.dateTime >= 1735689600 AND a.dateTime < 1767225600 THEN '2025'
             WHEN a.dateTime >= 1767225600 AND a.dateTime < 1798761600 THEN '2026'
             ELSE 'out_of_scope'
           END AS scope,
           243.04 * (
             LN(a.outHumidity / 100) + 17.625 * a.outTemp / (243.04 + a.outTemp)
           ) / (
             17.625 - (LN(a.outHumidity / 100) + 17.625 * a.outTemp / (243.04 + a.outTemp))
           ) AS dp_from_current_rh,
           CASE WHEN l.old_value BETWEEN 1 AND 100 THEN
             243.04 * (
               LN(l.old_value / 100) + 17.625 * a.outTemp / (243.04 + a.outTemp)
             ) / (
               17.625 - (LN(l.old_value / 100) + 17.625 * a.outTemp / (243.04 + a.outTemp))
             )
           END AS dp_from_old_rh
    FROM latest l
    JOIN `loucka_reconstruction`.archive a ON a.dateTime = l.target_time
    LEFT JOIN derived_history d ON d.target_time = a.dateTime
    WHERE a.outTemp IS NOT NULL
      AND a.outHumidity BETWEEN 1 AND 100
      AND a.dewpoint IS NOT NULL
)
SELECT scope, COUNT(*) AS compared_rows,
       SUM(old_rh IS NOT NULL) AS old_rh_present,
       SUM(outHumidity <=> latest_new_rh) AS current_rh_matches_latest_new,
       SUM(ABS(dewpoint - dp_from_current_rh) > 2) AS current_rh_delta_gt2c,
       SUM(ABS(dewpoint - dp_from_old_rh) <= 0.1) AS stored_dp_matches_old_rh_within_0_1c,
       AVG(ABS(dewpoint - dp_from_old_rh)) AS old_rh_mean_abs_delta_c,
       MAX(ABS(dewpoint - dp_from_old_rh)) AS old_rh_max_abs_delta_c,
       SUM(has_dewpoint_history IS NOT NULL) AS with_dewpoint_history
FROM calc
GROUP BY scope ORDER BY scope;

-- Audit overlapping applied temperature changes: old_temperature was NULL
-- for every overlapping RH/temperature target in this live snapshot.
WITH rh_targets AS (
    SELECT DISTINCT target_time
    FROM `loucka_reconstruction`.reconstruction_changes
    WHERE variable = 'outHumidity' AND state = 'applied'
      AND (target_time < 1609459200 OR target_time >= 1640995200)
), temp_ranked AS (
    SELECT target_time, old_value, new_value, created_at, id,
           ROW_NUMBER() OVER (
               PARTITION BY target_time ORDER BY created_at DESC, id DESC
           ) AS rn
    FROM `loucka_reconstruction`.reconstruction_changes
    WHERE variable = 'outTemp' AND state = 'applied'
)
SELECT COUNT(*) AS overlapping_applied_targets,
       SUM(t.old_value IS NULL) AS old_temperature_null,
       SUM(t.new_value IS NOT NULL) AS new_temperature_present
FROM rh_targets r
JOIN temp_ranked t ON t.target_time = r.target_time AND t.rn = 1;
