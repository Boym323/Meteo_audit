-- Wide SELECT-only screening of indoor, extra and soil channels.
-- Thresholds are triage bounds only; channel map/install epochs are unverified.
SELECT COUNT(*) AS rows_total,
       SUM(inTemp IS NOT NULL) AS inTemp_n, MIN(inTemp) AS inTemp_min, MAX(inTemp) AS inTemp_max,
       SUM(inTemp < -30 OR inTemp > 70) AS inTemp_outside_screen,
       SUM(inHumidity IS NOT NULL) AS inHumidity_n, MIN(inHumidity) AS inHumidity_min, MAX(inHumidity) AS inHumidity_max,
       SUM(inHumidity < 0 OR inHumidity > 100) AS inHumidity_outside_0_100,
       SUM(extraTemp1 IS NOT NULL) AS extraTemp1_n, MIN(extraTemp1) AS extraTemp1_min, MAX(extraTemp1) AS extraTemp1_max,
       SUM(extraTemp1 < -50 OR extraTemp1 > 80) AS extraTemp1_outside_screen,
       SUM(extraTemp2 IS NOT NULL) AS extraTemp2_n, MIN(extraTemp2) AS extraTemp2_min, MAX(extraTemp2) AS extraTemp2_max,
       SUM(extraTemp2 < -50 OR extraTemp2 > 80) AS extraTemp2_outside_screen,
       SUM(extraTemp2 > 80 AND extraTemp2 < 100) AS extraTemp2_80_to_100,
       SUM(extraTemp2 >= 822 AND extraTemp2 < 823) AS extraTemp2_822_to_823,
       SUM(extraHumid1 IS NOT NULL) AS extraHumid1_n, MIN(extraHumid1) AS extraHumid1_min, MAX(extraHumid1) AS extraHumid1_max,
       SUM(extraHumid2 IS NOT NULL) AS extraHumid2_n, MIN(extraHumid2) AS extraHumid2_min, MAX(extraHumid2) AS extraHumid2_max,
       SUM(soilTemp1 IS NOT NULL) AS soilTemp1_n, MIN(soilTemp1) AS soilTemp1_min, MAX(soilTemp1) AS soilTemp1_max,
       SUM(soilTemp1 < -40 OR soilTemp1 > 60) AS soilTemp1_outside_screen,
       SUM(soilTemp2 IS NOT NULL) AS soilTemp2_n, MIN(soilTemp2) AS soilTemp2_min, MAX(soilTemp2) AS soilTemp2_max,
       SUM(soilTemp2 < -40 OR soilTemp2 > 60) AS soilTemp2_outside_screen,
       SUM(soilTemp3 IS NOT NULL) AS soilTemp3_n, MIN(soilTemp3) AS soilTemp3_min, MAX(soilTemp3) AS soilTemp3_max,
       SUM(soilTemp3 < -40 OR soilTemp3 > 60) AS soilTemp3_outside_screen,
       SUM(soilTemp4 IS NOT NULL) AS soilTemp4_n, MIN(soilTemp4) AS soilTemp4_min, MAX(soilTemp4) AS soilTemp4_max,
       SUM(soilTemp4 < -40 OR soilTemp4 > 60) AS soilTemp4_outside_screen,
       SUM(soilTemp5 IS NOT NULL) AS soilTemp5_n, MIN(soilTemp5) AS soilTemp5_min, MAX(soilTemp5) AS soilTemp5_max,
       SUM(soilTemp5 < -40 OR soilTemp5 > 60) AS soilTemp5_outside_screen,
       SUM(soilTemp6 IS NOT NULL) AS soilTemp6_n, MIN(soilTemp6) AS soilTemp6_min, MAX(soilTemp6) AS soilTemp6_max,
       SUM(soilTemp6 < -40 OR soilTemp6 > 60) AS soilTemp6_outside_screen,
       SUM(soilMoist1 IS NOT NULL) AS soilMoist1_n, MIN(soilMoist1) AS soilMoist1_min, MAX(soilMoist1) AS soilMoist1_max,
       SUM(soilMoist1 < 0 OR soilMoist1 > 100) AS soilMoist1_outside_0_100,
       SUM(soilad1 IS NOT NULL) AS soilad1_n, MIN(soilad1) AS soilad1_min, MAX(soilad1) AS soilad1_max
FROM `loucka_reconstruction`.archive;

-- Source reconciliation: identical timestamp overlap, archive vs current main.
-- Matching copies are not treated as independent measurements.
SELECT 'extraTemp2_gt80' AS signal, COUNT(*) AS target_rows,
       SUM(m.extraTemp2 IS NOT NULL) AS main_available,
       SUM(m.extraTemp2 = a.extraTemp2) AS exact_matches
FROM `loucka_reconstruction`.archive a
LEFT JOIN `pocasi-loucka.eu`.archive m ON m.dateTime = a.dateTime
WHERE a.extraTemp2 > 80
UNION ALL
SELECT 'soil_temperature_lt_minus40', COUNT(*),
       SUM(m.dateTime IS NOT NULL),
       SUM((a.soilTemp1 < -40 AND m.soilTemp1 = a.soilTemp1)
        OR (a.soilTemp5 < -40 AND m.soilTemp5 = a.soilTemp5)
        OR (a.soilTemp6 < -40 AND m.soilTemp6 = a.soilTemp6))
FROM `loucka_reconstruction`.archive a
LEFT JOIN `pocasi-loucka.eu`.archive m ON m.dateTime = a.dateTime
WHERE a.soilTemp1 < -40 OR a.soilTemp5 < -40 OR a.soilTemp6 < -40;
