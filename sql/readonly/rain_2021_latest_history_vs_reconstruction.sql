-- Diagnostic-only reconciliation for protected 2021 rain targets.
-- Compare latest logged applied/reverted expectation with current archive,
-- the separate CHMI reconstruction table, and original archive snapshot.
WITH ranked AS (
  SELECT c.target_time,c.state,c.old_value,c.new_value,c.batch_key,c.created_at,c.id,
         ROW_NUMBER() OVER(PARTITION BY c.target_time
                           ORDER BY c.created_at DESC,c.id DESC) AS rn
  FROM reconstruction_changes c
  WHERE c.variable='rain'
), latest AS (SELECT * FROM ranked WHERE rn=1), mismatches AS (
  SELECT l.* FROM latest l JOIN archive a ON a.dateTime=l.target_time
  WHERE (l.state='applied' AND NOT (a.rain <=> l.new_value))
     OR (l.state='reverted' AND NOT (a.rain <=> l.old_value))
)
SELECT m.state,m.batch_key,COUNT(*) AS targets,
       MIN(m.target_time) AS first_epoch,MAX(m.target_time) AS last_epoch,
       SUM(a.rain IS NULL) AS current_null,
       SUM(a.rain <=> 0) AS current_zero,
       SUM(r.dateTime IS NOT NULL) AS reconstruction_rows,
       SUM(a.rain <=> r.rain_cm) AS current_matches_reconstruction,
       SUM(m.old_value <=> o.original_rain_cm) AS history_old_matches_original,
       SUM(au.target_time IS NOT NULL) AS audit_rows,
       SUM(q.target_time IS NOT NULL) AS qc_rows,
       MIN(r.method) AS method_min,MAX(r.method) AS method_max
FROM mismatches m
JOIN archive a ON a.dateTime=m.target_time
LEFT JOIN rain_reconstruction_202107_chmi_v1 r ON r.dateTime=m.target_time
LEFT JOIN rain_archive_original_202107 o ON o.target_time=m.target_time
LEFT JOIN rain_audit_202107 au ON au.target_time=m.target_time
LEFT JOIN rain_qc_202107 q ON q.target_time=m.target_time
GROUP BY m.state,m.batch_key ORDER BY m.state,m.batch_key;
