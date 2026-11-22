-- SELECT-only exact-time regional reference context for three zero-heavy gaps.
-- No nearest-time matching is done; LuhaMet remains reference_only, not local truth.
SELECT 2 AS gap_id, COUNT(*) AS source_rows, COUNT(r.observed_at_utc) AS exact_luhamet_pairs,
       SUM(r.temperature_c IS NOT NULL) AS reference_temp_n,
       SUM(r.temperature_c<0) AS reference_below0,
       SUM(r.temperature_c=0) AS reference_zero,
       SUM(r.temperature_c>0) AS reference_above0,
       MIN(r.temperature_c) AS reference_min_c, MAX(r.temperature_c) AS reference_max_c,
       SUM(b.outTemp=0 AND r.temperature_c IS NOT NULL) AS zero_source_with_reference,
       COUNT(DISTINCT r.quality_status) AS qc_statuses,
       MIN(r.quality_status) AS qc_status,
       MIN(r.source_resolution) AS source_resolution
FROM `weewx_WH1080`.`archive` b
LEFT JOIN `loucka_reconstruction`.`reference_observations` r
  ON r.observed_at_utc=b.dateTime AND r.station_id='luhamet_sehradice'
WHERE b.dateTime BETWEEN 1453156500 AND 1454764200
UNION ALL
SELECT 3, COUNT(*), COUNT(r.observed_at_utc), SUM(r.temperature_c IS NOT NULL),
       SUM(r.temperature_c<0), SUM(r.temperature_c=0), SUM(r.temperature_c>0),
       MIN(r.temperature_c), MAX(r.temperature_c), SUM(b.outTemp=0 AND r.temperature_c IS NOT NULL),
       COUNT(DISTINCT r.quality_status), MIN(r.quality_status), MIN(r.source_resolution)
FROM `weewx_WH1080`.`archive` b
LEFT JOIN `loucka_reconstruction`.`reference_observations` r
  ON r.observed_at_utc=b.dateTime AND r.station_id='luhamet_sehradice'
WHERE b.dateTime BETWEEN 1494564600 AND 1496007900
UNION ALL
SELECT 5, COUNT(*), COUNT(r.observed_at_utc), SUM(r.temperature_c IS NOT NULL),
       SUM(r.temperature_c<0), SUM(r.temperature_c=0), SUM(r.temperature_c>0),
       MIN(r.temperature_c), MAX(r.temperature_c), SUM(b.outTemp=0 AND r.temperature_c IS NOT NULL),
       COUNT(DISTINCT r.quality_status), MIN(r.quality_status), MIN(r.source_resolution)
FROM `weewx_WH1080`.`archive` b
LEFT JOIN `loucka_reconstruction`.`reference_observations` r
  ON r.observed_at_utc=b.dateTime AND r.station_id='luhamet_sehradice'
WHERE b.dateTime BETWEEN 1483966800 AND 1484645400;
