-- READ-ONLY exact-key review of three previously catalogued singleton source rows.
-- Run with loucka_reconstruction selected; every other database is explicitly qualified.
SELECT x.dateTime,
       x.dateTime % 300 AS epoch_grid_remainder,
       r.dateTime IS NOT NULL AS reconstruction_row,
       e.dateTime IS NOT NULL AS pocasi_eu_row,
       g.dateTime IS NOT NULL AS gw1000_row,
       eo.dateTime IS NOT NULL AS eu_old_row,
       o.dateTime IS NOT NULL AS old_weewx_row,
       w.dateTime IS NOT NULL AS wh1080_row,
       o.outTemp AS old_outTemp, w.outTemp AS wh_outTemp,
       o.outHumidity AS old_outHumidity, w.outHumidity AS wh_outHumidity,
       o.rain AS old_rain, w.rain AS wh_rain,
       o.rainRate AS old_rainRate, w.rainRate AS wh_rainRate,
       o.usUnits AS old_usUnits, w.usUnits AS wh_usUnits,
       o.`interval` AS old_interval, w.`interval` AS wh_interval,
       (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c
         WHERE c.target_time=x.dateTime) AS reconstruction_change_events
FROM (SELECT 1248436740 AS dateTime
      UNION ALL SELECT 1355404980
      UNION ALL SELECT 1360266480) x
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=x.dateTime
LEFT JOIN `pocasi-loucka.eu`.archive e ON e.dateTime=x.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=x.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive eo ON eo.dateTime=x.dateTime
LEFT JOIN old_weewx.archive o ON o.dateTime=x.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=x.dateTime
ORDER BY x.dateTime;
