SELECT COUNT(*) AS eu_old_rows,COUNT(DISTINCT e.dateTime) AS eu_old_unique_timestamps,
 SUM(e.outTemp IS NOT NULL) AS eu_old_outTemp_nonnull,
 SUM(e.usUnits=16 AND e.interval=5) AS expected_unit_interval_rows,
 MIN(e.outTemp) AS source_outTemp_min_c,MAX(e.outTemp) AS source_outTemp_max_c,
 COUNT(DISTINCT CASE WHEN r.dateTime IS NOT NULL THEN e.dateTime END) AS reconstruction_rows,
 COUNT(DISTINCT CASE WHEN p.dateTime IS NOT NULL THEN e.dateTime END) AS eu_rows,
 COUNT(DISTINCT CASE WHEN g.dateTime IS NOT NULL THEN e.dateTime END) AS gw1000_rows,
 COUNT(DISTINCT CASE WHEN o.dateTime IS NOT NULL THEN e.dateTime END) AS old_weewx_rows,
 COUNT(DISTINCT CASE WHEN w.dateTime IS NOT NULL THEN e.dateTime END) AS wh1080_rows,
 COUNT(DISTINCT CASE WHEN x.target_time IS NOT NULL THEN e.dateTime END) AS target_timestamps_with_any_change_event,
 COUNT(DISTINCT CASE WHEN x.variable='outTemp' THEN e.dateTime END) AS target_timestamps_with_outTemp_event
FROM `pocasi-loucka.eu_old`.archive e
LEFT JOIN `loucka_reconstruction`.archive r ON r.dateTime=e.dateTime
LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=e.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=e.dateTime
LEFT JOIN `old_weewx`.archive o ON o.dateTime=e.dateTime
LEFT JOIN `weewx_WH1080`.archive w ON w.dateTime=e.dateTime
LEFT JOIN `loucka_reconstruction`.reconstruction_changes x ON x.target_time=e.dateTime
WHERE e.dateTime>1685274900 AND e.dateTime<1685332200