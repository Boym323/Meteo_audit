-- SELECT-only: source outTemp timestamps in the five >=7-day gaps against change history.
-- UNION deduplicates exact source timestamps across old_weewx and weewx_WH1080.
SELECT c.gap_id, COUNT(*) AS source_timestamps_with_outTemp,
       COUNT(h.id) AS history_events,
       COUNT(DISTINCT CASE WHEN h.id IS NOT NULL THEN c.dateTime END) AS targets_with_history,
       SUM(CASE WHEN h.state='applied' THEN 1 ELSE 0 END) AS applied_events,
       SUM(CASE WHEN h.state='reverted' THEN 1 ELSE 0 END) AS reverted_events
FROM (
  SELECT 1 AS gap_id,dateTime FROM `old_weewx`.`archive` WHERE dateTime BETWEEN 1313438700 AND 1330593900 AND outTemp IS NOT NULL
  UNION SELECT 1,dateTime FROM `weewx_WH1080`.`archive` WHERE dateTime BETWEEN 1313438700 AND 1330593900 AND outTemp IS NOT NULL
  UNION SELECT 2,dateTime FROM `old_weewx`.`archive` WHERE dateTime BETWEEN 1453156500 AND 1454764200 AND outTemp IS NOT NULL
  UNION SELECT 2,dateTime FROM `weewx_WH1080`.`archive` WHERE dateTime BETWEEN 1453156500 AND 1454764200 AND outTemp IS NOT NULL
  UNION SELECT 3,dateTime FROM `old_weewx`.`archive` WHERE dateTime BETWEEN 1494564600 AND 1496007900 AND outTemp IS NOT NULL
  UNION SELECT 3,dateTime FROM `weewx_WH1080`.`archive` WHERE dateTime BETWEEN 1494564600 AND 1496007900 AND outTemp IS NOT NULL
  UNION SELECT 4,dateTime FROM `old_weewx`.`archive` WHERE dateTime BETWEEN 1403304600 AND 1404406800 AND outTemp IS NOT NULL
  UNION SELECT 4,dateTime FROM `weewx_WH1080`.`archive` WHERE dateTime BETWEEN 1403304600 AND 1404406800 AND outTemp IS NOT NULL
  UNION SELECT 5,dateTime FROM `old_weewx`.`archive` WHERE dateTime BETWEEN 1483966800 AND 1484645400 AND outTemp IS NOT NULL
  UNION SELECT 5,dateTime FROM `weewx_WH1080`.`archive` WHERE dateTime BETWEEN 1483966800 AND 1484645400 AND outTemp IS NOT NULL
) c
LEFT JOIN `loucka_reconstruction`.`reconstruction_changes` h
  ON h.target_time=c.dateTime AND h.variable='outTemp'
GROUP BY c.gap_id
ORDER BY c.gap_id;
