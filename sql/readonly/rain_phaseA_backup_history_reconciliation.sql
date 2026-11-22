-- SELECT-only revalidation of historical rain correction chains against
-- original backup rows, matching batch event, latest event and archive.
WITH backups AS (
    SELECT 'daily_reset_2009_2011' AS backup_name,
           'rain-2009-2011-utc-midnight-reset-v1' AS batch_key,
           dateTime, rain_before
    FROM loucka_reconstruction.rain_daily_reset_backup_2009_2011_v1
    UNION ALL
    SELECT 'june_2010_phase_a', 'rain-phaseA-june2010-corrected-20261030-v1',
           dateTime, rain_before
    FROM loucka_reconstruction.rain_phase_a_201006_backup_20261030_v1
    UNION ALL
    SELECT 'phase_a_other', 'rain-phaseA-apply-20261030-v1',
           dateTime, rain_before
    FROM loucka_reconstruction.rain_phase_a_backup_20261030_v1
), batch_events AS (
    SELECT b.backup_name, b.batch_key, b.dateTime, b.rain_before,
           COUNT(c.id) AS batch_event_count,
           MAX(c.id) AS batch_event_id,
           SUM(c.state = 'applied') AS batch_applied,
           SUM(c.old_value <=> b.rain_before) AS backup_old_matches_event,
           SUM(c.new_value = 0) AS event_new_zero
    FROM backups b
    LEFT JOIN loucka_reconstruction.reconstruction_changes c
      ON c.batch_key = b.batch_key
     AND c.target_time = b.dateTime
     AND c.variable = 'rain'
    GROUP BY b.backup_name, b.batch_key, b.dateTime, b.rain_before
), ranked AS (
    SELECT target_time, variable, batch_key, state, old_value, new_value,
           created_at, id,
           ROW_NUMBER() OVER (
               PARTITION BY target_time, variable
               ORDER BY created_at DESC, id DESC
           ) AS rn
    FROM loucka_reconstruction.reconstruction_changes
    WHERE variable = 'rain'
), latest AS (
    SELECT * FROM ranked WHERE rn = 1
)
SELECT b.backup_name, COUNT(*) AS backup_rows,
       SUM(b.batch_event_count = 1) AS exactly_one_initial_batch_event,
       SUM(b.batch_event_count = 0) AS missing_initial_event,
       SUM(b.batch_event_count > 1) AS multiple_initial_events,
       SUM(b.backup_old_matches_event = 1) AS backup_matches_initial_old,
       SUM(b.batch_applied = 1) AS initial_event_applied,
       SUM(b.event_new_zero = 1) AS initial_event_zero,
       SUM(l.state = 'applied') AS latest_event_applied,
       SUM(l.batch_key = 'rain-2010-2011-phaseA-unknown-null-review-v1') AS superseded_to_null_review,
       SUM(a.rain = 0) AS current_zero,
       SUM(a.rain IS NULL) AS current_null,
       SUM(a.rain <=> CASE l.state WHEN 'applied' THEN l.new_value
                                   WHEN 'reverted' THEN l.old_value END) AS current_matches_latest_event,
       SUM(l.id = b.batch_event_id) AS initial_event_still_latest
FROM batch_events b
LEFT JOIN latest l ON l.target_time = b.dateTime AND l.variable = 'rain'
LEFT JOIN loucka_reconstruction.archive a ON a.dateTime = b.dateTime
GROUP BY b.backup_name ORDER BY b.backup_name;
