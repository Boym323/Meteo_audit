-- Inventory and evidence queries. Execute in a read-only transaction.
START TRANSACTION READ ONLY;
SELECT VERSION(), @@version_comment, @@read_only;
SHOW DATABASES;
SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_ROWS
FROM information_schema.TABLES
WHERE TABLE_SCHEMA IN ('pocasi-loucka.eu','loucka_reconstruction','old_weewx',
                       'pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old','weewx_WH1080')
ORDER BY TABLE_SCHEMA, TABLE_NAME;
SELECT 'pocasi-loucka.eu' AS schema_name, COUNT(*), MIN(dateTime), MAX(dateTime)
FROM `pocasi-loucka.eu`.archive;
SELECT 'loucka_reconstruction' AS schema_name, COUNT(*), MIN(dateTime), MAX(dateTime)
FROM loucka_reconstruction.archive;
SELECT usUnits, `interval`, COUNT(*)
FROM `pocasi-loucka.eu`.archive
GROUP BY usUnits, `interval` ORDER BY usUnits, `interval`;
SELECT TABLE_SCHEMA, INDEX_NAME, SEQ_IN_INDEX, COLUMN_NAME, NON_UNIQUE
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA IN ('pocasi-loucka.eu','loucka_reconstruction') AND TABLE_NAME='archive'
ORDER BY TABLE_SCHEMA, INDEX_NAME, SEQ_IN_INDEX;
SELECT state, COUNT(*) FROM loucka_reconstruction.reconstruction_changes GROUP BY state;
ROLLBACK;
