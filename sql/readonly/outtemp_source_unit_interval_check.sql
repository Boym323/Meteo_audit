-- Read-only unit/interval compatibility check for exact-time outTemp source candidates.
SELECT o.usUnits AS old_units, w.usUnits AS wh_units,
       o.interval AS old_interval, w.interval AS wh_interval,
       COUNT(*) AS paired_targets,
       SUM(o.outTemp=w.outTemp) AS exact_equal,
       MIN(o.outTemp) AS min_outTemp, MAX(o.outTemp) AS max_outTemp
FROM old_weewx.archive o
JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
JOIN loucka_reconstruction.archive r ON r.dateTime=o.dateTime
WHERE o.dateTime>=1230768000 AND o.dateTime<1609459200
  AND o.outTemp IS NOT NULL AND w.outTemp IS NOT NULL AND r.outTemp IS NULL
  AND NOT EXISTS (
    SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
    WHERE c.target_time=o.dateTime AND c.variable='outTemp'
  )
GROUP BY o.usUnits,w.usUnits,o.interval,w.interval;
