-- 2021 diagnostic only. No values or candidates are emitted for application.
-- Reconcile targets whose latest applied rain event cleared rain to NULL,
-- while the current archive contains zero matching a separate CHMI artifact.
WITH applied_ranked AS (
  SELECT c.target_time,c.id,c.batch_key,c.old_value,c.new_value,c.created_at,
         ROW_NUMBER() OVER(PARTITION BY c.target_time
                           ORDER BY c.created_at DESC,c.id DESC) AS rn
  FROM reconstruction_changes c
  WHERE c.variable='rain' AND c.state='applied'
    AND c.target_time>=1626940800 AND c.target_time<=1627145700
), candidates AS (
  SELECT * FROM applied_ranked WHERE rn=1 AND new_value IS NULL
), all_ranked AS (
  SELECT c.target_time,c.id,c.batch_key,c.state,c.old_value,c.new_value,c.created_at,
         ROW_NUMBER() OVER(PARTITION BY c.target_time
                           ORDER BY c.created_at DESC,c.id DESC) AS rn
  FROM reconstruction_changes c
  JOIN candidates x ON x.target_time=c.target_time
  WHERE c.variable='rain'
), latest AS (SELECT * FROM all_ranked WHERE rn=1)
SELECT COUNT(*) AS targets,
       MIN(x.target_time) AS first_epoch,MAX(x.target_time) AS last_epoch,
       MIN(x.batch_key) AS applied_batch,
       SUM(x.old_value <=> o.original_rain_cm) AS applied_old_matches_original,
       SUM(a.rain IS NULL) AS current_null,
       SUM(a.rain <=> 0) AS current_zero,
       SUM(a.rain <=> x.old_value) AS current_matches_applied_old,
       SUM(a.rain <=> x.new_value) AS current_matches_applied_new,
       SUM(o.target_time IS NOT NULL) AS original_snapshot_rows,
       SUM(a.rain <=> o.original_rain_cm) AS current_matches_original,
       SUM(r.dateTime IS NOT NULL) AS reconstruction_rows,
       SUM(a.rain <=> r.rain_cm) AS current_matches_reconstruction,
       SUM(r.rain_cm <=> 0) AS reconstruction_zero,
       SUM(au.target_time IS NOT NULL) AS audit_rows,
       SUM(q.target_time IS NOT NULL) AS qc_rows,
       SUM(l.state='applied') AS latest_overall_applied,
       SUM(l.state='reverted') AS latest_overall_reverted,
       MIN(l.batch_key) AS latest_overall_batch,
       MIN(r.method) AS method,
       MIN(au.class_code) AS audit_class,
       MIN(au.evidence_level) AS evidence_level,
       MIN(q.qc_status) AS qc_status,
       MIN(q.confidence_level) AS confidence_level,
       MIN(l.created_at) AS latest_history_created_at_min,
       MAX(l.created_at) AS latest_history_created_at_max
FROM candidates x
JOIN latest l ON l.target_time=x.target_time
LEFT JOIN archive a ON a.dateTime=x.target_time
LEFT JOIN rain_archive_original_202107 o ON o.target_time=x.target_time
LEFT JOIN rain_reconstruction_202107_chmi_v1 r ON r.dateTime=x.target_time
LEFT JOIN rain_audit_202107 au ON au.target_time=x.target_time
LEFT JOIN rain_qc_202107 q ON q.target_time=x.target_time;
