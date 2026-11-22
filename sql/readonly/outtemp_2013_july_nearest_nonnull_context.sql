-- Read-only local-context screen for the 18 July 2013 negative source candidates.
-- Searches one day either side; GROUP_CONCAT ordering keeps the nearest pair first.
SELECT o.dateTime AS target_epoch,o.outTemp AS source_outTemp,
 SUBSTRING_INDEX(GROUP_CONCAT(CASE WHEN a.dateTime<o.dateTime THEN CONCAT(a.dateTime,':',a.outTemp) END ORDER BY a.dateTime DESC SEPARATOR ','),',',1) AS prev_pair,
 SUBSTRING_INDEX(GROUP_CONCAT(CASE WHEN a.dateTime>o.dateTime THEN CONCAT(a.dateTime,':',a.outTemp) END ORDER BY a.dateTime ASC SEPARATOR ','),',',1) AS next_pair
FROM old_weewx.archive o
JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
JOIN loucka_reconstruction.archive r ON r.dateTime=o.dateTime
JOIN loucka_reconstruction.archive a ON a.dateTime BETWEEN o.dateTime-86400 AND o.dateTime+86400 AND a.outTemp IS NOT NULL
WHERE o.dateTime>=1372636800 AND o.dateTime<1375315200
 AND o.outTemp<0 AND w.outTemp=o.outTemp AND r.outTemp IS NULL
 AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                WHERE c.target_time=o.dateTime AND c.variable='outTemp')
GROUP BY o.dateTime,o.outTemp ORDER BY o.dateTime;
