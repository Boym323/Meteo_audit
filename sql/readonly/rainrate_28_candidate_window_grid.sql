-- Issue #16; 22 November 2026 read-only live verification.
-- WeeWX archive.dateTime is UTC end of the interval. Each candidate gets
-- its OWN 25-slot +/-60-minute grid; overlapping windows are NOT deduplicated.
-- This is evidence of archive coverage, not verification of rainfall physics.
-- usUnits=16 rates are in cm/hour; do not convert rain*12 into rainRate.
-- No DDL/DML, and no replacement values are proposed here.
WITH RECURSIVE minute_offsets(n) AS (
  SELECT 0 UNION ALL SELECT n+1 FROM minute_offsets WHERE n < 24
), candidates AS (
  SELECT g.dateTime AS event_time, g.rainRate AS gw_rate, g.rain AS gw_rain,
         p.rainRate AS production_rate, r.rainRate AS reconstruction_rate,
         r.rain AS reconstruction_rain, g.usUnits AS gw_units,
         p.usUnits AS production_units, r.usUnits AS reconstruction_units
  FROM `pocasi-loucka.eu_GW1000`.`archive` g
  JOIN `pocasi-loucka.eu`.`archive` p ON p.dateTime = g.dateTime
  LEFT JOIN `loucka_reconstruction`.`archive` r ON r.dateTime = g.dateTime
  WHERE g.dateTime >= 1672531200 AND g.dateTime < 1735689600
    AND g.rainRate > 5 AND p.rainRate = 0
)
SELECT c.event_time, c.gw_rate, c.gw_rain, c.production_rate,
       c.reconstruction_rate, c.reconstruction_rain,
       c.gw_units, c.production_units, c.reconstruction_units,
       COUNT(*) AS expected_slots,
       SUM(g2.dateTime IS NOT NULL) AS gw_on_grid,
       SUM(p2.dateTime IS NOT NULL) AS production_on_grid,
       SUM(r2.dateTime IS NOT NULL) AS reconstruction_on_grid,
       GROUP_CONCAT(CASE WHEN g2.dateTime IS NULL THEN (minute_offsets.n-12)*5 END ORDER BY minute_offsets.n) AS gw_missing_offsets_minutes,
       GROUP_CONCAT(CASE WHEN p2.dateTime IS NULL THEN (minute_offsets.n-12)*5 END ORDER BY minute_offsets.n) AS production_missing_offsets_minutes,
       GROUP_CONCAT(CASE WHEN r2.dateTime IS NULL THEN (minute_offsets.n-12)*5 END ORDER BY minute_offsets.n) AS reconstruction_missing_offsets_minutes,
       (SELECT COUNT(*) FROM `loucka_reconstruction`.`reconstruction_changes` h
         WHERE h.target_time=c.event_time AND h.variable='rainRate') AS history_events,
       (SELECT COUNT(*) FROM `loucka_reconstruction`.`reconstruction_changes` h
         WHERE h.target_time=c.event_time AND h.variable='rainRate' AND h.state='applied') AS applied_history_events
FROM candidates c CROSS JOIN minute_offsets
LEFT JOIN `pocasi-loucka.eu_GW1000`.`archive` g2 ON g2.dateTime=c.event_time+(minute_offsets.n-12)*300
LEFT JOIN `pocasi-loucka.eu`.`archive` p2 ON p2.dateTime=c.event_time+(minute_offsets.n-12)*300
LEFT JOIN `loucka_reconstruction`.`archive` r2 ON r2.dateTime=c.event_time+(minute_offsets.n-12)*300
GROUP BY c.event_time,c.gw_rate,c.gw_rain,c.production_rate,c.reconstruction_rate,c.reconstruction_rain,c.gw_units,c.production_units,c.reconstruction_units
ORDER BY c.event_time;
