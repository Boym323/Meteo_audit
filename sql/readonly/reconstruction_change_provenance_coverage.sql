-- Field coverage and internal consistency of every reconstruction_changes row.
-- Source database/time fields are audited as recorded claims; not joined to source.
SELECT variable,state,COUNT(*) AS events,
       COUNT(DISTINCT CONCAT(target_time,':',variable)) AS target_variable_pairs,
       SUM(batch_key IS NULL OR TRIM(batch_key)='') AS batch_key_missing,
       SUM(source_database IS NULL OR TRIM(source_database)='') AS source_database_missing,
       SUM(source_time IS NULL) AS source_time_missing,
       SUM(source_value IS NULL) AS source_value_missing,
       SUM(reason IS NULL OR TRIM(reason)='') AS reason_missing,
       SUM(applied_at IS NULL) AS applied_at_missing,
       SUM(source_time=target_time) AS source_time_equals_target,
       SUM(source_time<>target_time) AS source_time_differs_target,
       SUM(source_value <=> old_value) AS source_value_matches_old,
       SUM(source_value <=> new_value) AS source_value_matches_new,
       SUM(old_value IS NULL) AS old_value_null,
       SUM(new_value IS NULL) AS new_value_null,
       SUM(old_value IS NULL AND new_value IS NOT NULL) AS old_null_new_nonnull,
       SUM(old_value IS NOT NULL AND new_value IS NULL) AS old_nonnull_new_null,
       SUM(old_value IS NOT NULL AND new_value IS NOT NULL AND old_value<>new_value) AS both_nonnull_different,
       COUNT(DISTINCT source_database) AS source_database_labels,
       COUNT(DISTINCT reason) AS distinct_reason_texts,
       MIN(CHAR_LENGTH(TRIM(reason))) AS min_reason_chars,
       MAX(CHAR_LENGTH(TRIM(reason))) AS max_reason_chars,
       COUNT(DISTINCT batch_key) AS distinct_batch_keys
FROM reconstruction_changes
GROUP BY variable,state ORDER BY variable,state;

-- Detail only for rows where source_time differs from the archive target time.
SELECT variable,state,source_database,COUNT(*) AS events,
       COUNT(DISTINCT source_time-target_time) AS distinct_offsets_s,
       MIN(source_time-target_time) AS min_offset_s,
       MAX(source_time-target_time) AS max_offset_s,
       SUM(source_value IS NULL) AS source_value_missing
FROM reconstruction_changes
WHERE source_time<>target_time
GROUP BY variable,state,source_database
ORDER BY variable,state,source_database;
