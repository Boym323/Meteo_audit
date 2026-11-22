-- Snapshot at 2026-11-13 02:16 UTC via Weather MCP against information_schema.
-- Read-only, bounded to the current reconstruction tail. No writes.
-- Query 1: current production rows after the reconstruction anchor; interval
-- LAG is computed over the bounded production slice beginning 2026-10-29.
WITH recon AS (
  SELECT MAX(dateTime) AS anchor_epoch
  FROM `loucka_reconstruction`.`archive`
), prod AS (
  SELECT dateTime, `interval`, usUnits, outTemp, outHumidity, rain, rainRate,
         LAG(dateTime) OVER (ORDER BY dateTime) AS prev_epoch
  FROM `pocasi-loucka.eu`.`archive`
  WHERE dateTime > 1793270400
), tail AS (
  SELECT prod.* FROM prod JOIN recon ON prod.dateTime > recon.anchor_epoch
)
SELECT `interval`, usUnits, COUNT(*) AS rows_n,
       MIN(dateTime) AS first_epoch, MAX(dateTime) AS last_epoch,
       SUM(outTemp IS NULL) AS outTemp_null,
       SUM(outHumidity IS NULL) AS outHumidity_null,
       SUM(rain IS NULL) AS rain_null,
       SUM(rainRate IS NULL) AS rainRate_null,
       SUM(prev_epoch IS NOT NULL AND dateTime-prev_epoch=`interval`*60) AS exact_interval_steps,
       SUM(prev_epoch IS NOT NULL AND dateTime-prev_epoch>`interval`*60) AS long_steps,
       SUM(prev_epoch IS NOT NULL AND dateTime-prev_epoch<`interval`*60) AS short_steps
FROM tail
GROUP BY `interval`, usUnits
ORDER BY `interval`, usUnits;

-- Query 2: bounded problem cases from the same snapshot.
WITH recon AS (
  SELECT MAX(dateTime) AS anchor_epoch
  FROM `loucka_reconstruction`.`archive`
), prod AS (
  SELECT dateTime, `interval`,
         LAG(dateTime) OVER (ORDER BY dateTime) AS prev_epoch
  FROM `pocasi-loucka.eu`.`archive`
  WHERE dateTime > 1793270400
)
SELECT prod.prev_epoch, prod.dateTime AS current_epoch,
       prod.dateTime-prod.prev_epoch AS delta_seconds,
       prod.`interval` AS current_interval_minutes, recon.anchor_epoch
FROM prod JOIN recon ON prod.dateTime > recon.anchor_epoch
WHERE prod.prev_epoch IS NOT NULL
  AND prod.dateTime-prod.prev_epoch > prod.`interval`*60
ORDER BY prod.dateTime;
