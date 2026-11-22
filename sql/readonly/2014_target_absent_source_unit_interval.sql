-- READ-ONLY unit/interval profile for exact 2014 source-only whole rows.
SELECT a0.usUnits AS old_units,a0.interval AS old_interval,a1.usUnits AS wh_units,a1.interval AS wh_interval,COUNT(*) AS rows_n,MIN(a0.dateTime) AS first_epoch,MAX(a0.dateTime) AS last_epoch
FROM `old_weewx`.`archive` a0 JOIN `weewx_WH1080`.`archive` a1 ON a1.dateTime=a0.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.`archive` a2 ON a2.dateTime=a0.dateTime
WHERE a0.dateTime>=1388534400 AND a0.dateTime<1420070400 AND a2.dateTime IS NULL
GROUP BY old_units,old_interval,wh_units,wh_interval;
