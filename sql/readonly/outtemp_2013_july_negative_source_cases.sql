-- Small problem-case extract: shared source outTemp below 0 C in July 2013.
-- Read-only; timestamp is Unix UTC. The CSV contains 18 rows.
SELECT o.dateTime AS target_epoch,o.outTemp AS old_outTemp,w.outTemp AS wh_outTemp,
       o.outHumidity AS old_outHumidity,w.outHumidity AS wh_outHumidity,
       o.interval AS old_interval,w.interval AS wh_interval
FROM old_weewx.archive o
JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
JOIN loucka_reconstruction.archive r ON r.dateTime=o.dateTime
WHERE o.dateTime>=1372636800 AND o.dateTime<1375315200
 AND o.outTemp<0 AND w.outTemp=o.outTemp AND r.outTemp IS NULL
 AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                WHERE c.target_time=o.dateTime AND c.variable='outTemp')
ORDER BY o.dateTime;
