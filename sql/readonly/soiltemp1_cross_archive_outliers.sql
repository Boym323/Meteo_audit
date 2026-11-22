-- Bounded exact-target census for the one soilTemp1 value below -40 C.
SELECT 'pocasi-loucka.eu' AS src, COUNT(*) AS target_n,
       SUM(s.dateTime IS NOT NULL) AS matched_rows,
       SUM(s.soilTemp1 IS NOT NULL) AS available_n,
       SUM(s.soilTemp1=a.soilTemp1) AS exact_match_n,
       COUNT(DISTINCT s.soilTemp1) AS distinct_values
FROM loucka_reconstruction.archive a
LEFT JOIN `pocasi-loucka.eu`.archive s ON s.dateTime=a.dateTime
WHERE a.soilTemp1 < -40
UNION ALL
SELECT 'pocasi-loucka.eu_GW1000',COUNT(*),SUM(s.dateTime IS NOT NULL),SUM(s.soilTemp1 IS NOT NULL),SUM(s.soilTemp1=a.soilTemp1),COUNT(DISTINCT s.soilTemp1)
FROM loucka_reconstruction.archive a LEFT JOIN `pocasi-loucka.eu_GW1000`.archive s ON s.dateTime=a.dateTime WHERE a.soilTemp1 < -40
UNION ALL
SELECT 'pocasi-loucka.eu_old',COUNT(*),SUM(s.dateTime IS NOT NULL),SUM(s.soilTemp1 IS NOT NULL),SUM(s.soilTemp1=a.soilTemp1),COUNT(DISTINCT s.soilTemp1)
FROM loucka_reconstruction.archive a LEFT JOIN `pocasi-loucka.eu_old`.archive s ON s.dateTime=a.dateTime WHERE a.soilTemp1 < -40
UNION ALL
SELECT 'old_weewx',COUNT(*),SUM(s.dateTime IS NOT NULL),SUM(s.soilTemp1 IS NOT NULL),SUM(s.soilTemp1=a.soilTemp1),COUNT(DISTINCT s.soilTemp1)
FROM loucka_reconstruction.archive a LEFT JOIN old_weewx.archive s ON s.dateTime=a.dateTime WHERE a.soilTemp1 < -40
UNION ALL
SELECT 'weewx_WH1080',COUNT(*),SUM(s.dateTime IS NOT NULL),SUM(s.soilTemp1 IS NOT NULL),SUM(s.soilTemp1=a.soilTemp1),COUNT(DISTINCT s.soilTemp1)
FROM loucka_reconstruction.archive a LEFT JOIN weewx_WH1080.archive s ON s.dateTime=a.dateTime WHERE a.soilTemp1 < -40;
