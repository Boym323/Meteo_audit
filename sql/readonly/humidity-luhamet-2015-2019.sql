-- Read-only historical LuhaMet humidity reconstruction candidates, 2015–2019.
-- Source WH1080 RH was intentionally removed on migration due to invalid sensor data.
-- NEVER use it to populate Loucka RH. This query writes nothing.
-- The archive is an interval-END series. For exact local-day reporting use
-- externally generated Europe/Prague boundaries (start,end].
-- Substitute year epoch limits if needed; illustrated with 2016 UTC year.
SELECT a.dateTime AS target_time_utc,
       a.outHumidity AS expected_old_value,
       a.outTemp AS local_temp_c,
       r.observed_at_utc AS source_time_utc,
       r.relative_humidity_pct AS luhamet_rh_pct,
       r.temperature_c AS luhamet_temp_c,
       ROUND(LEAST(100,GREATEST(1,
           r.relative_humidity_pct *
           EXP(17.62*r.temperature_c/(243.12+r.temperature_c)
              -17.62*a.outTemp/(243.12+a.outTemp))
       )),1) AS proposed_rh_pct
FROM `loucka_reconstruction`.archive a
JOIN `loucka_reconstruction`.reference_observations r
  ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
JOIN `loucka_reconstruction`.reference_observations prev
  ON prev.station_id='luhamet_sehradice' AND prev.observed_at_utc=r.observed_at_utc-300
JOIN `loucka_reconstruction`.reference_observations nxt
  ON nxt.station_id='luhamet_sehradice' AND nxt.observed_at_utc=r.observed_at_utc+300
WHERE a.dateTime>=1451606400 AND a.dateTime<1483228800
  AND a.outHumidity IS NULL
  AND a.usUnits=16 AND a.`interval`=5
  AND a.outTemp BETWEEN -40 AND 45
  AND r.relative_humidity_pct BETWEEN 30 AND 98
  AND r.temperature_c BETWEEN -40 AND 45
  AND ABS(a.outTemp-r.temperature_c)<=1.5
  AND prev.relative_humidity_pct BETWEEN 30 AND 98
  AND nxt.relative_humidity_pct BETWEEN 30 AND 98
  AND ABS(prev.relative_humidity_pct-r.relative_humidity_pct)<=6
  AND ABS(nxt.relative_humidity_pct-r.relative_humidity_pct)<=6
  AND NOT EXISTS (
    SELECT 1 FROM `loucka_reconstruction`.reconstruction_changes c
    WHERE c.target_time=a.dateTime AND c.variable='outHumidity'
      AND c.state='applied'
  )
ORDER BY a.dateTime
LIMIT 50;

-- Post-write audit; originals remain immutable.
SELECT SUBSTRING(batch_key,10,4) AS year_utc,
       COUNT(*) AS corrections,
       SUM(state='applied') AS applied,
       SUM(old_value IS NULL) AS originally_null,
       COUNT(DISTINCT target_time) AS unique_timestamps
FROM `loucka_reconstruction`.reconstruction_changes
WHERE batch_key REGEXP '^humidity-201[5-9]-luhamet-vapor-v1-[0-9]{4}$'
GROUP BY SUBSTRING(batch_key,10,4)
ORDER BY year_utc;
