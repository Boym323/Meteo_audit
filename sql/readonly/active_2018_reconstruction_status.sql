-- Read-only reconciliation of changes observed in Q1 2018 on 2026-11-12.
-- created_at is DATETIME in server/session SYSTEM=CET; target_time is UTC epoch.
WITH recent AS (
  SELECT c.id,c.batch_key,c.target_time,c.variable,c.state,c.new_value,c.created_at,
         CASE WHEN c.batch_key LIKE '%2018-jan%' THEN 'batch_2018-01'
              WHEN c.batch_key LIKE '%2018-02%' THEN 'batch_2018-02'
              WHEN c.batch_key LIKE '%2018-03%' THEN 'batch_2018-03'
              ELSE 'other_or_unparsed' END AS batch_month_label,
         CASE WHEN c.target_time < 1517443200 THEN 'target_2018-01'
              WHEN c.target_time < 1520121600 THEN 'target_2018-02'
              ELSE 'target_2018-03' END AS target_utc_month
  FROM reconstruction_changes c
  WHERE c.target_time >= 1514764800 AND c.target_time < 1522540800
    AND c.created_at >= '2026-11-12 00:00:00'
    AND c.variable IN ('outTemp','outHumidity')
)
SELECT r.batch_month_label,r.target_utc_month,r.variable,r.state,
       COUNT(*) AS event_rows,COUNT(DISTINCT r.target_time) AS unique_target_times,
       COUNT(DISTINCT r.batch_key) AS batch_keys,
       MIN(r.created_at) AS first_created_at_cet,MAX(r.created_at) AS last_created_at_cet,
       SUM(a.dateTime IS NULL) AS missing_archive,
       SUM(CASE WHEN r.variable='outTemp'
                 AND ((r.new_value IS NULL AND a.outTemp IS NULL)
                      OR (r.new_value IS NOT NULL AND a.outTemp=r.new_value)) THEN 1
                WHEN r.variable='outHumidity'
                 AND ((r.new_value IS NULL AND a.outHumidity IS NULL)
                      OR (r.new_value IS NOT NULL AND a.outHumidity=r.new_value)) THEN 1
                ELSE 0 END) AS current_matches_event_new_value
FROM recent r LEFT JOIN archive a ON a.dateTime=r.target_time
GROUP BY r.batch_month_label,r.target_utc_month,r.variable,r.state
ORDER BY r.batch_month_label,r.target_utc_month,r.variable,r.state;

-- Latest event per variable/time across all history for Q1 2018; current value check.
WITH ranked AS (
  SELECT c.target_time,c.variable,c.state,c.new_value,c.id,
         ROW_NUMBER() OVER (PARTITION BY c.target_time,c.variable ORDER BY c.id DESC) AS rn
  FROM reconstruction_changes c
  WHERE c.target_time >= 1514764800 AND c.target_time < 1522540800
    AND c.variable IN ('outTemp','outHumidity')
), latest AS (SELECT * FROM ranked WHERE rn=1)
SELECT l.variable,l.state,COUNT(*) AS unique_latest_targets,
       MIN(l.target_time) AS first_target_epoch,MAX(l.target_time) AS last_target_epoch,
       SUM(a.dateTime IS NULL) AS missing_archive,
       SUM(CASE WHEN l.variable='outTemp'
                 AND ((l.new_value IS NULL AND a.outTemp IS NULL)
                      OR (l.new_value IS NOT NULL AND a.outTemp=l.new_value)) THEN 1
                WHEN l.variable='outHumidity'
                 AND ((l.new_value IS NULL AND a.outHumidity IS NULL)
                      OR (l.new_value IS NOT NULL AND a.outHumidity=l.new_value)) THEN 1
                ELSE 0 END) AS current_matches_latest_new_value
FROM latest l LEFT JOIN archive a ON a.dateTime=l.target_time
GROUP BY l.variable,l.state ORDER BY l.variable,l.state;
