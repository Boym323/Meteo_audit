-- SELECT-only: locate source timestamps absent from either original archive
-- during the full 2013-03-01/02 constant T/RH run.
SELECT a.dateTime AS archive_epoch,
       CASE WHEN o.dateTime IS NULL THEN 1 ELSE 0 END AS missing_old_weewx,
       CASE WHEN w.dateTime IS NULL THEN 1 ELSE 0 END AS missing_weewx_wh1080
FROM loucka_reconstruction.archive a
LEFT JOIN old_weewx.archive o ON o.dateTime=a.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=a.dateTime
WHERE a.dateTime >= 1362171600 AND a.dateTime <= 1362247200
  AND (o.dateTime IS NULL OR w.dateTime IS NULL)
ORDER BY a.dateTime;
