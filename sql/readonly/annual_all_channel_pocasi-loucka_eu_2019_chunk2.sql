-- READ-ONLY; fixed UTC year bounds; diagnostic availability only.
-- Source schema: `pocasi-loucka.eu`. Year: 2019. Fields: soilTemp4, soilTemp5, soilTemp6, soilad1, sunshineDur, sunshine_time, vpd, wbgt, wh26_rssi, wh31_ch1_rssi, wh31_ch1_sig, wh31_ch2_sig, wh40_rssi, wh41_ch1_rssi, wh51_ch1_rssi, wh51_ch1_sig, wh57_rssi, windDir, windGust, windGustDir, windSpeed, windchill, windrun, ws80_batt, ws80_rssi, ws80_sig, yearGDD
SELECT
  COUNT(*) AS archive_rows,
  COUNT(`soilTemp4`) AS `soilTemp4_nonnull`,
  COUNT(`soilTemp5`) AS `soilTemp5_nonnull`,
  COUNT(`soilTemp6`) AS `soilTemp6_nonnull`,
  COUNT(`soilad1`) AS `soilad1_nonnull`,
  COUNT(`sunshineDur`) AS `sunshineDur_nonnull`,
  COUNT(`sunshine_time`) AS `sunshine_time_nonnull`,
  COUNT(`vpd`) AS `vpd_nonnull`,
  COUNT(`wbgt`) AS `wbgt_nonnull`,
  COUNT(`wh26_rssi`) AS `wh26_rssi_nonnull`,
  COUNT(`wh31_ch1_rssi`) AS `wh31_ch1_rssi_nonnull`,
  COUNT(`wh31_ch1_sig`) AS `wh31_ch1_sig_nonnull`,
  COUNT(`wh31_ch2_sig`) AS `wh31_ch2_sig_nonnull`,
  COUNT(`wh40_rssi`) AS `wh40_rssi_nonnull`,
  COUNT(`wh41_ch1_rssi`) AS `wh41_ch1_rssi_nonnull`,
  COUNT(`wh51_ch1_rssi`) AS `wh51_ch1_rssi_nonnull`,
  COUNT(`wh51_ch1_sig`) AS `wh51_ch1_sig_nonnull`,
  COUNT(`wh57_rssi`) AS `wh57_rssi_nonnull`,
  COUNT(`windDir`) AS `windDir_nonnull`,
  COUNT(`windGust`) AS `windGust_nonnull`,
  COUNT(`windGustDir`) AS `windGustDir_nonnull`,
  COUNT(`windSpeed`) AS `windSpeed_nonnull`,
  COUNT(`windchill`) AS `windchill_nonnull`,
  COUNT(`windrun`) AS `windrun_nonnull`,
  COUNT(`ws80_batt`) AS `ws80_batt_nonnull`,
  COUNT(`ws80_rssi`) AS `ws80_rssi_nonnull`,
  COUNT(`ws80_sig`) AS `ws80_sig_nonnull`,
  COUNT(`yearGDD`) AS `yearGDD_nonnull`
FROM `pocasi-loucka.eu`.`archive`
WHERE `dateTime` >= 1546300800 AND `dateTime` < 1577836800;
