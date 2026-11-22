-- Exact-time, named-reference cross-check for the 10 strict 2017 source-only outTemp=0 rows. READ-ONLY.
SELECT w.dateTime AS target_time,w.outTemp AS wh_outTemp,o.outTemp AS old_outTemp,
       l.temperature_c AS luhamet_temperature_c,l.relative_humidity_pct AS luhamet_rh,
       l.source_resolution,l.quality_status,l.source_url
FROM weewx_WH1080.archive w
JOIN old_weewx.archive o ON o.dateTime=w.dateTime
LEFT JOIN loucka_reconstruction.reference_observations l
  ON l.station_id='luhamet_sehradice' AND l.observed_at_utc=w.dateTime
WHERE w.dateTime IN (1484914200,1485427500,1485776700,1485783900,1492722000,
                     1492724400,1492724700,1494440700,1494441000,1504063500)
ORDER BY w.dateTime;
