-- Read-only per-target evidence for two 2016 common-source RH candidates.
-- The target row, two exact +/-300s target neighbors, all six archives and
-- history counts are returned. Q1 2018 and 2021 are outside this query.
SELECT k.dateTime,
       r.usUnits AS recon_units, r.`interval` AS recon_interval,
       r.outTemp AS recon_temp, r.outHumidity AS recon_rh,
       e.outTemp AS euold_temp, e.outHumidity AS euold_rh,
       eu.outTemp AS eu_temp, eu.outHumidity AS eu_rh,
       gw.outTemp AS gw_temp, gw.outHumidity AS gw_rh,
       o.usUnits AS old_units, o.`interval` AS old_interval,
       o.outTemp AS old_temp, o.outHumidity AS old_rh,
       o.rain AS old_rain, o.rainRate AS old_rainRate,
       o.windSpeed AS old_windSpeed, o.windGust AS old_windGust,
       o.barometer AS old_barometer,
       w.usUnits AS wh_units, w.`interval` AS wh_interval,
       w.outTemp AS wh_temp, w.outHumidity AS wh_rh,
       w.rain AS wh_rain, w.rainRate AS wh_rainRate,
       w.windSpeed AS wh_windSpeed, w.windGust AS wh_windGust,
       w.barometer AS wh_barometer,
       (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c
        WHERE c.target_time=k.dateTime AND c.variable='outHumidity') AS rh_events,
       (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c
        WHERE c.target_time=k.dateTime) AS all_events
FROM (SELECT 1458239100 AS dateTime UNION ALL SELECT 1458239400
      UNION ALL SELECT 1458239700 UNION ALL SELECT 1474061100
      UNION ALL SELECT 1474061400 UNION ALL SELECT 1474061700) k
LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=k.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive e ON e.dateTime=k.dateTime
LEFT JOIN `pocasi-loucka.eu`.archive eu ON eu.dateTime=k.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive gw ON gw.dateTime=k.dateTime
LEFT JOIN old_weewx.archive o ON o.dateTime=k.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=k.dateTime
ORDER BY k.dateTime;
