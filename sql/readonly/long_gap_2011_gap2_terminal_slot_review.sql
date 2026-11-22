-- READ-ONLY target/source state review for the terminal 2011 long-gap slots.
-- Run with loucka_reconstruction selected; archive schemas are qualified.
SELECT x.dateTime,
       x.dateTime % 300 AS epoch_grid_remainder,
       r.dateTime AS reconstruction_time, r.outTemp AS reconstruction_outTemp,
       e.dateTime AS pocasi_eu_time, e.outTemp AS pocasi_eu_outTemp,
       g.dateTime AS gw1000_time, g.outTemp AS gw1000_outTemp,
       eo.dateTime AS eu_old_time, eo.outTemp AS eu_old_outTemp,
       o.dateTime AS old_weewx_time, o.outTemp AS old_weewx_outTemp,
       w.dateTime AS wh1080_time, w.outTemp AS wh1080_outTemp,
       o.outHumidity AS old_weewx_RH, w.outHumidity AS wh1080_RH,
       o.rain AS old_weewx_rain, w.rain AS wh1080_rain,
       (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c
         WHERE c.target_time=x.dateTime) AS change_events
FROM (SELECT 1312296300 AS dateTime
      UNION ALL SELECT 1312296600
      UNION ALL SELECT 1312296840
      UNION ALL SELECT 1312296900) x
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=x.dateTime
LEFT JOIN `pocasi-loucka.eu`.archive e ON e.dateTime=x.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=x.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive eo ON eo.dateTime=x.dateTime
LEFT JOIN old_weewx.archive o ON o.dateTime=x.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=x.dateTime
ORDER BY x.dateTime;
