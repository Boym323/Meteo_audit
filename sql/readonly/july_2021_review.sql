-- Read-only status review of existing July 2021 QC and reconstruction artifacts.
START TRANSACTION READ ONLY;
SELECT COUNT(*), SUM(rain), SUM(rain IS NULL), MAX(rain)
FROM `pocasi-loucka.eu`.archive WHERE dateTime >= 1625090400 AND dateTime < 1627768800;
SELECT COUNT(*), SUM(rain), SUM(rain IS NULL), MAX(rain)
FROM loucka_reconstruction.archive WHERE dateTime >= 1625090400 AND dateTime < 1627768800;
SELECT COUNT(*), SUM(original_rain_mm), SUM(screened_unverified_mm), SUM(suspect_intervals),
       SUM(suspect_original_mm), SUM(plausible_intervals), SUM(unresolved_intervals),
       SUM(verified_daily_rain_mm IS NULL), SUM(archive_missing_rain_intervals),
       SUM(archive_missing_rate_intervals)
FROM loucka_reconstruction.rain_qc_daily_202107;
SELECT method, COUNT(*), SUM(rain_cm), SUM(rainRate_cm_h IS NULL)
FROM loucka_reconstruction.rain_reconstruction_202107_chmi_v1 GROUP BY method;
SELECT batch_key, variable, state, COUNT(*)
FROM loucka_reconstruction.reconstruction_changes
WHERE target_time >= 1625090400 AND target_time < 1627768800
GROUP BY batch_key, variable, state ORDER BY batch_key, variable, state;
ROLLBACK;
