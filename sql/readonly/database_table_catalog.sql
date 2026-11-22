-- Table catalog for all currently discovered meteorological schemas.
-- Metadata-only; TABLE_ROWS / lengths are estimates, not exact counts.
SELECT TABLE_SCHEMA,TABLE_NAME,TABLE_TYPE,ENGINE,ROW_FORMAT,TABLE_ROWS,
       DATA_LENGTH,INDEX_LENGTH,CREATE_TIME,UPDATE_TIME
FROM information_schema.TABLES
WHERE TABLE_SCHEMA IN ('loucka_reconstruction','pocasi-loucka.eu',
                       'pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old',
                       'old_weewx','weewx_WH1080')
ORDER BY TABLE_SCHEMA,TABLE_TYPE,TABLE_NAME;
