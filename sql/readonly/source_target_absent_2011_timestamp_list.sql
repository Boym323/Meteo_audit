-- READ-ONLY diagnostic: source timestamps present in both historical archives
-- but absent as whole rows in pocasi-loucka.eu_old, fixed UTC 2011.
-- Local run-length analysis is performed by scripts/summarize_2011_target_absent_episodes.py.
SELECT a0.dateTime
FROM `old_weewx`.`archive` a0
JOIN `weewx_WH1080`.`archive` a1 ON a1.dateTime = a0.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.`archive` a2 ON a2.dateTime = a0.dateTime
WHERE a0.dateTime >= 1293840000 AND a0.dateTime < 1325376000
  AND a2.dateTime IS NULL
ORDER BY a0.dateTime;
