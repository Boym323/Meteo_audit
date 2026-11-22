-- Reconstruction v1 parity checkpoint (single-statement consistent snapshot).
-- Read-only diagnostic, NEVER an authorization to publish reconstructed values.
-- Both schemas are on the same MariaDB instance; MySQL/InnoDB MVCC applies
-- per statement. Live source continues to grow between independent statements.
--
-- A. Row identity parity and target-only change lineage (one SELECT).
SELECT
 s.source_rows, s.source_latest,
 t.target_rows, t.target_latest,
 m.missing_source_rows_in_target,
 e.target_only_rows,
 e.target_only_without_change_history,
 (s.source_rows + e.target_only_rows - m.missing_source_rows_in_target = t.target_rows)
   AS row_identity_accounting_pass,
 (m.missing_source_rows_in_target = 0 AND e.target_only_without_change_history = 0)
   AS row_provenance_presence_pass
FROM
 (SELECT COUNT(*) AS source_rows, MAX(dateTime) AS source_latest
  FROM `pocasi-loucka.eu`.archive) s
CROSS JOIN
 (SELECT COUNT(*) AS target_rows, MAX(dateTime) AS target_latest
  FROM `loucka_reconstruction`.archive) t
CROSS JOIN
 (SELECT COUNT(*) AS missing_source_rows_in_target
  FROM `pocasi-loucka.eu`.archive p
  LEFT JOIN `loucka_reconstruction`.archive r ON r.dateTime=p.dateTime
  WHERE r.dateTime IS NULL) m
CROSS JOIN
 (SELECT COUNT(*) AS target_only_rows,
         COALESCE(SUM(NOT EXISTS(
           SELECT 1 FROM `loucka_reconstruction`.reconstruction_changes h
           WHERE h.target_time=r.dateTime
         )),0) AS target_only_without_change_history
  FROM `loucka_reconstruction`.archive r
  LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=r.dateTime
  WHERE p.dateTime IS NULL) e;

-- B. UTC-year cohort breakdown for target-only rows. MySQL session timezone
-- MUST NOT be used to assign years (do not use YEAR(FROM_UNIXTIME(dateTime))).
WITH extra AS (
 SELECT r.dateTime,r.outTemp,r.outHumidity,r.rainRate
 FROM `loucka_reconstruction`.archive r
 LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=r.dateTime
 WHERE p.dateTime IS NULL
)
SELECT CASE WHEN dateTime<1388534400 THEN '2013_or_earlier'
            WHEN dateTime<1420070400 THEN '2014'
            WHEN dateTime<1451606400 THEN '2015'
            WHEN dateTime<1483228800 THEN '2016'
            WHEN dateTime<1514764800 THEN '2017'
            WHEN dateTime<1546300800 THEN '2018'
            WHEN dateTime<1577836800 THEN '2019'
            WHEN dateTime<1609459200 THEN '2020'
            WHEN dateTime<1640995200 THEN '2021'
            WHEN dateTime<1672531200 THEN '2022'
            WHEN dateTime<1704067200 THEN '2023'
            ELSE '2024_plus' END AS utc_year,
 COUNT(*) AS target_only_rows,
 SUM(outTemp IS NOT NULL) AS with_temp,
 SUM(outHumidity IS NOT NULL) AS with_rh,
 SUM(rainRate IS NOT NULL) AS with_rainrate
FROM extra GROUP BY utc_year ORDER BY utc_year;
