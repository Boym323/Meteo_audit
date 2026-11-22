-- Read-only reconciliation of the April 2022 RH decision table, current archive,
-- and latest applied/history event. UTC range [1648771200,1651363200).
WITH ranked AS (
 SELECT id,target_time,variable,state,old_value,new_value,source_value,created_at,
        ROW_NUMBER() OVER (
          PARTITION BY target_time,variable ORDER BY created_at DESC,id DESC
        ) AS rn
 FROM loucka_reconstruction.reconstruction_changes
 WHERE variable='outHumidity'
   AND target_time>=1648771200 AND target_time<1651363200
), latest AS (SELECT * FROM ranked WHERE rn=1)
SELECT t.decision, COUNT(*) AS decision_rows,
       SUM(a.dateTime IS NULL) AS missing_archive_row,
       SUM(a.outHumidity IS NULL) AS current_rh_null,
       SUM(a.outHumidity <=> t.original_humidity_pct) AS current_matches_original,
       SUM(a.outHumidity <=> t.proposed_humidity_pct) AS current_matches_proposed,
       SUM(h.state='applied') AS latest_applied_event,
       SUM(h.state='applied' AND a.outHumidity <=> h.new_value) AS current_matches_latest_applied_value,
       SUM(h.state='applied' AND h.old_value <=> t.original_humidity_pct) AS history_old_matches_original,
       SUM(h.target_time IS NULL) AS no_change_event,
       MIN(t.target_time) AS min_target_epoch,
       MAX(t.target_time) AS max_target_epoch
FROM loucka_reconstruction.reconstruction_humidity_202204 t
LEFT JOIN loucka_reconstruction.archive a ON a.dateTime=t.target_time
LEFT JOIN latest h ON h.target_time=t.target_time AND h.variable='outHumidity'
GROUP BY t.decision ORDER BY t.decision;
