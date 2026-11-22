-- Full 80-column source versus reconstruction parity checkpoint, 2026-11-22.
-- Original fields: 80 columns total, dateTime is equality join key, 79
-- remaining columns compared NULL-safely using <=> in 3 independent chunks.
-- Data snapshot cutoff is inclusive UTC epoch 1795377300.
-- All statements are SELECT only, never changes original or target rows.
-- These checks verify actual DB DIFFERENCES, not meteorological accuracy.
-- At each SELECT: overlapping source rows should be 1686768. All unchanged
-- fields should return 0. Only outTemp,outHumidity,rain,rainRate may differ.
-- Expected totals from verified live check: 47,20422,2201,59595 respectively.
-- Individual chunks may execute at different instants, but the fixed UTC
-- cutoff prevents later appended GW3000 rows from changing membership.
-- NOTE: target-only 10399 rows are excluded here and verified separately.

-- Chunk 1/3: 28 columns.
SELECT COUNT(*) AS overlap_rows,
       SUM(NOT (s.`usUnits` <=> t.`usUnits`)) AS `diff_usUnits`,
       SUM(NOT (s.`interval` <=> t.`interval`)) AS `diff_interval`,
       SUM(NOT (s.`altimeter` <=> t.`altimeter`)) AS `diff_altimeter`,
       SUM(NOT (s.`appTemp` <=> t.`appTemp`)) AS `diff_appTemp`,
       SUM(NOT (s.`barometer` <=> t.`barometer`)) AS `diff_barometer`,
       SUM(NOT (s.`batteryStatus1` <=> t.`batteryStatus1`)) AS `diff_batteryStatus1`,
       SUM(NOT (s.`batteryStatus2` <=> t.`batteryStatus2`)) AS `diff_batteryStatus2`,
       SUM(NOT (s.`bgt` <=> t.`bgt`)) AS `diff_bgt`,
       SUM(NOT (s.`cloudbase` <=> t.`cloudbase`)) AS `diff_cloudbase`,
       SUM(NOT (s.`dewpoint` <=> t.`dewpoint`)) AS `diff_dewpoint`,
       SUM(NOT (s.`ET` <=> t.`ET`)) AS `diff_ET`,
       SUM(NOT (s.`extraHumid1` <=> t.`extraHumid1`)) AS `diff_extraHumid1`,
       SUM(NOT (s.`extraHumid2` <=> t.`extraHumid2`)) AS `diff_extraHumid2`,
       SUM(NOT (s.`extraTemp1` <=> t.`extraTemp1`)) AS `diff_extraTemp1`,
       SUM(NOT (s.`extraTemp2` <=> t.`extraTemp2`)) AS `diff_extraTemp2`,
       SUM(NOT (s.`heatindex` <=> t.`heatindex`)) AS `diff_heatindex`,
       SUM(NOT (s.`humidex` <=> t.`humidex`)) AS `diff_humidex`,
       SUM(NOT (s.`inDewpoint` <=> t.`inDewpoint`)) AS `diff_inDewpoint`,
       SUM(NOT (s.`inHumidity` <=> t.`inHumidity`)) AS `diff_inHumidity`,
       SUM(NOT (s.`inTemp` <=> t.`inTemp`)) AS `diff_inTemp`,
       SUM(NOT (s.`lightning_Batt` <=> t.`lightning_Batt`)) AS `diff_lightning_Batt`,
       SUM(NOT (s.`lightning_distance` <=> t.`lightning_distance`)) AS `diff_lightning_distance`,
       SUM(NOT (s.`lightning_disturber_count` <=> t.`lightning_disturber_count`)) AS `diff_lightning_disturber_count`,
       SUM(NOT (s.`lightning_energy` <=> t.`lightning_energy`)) AS `diff_lightning_energy`,
       SUM(NOT (s.`lightning_noise_count` <=> t.`lightning_noise_count`)) AS `diff_lightning_noise_count`,
       SUM(NOT (s.`lightning_strike_count` <=> t.`lightning_strike_count`)) AS `diff_lightning_strike_count`,
       SUM(NOT (s.`luminosity` <=> t.`luminosity`)) AS `diff_luminosity`,
       SUM(NOT (s.`maxSolarRad` <=> t.`maxSolarRad`)) AS `diff_maxSolarRad`
FROM `pocasi-loucka.eu`.archive s
JOIN loucka_reconstruction.archive t ON t.dateTime=s.dateTime
WHERE s.dateTime<=1795377300;

-- Chunk 2/3: 28 columns.
SELECT COUNT(*) AS overlap_rows,
       SUM(NOT (s.`outHumidity` <=> t.`outHumidity`)) AS `diff_outHumidity`,
       SUM(NOT (s.`outTemp` <=> t.`outTemp`)) AS `diff_outTemp`,
       SUM(NOT (s.`pb` <=> t.`pb`)) AS `diff_pb`,
       SUM(NOT (s.`pm25_1` <=> t.`pm25_1`)) AS `diff_pm25_1`,
       SUM(NOT (s.`pm25_Batt1` <=> t.`pm25_Batt1`)) AS `diff_pm25_Batt1`,
       SUM(NOT (s.`pressure` <=> t.`pressure`)) AS `diff_pressure`,
       SUM(NOT (s.`radiation` <=> t.`radiation`)) AS `diff_radiation`,
       SUM(NOT (s.`rain` <=> t.`rain`)) AS `diff_rain`,
       SUM(NOT (s.`rainDur` <=> t.`rainDur`)) AS `diff_rainDur`,
       SUM(NOT (s.`rainRate` <=> t.`rainRate`)) AS `diff_rainRate`,
       SUM(NOT (s.`soilad1` <=> t.`soilad1`)) AS `diff_soilad1`,
       SUM(NOT (s.`soilMoist1` <=> t.`soilMoist1`)) AS `diff_soilMoist1`,
       SUM(NOT (s.`soilMoistBatt1` <=> t.`soilMoistBatt1`)) AS `diff_soilMoistBatt1`,
       SUM(NOT (s.`soilTemp1` <=> t.`soilTemp1`)) AS `diff_soilTemp1`,
       SUM(NOT (s.`soilTemp2` <=> t.`soilTemp2`)) AS `diff_soilTemp2`,
       SUM(NOT (s.`soilTemp3` <=> t.`soilTemp3`)) AS `diff_soilTemp3`,
       SUM(NOT (s.`soilTemp4` <=> t.`soilTemp4`)) AS `diff_soilTemp4`,
       SUM(NOT (s.`soilTemp5` <=> t.`soilTemp5`)) AS `diff_soilTemp5`,
       SUM(NOT (s.`soilTemp6` <=> t.`soilTemp6`)) AS `diff_soilTemp6`,
       SUM(NOT (s.`sunshine_time` <=> t.`sunshine_time`)) AS `diff_sunshine_time`,
       SUM(NOT (s.`sunshineDur` <=> t.`sunshineDur`)) AS `diff_sunshineDur`,
       SUM(NOT (s.`UV` <=> t.`UV`)) AS `diff_UV`,
       SUM(NOT (s.`vpd` <=> t.`vpd`)) AS `diff_vpd`,
       SUM(NOT (s.`wbgt` <=> t.`wbgt`)) AS `diff_wbgt`,
       SUM(NOT (s.`wh26_rssi` <=> t.`wh26_rssi`)) AS `diff_wh26_rssi`,
       SUM(NOT (s.`wh31_ch1_rssi` <=> t.`wh31_ch1_rssi`)) AS `diff_wh31_ch1_rssi`,
       SUM(NOT (s.`wh31_ch1_sig` <=> t.`wh31_ch1_sig`)) AS `diff_wh31_ch1_sig`,
       SUM(NOT (s.`wh31_ch2_sig` <=> t.`wh31_ch2_sig`)) AS `diff_wh31_ch2_sig`
FROM `pocasi-loucka.eu`.archive s
JOIN loucka_reconstruction.archive t ON t.dateTime=s.dateTime
WHERE s.dateTime<=1795377300;

-- Chunk 3/3: 23 columns.
SELECT COUNT(*) AS overlap_rows,
       SUM(NOT (s.`wh40_rssi` <=> t.`wh40_rssi`)) AS `diff_wh40_rssi`,
       SUM(NOT (s.`wh41_ch1_rssi` <=> t.`wh41_ch1_rssi`)) AS `diff_wh41_ch1_rssi`,
       SUM(NOT (s.`wh51_ch1_rssi` <=> t.`wh51_ch1_rssi`)) AS `diff_wh51_ch1_rssi`,
       SUM(NOT (s.`wh51_ch1_sig` <=> t.`wh51_ch1_sig`)) AS `diff_wh51_ch1_sig`,
       SUM(NOT (s.`wh57_rssi` <=> t.`wh57_rssi`)) AS `diff_wh57_rssi`,
       SUM(NOT (s.`windchill` <=> t.`windchill`)) AS `diff_windchill`,
       SUM(NOT (s.`windDir` <=> t.`windDir`)) AS `diff_windDir`,
       SUM(NOT (s.`windGust` <=> t.`windGust`)) AS `diff_windGust`,
       SUM(NOT (s.`windGustDir` <=> t.`windGustDir`)) AS `diff_windGustDir`,
       SUM(NOT (s.`windrun` <=> t.`windrun`)) AS `diff_windrun`,
       SUM(NOT (s.`windSpeed` <=> t.`windSpeed`)) AS `diff_windSpeed`,
       SUM(NOT (s.`ws80_batt` <=> t.`ws80_batt`)) AS `diff_ws80_batt`,
       SUM(NOT (s.`ws80_rssi` <=> t.`ws80_rssi`)) AS `diff_ws80_rssi`,
       SUM(NOT (s.`ws80_sig` <=> t.`ws80_sig`)) AS `diff_ws80_sig`,
       SUM(NOT (s.`outEquiTemp` <=> t.`outEquiTemp`)) AS `diff_outEquiTemp`,
       SUM(NOT (s.`GTS` <=> t.`GTS`)) AS `diff_GTS`,
       SUM(NOT (s.`GTSdate` <=> t.`GTSdate`)) AS `diff_GTSdate`,
       SUM(NOT (s.`dayET` <=> t.`dayET`)) AS `diff_dayET`,
       SUM(NOT (s.`ET24` <=> t.`ET24`)) AS `diff_ET24`,
       SUM(NOT (s.`yearGDD` <=> t.`yearGDD`)) AS `diff_yearGDD`,
       SUM(NOT (s.`seasonGDD` <=> t.`seasonGDD`)) AS `diff_seasonGDD`,
       SUM(NOT (s.`outHumAbs` <=> t.`outHumAbs`)) AS `diff_outHumAbs`,
       SUM(NOT (s.`outThetaE` <=> t.`outThetaE`)) AS `diff_outThetaE`
FROM `pocasi-loucka.eu`.archive s
JOIN loucka_reconstruction.archive t ON t.dateTime=s.dateTime
WHERE s.dateTime<=1795377300;

-- Count timestamp discrepancies for the SAME frozen cutoff only.
SELECT
 (SELECT COUNT(*) FROM `pocasi-loucka.eu`.archive s
   LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=s.dateTime
   WHERE s.dateTime<=1795377300 AND t.dateTime IS NULL) AS source_missing_in_target,
 (SELECT COUNT(*) FROM loucka_reconstruction.archive t
   LEFT JOIN `pocasi-loucka.eu`.archive s ON s.dateTime=t.dateTime
   WHERE t.dateTime<=1795377300 AND s.dateTime IS NULL) AS target_only,
 (SELECT COUNT(*) FROM `pocasi-loucka.eu`.archive s
   JOIN loucka_reconstruction.archive t ON t.dateTime=s.dateTime
   WHERE s.dateTime<=1795377300) AS overlap_rows;
