-- READ-ONLY; fixed UTC year bounds; diagnostic availability only.
-- Source schema: `pocasi-loucka.eu_old`. Year: 2012. Fields: soilTemp4, supplyVoltage, txBatteryStatus, uvBatteryStatus, windBatteryStatus, windDir, windGust, windGustDir, windSpeed, windchill, windrun
SELECT
  COUNT(*) AS archive_rows,
  COUNT(`soilTemp4`) AS `soilTemp4_nonnull`,
  COUNT(`supplyVoltage`) AS `supplyVoltage_nonnull`,
  COUNT(`txBatteryStatus`) AS `txBatteryStatus_nonnull`,
  COUNT(`uvBatteryStatus`) AS `uvBatteryStatus_nonnull`,
  COUNT(`windBatteryStatus`) AS `windBatteryStatus_nonnull`,
  COUNT(`windDir`) AS `windDir_nonnull`,
  COUNT(`windGust`) AS `windGust_nonnull`,
  COUNT(`windGustDir`) AS `windGustDir_nonnull`,
  COUNT(`windSpeed`) AS `windSpeed_nonnull`,
  COUNT(`windchill`) AS `windchill_nonnull`,
  COUNT(`windrun`) AS `windrun_nonnull`
FROM `pocasi-loucka.eu_old`.`archive`
WHERE `dateTime` >= 1325376000 AND `dateTime` < 1356998400;
