-- READ-ONLY exact source-only offset and nearest projected 5-minute target comparison.
SELECT MOD(a0.dateTime,300) AS remainder_seconds,
 CASE WHEN MOD(a0.dateTime,300)<=150 THEN MOD(a0.dateTime,300) ELSE MOD(a0.dateTime,300)-300 END AS signed_offset_seconds,
 COUNT(*) AS source_rows,
 SUM(r.dateTime IS NOT NULL) AS projected_target_present,
 SUM(r.outTemp IS NOT NULL AND a0.outTemp IS NOT NULL AND r.outTemp=a0.outTemp) AS projected_temperature_equal,
 SUM(r.outTemp IS NOT NULL AND a0.outTemp IS NOT NULL AND r.outTemp<>a0.outTemp) AS projected_temperature_conflict,
 SUM(z.dateTime IS NOT NULL) AS eu_old_exact_row,
 SUM(z.outTemp IS NOT NULL AND z.outTemp=a0.outTemp) AS eu_old_temperature_equal
FROM old_weewx.archive a0 JOIN weewx_WH1080.archive a1 ON a1.dateTime=a0.dateTime
LEFT JOIN loucka_reconstruction.archive x ON x.dateTime=a0.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive z ON z.dateTime=a0.dateTime
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=(a0.dateTime-MOD(a0.dateTime,300)+CASE WHEN MOD(a0.dateTime,300)<=150 THEN 0 ELSE 300 END)
WHERE a0.dateTime>=1546300800 AND a0.dateTime<1577836800 AND x.dateTime IS NULL
GROUP BY remainder_seconds,signed_offset_seconds;
