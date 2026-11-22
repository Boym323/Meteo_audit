-- READ-ONLY; fixed UTC year bounds; diagnostic availability only.
-- Source schema: `pocasi-loucka.eu_GW1000`. Year: 2018. Fields: signal8, soilMoist1, soilTemp1, soilTemp2, soilTemp3, soilTemp4, supplyVoltage, windDir, windGust, windGustDir, windSpeed, windchill, windrun
SELECT
  COUNT(*) AS archive_rows,
  COUNT(`signal8`) AS `signal8_nonnull`,
  COUNT(`soilMoist1`) AS `soilMoist1_nonnull`,
  COUNT(`soilTemp1`) AS `soilTemp1_nonnull`,
  COUNT(`soilTemp2`) AS `soilTemp2_nonnull`,
  COUNT(`soilTemp3`) AS `soilTemp3_nonnull`,
  COUNT(`soilTemp4`) AS `soilTemp4_nonnull`,
  COUNT(`supplyVoltage`) AS `supplyVoltage_nonnull`,
  COUNT(`windDir`) AS `windDir_nonnull`,
  COUNT(`windGust`) AS `windGust_nonnull`,
  COUNT(`windGustDir`) AS `windGustDir_nonnull`,
  COUNT(`windSpeed`) AS `windSpeed_nonnull`,
  COUNT(`windchill`) AS `windchill_nonnull`,
  COUNT(`windrun`) AS `windrun_nonnull`
FROM `pocasi-loucka.eu_GW1000`.`archive`
WHERE `dateTime` >= 1514764800 AND `dateTime` < 1546300800;
