-- READ-ONLY snapshot queries for the frozen GW3000 one-time insert-only backfill.
-- Execute each SELECT independently. Source watermark is captured by MAX(dateTime);
-- end bound for reads is captured_source_max + 1 (exclusive).
SELECT COUNT(*) AS source_rows, MIN(s.dateTime) AS source_min, MAX(s.dateTime) AS captured_source_max,
       COUNT(DISTINCT s.dateTime) AS unique_timestamps,
       SUM(s.usUnits=16 AND s.interval=5) AS expected_metadata_rows,
       SUM(t.dateTime IS NULL) AS target_absent, SUM(t.dateTime IS NOT NULL) AS target_present
FROM `pocasi-loucka.eu`.archive s
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=s.dateTime
WHERE s.dateTime>1793286600;

-- Exact 80-column schema compatibility (returns any mismatch).
SELECT s.column_name,s.column_type AS source_type,t.column_type AS target_type,
       s.is_nullable AS source_nullable,t.is_nullable AS target_nullable
FROM information_schema.columns s
JOIN information_schema.columns t ON t.table_name=s.table_name AND t.column_name=s.column_name
WHERE s.table_name='archive' AND s.table_schema='pocasi-loucka.eu'
  AND t.table_schema='loucka_reconstruction'
  AND (s.column_type<>t.column_type OR s.is_nullable<>t.is_nullable);

-- NULL count for every nullable/value column in the exact row mapping.
SELECT SUM(s.`ET` IS NULL) AS `ET`,
  SUM(s.`ET24` IS NULL) AS `ET24`,
  SUM(s.`GTS` IS NULL) AS `GTS`,
  SUM(s.`GTSdate` IS NULL) AS `GTSdate`,
  SUM(s.`UV` IS NULL) AS `UV`,
  SUM(s.`altimeter` IS NULL) AS `altimeter`,
  SUM(s.`appTemp` IS NULL) AS `appTemp`,
  SUM(s.`barometer` IS NULL) AS `barometer`,
  SUM(s.`batteryStatus1` IS NULL) AS `batteryStatus1`,
  SUM(s.`batteryStatus2` IS NULL) AS `batteryStatus2`,
  SUM(s.`bgt` IS NULL) AS `bgt`,
  SUM(s.`cloudbase` IS NULL) AS `cloudbase`,
  SUM(s.`dayET` IS NULL) AS `dayET`,
  SUM(s.`dewpoint` IS NULL) AS `dewpoint`,
  SUM(s.`extraHumid1` IS NULL) AS `extraHumid1`,
  SUM(s.`extraHumid2` IS NULL) AS `extraHumid2`,
  SUM(s.`extraTemp1` IS NULL) AS `extraTemp1`,
  SUM(s.`extraTemp2` IS NULL) AS `extraTemp2`,
  SUM(s.`heatindex` IS NULL) AS `heatindex`,
  SUM(s.`humidex` IS NULL) AS `humidex`,
  SUM(s.`inDewpoint` IS NULL) AS `inDewpoint`,
  SUM(s.`inHumidity` IS NULL) AS `inHumidity`,
  SUM(s.`inTemp` IS NULL) AS `inTemp`,
  SUM(s.`lightning_Batt` IS NULL) AS `lightning_Batt`,
  SUM(s.`lightning_distance` IS NULL) AS `lightning_distance`,
  SUM(s.`lightning_disturber_count` IS NULL) AS `lightning_disturber_count`,
  SUM(s.`lightning_energy` IS NULL) AS `lightning_energy`,
  SUM(s.`lightning_noise_count` IS NULL) AS `lightning_noise_count`,
  SUM(s.`lightning_strike_count` IS NULL) AS `lightning_strike_count`,
  SUM(s.`luminosity` IS NULL) AS `luminosity`,
  SUM(s.`maxSolarRad` IS NULL) AS `maxSolarRad`,
  SUM(s.`outEquiTemp` IS NULL) AS `outEquiTemp`,
  SUM(s.`outHumAbs` IS NULL) AS `outHumAbs`,
  SUM(s.`outHumidity` IS NULL) AS `outHumidity`,
  SUM(s.`outTemp` IS NULL) AS `outTemp`,
  SUM(s.`outThetaE` IS NULL) AS `outThetaE`,
  SUM(s.`pb` IS NULL) AS `pb`,
  SUM(s.`pm25_1` IS NULL) AS `pm25_1`,
  SUM(s.`pm25_Batt1` IS NULL) AS `pm25_Batt1`,
  SUM(s.`pressure` IS NULL) AS `pressure`,
  SUM(s.`radiation` IS NULL) AS `radiation`,
  SUM(s.`rain` IS NULL) AS `rain`,
  SUM(s.`rainDur` IS NULL) AS `rainDur`,
  SUM(s.`rainRate` IS NULL) AS `rainRate`,
  SUM(s.`seasonGDD` IS NULL) AS `seasonGDD`,
  SUM(s.`soilMoist1` IS NULL) AS `soilMoist1`,
  SUM(s.`soilMoistBatt1` IS NULL) AS `soilMoistBatt1`,
  SUM(s.`soilTemp1` IS NULL) AS `soilTemp1`,
  SUM(s.`soilTemp2` IS NULL) AS `soilTemp2`,
  SUM(s.`soilTemp3` IS NULL) AS `soilTemp3`,
  SUM(s.`soilTemp4` IS NULL) AS `soilTemp4`,
  SUM(s.`soilTemp5` IS NULL) AS `soilTemp5`,
  SUM(s.`soilTemp6` IS NULL) AS `soilTemp6`,
  SUM(s.`soilad1` IS NULL) AS `soilad1`,
  SUM(s.`sunshineDur` IS NULL) AS `sunshineDur`,
  SUM(s.`sunshine_time` IS NULL) AS `sunshine_time`,
  SUM(s.`vpd` IS NULL) AS `vpd`,
  SUM(s.`wbgt` IS NULL) AS `wbgt`,
  SUM(s.`wh26_rssi` IS NULL) AS `wh26_rssi`,
  SUM(s.`wh31_ch1_rssi` IS NULL) AS `wh31_ch1_rssi`,
  SUM(s.`wh31_ch1_sig` IS NULL) AS `wh31_ch1_sig`,
  SUM(s.`wh31_ch2_sig` IS NULL) AS `wh31_ch2_sig`,
  SUM(s.`wh40_rssi` IS NULL) AS `wh40_rssi`,
  SUM(s.`wh41_ch1_rssi` IS NULL) AS `wh41_ch1_rssi`,
  SUM(s.`wh51_ch1_rssi` IS NULL) AS `wh51_ch1_rssi`,
  SUM(s.`wh51_ch1_sig` IS NULL) AS `wh51_ch1_sig`,
  SUM(s.`wh57_rssi` IS NULL) AS `wh57_rssi`,
  SUM(s.`windDir` IS NULL) AS `windDir`,
  SUM(s.`windGust` IS NULL) AS `windGust`,
  SUM(s.`windGustDir` IS NULL) AS `windGustDir`,
  SUM(s.`windSpeed` IS NULL) AS `windSpeed`,
  SUM(s.`windchill` IS NULL) AS `windchill`,
  SUM(s.`windrun` IS NULL) AS `windrun`,
  SUM(s.`ws80_batt` IS NULL) AS `ws80_batt`,
  SUM(s.`ws80_rssi` IS NULL) AS `ws80_rssi`,
  SUM(s.`ws80_sig` IS NULL) AS `ws80_sig`,
  SUM(s.`yearGDD` IS NULL) AS `yearGDD`
FROM `pocasi-loucka.eu`.archive s WHERE s.dateTime>1793286600;

-- Stable ordered row digest. JSON_ARRAY argument order is the sorted 80-column list:
-- ["ET","ET24","GTS","GTSdate","UV","altimeter","appTemp","barometer","batteryStatus1","batteryStatus2","bgt","cloudbase","dateTime","dayET","dewpoint","extraHumid1","extraHumid2","extraTemp1","extraTemp2","heatindex","humidex","inDewpoint","inHumidity","inTemp","interval","lightning_Batt","lightning_distance","lightning_disturber_count","lightning_energy","lightning_noise_count","lightning_strike_count","luminosity","maxSolarRad","outEquiTemp","outHumAbs","outHumidity","outTemp","outThetaE","pb","pm25_1","pm25_Batt1","pressure","radiation","rain","rainDur","rainRate","seasonGDD","soilMoist1","soilMoistBatt1","soilTemp1","soilTemp2","soilTemp3","soilTemp4","soilTemp5","soilTemp6","soilad1","sunshineDur","sunshine_time","usUnits","vpd","wbgt","wh26_rssi","wh31_ch1_rssi","wh31_ch1_sig","wh31_ch2_sig","wh40_rssi","wh41_ch1_rssi","wh51_ch1_rssi","wh51_ch1_sig","wh57_rssi","windDir","windGust","windGustDir","windSpeed","windchill","windrun","ws80_batt","ws80_rssi","ws80_sig","yearGDD"]
SELECT COUNT(*) AS row_count,MIN(dateTime) AS source_min,MAX(dateTime) AS captured_source_max,
       SHA2(GROUP_CONCAT(row_sha ORDER BY dateTime SEPARATOR ''),256) AS ordered_row_sha256,
       SHA2(GROUP_CONCAT(CAST(dateTime AS CHAR) ORDER BY dateTime SEPARATOR ','),256) AS ordered_timestamp_sha256,
       CHAR_LENGTH(GROUP_CONCAT(row_sha ORDER BY dateTime SEPARATOR '')) AS row_sha_stream_length
FROM (SELECT s.dateTime,SHA2(CAST(JSON_ARRAY(s.`ET`, s.`ET24`, s.`GTS`, s.`GTSdate`, s.`UV`, s.`altimeter`, s.`appTemp`, s.`barometer`, s.`batteryStatus1`, s.`batteryStatus2`, s.`bgt`, s.`cloudbase`, s.`dateTime`, s.`dayET`, s.`dewpoint`, s.`extraHumid1`, s.`extraHumid2`, s.`extraTemp1`, s.`extraTemp2`, s.`heatindex`, s.`humidex`, s.`inDewpoint`, s.`inHumidity`, s.`inTemp`, s.`interval`, s.`lightning_Batt`, s.`lightning_distance`, s.`lightning_disturber_count`, s.`lightning_energy`, s.`lightning_noise_count`, s.`lightning_strike_count`, s.`luminosity`, s.`maxSolarRad`, s.`outEquiTemp`, s.`outHumAbs`, s.`outHumidity`, s.`outTemp`, s.`outThetaE`, s.`pb`, s.`pm25_1`, s.`pm25_Batt1`, s.`pressure`, s.`radiation`, s.`rain`, s.`rainDur`, s.`rainRate`, s.`seasonGDD`, s.`soilMoist1`, s.`soilMoistBatt1`, s.`soilTemp1`, s.`soilTemp2`, s.`soilTemp3`, s.`soilTemp4`, s.`soilTemp5`, s.`soilTemp6`, s.`soilad1`, s.`sunshineDur`, s.`sunshine_time`, s.`usUnits`, s.`vpd`, s.`wbgt`, s.`wh26_rssi`, s.`wh31_ch1_rssi`, s.`wh31_ch1_sig`, s.`wh31_ch2_sig`, s.`wh40_rssi`, s.`wh41_ch1_rssi`, s.`wh51_ch1_rssi`, s.`wh51_ch1_sig`, s.`wh57_rssi`, s.`windDir`, s.`windGust`, s.`windGustDir`, s.`windSpeed`, s.`windchill`, s.`windrun`, s.`ws80_batt`, s.`ws80_rssi`, s.`ws80_sig`, s.`yearGDD`) AS CHAR),256) AS row_sha
      FROM `pocasi-loucka.eu`.archive s WHERE s.dateTime>1793286600) snapshot_hash;

-- Cadence grid gaps are conditional slots, not confirmed lost measurements.
SELECT previous_timestamp,dateTime,delta_seconds,delta_seconds/300-1 AS conditional_missing_5m_slots
FROM (SELECT dateTime,LAG(dateTime) OVER (ORDER BY dateTime) AS previous_timestamp,
             dateTime-LAG(dateTime) OVER (ORDER BY dateTime) AS delta_seconds
      FROM `pocasi-loucka.eu`.archive WHERE dateTime>1793286600) steps
WHERE delta_seconds>300 ORDER BY previous_timestamp;

-- Audit-history coverage in the bounded candidate range.
SELECT COUNT(*) AS change_rows FROM loucka_reconstruction.reconstruction_changes
WHERE target_time>1793286600;
