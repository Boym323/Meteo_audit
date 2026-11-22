-- Exact-time read-only evidence for the six 2019 RH candidates whose source RH
-- falls inside both non-NULL target-neighbor values. Q1 2018 and 2021 excluded.
SELECT o.dateTime, o.outHumidity AS source_rh, o.outTemp AS source_temp,
       r.dateTime AS recon_row_time, e.dateTime AS euold_row_time,
       eu.dateTime AS eu_row_time, gw.dateTime AS gw_row_time,
       o.dateTime AS old_row_time, w.dateTime AS wh_row_time,
       w.outTemp AS wh_temp, r.usUnits AS target_units,
       r.`interval` AS target_interval, r.outTemp AS target_temp,
       rp.outHumidity AS prev_rh, rn.outHumidity AS next_rh,
       rp.outTemp AS prev_temp, rn.outTemp AS next_temp,
       e.outHumidity AS euold_rh, eu.outHumidity AS eu_rh,
       gw.outHumidity AS gw_rh, o.usUnits AS old_units,
       o.`interval` AS old_interval, w.usUnits AS wh_units,
       w.`interval` AS wh_interval, o.rain AS source_rain,
       w.rainRate AS source_rainRate, o.windSpeed AS source_wind,
       w.windGust AS source_gust, o.barometer AS source_barometer,
       ref.relative_humidity_pct AS luhamet_rh,
       ref.temperature_c AS luhamet_temp,
       (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c
        WHERE c.target_time=o.dateTime AND c.variable='outHumidity') AS rh_events,
       (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c
        WHERE c.target_time=o.dateTime) AS all_events
FROM old_weewx.archive o
JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
JOIN loucka_reconstruction.archive r ON r.dateTime=o.dateTime
JOIN loucka_reconstruction.archive rp ON rp.dateTime=o.dateTime-300
JOIN loucka_reconstruction.archive rn ON rn.dateTime=o.dateTime+300
LEFT JOIN `pocasi-loucka.eu_old`.archive e ON e.dateTime=o.dateTime
LEFT JOIN `pocasi-loucka.eu`.archive eu ON eu.dateTime=o.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive gw ON gw.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.reference_observations ref
  ON ref.station_id='luhamet_sehradice' AND ref.observed_at_utc=o.dateTime
WHERE o.dateTime>=1546300800 AND o.dateTime<1577836800
  AND o.outHumidity IS NOT NULL AND o.outHumidity=w.outHumidity
  AND r.outHumidity IS NULL AND rp.outHumidity IS NOT NULL
  AND rn.outHumidity IS NOT NULL
  AND o.outTemp=w.outTemp AND o.outTemp=r.outTemp
  AND o.outHumidity BETWEEN LEAST(rp.outHumidity,rn.outHumidity)
                        AND GREATEST(rp.outHumidity,rn.outHumidity)
  AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                 WHERE c.target_time=o.dateTime AND c.variable='outHumidity')
ORDER BY o.dateTime;
