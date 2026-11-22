-- Read-only exact timestamp source-availability screen, UTC epoch boundaries.
-- A nonzero RH reference is a screening condition, not transfer validation.
SELECT CASE WHEN a.dateTime<1451606400 THEN 2015
            WHEN a.dateTime<1483228800 THEN 2016 ELSE 2017 END AS utc_year,
       COUNT(DISTINCT a.dateTime) AS archive_rows,
       COUNT(DISTINCT CASE WHEN a.outHumidity IS NULL THEN a.dateTime END) AS target_rh_null,
       COUNT(DISTINCT CASE WHEN r.observed_at_utc IS NOT NULL THEN a.dateTime END) AS exact_luhamet_timestamps,
       COUNT(DISTINCT CASE WHEN r.relative_humidity_pct>0 AND r.relative_humidity_pct<=100 THEN a.dateTime END) AS valid_nonzero_luhamet_rh,
       COUNT(DISTINCT CASE WHEN a.outHumidity IS NULL AND r.relative_humidity_pct>0
                           AND r.relative_humidity_pct<=100
                           AND NOT EXISTS (SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                             WHERE c.target_time=a.dateTime AND c.variable='outHumidity')
                      THEN a.dateTime END) AS null_target_valid_exact_reference_no_rh_history,
       COUNT(DISTINCT CASE WHEN a.outHumidity IS NULL AND r.relative_humidity_pct=0
                      THEN a.dateTime END) AS null_target_reference_rh_zero
FROM loucka_reconstruction.archive a
LEFT JOIN loucka_reconstruction.reference_observations r
  ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
WHERE a.dateTime>=1420070400 AND a.dateTime<1514764800
GROUP BY CASE WHEN a.dateTime<1451606400 THEN 2015
              WHEN a.dateTime<1483228800 THEN 2016 ELSE 2017 END
ORDER BY utc_year;

-- Reference QC / resolution for the exact-time target-gap subset.
SELECT CASE WHEN a.dateTime<1451606400 THEN 2015
            WHEN a.dateTime<1483228800 THEN 2016 ELSE 2017 END AS utc_year,
       r.quality_status,r.source_resolution,COUNT(DISTINCT a.dateTime) AS candidate_times
FROM loucka_reconstruction.archive a
JOIN loucka_reconstruction.reference_observations r
  ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
WHERE a.dateTime>=1420070400 AND a.dateTime<1514764800
  AND a.outHumidity IS NULL AND r.relative_humidity_pct>0 AND r.relative_humidity_pct<=100
  AND NOT EXISTS (SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
    WHERE c.target_time=a.dateTime AND c.variable='outHumidity')
GROUP BY utc_year,r.quality_status,r.source_resolution
ORDER BY utc_year,r.quality_status,r.source_resolution;
