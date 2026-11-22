-- Exact row-count snapshot for all 17 non-archive tables in loucka_reconstruction.
-- One SELECT statement; Weather MCP read-only execution; snapshot 2026-11-13 ~03:58 UTC.
SELECT 'rain_archive_original_202107' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`rain_archive_original_202107`
UNION ALL
SELECT 'rain_audit_202107' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`rain_audit_202107`
UNION ALL
SELECT 'rain_backup_202107_before_chmi_v1' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`rain_backup_202107_before_chmi_v1`
UNION ALL
SELECT 'rain_daily_reset_backup_2009_2011_v1' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`rain_daily_reset_backup_2009_2011_v1`
UNION ALL
SELECT 'rain_phase_a_201006_backup_20261030_v1' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`rain_phase_a_201006_backup_20261030_v1`
UNION ALL
SELECT 'rain_phase_a_backup_20261030_v1' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`rain_phase_a_backup_20261030_v1`
UNION ALL
SELECT 'rain_qc_202107' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`rain_qc_202107`
UNION ALL
SELECT 'rain_qc_daily_202107' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`rain_qc_daily_202107`
UNION ALL
SELECT 'rain_reconstruction_202107_chmi_v1' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`rain_reconstruction_202107_chmi_v1`
UNION ALL
SELECT 'reconstruction_batches' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`reconstruction_batches`
UNION ALL
SELECT 'reconstruction_candidates' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`reconstruction_candidates`
UNION ALL
SELECT 'reconstruction_changes' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`reconstruction_changes`
UNION ALL
SELECT 'reconstruction_humidity_202204' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`reconstruction_humidity_202204`
UNION ALL
SELECT 'reference_daily' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`reference_daily`
UNION ALL
SELECT 'reference_observations' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`reference_observations`
UNION ALL
SELECT 'reference_stations' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`reference_stations`
UNION ALL
SELECT 'wh1080_missing_5min_candidates_20261030' AS table_name, COUNT(*) AS exact_rows FROM `loucka_reconstruction`.`wh1080_missing_5min_candidates_20261030`
