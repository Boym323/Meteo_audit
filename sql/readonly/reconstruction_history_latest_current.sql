-- Current aggregated audit of logged reconstruction history versus archive.
-- SELECT-only. created_at is left in DB DATETIME display; target_time is UTC epoch.
SELECT variable,state,COUNT(*) AS event_rows,
       COUNT(DISTINCT CONCAT(target_time,':',variable)) AS target_variable_pairs,
       MIN(target_time) AS min_target_epoch,MAX(target_time) AS max_target_epoch,
       MAX(created_at) AS latest_event_created_at
FROM reconstruction_changes
GROUP BY variable,state ORDER BY variable,state;

WITH ranked AS (
  SELECT c.target_time,c.variable,c.state,c.new_value,c.old_value,c.id,c.created_at,
         ROW_NUMBER() OVER(PARTITION BY c.target_time,c.variable
                           ORDER BY c.created_at DESC,c.id DESC) AS rn
  FROM reconstruction_changes c
), latest AS (SELECT * FROM ranked WHERE rn=1), joined AS (
  SELECT l.*,a.dateTime AS archive_time,
         CASE l.variable WHEN 'outTemp' THEN a.outTemp
                         WHEN 'outHumidity' THEN a.outHumidity
                         WHEN 'rain' THEN a.rain
                         WHEN 'rainRate' THEN a.rainRate END AS current_value,
         CASE l.state WHEN 'applied' THEN l.new_value
                      WHEN 'reverted' THEN l.old_value END AS expected_value
  FROM latest l LEFT JOIN archive a ON a.dateTime=l.target_time
)
SELECT variable,state,COUNT(*) AS unique_target_variables,
       MIN(target_time) AS min_target_epoch,MAX(target_time) AS max_target_epoch,
       MAX(created_at) AS latest_event_created_at,
       SUM(archive_time IS NULL) AS missing_archive_target,
       SUM(current_value <=> expected_value) AS current_matches_expected,
       SUM(expected_value IS NULL) AS expected_null,
       SUM(NOT (current_value <=> expected_value)) AS current_mismatch
FROM joined GROUP BY variable,state ORDER BY variable,state;

SELECT b.state,COUNT(DISTINCT b.batch_id) AS batches,
       COUNT(c.batch_id) AS candidate_rows,
       COUNT(DISTINCT c.target_time,c.variable) AS unique_target_variables,
       MIN(c.target_time) AS min_target_epoch,MAX(c.target_time) AS max_target_epoch,
       MAX(b.created_at) AS latest_batch_created_at
FROM reconstruction_batches b
LEFT JOIN reconstruction_candidates c ON c.batch_id=b.batch_id
GROUP BY b.state ORDER BY b.state;
