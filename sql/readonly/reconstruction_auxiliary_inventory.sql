-- Read-only reconstruction DB auxiliary inventory; execute statements separately.
-- Snapshot used in report: 2026-11-12 22:11:11 UTC.
SELECT UTC_TIMESTAMP() AS captured_utc, NOW() AS db_now,
       @@session.time_zone AS session_time_zone,
       @@system_time_zone AS system_time_zone;
SELECT TABLE_NAME, TABLE_ROWS AS estimated_rows, ENGINE
FROM information_schema.TABLES
WHERE TABLE_SCHEMA='loucka_reconstruction'
ORDER BY TABLE_NAME;
SELECT COUNT(*) AS exact_archive_rows, MIN(dateTime) AS min_epoch,
       MAX(dateTime) AS max_epoch
FROM loucka_reconstruction.archive;
SELECT b.state, COUNT(DISTINCT b.batch_id) AS batches,
       COUNT(c.batch_id) AS candidates, MIN(c.target_time) AS min_target_epoch,
       MAX(c.target_time) AS max_target_epoch
FROM loucka_reconstruction.reconstruction_batches b
LEFT JOIN loucka_reconstruction.reconstruction_candidates c
  ON c.batch_id=b.batch_id
GROUP BY b.state ORDER BY b.state;
SELECT state, COUNT(*) AS events,
       COUNT(DISTINCT CONCAT(target_time, ':', variable)) AS target_variable_pairs,
       MAX(created_at) AS latest_event
FROM loucka_reconstruction.reconstruction_changes
GROUP BY state ORDER BY state;
-- Exact per-table counts (kept separate for connector compatibility).
SELECT 'reconstruction_humidity_202204' AS table_name, COUNT(*) AS exact_rows FROM loucka_reconstruction.reconstruction_humidity_202204;
SELECT 'reference_daily' AS table_name, COUNT(*) AS exact_rows FROM loucka_reconstruction.reference_daily;
SELECT 'reference_stations' AS table_name, COUNT(*) AS exact_rows FROM loucka_reconstruction.reference_stations;
SELECT 'rain_audit_202107' AS table_name, COUNT(*) AS exact_rows FROM loucka_reconstruction.rain_audit_202107;
SELECT 'rain_qc_202107' AS table_name, COUNT(*) AS exact_rows FROM loucka_reconstruction.rain_qc_202107;
SELECT 'rain_qc_daily_202107' AS table_name, COUNT(*) AS exact_rows FROM loucka_reconstruction.rain_qc_daily_202107;
SELECT 'rain_archive_original_202107' AS table_name, COUNT(*) AS exact_rows FROM loucka_reconstruction.rain_archive_original_202107;
SELECT 'rain_reconstruction_202107_chmi_v1' AS table_name, COUNT(*) AS exact_rows FROM loucka_reconstruction.rain_reconstruction_202107_chmi_v1;
SELECT 'rain_backup_202107_before_chmi_v1' AS table_name, COUNT(*) AS exact_rows FROM loucka_reconstruction.rain_backup_202107_before_chmi_v1;
SELECT 'rain_daily_reset_backup_2009_2011_v1' AS table_name, COUNT(*) AS exact_rows FROM loucka_reconstruction.rain_daily_reset_backup_2009_2011_v1;
SELECT 'rain_phase_a_201006_backup_20261030_v1' AS table_name, COUNT(*) AS exact_rows FROM loucka_reconstruction.rain_phase_a_201006_backup_20261030_v1;
SELECT 'rain_phase_a_backup_20261030_v1' AS table_name, COUNT(*) AS exact_rows FROM loucka_reconstruction.rain_phase_a_backup_20261030_v1;
SELECT 'wh1080_missing_5min_candidates_20261030' AS table_name, COUNT(*) AS exact_rows FROM loucka_reconstruction.wh1080_missing_5min_candidates_20261030;
SELECT decision, COUNT(*) AS rows_count, MIN(target_time) AS min_target_epoch,
       MAX(target_time) AS max_target_epoch, MAX(created_at) AS latest_created
FROM loucka_reconstruction.reconstruction_humidity_202204
GROUP BY decision ORDER BY decision;
SELECT station_id, quality_status, COUNT(*) AS rows_count,
       MIN(local_date) AS first_date, MAX(local_date) AS last_date
FROM loucka_reconstruction.reference_daily
GROUP BY station_id, quality_status ORDER BY station_id, quality_status;
SELECT class_code, evidence_level, COUNT(*) AS rows_count,
       SUM(proposed_replacement_mm IS NOT NULL) AS proposed_nonnull,
       MIN(target_time) AS min_target_epoch, MAX(target_time) AS max_target_epoch
FROM loucka_reconstruction.rain_audit_202107
GROUP BY class_code, evidence_level ORDER BY class_code;
SELECT source_db, status, COUNT(*) AS rows_count,
       MIN(target_time) AS min_target_epoch, MAX(target_time) AS max_target_epoch,
       MAX(created_at) AS latest_created
FROM loucka_reconstruction.wh1080_missing_5min_candidates_20261030
GROUP BY source_db, status ORDER BY source_db, status;
