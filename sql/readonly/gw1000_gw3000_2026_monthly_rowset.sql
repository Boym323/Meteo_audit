-- READ-ONLY fixed UTC-month rowset/concordance snapshot query; November is partial.
START TRANSACTION READ ONLY;
WITH month_bounds AS (
  SELECT '2026-01' AS month_utc, 1767225600 AS start_epoch, 1769904000 AS end_epoch UNION ALL
  SELECT '2026-02' AS month_utc, 1769904000 AS start_epoch, 1772323200 AS end_epoch UNION ALL
  SELECT '2026-03' AS month_utc, 1772323200 AS start_epoch, 1775001600 AS end_epoch UNION ALL
  SELECT '2026-04' AS month_utc, 1775001600 AS start_epoch, 1777593600 AS end_epoch UNION ALL
  SELECT '2026-05' AS month_utc, 1777593600 AS start_epoch, 1780272000 AS end_epoch UNION ALL
  SELECT '2026-06' AS month_utc, 1780272000 AS start_epoch, 1782864000 AS end_epoch UNION ALL
  SELECT '2026-07' AS month_utc, 1782864000 AS start_epoch, 1785542400 AS end_epoch UNION ALL
  SELECT '2026-08' AS month_utc, 1785542400 AS start_epoch, 1788220800 AS end_epoch UNION ALL
  SELECT '2026-09' AS month_utc, 1788220800 AS start_epoch, 1790812800 AS end_epoch UNION ALL
  SELECT '2026-10' AS month_utc, 1790812800 AS start_epoch, 1793491200 AS end_epoch UNION ALL
  SELECT '2026-11' AS month_utc, 1793491200 AS start_epoch, 1796083200 AS end_epoch
)
SELECT m.month_utc,
  (SELECT COUNT(*) FROM `pocasi-loucka.eu`.archive p WHERE p.dateTime>=m.start_epoch AND p.dateTime<m.end_epoch) AS gw3000_rows,
  (SELECT COUNT(*) FROM `pocasi-loucka.eu_GW1000`.archive g WHERE g.dateTime>=m.start_epoch AND g.dateTime<m.end_epoch) AS gw1000_snapshot_rows,
  (SELECT COUNT(*) FROM `pocasi-loucka.eu`.archive p JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=p.dateTime WHERE p.dateTime>=m.start_epoch AND p.dateTime<m.end_epoch) AS exact_timestamp_pairs
FROM month_bounds m ORDER BY m.start_epoch;
