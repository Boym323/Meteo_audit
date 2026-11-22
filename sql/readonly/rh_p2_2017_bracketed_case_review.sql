-- Read-only exact-time screen for 2017 source RH values within target-neighbor
-- brackets and exact source/target temperature matches. All of 2017 is outside
-- the protected 2018-Q1 window. Includes six-archive row presence, history and
-- exact LuhaMet reference context; LuhaMet is not local ground truth.
SELECT o.dateTime, o.outHumidity AS source_rh, o.outTemp AS source_temp,
       r.outTemp AS target_temp, r.outHumidity AS target_rh,
       rp.outHumidity AS prev_rh, rn.outHumidity AS next_rh,
       rp.outTemp AS prev_temp, rn.outTemp AS next_temp,
       e.dateTime AS euold_time, e.outHumidity AS euold_rh,
       eu.dateTime AS eu_time, eu.outHumidity AS eu_rh,
       gw.dateTime AS gw_time, gw.outHumidity AS gw_rh,
       o.usUnits AS old_units, o.`interval` AS old_interval,
       w.usUnits AS wh_units, w.`interval` AS wh_interval,
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
WHERE o.dateTime>=1483228800 AND o.dateTime<1514764800
  AND o.outHumidity IS NOT NULL AND o.outHumidity=w.outHumidity
  AND r.outHumidity IS NULL AND rp.outHumidity IS NOT NULL
  AND rn.outHumidity IS NOT NULL AND o.outTemp=w.outTemp
  AND o.outTemp=r.outTemp
  AND o.outHumidity BETWEEN LEAST(rp.outHumidity,rn.outHumidity)
                        AND GREATEST(rp.outHumidity,rn.outHumidity)
  AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                 WHERE c.target_time=o.dateTime AND c.variable='outHumidity')
ORDER BY o.dateTime;
