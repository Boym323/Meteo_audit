-- SELECT-only exact-timestamp local neighbor/reference context for the
-- six conflicting RH candidates on 2019-06-20 05:10-05:45 UTC.
SELECT a.dateTime,
       a.outTemp AS recon_outTemp,
       a.outHumidity AS recon_outHumidity,
       o.outTemp AS old_outTemp,
       o.outHumidity AS old_outHumidity,
       o.`interval` AS old_interval,
       o.usUnits AS old_usUnits,
       w.outTemp AS wh_outTemp,
       w.outHumidity AS wh_outHumidity,
       w.`interval` AS wh_interval,
       w.usUnits AS wh_usUnits,
       r.temperature_c AS luhamet_temperature_c,
       r.relative_humidity_pct AS luhamet_rh_pct,
       r.quality_status AS luhamet_quality_status,
       r.source_resolution AS luhamet_source_resolution
FROM loucka_reconstruction.archive a
LEFT JOIN old_weewx.archive o ON o.dateTime=a.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=a.dateTime
LEFT JOIN loucka_reconstruction.reference_observations r
  ON r.station_id='luhamet_sehradice' AND r.observed_at_utc=a.dateTime
WHERE a.dateTime BETWEEN 1561006800 AND 1561009800
ORDER BY a.dateTime;
