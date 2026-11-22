-- READ-ONLY epoch remainder / projected slot screen; projection is diagnostic only.
SELECT MOD(a0.dateTime,300) AS epoch_remainder,
 CASE WHEN MOD(a0.dateTime,300)<=150 THEN MOD(a0.dateTime,300) ELSE MOD(a0.dateTime,300)-300 END AS signed_nearest_offset_seconds,
 COUNT(*) AS source_rows,
 SUM(r.dateTime IS NOT NULL) AS projected_target_present,
 SUM(r.dateTime IS NULL) AS projected_target_absent,
 SUM(a0.outTemp IS NOT NULL AND a1.outTemp IS NOT NULL AND a0.outTemp=a1.outTemp) AS exact_source_copy_temp
FROM old_weewx.archive a0 JOIN weewx_WH1080.archive a1 ON a1.dateTime=a0.dateTime
LEFT JOIN loucka_reconstruction.archive a2 ON a2.dateTime=a0.dateTime
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=(a0.dateTime-MOD(a0.dateTime,300)+CASE WHEN MOD(a0.dateTime,300)<=150 THEN 0 ELSE 300 END)
WHERE a0.dateTime>=1230768000 AND a0.dateTime<1262304000 AND a2.dateTime IS NULL
GROUP BY epoch_remainder,signed_nearest_offset_seconds ORDER BY source_rows DESC;
