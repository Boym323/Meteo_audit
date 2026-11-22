-- READ-ONLY alignment by nearest projected five-minute slot; projection is diagnostic only.
SELECT MOD(a0.dateTime,300) AS remainder_seconds,
 CASE WHEN MOD(a0.dateTime,300)<=150 THEN MOD(a0.dateTime,300) ELSE MOD(a0.dateTime,300)-300 END AS signed_offset_seconds,
 COUNT(*) AS source_rows,
 SUM(r.dateTime IS NOT NULL) AS projected_target_present,
 SUM(a0.outTemp=a1.outTemp) AS exact_source_temp_matches,
 SUM(a0.outHumidity IS NOT NULL AND a1.outHumidity IS NOT NULL AND a0.outHumidity<>a1.outHumidity) AS source_RH_conflicts
FROM old_weewx.archive a0 JOIN weewx_WH1080.archive a1 ON a1.dateTime=a0.dateTime
LEFT JOIN loucka_reconstruction.archive a2 ON a2.dateTime=a0.dateTime
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=(a0.dateTime-MOD(a0.dateTime,300)+CASE WHEN MOD(a0.dateTime,300)<=150 THEN 0 ELSE 300 END)
WHERE a0.dateTime>=1577836800 AND a0.dateTime<1609459200 AND a2.dateTime IS NULL
GROUP BY remainder_seconds,signed_offset_seconds;

-- Exact-grid temperature-only contextual screen; does not authorize restoration.
SELECT COUNT(*) AS rows_n, AVG(ABS(a0.outTemp-o.temperature_c)) AS MAE_vs_LuhaMet_C,
 MAX(ABS(a0.outTemp-o.temperature_c)) AS max_abs_vs_LuhaMet_C,
 SUM(ABS(a0.outTemp-o.temperature_c)<=1) AS within_1C,
 SUM(ABS(a0.outTemp-o.temperature_c)<=2) AS within_2C,
 SUM(ABS(a0.outTemp-o.temperature_c)>3) AS over_3C,
 AVG(ABS(a0.outTemp-(p.outTemp+n.outTemp)/2)) AS MAE_vs_neighbor_midpoint_C
FROM old_weewx.archive a0 JOIN weewx_WH1080.archive a1 ON a1.dateTime=a0.dateTime
LEFT JOIN loucka_reconstruction.archive x ON x.dateTime=a0.dateTime
JOIN loucka_reconstruction.archive p ON p.dateTime=a0.dateTime-300 AND p.outTemp IS NOT NULL
JOIN loucka_reconstruction.archive n ON n.dateTime=a0.dateTime+300 AND n.outTemp IS NOT NULL
JOIN loucka_reconstruction.reference_observations o ON o.station_id='luhamet_sehradice' AND o.observed_at_utc=a0.dateTime
WHERE a0.dateTime>=1577836800 AND a0.dateTime<1609459200 AND x.dateTime IS NULL AND MOD(a0.dateTime,300)=0 AND a0.outTemp=a1.outTemp;
