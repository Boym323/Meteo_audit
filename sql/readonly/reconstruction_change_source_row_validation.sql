-- SELECT-only verification of source row existence and raw-field concordance.
-- Database-qualified table names are intentionally explicit; source_database
-- is free text and must not be treated as an SQL identifier.
SELECT variable, source_database, COUNT(*) AS events,
       SUM(source_row_missing) AS source_row_missing,
       SUM(source_value_matches_raw_field) AS source_value_matches_raw_field,
       SUM(source_value_null) AS source_value_null,
       SUM(target_time_equals_source_time) AS target_time_equals_source_time
FROM (
  SELECT c.variable,c.source_database,c.source_value,
         (s.dateTime IS NULL) source_row_missing,
         (c.source_value <=> s.outTemp) source_value_matches_raw_field,
         (c.source_value IS NULL) source_value_null,
         (c.source_time=c.target_time) target_time_equals_source_time
  FROM loucka_reconstruction.reconstruction_changes c
  LEFT JOIN old_weewx.archive s ON s.dateTime=c.source_time
  WHERE c.state='applied' AND c.variable='outTemp' AND c.source_database='old_weewx'
  UNION ALL
  SELECT c.variable,c.source_database,c.source_value,(s.dateTime IS NULL),
         (c.source_value <=> s.outHumidity),(c.source_value IS NULL),(c.source_time=c.target_time)
  FROM loucka_reconstruction.reconstruction_changes c
  LEFT JOIN `pocasi-loucka.eu_GW1000`.archive s ON s.dateTime=c.source_time
  WHERE c.state='applied' AND c.variable='outHumidity' AND c.source_database='pocasi-loucka.eu_GW1000'
  UNION ALL
  SELECT c.variable,c.source_database,c.source_value,(s.dateTime IS NULL),
         (c.source_value <=> s.rain),(c.source_value IS NULL),(c.source_time=c.target_time)
  FROM loucka_reconstruction.reconstruction_changes c
  LEFT JOIN old_weewx.archive s ON s.dateTime=c.source_time
  WHERE c.state='applied' AND c.variable='rain' AND c.source_database='old_weewx'
  UNION ALL
  SELECT c.variable,c.source_database,c.source_value,(s.dateTime IS NULL),
         (c.source_value <=> s.rain),(c.source_value IS NULL),(c.source_time=c.target_time)
  FROM loucka_reconstruction.reconstruction_changes c
  LEFT JOIN `pocasi-loucka.eu_GW1000`.archive s ON s.dateTime=c.source_time
  WHERE c.state='applied' AND c.variable='rain' AND c.source_database='pocasi-loucka.eu_GW1000'
  UNION ALL
  SELECT c.variable,c.source_database,c.source_value,(s.dateTime IS NULL),
         (c.source_value <=> s.rain),(c.source_value IS NULL),(c.source_time=c.target_time)
  FROM loucka_reconstruction.reconstruction_changes c
  LEFT JOIN `pocasi-loucka.eu`.archive s ON s.dateTime=c.source_time
  WHERE c.state='applied' AND c.variable='rain' AND c.source_database='pocasi-loucka.eu'
  UNION ALL
  SELECT c.variable,c.source_database,c.source_value,(s.dateTime IS NULL),
         (c.source_value <=> s.rain),(c.source_value IS NULL),(c.source_time=c.target_time)
  FROM loucka_reconstruction.reconstruction_changes c
  LEFT JOIN `pocasi-loucka.eu_old`.archive s ON s.dateTime=c.source_time
  WHERE c.state='applied' AND c.variable='rain' AND c.source_database='pocasi-loucka.eu_old'
  UNION ALL
  SELECT c.variable,c.source_database,c.source_value,(s.dateTime IS NULL),
         (c.source_value <=> s.rain_cm),(c.source_value IS NULL),(c.source_time=c.target_time)
  FROM loucka_reconstruction.reconstruction_changes c
  LEFT JOIN loucka_reconstruction.rain_reconstruction_202107_chmi_v1 s ON s.dateTime=c.source_time
  WHERE c.state='applied' AND c.variable='rain' AND c.source_database='rain_reconstruction_202107_chmi_v1'
  UNION ALL
  SELECT c.variable,c.source_database,c.source_value,(s.dateTime IS NULL),
         (c.source_value <=> s.rainRate),(c.source_value IS NULL),(c.source_time=c.target_time)
  FROM loucka_reconstruction.reconstruction_changes c
  LEFT JOIN `pocasi-loucka.eu_GW1000`.archive s ON s.dateTime=c.source_time
  WHERE c.state='applied' AND c.variable='rainRate' AND c.source_database='pocasi-loucka.eu_GW1000'
  UNION ALL
  SELECT c.variable,c.source_database,c.source_value,(s.dateTime IS NULL),
         (c.source_value <=> s.rainRate),(c.source_value IS NULL),(c.source_time=c.target_time)
  FROM loucka_reconstruction.reconstruction_changes c
  LEFT JOIN `pocasi-loucka.eu_old`.archive s ON s.dateTime=c.source_time
  WHERE c.state='applied' AND c.variable='rainRate' AND c.source_database='pocasi-loucka.eu_old'
  UNION ALL
  SELECT c.variable,c.source_database,c.source_value,(s.dateTime IS NULL),
         (c.source_value <=> s.rainRate_before_cm_h),(c.source_value IS NULL),(c.source_time=c.target_time)
  FROM loucka_reconstruction.reconstruction_changes c
  LEFT JOIN loucka_reconstruction.rain_backup_202107_before_chmi_v1 s ON s.dateTime=c.source_time
  WHERE c.state='applied' AND c.variable='rainRate' AND c.source_database='rain_backup_202107_before_chmi_v1'
) q
GROUP BY variable,source_database ORDER BY variable,source_database;

-- Self-source RH aggregate: distinguishes target equality from an exact source row.
SELECT COUNT(*) AS events,
       SUM(s.dateTime IS NULL) AS source_row_missing,
       SUM(c.source_value IS NULL) AS source_value_null,
       SUM(c.source_value <=> s.outHumidity) AS source_value_matches_raw,
       SUM(c.source_time=c.target_time) AS target_time_equals_source_time,
       MIN(c.source_time) AS min_source_time, MAX(c.source_time) AS max_source_time
FROM loucka_reconstruction.reconstruction_changes c
LEFT JOIN loucka_reconstruction.archive s ON s.dateTime=c.source_time
WHERE c.state='applied' AND c.variable='outHumidity'
  AND c.source_database='loucka_reconstruction';
