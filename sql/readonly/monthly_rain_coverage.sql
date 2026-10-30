-- Read-only template for one local calendar month.
-- The interval ending at start is excluded; the interval ending at stop is
-- included, following WeeWX's (start, stop] archive semantics. Convert local
-- boundaries with Europe/Prague and replace the integer epoch values below.
START TRANSACTION READ ONLY;
SELECT dateTime, `interval`, usUnits, rain, rainRate
FROM `loucka_reconstruction`.`archive`
WHERE dateTime > 1625090400 AND dateTime <= 1627768800
ORDER BY dateTime;
ROLLBACK;
