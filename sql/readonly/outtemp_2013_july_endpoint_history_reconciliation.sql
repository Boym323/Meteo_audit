-- Read-only check: history and source-copy agreement at the nearest +/-24h endpoints.
SELECT COUNT(*) AS cases,
 SUM(po.outTemp IS NOT NULL AND pw.outTemp IS NOT NULL AND rp.outTemp IS NOT NULL) AS prev_present_all_archives,
 SUM(no.outTemp IS NOT NULL AND nw.outTemp IS NOT NULL AND rn.outTemp IS NOT NULL) AS next_present_all_archives,
 SUM(po.outTemp=pw.outTemp AND po.outTemp=rp.outTemp) AS prev_exact_agreement,
 SUM(no.outTemp=nw.outTemp AND no.outTemp=rn.outTemp) AS next_exact_agreement,
 SUM(ABS(po.outTemp-pw.outTemp)>0.01) AS prev_source_disagreement,
 SUM(ABS(no.outTemp-nw.outTemp)>0.01) AS next_source_disagreement,
 COUNT(DISTINCT cp.id) AS prev_endpoint_history_events,
 COUNT(DISTINCT cn.id) AS next_endpoint_history_events
FROM (
 SELECT o.dateTime AS target_epoch,
  CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(GROUP_CONCAT(CASE WHEN a.dateTime<o.dateTime THEN CONCAT(a.dateTime,':',a.outTemp) END ORDER BY a.dateTime DESC SEPARATOR ','),',',1),':',1) AS UNSIGNED) AS prev_epoch,
  CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(GROUP_CONCAT(CASE WHEN a.dateTime>o.dateTime THEN CONCAT(a.dateTime,':',a.outTemp) END ORDER BY a.dateTime ASC SEPARATOR ','),',',1),':',1) AS UNSIGNED) AS next_epoch
 FROM old_weewx.archive o
 JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
 JOIN loucka_reconstruction.archive r ON r.dateTime=o.dateTime
 JOIN loucka_reconstruction.archive a ON a.dateTime BETWEEN o.dateTime-86400 AND o.dateTime+86400 AND a.outTemp IS NOT NULL
 WHERE o.dateTime>=1372636800 AND o.dateTime<1375315200
  AND o.outTemp<0 AND w.outTemp=o.outTemp AND r.outTemp IS NULL
  AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                 WHERE c.target_time=o.dateTime AND c.variable='outTemp')
 GROUP BY o.dateTime
) e
LEFT JOIN old_weewx.archive po ON po.dateTime=e.prev_epoch
LEFT JOIN weewx_WH1080.archive pw ON pw.dateTime=e.prev_epoch
LEFT JOIN loucka_reconstruction.archive rp ON rp.dateTime=e.prev_epoch
LEFT JOIN old_weewx.archive no ON no.dateTime=e.next_epoch
LEFT JOIN weewx_WH1080.archive nw ON nw.dateTime=e.next_epoch
LEFT JOIN loucka_reconstruction.archive rn ON rn.dateTime=e.next_epoch
LEFT JOIN loucka_reconstruction.reconstruction_changes cp ON cp.target_time=e.prev_epoch AND cp.variable='outTemp'
LEFT JOIN loucka_reconstruction.reconstruction_changes cn ON cn.target_time=e.next_epoch AND cn.variable='outTemp';
