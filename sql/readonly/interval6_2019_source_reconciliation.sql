-- Read-only source concordance around the lone 2019 target row declaring interval=6.
SELECT a.dateTime AS dateTime_utc_epoch,a.`interval` AS target_interval_minutes,
       a.usUnits AS target_usUnits,a.outTemp AS target_outTemp,
       o.`interval` AS old_interval_minutes,o.outTemp AS old_outTemp,
       w.`interval` AS wh_interval_minutes,w.outTemp AS wh_outTemp,
       p.`interval` AS prod_interval_minutes,p.outTemp AS prod_outTemp,
       g.`interval` AS gw_interval_minutes,g.outTemp AS gw_outTemp,
       e.`interval` AS legacy_prod_interval_minutes,e.outTemp AS legacy_prod_outTemp,
       (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c
        WHERE c.target_time=a.dateTime AND c.variable='outTemp') AS outTemp_events
FROM loucka_reconstruction.archive a
LEFT JOIN old_weewx.archive o ON o.dateTime=a.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive e ON e.dateTime=a.dateTime
WHERE a.dateTime BETWEEN 1551328500 AND 1551329100
ORDER BY a.dateTime;
