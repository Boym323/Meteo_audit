-- SELECT-only annual exact timestamp and source-field availability reconciliation.
-- Run separately for each source schema and UTC year, substituting only one of
-- the allowlisted schemas: old_weewx or weewx_WH1080.
SELECT s.interval AS source_interval,COUNT(*) AS source_rows,
       SUM(r.dateTime IS NOT NULL) AS exact_recon_timestamps,
       SUM(r.dateTime IS NULL) AS source_timestamp_missing_in_recon,
       SUM(r.dateTime IS NULL AND s.outTemp IS NOT NULL) AS missing_outTemp_available,
       SUM(r.dateTime IS NULL AND s.outHumidity IS NOT NULL) AS missing_outHumidity_available,
       SUM(r.dateTime IS NULL AND s.rain IS NOT NULL) AS missing_rain_available,
       SUM(r.dateTime IS NULL AND s.rainRate IS NOT NULL) AS missing_rainRate_available,
       SUM(r.dateTime IS NOT NULL AND r.outTemp IS NULL AND s.outTemp IS NOT NULL) AS recon_null_outTemp_source_has_value,
       SUM(r.dateTime IS NOT NULL AND r.outHumidity IS NULL AND s.outHumidity IS NOT NULL) AS recon_null_outHumidity_source_has_value,
       SUM(r.dateTime IS NOT NULL AND r.rain IS NULL AND s.rain IS NOT NULL) AS recon_null_rain_source_has_value,
       SUM(r.dateTime IS NOT NULL AND r.rainRate IS NULL AND s.rainRate IS NOT NULL) AS recon_null_rainRate_source_has_value
FROM <ALLOWLISTED_SOURCE_SCHEMA>.archive AS s
LEFT JOIN loucka_reconstruction.archive AS r ON r.dateTime=s.dateTime
WHERE s.dateTime >= :utc_year_start AND s.dateTime < :utc_year_end
GROUP BY s.interval ORDER BY s.interval;

-- Diagnostic nearest-300s grid only; not an approved timestamp alignment.
-- Run by target-grid UTC year and include a ±150s source-boundary margin.
SELECT COUNT(*) AS target_grid_slots,SUM(g.n_source) AS source_rows,
       SUM(g.n_offgrid) AS source_rows_off_target_epoch,
       SUM(g.n_offgrid*(a.dateTime IS NOT NULL)) AS offgrid_rows_with_recon_grid,
       SUM(g.n_offgrid=1 AND g.n_source=1 AND a.dateTime IS NOT NULL) AS unique_offgrid_source_recon_pairs,
       SUM(g.n_offgrid>0 AND g.n_source>1 AND a.dateTime IS NOT NULL) AS ambiguous_target_slots,
       MAX(g.n_source) AS max_source_rows_per_target
FROM (
  SELECT nearest_epoch,COUNT(*) AS n_source,
         SUM(source_ts=nearest_epoch) AS n_exact,
         SUM(source_ts<>nearest_epoch) AS n_offgrid
  FROM (
    SELECT s.dateTime AS source_ts,FLOOR((s.dateTime+150)/300)*300 AS nearest_epoch
    FROM <ALLOWLISTED_SOURCE_SCHEMA>.archive AS s
    WHERE s.dateTime >= :utc_year_start-150 AND s.dateTime < :utc_year_end+150
  ) AS source_nearest
  GROUP BY nearest_epoch
  HAVING nearest_epoch >= :utc_year_start AND nearest_epoch < :utc_year_end
) AS g
LEFT JOIN loucka_reconstruction.archive AS a ON a.dateTime=g.nearest_epoch;
