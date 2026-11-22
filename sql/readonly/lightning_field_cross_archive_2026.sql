-- Bounded cross-archive source concordance for 2026 epoch-valued field targets.
SELECT 'pocasi-loucka.eu' AS src, COUNT(*) AS target_n,
       SUM(s.dateTime IS NOT NULL) AS matched_rows,
       SUM(s.lightning_disturber_count IS NOT NULL) AS disturber_nonnull,
       SUM(s.lightning_disturber_count=a.lightning_disturber_count) AS disturber_exact_matches,
       SUM(s.lightning_noise_count IS NOT NULL) AS noise_nonnull,
       SUM(s.lightning_noise_count=s.lightning_strike_count) AS noise_equals_strike
FROM loucka_reconstruction.archive a LEFT JOIN `pocasi-loucka.eu`.archive s ON s.dateTime=a.dateTime
WHERE a.dateTime>=1767225600 AND a.dateTime<1798761600 AND a.lightning_disturber_count IS NOT NULL
UNION ALL
SELECT 'pocasi-loucka.eu_GW1000',COUNT(*),SUM(s.dateTime IS NOT NULL),SUM(s.lightning_disturber_count IS NOT NULL),SUM(s.lightning_disturber_count=a.lightning_disturber_count),SUM(s.lightning_noise_count IS NOT NULL),SUM(s.lightning_noise_count=s.lightning_strike_count)
FROM loucka_reconstruction.archive a LEFT JOIN `pocasi-loucka.eu_GW1000`.archive s ON s.dateTime=a.dateTime
WHERE a.dateTime>=1767225600 AND a.dateTime<1798761600 AND a.lightning_disturber_count IS NOT NULL
UNION ALL
SELECT 'pocasi-loucka.eu_old',COUNT(*),SUM(s.dateTime IS NOT NULL),SUM(s.lightning_disturber_count IS NOT NULL),SUM(s.lightning_disturber_count=a.lightning_disturber_count),SUM(s.lightning_noise_count IS NOT NULL),SUM(s.lightning_noise_count=s.lightning_strike_count)
FROM loucka_reconstruction.archive a LEFT JOIN `pocasi-loucka.eu_old`.archive s ON s.dateTime=a.dateTime
WHERE a.dateTime>=1767225600 AND a.dateTime<1798761600 AND a.lightning_disturber_count IS NOT NULL
UNION ALL
SELECT 'weewx_WH1080',COUNT(*),SUM(s.dateTime IS NOT NULL),SUM(s.lightning_disturber_count IS NOT NULL),SUM(s.lightning_disturber_count=a.lightning_disturber_count),SUM(s.lightning_noise_count IS NOT NULL),SUM(s.lightning_noise_count=s.lightning_strike_count)
FROM loucka_reconstruction.archive a LEFT JOIN weewx_WH1080.archive s ON s.dateTime=a.dateTime
WHERE a.dateTime>=1767225600 AND a.dateTime<1798761600 AND a.lightning_disturber_count IS NOT NULL;
