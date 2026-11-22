-- Reconstruction v1: classify origin of target-only inserted archive timestamps.
-- Read-only SELECT, source/target compared by exact UTC dateTime.
-- This classification is diagnostic: the free-text change.reason is not
-- an immutable, versioned quality code and cannot be used to certify values.
WITH extra AS (
 SELECT r.dateTime
 FROM `loucka_reconstruction`.archive r
 LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=r.dateTime
 WHERE p.dateTime IS NULL
), flags AS (
 SELECT e.dateTime,COUNT(h.id) AS history_events,
 MAX(h.reason LIKE 'insert: ESTIMATED%') AS estimated_insert,
 MAX(h.reason LIKE 'insert: RESTORED%') AS restored_insert,
 MAX(h.reason LIKE 'insert: RECOVERED_SOURCE%') AS recovered_insert,
 MAX(h.reason LIKE 'insert: Insert missing archive grid%') AS bootstrap_insert,
 MAX(h.reason LIKE 'update: Spatial estimate:%') AS spatial_rain_update,
 MAX(h.variable='outHumidity' AND h.reason LIKE 'update: ESTIMATED%')
   AS estimated_rh_update
 FROM extra e
 LEFT JOIN `loucka_reconstruction`.reconstruction_changes h ON h.target_time=e.dateTime
 GROUP BY e.dateTime
)
SELECT
 COUNT(*) AS target_only_rows,
 SUM(history_events=0) AS without_history,
 SUM(estimated_insert) AS initial_estimated,
 SUM(restored_insert) AS initial_restored,
 SUM(recovered_insert) AS initial_recovered_source,
 SUM(bootstrap_insert) AS initial_temporary_bootstrap,
 SUM(spatial_rain_update) AS subsequent_spatial_rain_estimate,
 SUM(estimated_rh_update) AS subsequent_estimated_rh,
 SUM(estimated_insert>0 AND estimated_rh_update>0)
   AS initial_estimated_with_rh_estimate,
 SUM(restored_insert>0 AND estimated_rh_update>0)
   AS initial_restored_with_rh_estimate,
 SUM(history_events>1) AS timestamps_with_multiple_audit_events,
 SUM(estimated_insert+restored_insert+recovered_insert+bootstrap_insert<>1)
   AS ambiguous_initial_insert_classification
FROM flags;
