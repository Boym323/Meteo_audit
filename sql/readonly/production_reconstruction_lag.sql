-- Current read-only max/count inventory. Epochs are Unix UTC.
SELECT 'loucka_reconstruction' AS archive_name,COUNT(*) AS rows_n,MIN(dateTime) AS first_epoch,MAX(dateTime) AS last_epoch
FROM `loucka_reconstruction`.archive
UNION ALL
SELECT 'pocasi-loucka.eu',COUNT(*),MIN(dateTime),MAX(dateTime)
FROM `pocasi-loucka.eu`.archive;

-- Main production rows after the last reconstruction archive row (1793286600).
-- One anchor row is included to count the first time step; remaining rows are new.
WITH recent AS (
  SELECT p.dateTime,p.`interval`,p.usUnits,p.radiation,p.UV,p.windSpeed,p.windGust,p.rain,
         LAG(p.dateTime) OVER (ORDER BY p.dateTime) AS prev_time
  FROM `pocasi-loucka.eu`.archive p
  WHERE p.dateTime >= 1793286600
)
SELECT COUNT(*) AS rows_including_anchor,
       SUM(dateTime > 1793286600) AS post_reconstruction_rows,
       MIN(dateTime) AS first_epoch,MAX(dateTime) AS last_epoch,
       SUM(dateTime > 1793286600 AND radiation IS NOT NULL) AS radiation_nonnull,
       SUM(dateTime > 1793286600 AND UV IS NOT NULL) AS UV_nonnull,
       SUM(dateTime > 1793286600 AND windSpeed IS NOT NULL) AS windSpeed_nonnull,
       SUM(dateTime > 1793286600 AND windGust IS NOT NULL) AS windGust_nonnull,
       SUM(dateTime > 1793286600 AND rain IS NOT NULL) AS rain_nonnull,
       SUM(dateTime > 1793286600 AND `interval` <> 5) AS interval_not_5,
       SUM(prev_time IS NOT NULL AND dateTime-prev_time=300) AS delta_300s,
       SUM(prev_time IS NOT NULL AND dateTime-prev_time<>300) AS delta_not_300s
FROM recent;

-- Exact non-300s gaps in this live production tail.
WITH recent AS (
  SELECT p.dateTime,p.`interval`,p.outTemp,p.outHumidity,p.rain,p.rainRate,
         LAG(p.dateTime) OVER (ORDER BY p.dateTime) AS prev_time
  FROM `pocasi-loucka.eu`.archive p
  WHERE p.dateTime >= 1793286600
)
SELECT prev_time AS previous_epoch,dateTime AS next_epoch,dateTime-prev_time AS delta_seconds,
       `interval`,outTemp,outHumidity,rain,rainRate
FROM recent
WHERE prev_time IS NOT NULL AND dateTime-prev_time<>300
ORDER BY dateTime;
