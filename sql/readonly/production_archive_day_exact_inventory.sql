-- Read-only exact count and dateTime-key range for all metric archive_day tables.
-- Execute through the approved Weather MCP SELECT-only path.
-- Snapshot: 2026-11-13; dateTime epochs are preserved as raw keys.
SELECT 'archive_day_altimeter' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_altimeter`
UNION ALL
SELECT 'archive_day_appTemp' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_appTemp`
UNION ALL
SELECT 'archive_day_barometer' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_barometer`
UNION ALL
SELECT 'archive_day_batteryStatus1' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_batteryStatus1`
UNION ALL
SELECT 'archive_day_batteryStatus2' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_batteryStatus2`
UNION ALL
SELECT 'archive_day_bgt' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_bgt`
UNION ALL
SELECT 'archive_day_cloudbase' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_cloudbase`
UNION ALL
SELECT 'archive_day_dayET' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_dayET`
UNION ALL
SELECT 'archive_day_dewpoint' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_dewpoint`
UNION ALL
SELECT 'archive_day_ET' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_ET`
UNION ALL
SELECT 'archive_day_ET24' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_ET24`
UNION ALL
SELECT 'archive_day_extraHumid1' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_extraHumid1`
UNION ALL
SELECT 'archive_day_extraHumid2' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_extraHumid2`
UNION ALL
SELECT 'archive_day_extraTemp1' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_extraTemp1`
UNION ALL
SELECT 'archive_day_extraTemp2' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_extraTemp2`
UNION ALL
SELECT 'archive_day_GTS' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_GTS`
UNION ALL
SELECT 'archive_day_GTSdate' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_GTSdate`
UNION ALL
SELECT 'archive_day_heatindex' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_heatindex`
UNION ALL
SELECT 'archive_day_humidex' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_humidex`
UNION ALL
SELECT 'archive_day_inDewpoint' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_inDewpoint`
UNION ALL
SELECT 'archive_day_inHumidity' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_inHumidity`
UNION ALL
SELECT 'archive_day_inTemp' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_inTemp`
UNION ALL
SELECT 'archive_day_lightning_Batt' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_lightning_Batt`
UNION ALL
SELECT 'archive_day_lightning_distance' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_lightning_distance`
UNION ALL
SELECT 'archive_day_lightning_disturber_count' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_lightning_disturber_count`
UNION ALL
SELECT 'archive_day_lightning_energy' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_lightning_energy`
UNION ALL
SELECT 'archive_day_lightning_noise_count' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_lightning_noise_count`
UNION ALL
SELECT 'archive_day_lightning_strike_count' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_lightning_strike_count`
UNION ALL
SELECT 'archive_day_luminosity' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_luminosity`
UNION ALL
SELECT 'archive_day_maxSolarRad' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_maxSolarRad`
UNION ALL
SELECT 'archive_day_outEquiTemp' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_outEquiTemp`
UNION ALL
SELECT 'archive_day_outHumAbs' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_outHumAbs`
UNION ALL
SELECT 'archive_day_outHumidity' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_outHumidity`
UNION ALL
SELECT 'archive_day_outTemp' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_outTemp`
UNION ALL
SELECT 'archive_day_outThetaE' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_outThetaE`
UNION ALL
SELECT 'archive_day_pb' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_pb`
UNION ALL
SELECT 'archive_day_pm25_1' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_pm25_1`
UNION ALL
SELECT 'archive_day_pm25_Batt1' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_pm25_Batt1`
UNION ALL
SELECT 'archive_day_pressure' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_pressure`
UNION ALL
SELECT 'archive_day_radiation' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_radiation`
UNION ALL
SELECT 'archive_day_rain' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_rain`
UNION ALL
SELECT 'archive_day_rainDur' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_rainDur`
UNION ALL
SELECT 'archive_day_rainRate' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_rainRate`
UNION ALL
SELECT 'archive_day_seasonGDD' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_seasonGDD`
UNION ALL
SELECT 'archive_day_soilad1' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_soilad1`
UNION ALL
SELECT 'archive_day_soilMoist1' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_soilMoist1`
UNION ALL
SELECT 'archive_day_soilMoistBatt1' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_soilMoistBatt1`
UNION ALL
SELECT 'archive_day_soilTemp1' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_soilTemp1`
UNION ALL
SELECT 'archive_day_soilTemp2' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_soilTemp2`
UNION ALL
SELECT 'archive_day_soilTemp3' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_soilTemp3`
UNION ALL
SELECT 'archive_day_soilTemp4' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_soilTemp4`
UNION ALL
SELECT 'archive_day_soilTemp5' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_soilTemp5`
UNION ALL
SELECT 'archive_day_soilTemp6' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_soilTemp6`
UNION ALL
SELECT 'archive_day_sunshineDur' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_sunshineDur`
UNION ALL
SELECT 'archive_day_sunshine_time' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_sunshine_time`
UNION ALL
SELECT 'archive_day_UV' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_UV`
UNION ALL
SELECT 'archive_day_vpd' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_vpd`
UNION ALL
SELECT 'archive_day_wbgt' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_wbgt`
UNION ALL
SELECT 'archive_day_wh26_rssi' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_wh26_rssi`
UNION ALL
SELECT 'archive_day_wh31_ch1_rssi' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_wh31_ch1_rssi`
UNION ALL
SELECT 'archive_day_wh31_ch1_sig' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_wh31_ch1_sig`
UNION ALL
SELECT 'archive_day_wh31_ch2_sig' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_wh31_ch2_sig`
UNION ALL
SELECT 'archive_day_wh40_rssi' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_wh40_rssi`
UNION ALL
SELECT 'archive_day_wh41_ch1_rssi' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_wh41_ch1_rssi`
UNION ALL
SELECT 'archive_day_wh51_ch1_rssi' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_wh51_ch1_rssi`
UNION ALL
SELECT 'archive_day_wh51_ch1_sig' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_wh51_ch1_sig`
UNION ALL
SELECT 'archive_day_wh57_rssi' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_wh57_rssi`
UNION ALL
SELECT 'archive_day_wind' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_wind`
UNION ALL
SELECT 'archive_day_windchill' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_windchill`
UNION ALL
SELECT 'archive_day_windDir' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_windDir`
UNION ALL
SELECT 'archive_day_windGust' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_windGust`
UNION ALL
SELECT 'archive_day_windGustDir' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_windGustDir`
UNION ALL
SELECT 'archive_day_windrun' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_windrun`
UNION ALL
SELECT 'archive_day_windSpeed' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_windSpeed`
UNION ALL
SELECT 'archive_day_ws80_batt' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_ws80_batt`
UNION ALL
SELECT 'archive_day_ws80_rssi' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_ws80_rssi`
UNION ALL
SELECT 'archive_day_ws80_sig' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_ws80_sig`
UNION ALL
SELECT 'archive_day_yearGDD' AS table_name, COUNT(*) AS exact_rows, MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch FROM `pocasi-loucka.eu`.`archive_day_yearGDD`
