-- Exact-hour local change-history counts used in CHMI winter context validation.
-- UTC ranges are identical to chmi_rh_winter_reference_join.sql. SELECT only.
SELECT YEAR(FROM_UNIXTIME(a.dateTime)) AS utc_year,COUNT(*) AS rows_n,
       SUM(EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                  WHERE c.target_time=a.dateTime AND c.variable='outTemp')) AS outtemp_history_rows,
       SUM(EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                  WHERE c.target_time=a.dateTime AND c.variable='outHumidity')) AS humidity_history_rows
FROM loucka_reconstruction.archive a
WHERE ((a.dateTime>=1546300800 AND a.dateTime<1551484800)
    OR (a.dateTime>=1577836800 AND a.dateTime<1583020800)
    OR (a.dateTime>=1609459200 AND a.dateTime<1614556800)
    OR (a.dateTime>=1640995200 AND a.dateTime<1646092800))
  AND MOD(a.dateTime,3600)=0
GROUP BY utc_year ORDER BY utc_year;
