-- Bounded target set: only reconstruction rows with extraTemp2 > 80.
-- Read-only cross-schema census; matching copies are not independent validation.
SELECT 'pocasi-loucka.eu' AS src, COUNT(*) AS target_n,
       SUM(s.dateTime IS NOT NULL) AS matched_rows,
       SUM(s.extraTemp2 IS NOT NULL) AS available_n,
       SUM(s.extraTemp2 = a.extraTemp2) AS exact_match_n,
       COUNT(DISTINCT s.extraTemp2) AS distinct_values
FROM loucka_reconstruction.archive a
LEFT JOIN `pocasi-loucka.eu`.archive s ON s.dateTime=a.dateTime
WHERE a.extraTemp2>80
UNION ALL
SELECT 'pocasi-loucka.eu_GW1000', COUNT(*), SUM(s.dateTime IS NOT NULL),
       SUM(s.extraTemp2 IS NOT NULL), SUM(s.extraTemp2=a.extraTemp2), COUNT(DISTINCT s.extraTemp2)
FROM loucka_reconstruction.archive a
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive s ON s.dateTime=a.dateTime
WHERE a.extraTemp2>80
UNION ALL
SELECT 'pocasi-loucka.eu_old', COUNT(*), SUM(s.dateTime IS NOT NULL),
       SUM(s.extraTemp2 IS NOT NULL), SUM(s.extraTemp2=a.extraTemp2), COUNT(DISTINCT s.extraTemp2)
FROM loucka_reconstruction.archive a
LEFT JOIN `pocasi-loucka.eu_old`.archive s ON s.dateTime=a.dateTime
WHERE a.extraTemp2>80
UNION ALL
SELECT 'old_weewx', COUNT(*), SUM(s.dateTime IS NOT NULL),
       SUM(s.extraTemp2 IS NOT NULL), SUM(s.extraTemp2=a.extraTemp2), COUNT(DISTINCT s.extraTemp2)
FROM loucka_reconstruction.archive a
LEFT JOIN old_weewx.archive s ON s.dateTime=a.dateTime
WHERE a.extraTemp2>80
UNION ALL
SELECT 'weewx_WH1080', COUNT(*), SUM(s.dateTime IS NOT NULL),
       SUM(s.extraTemp2 IS NOT NULL), SUM(s.extraTemp2=a.extraTemp2), COUNT(DISTINCT s.extraTemp2)
FROM loucka_reconstruction.archive a
LEFT JOIN weewx_WH1080.archive s ON s.dateTime=a.dateTime
WHERE a.extraTemp2>80;
