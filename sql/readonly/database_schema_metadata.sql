-- Exact schema metadata for all tables in the six discovered meteo databases.
-- Query 1: column definitions. Query 2: index key parts.
SELECT TABLE_SCHEMA,TABLE_NAME,ORDINAL_POSITION,COLUMN_NAME,COLUMN_TYPE,
       IS_NULLABLE,COLUMN_DEFAULT,EXTRA,COLUMN_KEY
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA IN ('loucka_reconstruction','pocasi-loucka.eu',
                       'pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old',
                       'old_weewx','weewx_WH1080')
ORDER BY TABLE_SCHEMA,TABLE_NAME,ORDINAL_POSITION;

SELECT TABLE_SCHEMA,TABLE_NAME,INDEX_NAME,NON_UNIQUE,SEQ_IN_INDEX,COLUMN_NAME,
       COLLATION,CARDINALITY,SUB_PART,INDEX_TYPE,COMMENT
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA IN ('loucka_reconstruction','pocasi-loucka.eu',
                       'pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old',
                       'old_weewx','weewx_WH1080')
ORDER BY TABLE_SCHEMA,TABLE_NAME,INDEX_NAME,SEQ_IN_INDEX;
