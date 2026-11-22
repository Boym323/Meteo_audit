-- SELECT-only inventory of radio/signal/battery diagnostic channels.
SELECT COUNT(*) AS archive_rows,
       SUM(wh26_rssi IS NOT NULL) AS wh26_rssi_n, MIN(wh26_rssi) AS wh26_rssi_min, MAX(wh26_rssi) AS wh26_rssi_max,
       SUM(wh31_ch1_rssi IS NOT NULL) AS wh31_ch1_rssi_n, MIN(wh31_ch1_rssi) AS wh31_ch1_rssi_min, MAX(wh31_ch1_rssi) AS wh31_ch1_rssi_max,
       SUM(wh31_ch1_sig IS NOT NULL) AS wh31_ch1_sig_n, MIN(wh31_ch1_sig) AS wh31_ch1_sig_min, MAX(wh31_ch1_sig) AS wh31_ch1_sig_max,
       SUM(wh31_ch2_sig IS NOT NULL) AS wh31_ch2_sig_n, MIN(wh31_ch2_sig) AS wh31_ch2_sig_min, MAX(wh31_ch2_sig) AS wh31_ch2_sig_max,
       SUM(wh40_rssi IS NOT NULL) AS wh40_rssi_n, MIN(wh40_rssi) AS wh40_rssi_min, MAX(wh40_rssi) AS wh40_rssi_max,
       SUM(wh41_ch1_rssi IS NOT NULL) AS wh41_ch1_rssi_n, MIN(wh41_ch1_rssi) AS wh41_ch1_rssi_min, MAX(wh41_ch1_rssi) AS wh41_ch1_rssi_max,
       SUM(wh51_ch1_rssi IS NOT NULL) AS wh51_ch1_rssi_n, MIN(wh51_ch1_rssi) AS wh51_ch1_rssi_min, MAX(wh51_ch1_rssi) AS wh51_ch1_rssi_max,
       SUM(wh51_ch1_sig IS NOT NULL) AS wh51_ch1_sig_n, MIN(wh51_ch1_sig) AS wh51_ch1_sig_min, MAX(wh51_ch1_sig) AS wh51_ch1_sig_max,
       SUM(wh57_rssi IS NOT NULL) AS wh57_rssi_n, MIN(wh57_rssi) AS wh57_rssi_min, MAX(wh57_rssi) AS wh57_rssi_max,
       SUM(ws80_rssi IS NOT NULL) AS ws80_rssi_n, MIN(ws80_rssi) AS ws80_rssi_min, MAX(ws80_rssi) AS ws80_rssi_max,
       SUM(ws80_sig IS NOT NULL) AS ws80_sig_n, MIN(ws80_sig) AS ws80_sig_min, MAX(ws80_sig) AS ws80_sig_max,
       SUM(batteryStatus1 IS NOT NULL) AS batteryStatus1_n, MIN(batteryStatus1) AS batteryStatus1_min, MAX(batteryStatus1) AS batteryStatus1_max,
       SUM(batteryStatus2 IS NOT NULL) AS batteryStatus2_n, MIN(batteryStatus2) AS batteryStatus2_min, MAX(batteryStatus2) AS batteryStatus2_max,
       SUM(lightning_Batt IS NOT NULL) AS lightning_Batt_n, MIN(lightning_Batt) AS lightning_Batt_min, MAX(lightning_Batt) AS lightning_Batt_max,
       SUM(pm25_Batt1 IS NOT NULL) AS pm25_Batt1_n, MIN(pm25_Batt1) AS pm25_Batt1_min, MAX(pm25_Batt1) AS pm25_Batt1_max,
       SUM(soilMoistBatt1 IS NOT NULL) AS soilMoistBatt1_n, MIN(soilMoistBatt1) AS soilMoistBatt1_min, MAX(soilMoistBatt1) AS soilMoistBatt1_max,
       SUM(ws80_batt IS NOT NULL) AS ws80_batt_n, MIN(ws80_batt) AS ws80_batt_min, MAX(ws80_batt) AS ws80_batt_max
FROM `loucka_reconstruction`.archive;

-- The stored ws80_sig meaning changes discontinuously by sign at the epoch
-- boundary below. Keep this diagnostic split explicit; do not infer units.
SELECT CASE WHEN ws80_sig < 0 THEN 'negative' ELSE 'nonnegative' END AS signal_class,
       COUNT(*) AS n, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch,
       MIN(ws80_sig) AS min_value, MAX(ws80_sig) AS max_value,
       SUM(ws80_rssi IS NOT NULL) AS simultaneous_ws80_rssi,
       SUM(ws80_batt IS NOT NULL) AS simultaneous_ws80_batt
FROM `loucka_reconstruction`.archive
WHERE ws80_sig IS NOT NULL
GROUP BY signal_class ORDER BY signal_class;

-- Exact timestamp/value reconciliation against the current main archive.
SELECT CASE WHEN a.ws80_sig < 0 THEN 'negative_era' ELSE 'nonnegative_era' END AS signal_class,
       COUNT(*) AS recon_rows, SUM(m.ws80_sig IS NOT NULL) AS main_available,
       SUM(a.ws80_sig = m.ws80_sig) AS exact_matches,
       SUM(m.ws80_sig IS NOT NULL AND ((a.ws80_sig < 0) <> (m.ws80_sig < 0))) AS sign_conflicts,
       MIN(a.dateTime) AS first_epoch, MAX(a.dateTime) AS last_epoch
FROM `loucka_reconstruction`.archive a
LEFT JOIN `pocasi-loucka.eu`.archive m ON m.dateTime = a.dateTime
WHERE a.ws80_sig IS NOT NULL
GROUP BY signal_class ORDER BY signal_class;
