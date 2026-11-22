-- Read-only indexed four-row samples around 17 UTC year boundaries in loucka_reconstruction.archive.
-- 2018 Q1 is interim; 2021 is diagnostic.
SELECT 2010 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1262304000 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2010 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1262304000 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2011 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1293840000 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2011 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1293840000 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2012 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1325376000 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2012 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1325376000 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2013 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1356998400 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2013 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1356998400 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2014 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1388534400 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2014 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1388534400 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2015 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1420070400 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2015 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1420070400 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2016 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1451606400 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2016 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1451606400 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2017 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1483228800 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2017 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1483228800 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2018 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1514764800 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2018 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1514764800 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2019 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1546300800 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2019 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1546300800 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2020 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1577836800 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2020 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1577836800 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2021 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1609459200 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2021 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1609459200 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2022 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1640995200 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2022 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1640995200 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2023 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1672531200 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2023 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1672531200 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2024 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1704067200 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2024 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1704067200 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2025 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1735689600 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2025 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1735689600 ORDER BY dateTime ASC LIMIT 2) n
UNION ALL
SELECT 2026 AS utc_year, 'before' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime < 1767225600 ORDER BY dateTime DESC LIMIT 2) p
UNION ALL
SELECT 2026 AS utc_year, 'after' AS side, dateTime, `interval` AS interval_min FROM (SELECT dateTime, `interval` FROM loucka_reconstruction.archive WHERE dateTime >= 1767225600 ORDER BY dateTime ASC LIMIT 2) n
