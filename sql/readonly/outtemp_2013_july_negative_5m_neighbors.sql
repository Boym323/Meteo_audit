-- Read-only immediate exact 300s neighbor counts for July negative candidates.
SELECT COUNT(*) AS candidates,
 SUM(p.outTemp IS NOT NULL) AS prev_300_nonnull,
 SUM(n.outTemp IS NOT NULL) AS next_300_nonnull,
 SUM(p.outTemp IS NOT NULL AND n.outTemp IS NOT NULL) AS both_300_nonnull
FROM old_weewx.archive o
JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
JOIN loucka_reconstruction.archive r ON r.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive p ON p.dateTime=o.dateTime-300
LEFT JOIN loucka_reconstruction.archive n ON n.dateTime=o.dateTime+300
WHERE o.dateTime>=1372636800 AND o.dateTime<1375315200
 AND o.outTemp<0 AND w.outTemp=o.outTemp AND r.outTemp IS NULL
 AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                WHERE c.target_time=o.dateTime AND c.variable='outTemp');
