-- READ-ONLY exact source-only units/interval profile for UTC 2015.
SELECT a0.usUnits AS old_usUnits,a0.interval AS old_interval,
       a1.usUnits AS wh_usUnits,a1.interval AS wh_interval,COUNT(*) AS rows_n
FROM old_weewx.archive a0
JOIN weewx_WH1080.archive a1 ON a1.dateTime=a0.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive a2 ON a2.dateTime=a0.dateTime
WHERE a0.dateTime>=1420070400 AND a0.dateTime<1451606400 AND a2.dateTime IS NULL
GROUP BY old_usUnits,old_interval,wh_usUnits,wh_interval;
