-- Compare latest recorded event to current reconstruction archive; SELECT-only.
-- Ordering is created_at DESC, id DESC. Excludes protected year 2021;
-- 2018 Q1 remains an interim/live snapshot.
WITH ranked AS (
 SELECT id,target_time,variable,state,old_value,new_value,created_at,
        ROW_NUMBER() OVER (
          PARTITION BY target_time,variable
          ORDER BY created_at DESC,id DESC
        ) AS rn
 FROM loucka_reconstruction.reconstruction_changes
 WHERE variable IN ('outTemp','outHumidity','rain','rainRate')
   AND (target_time < 1609459200 OR target_time >= 1640995200)
), latest AS (
 SELECT * FROM ranked WHERE rn=1
)
SELECT h.variable,
       CASE WHEN h.target_time>=1514764800 AND h.target_time<1522540800
            THEN '2018_Q1_INTERIM' ELSE 'other_non_2021' END AS audit_period,
       h.state, COUNT(*) AS target_variable_count,
       SUM(a.dateTime IS NULL) AS missing_archive_row,
       SUM((CASE h.variable
              WHEN 'outTemp' THEN a.outTemp
              WHEN 'outHumidity' THEN a.outHumidity
              WHEN 'rain' THEN a.rain
              WHEN 'rainRate' THEN a.rainRate END)
           <=>
           (CASE h.state WHEN 'applied' THEN h.new_value
                         WHEN 'reverted' THEN h.old_value ELSE NULL END)
       ) AS current_matches_expected_state_value,
       SUM(NOT ((CASE h.variable
                   WHEN 'outTemp' THEN a.outTemp
                   WHEN 'outHumidity' THEN a.outHumidity
                   WHEN 'rain' THEN a.rain
                   WHEN 'rainRate' THEN a.rainRate END)
                <=>
                (CASE h.state WHEN 'applied' THEN h.new_value
                              WHEN 'reverted' THEN h.old_value ELSE NULL END)
       )) AS current_differs_expected_or_uncomparable,
       MIN(h.target_time) AS min_target_epoch,
       MAX(h.target_time) AS max_target_epoch
FROM latest h
LEFT JOIN loucka_reconstruction.archive a ON a.dateTime=h.target_time
GROUP BY h.variable,audit_period,h.state
ORDER BY h.variable,audit_period,h.state;
