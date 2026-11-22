-- Four source-copy RH candidates in 2016 with interval=6 in both copies.
-- SELECT-only; Weather MCP read-only executor. Exact problem rows only.
SELECT o.dateTime,o.outTemp old_temp,o.outHumidity old_rh,o.interval old_interval,o.usUnits old_units,
       w.outTemp wh_temp,w.outHumidity wh_rh,w.interval wh_interval,w.usUnits wh_units,a.outHumidity target_rh
FROM old_weewx.archive o
JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
JOIN loucka_reconstruction.archive a ON a.dateTime=o.dateTime
WHERE o.dateTime>=1451606400 AND o.dateTime<1483228800
  AND o.outHumidity IS NOT NULL AND w.outHumidity IS NOT NULL AND a.outHumidity IS NULL
  AND o.interval=6 AND w.interval=6
  AND NOT EXISTS (SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                  WHERE c.target_time=a.dateTime AND c.variable='outHumidity')
ORDER BY o.dateTime;
