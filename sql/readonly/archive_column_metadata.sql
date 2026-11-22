-- Exact archive column metadata for all discovered meteorological archives.
-- Metadata-only SELECT; does not scan archive data rows.
SELECT TABLE_SCHEMA,TABLE_NAME,ORDINAL_POSITION,COLUMN_NAME,COLUMN_TYPE,
       IS_NULLABLE,COLUMN_DEFAULT,EXTRA,COLUMN_KEY
FROM information_schema.COLUMNS
WHERE TABLE_NAME='archive'
  AND TABLE_SCHEMA IN ('loucka_reconstruction','pocasi-loucka.eu',
                       'pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old',
                       'old_weewx','weewx_WH1080')
ORDER BY TABLE_SCHEMA,ORDINAL_POSITION;
