-- Reproducible 80-column exact snapshot comparison, 2026-11-22 20:20 UTC.
-- Immutable audit cutoff: 1795378800. Production continues to grow after it.
-- 79 NULL-safe data/metadata columns; dateTime is the exact primary-key join.
-- Run each SELECT separately, READ ONLY. Expected 1,686,773 common rows.
-- 75 unchanged non-key columns; changes in outTemp, outHumidity, rain, rainRate.

-- Block 1: 27 fields.
SELECT COUNT(*) AS common_rows,
 SUM(NOT(s.`usUnits` <=> t.`usUnits`)) AS `changed_usUnits`,
 SUM(NOT(s.`interval` <=> t.`interval`)) AS `changed_interval`,
 SUM(NOT(s.`altimeter` <=> t.`altimeter`)) AS `changed_altimeter`,
 SUM(NOT(s.`appTemp` <=> t.`appTemp`)) AS `changed_appTemp`,
 SUM(NOT(s.`barometer` <=> t.`barometer`)) AS `changed_barometer`,
 SUM(NOT(s.`batteryStatus1` <=> t.`batteryStatus1`)) AS `changed_batteryStatus1`,
 SUM(NOT(s.`batteryStatus2` <=> t.`batteryStatus2`)) AS `changed_batteryStatus2`,
 SUM(NOT(s.`bgt` <=> t.`bgt`)) AS `changed_bgt`,
 SUM(NOT(s.`cloudbase` <=> t.`cloudbase`)) AS `changed_cloudbase`,
 SUM(NOT(s.`dewpoint` <=> t.`dewpoint`)) AS `changed_dewpoint`,
 SUM(NOT(s.`ET` <=> t.`ET`)) AS `changed_ET`,
 SUM(NOT(s.`extraHumid1` <=> t.`extraHumid1`)) AS `changed_extraHumid1`,
 SUM(NOT(s.`extraHumid2` <=> t.`extraHumid2`)) AS `changed_extraHumid2`,
 SUM(NOT(s.`extraTemp1` <=> t.`extraTemp1`)) AS `changed_extraTemp1`,
 SUM(NOT(s.`extraTemp2` <=> t.`extraTemp2`)) AS `changed_extraTemp2`,
 SUM(NOT(s.`heatindex` <=> t.`heatindex`)) AS `changed_heatindex`,
 SUM(NOT(s.`humidex` <=> t.`humidex`)) AS `changed_humidex`,
 SUM(NOT(s.`inDewpoint` <=> t.`inDewpoint`)) AS `changed_inDewpoint`,
 SUM(NOT(s.`inHumidity` <=> t.`inHumidity`)) AS `changed_inHumidity`,
 SUM(NOT(s.`inTemp` <=> t.`inTemp`)) AS `changed_inTemp`,
 SUM(NOT(s.`lightning_Batt` <=> t.`lightning_Batt`)) AS `changed_lightning_Batt`,
 SUM(NOT(s.`lightning_distance` <=> t.`lightning_distance`)) AS `changed_lightning_distance`,
 SUM(NOT(s.`lightning_disturber_count` <=> t.`lightning_disturber_count`)) AS `changed_lightning_disturber_count`,
 SUM(NOT(s.`lightning_energy` <=> t.`lightning_energy`)) AS `changed_lightning_energy`,
 SUM(NOT(s.`lightning_noise_count` <=> t.`lightning_noise_count`)) AS `changed_lightning_noise_count`,
 SUM(NOT(s.`lightning_strike_count` <=> t.`lightning_strike_count`)) AS `changed_lightning_strike_count`,
 SUM(NOT(s.`luminosity` <=> t.`luminosity`)) AS `changed_luminosity`
FROM `pocasi-loucka.eu`.archive s
JOIN loucka_reconstruction.archive t ON t.dateTime=s.dateTime
WHERE s.dateTime<=1795378800;

-- Block 2: 27 fields.
SELECT COUNT(*) AS common_rows,
 SUM(NOT(s.`maxSolarRad` <=> t.`maxSolarRad`)) AS `changed_maxSolarRad`,
 SUM(NOT(s.`outHumidity` <=> t.`outHumidity`)) AS `changed_outHumidity`,
 SUM(NOT(s.`outTemp` <=> t.`outTemp`)) AS `changed_outTemp`,
 SUM(NOT(s.`pb` <=> t.`pb`)) AS `changed_pb`,
 SUM(NOT(s.`pm25_1` <=> t.`pm25_1`)) AS `changed_pm25_1`,
 SUM(NOT(s.`pm25_Batt1` <=> t.`pm25_Batt1`)) AS `changed_pm25_Batt1`,
 SUM(NOT(s.`pressure` <=> t.`pressure`)) AS `changed_pressure`,
 SUM(NOT(s.`radiation` <=> t.`radiation`)) AS `changed_radiation`,
 SUM(NOT(s.`rain` <=> t.`rain`)) AS `changed_rain`,
 SUM(NOT(s.`rainDur` <=> t.`rainDur`)) AS `changed_rainDur`,
 SUM(NOT(s.`rainRate` <=> t.`rainRate`)) AS `changed_rainRate`,
 SUM(NOT(s.`soilad1` <=> t.`soilad1`)) AS `changed_soilad1`,
 SUM(NOT(s.`soilMoist1` <=> t.`soilMoist1`)) AS `changed_soilMoist1`,
 SUM(NOT(s.`soilMoistBatt1` <=> t.`soilMoistBatt1`)) AS `changed_soilMoistBatt1`,
 SUM(NOT(s.`soilTemp1` <=> t.`soilTemp1`)) AS `changed_soilTemp1`,
 SUM(NOT(s.`soilTemp2` <=> t.`soilTemp2`)) AS `changed_soilTemp2`,
 SUM(NOT(s.`soilTemp3` <=> t.`soilTemp3`)) AS `changed_soilTemp3`,
 SUM(NOT(s.`soilTemp4` <=> t.`soilTemp4`)) AS `changed_soilTemp4`,
 SUM(NOT(s.`soilTemp5` <=> t.`soilTemp5`)) AS `changed_soilTemp5`,
 SUM(NOT(s.`soilTemp6` <=> t.`soilTemp6`)) AS `changed_soilTemp6`,
 SUM(NOT(s.`sunshine_time` <=> t.`sunshine_time`)) AS `changed_sunshine_time`,
 SUM(NOT(s.`sunshineDur` <=> t.`sunshineDur`)) AS `changed_sunshineDur`,
 SUM(NOT(s.`UV` <=> t.`UV`)) AS `changed_UV`,
 SUM(NOT(s.`vpd` <=> t.`vpd`)) AS `changed_vpd`,
 SUM(NOT(s.`wbgt` <=> t.`wbgt`)) AS `changed_wbgt`,
 SUM(NOT(s.`wh26_rssi` <=> t.`wh26_rssi`)) AS `changed_wh26_rssi`,
 SUM(NOT(s.`wh31_ch1_rssi` <=> t.`wh31_ch1_rssi`)) AS `changed_wh31_ch1_rssi`
FROM `pocasi-loucka.eu`.archive s
JOIN loucka_reconstruction.archive t ON t.dateTime=s.dateTime
WHERE s.dateTime<=1795378800;

-- Block 3: 25 fields.
SELECT COUNT(*) AS common_rows,
 SUM(NOT(s.`wh31_ch1_sig` <=> t.`wh31_ch1_sig`)) AS `changed_wh31_ch1_sig`,
 SUM(NOT(s.`wh31_ch2_sig` <=> t.`wh31_ch2_sig`)) AS `changed_wh31_ch2_sig`,
 SUM(NOT(s.`wh40_rssi` <=> t.`wh40_rssi`)) AS `changed_wh40_rssi`,
 SUM(NOT(s.`wh41_ch1_rssi` <=> t.`wh41_ch1_rssi`)) AS `changed_wh41_ch1_rssi`,
 SUM(NOT(s.`wh51_ch1_rssi` <=> t.`wh51_ch1_rssi`)) AS `changed_wh51_ch1_rssi`,
 SUM(NOT(s.`wh51_ch1_sig` <=> t.`wh51_ch1_sig`)) AS `changed_wh51_ch1_sig`,
 SUM(NOT(s.`wh57_rssi` <=> t.`wh57_rssi`)) AS `changed_wh57_rssi`,
 SUM(NOT(s.`windchill` <=> t.`windchill`)) AS `changed_windchill`,
 SUM(NOT(s.`windDir` <=> t.`windDir`)) AS `changed_windDir`,
 SUM(NOT(s.`windGust` <=> t.`windGust`)) AS `changed_windGust`,
 SUM(NOT(s.`windGustDir` <=> t.`windGustDir`)) AS `changed_windGustDir`,
 SUM(NOT(s.`windrun` <=> t.`windrun`)) AS `changed_windrun`,
 SUM(NOT(s.`windSpeed` <=> t.`windSpeed`)) AS `changed_windSpeed`,
 SUM(NOT(s.`ws80_batt` <=> t.`ws80_batt`)) AS `changed_ws80_batt`,
 SUM(NOT(s.`ws80_rssi` <=> t.`ws80_rssi`)) AS `changed_ws80_rssi`,
 SUM(NOT(s.`ws80_sig` <=> t.`ws80_sig`)) AS `changed_ws80_sig`,
 SUM(NOT(s.`outEquiTemp` <=> t.`outEquiTemp`)) AS `changed_outEquiTemp`,
 SUM(NOT(s.`GTS` <=> t.`GTS`)) AS `changed_GTS`,
 SUM(NOT(s.`GTSdate` <=> t.`GTSdate`)) AS `changed_GTSdate`,
 SUM(NOT(s.`dayET` <=> t.`dayET`)) AS `changed_dayET`,
 SUM(NOT(s.`ET24` <=> t.`ET24`)) AS `changed_ET24`,
 SUM(NOT(s.`yearGDD` <=> t.`yearGDD`)) AS `changed_yearGDD`,
 SUM(NOT(s.`seasonGDD` <=> t.`seasonGDD`)) AS `changed_seasonGDD`,
 SUM(NOT(s.`outHumAbs` <=> t.`outHumAbs`)) AS `changed_outHumAbs`,
 SUM(NOT(s.`outThetaE` <=> t.`outThetaE`)) AS `changed_outThetaE`
FROM `pocasi-loucka.eu`.archive s
JOIN loucka_reconstruction.archive t ON t.dateTime=s.dateTime
WHERE s.dateTime<=1795378800;

