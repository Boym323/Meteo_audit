-- SELECT-only: count exact timestamps in the two historical source archives
-- inside each of the five >=7-day reconstruction gaps. Counts describe timestamp
-- overlap, not valid replacements or proof that the source archives are independent.
SELECT 1 AS gap_id, 1313438700 AS prev_ts, 1330593900 AS target_ts,
       (SELECT COUNT(*) FROM `old_weewx`.`archive` a WHERE a.dateTime BETWEEN 1313438700 AND 1330593900) AS old_weewx_rows,
       (SELECT COUNT(*) FROM `weewx_WH1080`.`archive` b WHERE b.dateTime BETWEEN 1313438700 AND 1330593900) AS wh1080_rows,
       (SELECT COUNT(*) FROM `old_weewx`.`archive` a JOIN `weewx_WH1080`.`archive` b USING(dateTime) WHERE a.dateTime BETWEEN 1313438700 AND 1330593900) AS shared_exact_timestamps
UNION ALL
SELECT 2, 1453156500, 1454764200,
       (SELECT COUNT(*) FROM `old_weewx`.`archive` a WHERE a.dateTime BETWEEN 1453156500 AND 1454764200),
       (SELECT COUNT(*) FROM `weewx_WH1080`.`archive` b WHERE b.dateTime BETWEEN 1453156500 AND 1454764200),
       (SELECT COUNT(*) FROM `old_weewx`.`archive` a JOIN `weewx_WH1080`.`archive` b USING(dateTime) WHERE a.dateTime BETWEEN 1453156500 AND 1454764200)
UNION ALL
SELECT 3, 1494564600, 1496007900,
       (SELECT COUNT(*) FROM `old_weewx`.`archive` a WHERE a.dateTime BETWEEN 1494564600 AND 1496007900),
       (SELECT COUNT(*) FROM `weewx_WH1080`.`archive` b WHERE b.dateTime BETWEEN 1494564600 AND 1496007900),
       (SELECT COUNT(*) FROM `old_weewx`.`archive` a JOIN `weewx_WH1080`.`archive` b USING(dateTime) WHERE a.dateTime BETWEEN 1494564600 AND 1496007900)
UNION ALL
SELECT 4, 1403304600, 1404406800,
       (SELECT COUNT(*) FROM `old_weewx`.`archive` a WHERE a.dateTime BETWEEN 1403304600 AND 1404406800),
       (SELECT COUNT(*) FROM `weewx_WH1080`.`archive` b WHERE b.dateTime BETWEEN 1403304600 AND 1404406800),
       (SELECT COUNT(*) FROM `old_weewx`.`archive` a JOIN `weewx_WH1080`.`archive` b USING(dateTime) WHERE a.dateTime BETWEEN 1403304600 AND 1404406800)
UNION ALL
SELECT 5, 1483966800, 1484645400,
       (SELECT COUNT(*) FROM `old_weewx`.`archive` a WHERE a.dateTime BETWEEN 1483966800 AND 1484645400),
       (SELECT COUNT(*) FROM `weewx_WH1080`.`archive` b WHERE b.dateTime BETWEEN 1483966800 AND 1484645400),
       (SELECT COUNT(*) FROM `old_weewx`.`archive` a JOIN `weewx_WH1080`.`archive` b USING(dateTime) WHERE a.dateTime BETWEEN 1483966800 AND 1484645400);
