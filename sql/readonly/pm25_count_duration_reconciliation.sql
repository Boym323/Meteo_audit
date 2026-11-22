-- Annual PM2.5 threshold counts use explicit UTC epoch boundaries.
SELECT CASE
 WHEN dateTime>=1640995200 AND dateTime<1672531200 THEN 2022
 WHEN dateTime>=1672531200 AND dateTime<1704067200 THEN 2023
 WHEN dateTime>=1704067200 AND dateTime<1735689600 THEN 2024
 WHEN dateTime>=1735689600 AND dateTime<1767225600 THEN 2025
 WHEN dateTime>=1767225600 AND dateTime<1798761600 THEN 2026
 END AS utc_year,
 COUNT(pm25_1) AS valid_rows,
 COUNT(CASE WHEN pm25_1>500 THEN 1 END) AS over_500,
 COUNT(CASE WHEN pm25_1>=999.8 THEN 1 END) AS at_or_above_999_8,
 COUNT(CASE WHEN pm25_1>250 THEN 1 END) AS over_250
FROM loucka_reconstruction.archive
WHERE dateTime>=1640995200 AND dateTime<1798761600
GROUP BY utc_year ORDER BY utc_year;

-- Endpoint span for the longest documented 2024-09 >500 segment.
SELECT COUNT(*) AS inclusive_rows, MIN(dateTime) AS first_epoch,
 MAX(dateTime) AS last_epoch, MAX(dateTime)-MIN(dateTime) AS elapsed_seconds,
 COUNT(CASE WHEN pm25_1>500 THEN 1 END) AS over_500
FROM loucka_reconstruction.archive
WHERE dateTime>=1726257900 AND dateTime<=1726391400;

-- Daily averages differ by the calendar boundary (UTC vs Europe/Prague).
SELECT 'UTC_2024-09-14' AS day_basis, COUNT(pm25_1) AS valid_rows,
 AVG(pm25_1) AS mean_pm, MIN(pm25_1) AS min_pm, MAX(pm25_1) AS max_pm,
 COUNT(CASE WHEN pm25_1>500 THEN 1 END) AS over_500
FROM loucka_reconstruction.archive WHERE dateTime>=1726272000 AND dateTime<1726358400
UNION ALL
SELECT 'Europe_Prague_2024-09-14', COUNT(pm25_1), AVG(pm25_1), MIN(pm25_1), MAX(pm25_1),
 COUNT(CASE WHEN pm25_1>500 THEN 1 END)
FROM loucka_reconstruction.archive WHERE dateTime>=1726264800 AND dateTime<1726351200;
