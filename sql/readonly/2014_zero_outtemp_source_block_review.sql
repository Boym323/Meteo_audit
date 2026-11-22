-- READ-ONLY bounded source/reconstruction review of 2014-06-16/17 zero-temperature block.
-- The second result set summarizes the surrounding two-day target context.
SELECT COUNT(*) AS source_pair_rows,
       MIN(a.dateTime) AS first_epoch, MAX(a.dateTime) AS last_epoch,
       SUM(a.outTemp=0 AND b.outTemp=0) AS both_zero,
       SUM(a.outTemp=b.outTemp) AS exact_copy_outTemp,
       SUM(MOD(a.dateTime,300)<>0) AS off_5m_grid,
       SUM(a.interval=5 AND b.interval=5 AND a.usUnits=17 AND b.usUnits=17) AS declared_unit_interval_match,
       SUM(a.outHumidity IS NOT NULL) AS old_RH_nonnull,
       SUM(b.outHumidity IS NOT NULL) AS WH_RH_nonnull,
       SUM(r.dateTime IS NOT NULL) AS reconstruction_rows,
       SUM(e.dateTime IS NOT NULL) AS eu_rows,
       SUM(g.dateTime IS NOT NULL) AS gw1000_rows,
       SUM(z.dateTime IS NOT NULL) AS eu_old_rows,
       SUM(COALESCE(ch.event_count,0)>0) AS target_times_with_outTemp_events
FROM old_weewx.archive a
JOIN weewx_WH1080.archive b ON b.dateTime=a.dateTime
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu`.archive e ON e.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive z ON z.dateTime=a.dateTime
LEFT JOIN (
  SELECT target_time,COUNT(*) event_count
  FROM loucka_reconstruction.reconstruction_changes
  WHERE variable='outTemp' GROUP BY target_time
) ch ON ch.target_time=a.dateTime
WHERE a.dateTime>=1402940340 AND a.dateTime<=1403011740
  AND a.outTemp IS NOT NULL AND b.outTemp IS NOT NULL
  AND a.outTemp=0 AND b.outTemp=0 AND z.dateTime IS NULL;

SELECT 'old_weewx' AS archive,
       (SELECT dateTime FROM old_weewx.archive WHERE dateTime<1402940340 AND outTemp IS NOT NULL ORDER BY dateTime DESC LIMIT 1) AS previous_ts,
       (SELECT outTemp FROM old_weewx.archive WHERE dateTime<1402940340 AND outTemp IS NOT NULL ORDER BY dateTime DESC LIMIT 1) AS previous_outTemp,
       (SELECT dateTime FROM old_weewx.archive WHERE dateTime>1403011740 AND outTemp IS NOT NULL ORDER BY dateTime LIMIT 1) AS next_ts,
       (SELECT outTemp FROM old_weewx.archive WHERE dateTime>1403011740 AND outTemp IS NOT NULL ORDER BY dateTime LIMIT 1) AS next_outTemp,
       (SELECT COUNT(*) FROM old_weewx.archive WHERE dateTime>=1402853940 AND dateTime<1403098140 AND outTemp IS NOT NULL) AS two_day_outTemp_rows,
       (SELECT SUM(outTemp<>0) FROM old_weewx.archive WHERE dateTime>=1402853940 AND dateTime<1403098140 AND outTemp IS NOT NULL) AS two_day_nonzero_outTemp_rows
UNION ALL
SELECT 'weewx_WH1080',
       (SELECT dateTime FROM weewx_WH1080.archive WHERE dateTime<1402940340 AND outTemp IS NOT NULL ORDER BY dateTime DESC LIMIT 1),
       (SELECT outTemp FROM weewx_WH1080.archive WHERE dateTime<1402940340 AND outTemp IS NOT NULL ORDER BY dateTime DESC LIMIT 1),
       (SELECT dateTime FROM weewx_WH1080.archive WHERE dateTime>1403011740 AND outTemp IS NOT NULL ORDER BY dateTime LIMIT 1),
       (SELECT outTemp FROM weewx_WH1080.archive WHERE dateTime>1403011740 AND outTemp IS NOT NULL ORDER BY dateTime LIMIT 1),
       (SELECT COUNT(*) FROM weewx_WH1080.archive WHERE dateTime>=1402853940 AND dateTime<1403098140 AND outTemp IS NOT NULL),
       (SELECT SUM(outTemp<>0) FROM weewx_WH1080.archive WHERE dateTime>=1402853940 AND dateTime<1403098140 AND outTemp IS NOT NULL)
UNION ALL
SELECT 'pocasi-loucka.eu_old',
       (SELECT dateTime FROM `pocasi-loucka.eu_old`.archive WHERE dateTime<1402940340 AND outTemp IS NOT NULL ORDER BY dateTime DESC LIMIT 1),
       (SELECT outTemp FROM `pocasi-loucka.eu_old`.archive WHERE dateTime<1402940340 AND outTemp IS NOT NULL ORDER BY dateTime DESC LIMIT 1),
       (SELECT dateTime FROM `pocasi-loucka.eu_old`.archive WHERE dateTime>1403011740 AND outTemp IS NOT NULL ORDER BY dateTime LIMIT 1),
       (SELECT outTemp FROM `pocasi-loucka.eu_old`.archive WHERE dateTime>1403011740 AND outTemp IS NOT NULL ORDER BY dateTime LIMIT 1),
       (SELECT COUNT(*) FROM `pocasi-loucka.eu_old`.archive WHERE dateTime>=1402853940 AND dateTime<1403098140 AND outTemp IS NOT NULL),
       (SELECT SUM(outTemp<>0) FROM `pocasi-loucka.eu_old`.archive WHERE dateTime>=1402853940 AND dateTime<1403098140 AND outTemp IS NOT NULL);
