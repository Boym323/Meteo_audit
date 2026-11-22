-- Exact bounded reconciliation after the reconstruction high-water mark.
-- Returns aggregates only; does not propose or apply inserts.
SELECT COUNT(*) AS production_rows_after_anchor,
       SUM(r.dateTime IS NOT NULL) AS timestamp_overlap_rows,
       MIN(p.dateTime) AS first_epoch,
       MAX(p.dateTime) AS latest_epoch,
       SUM(p.`interval` = 5) AS interval5_rows,
       SUM(p.usUnits = 16) AS usUnits16_rows,
       SUM(p.outTemp IS NOT NULL) AS outTemp_rows,
       SUM(p.outHumidity IS NOT NULL) AS outHumidity_rows,
       SUM(p.rain IS NOT NULL) AS rain_rows,
       SUM(p.rainRate IS NOT NULL) AS rainRate_rows
FROM `pocasi-loucka.eu`.archive AS p
LEFT JOIN loucka_reconstruction.archive AS r
  ON r.dateTime = p.dateTime
WHERE p.dateTime > 1793286600;
