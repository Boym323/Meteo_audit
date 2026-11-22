-- READ-ONLY monthly aggregation of 2014 source-only timestamps versus merged target.
SELECT MONTH(FROM_UNIXTIME(a.dateTime)) utc_month,COUNT(*) source_only_rows,
       SUM(a.outTemp IS NOT NULL) old_outTemp_nonnull,
       SUM(b.outTemp IS NOT NULL) WH_outTemp_nonnull,
       SUM(b.outTemp=0) WH_outTemp_zero,
       SUM(MOD(a.dateTime,300)=0) on_5m_grid,
       SUM(MOD(a.dateTime,300)<>0) off_5m_grid,
       SUM(a.usUnits=17 AND b.usUnits=17 AND a.interval=5 AND b.interval=5) units_interval_match,
       SUM(r.dateTime IS NOT NULL) reconstruction_rows,
       SUM(e.dateTime IS NOT NULL) eu_rows,
       SUM(g.dateTime IS NOT NULL) gw_rows,
       SUM(COALESCE(ch.ev,0)>0) outTemp_history_timestamps
FROM old_weewx.archive a
JOIN weewx_WH1080.archive b ON b.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive z ON z.dateTime=a.dateTime
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu`.archive e ON e.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=a.dateTime
LEFT JOIN (
  SELECT target_time,COUNT(*) ev FROM loucka_reconstruction.reconstruction_changes
  WHERE variable='outTemp' GROUP BY target_time
) ch ON ch.target_time=a.dateTime
WHERE a.dateTime>=1388534400 AND a.dateTime<1420070400
  AND z.dateTime IS NULL
GROUP BY utc_month ORDER BY utc_month;
