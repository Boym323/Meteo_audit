-- SELECT-only exact-time provenance trace; five rows from the descriptive upper-tail screen.
WITH c AS (
 SELECT a.dateTime,a.rain,a.rainRate,a.`interval` AS interval_min,a.usUnits
 FROM archive a
 WHERE (a.dateTime>=1356998400 AND a.dateTime<1388534400
        OR a.dateTime>=1672531200 AND a.dateTime<1704067200)
   AND (a.rain>1 OR a.rainRate>=10)
), op AS (
 SELECT c.dateTime AS target_time,s.dateTime AS source_time,s.rain,s.`interval` AS interval_min,
        ROW_NUMBER() OVER(PARTITION BY c.dateTime ORDER BY s.dateTime DESC) AS rn
 FROM c LEFT JOIN old_weewx.archive s
   ON s.dateTime<c.dateTime AND s.dateTime>=c.dateTime-600
), h AS (
 SELECT rc.target_time,rc.variable,rc.state,rc.batch_key,rc.old_value,rc.new_value,
        rc.source_database,rc.source_time,rc.source_value,
        ROW_NUMBER() OVER(PARTITION BY rc.target_time,rc.variable ORDER BY rc.created_at DESC,rc.id DESC) rn
 FROM loucka_reconstruction.reconstruction_changes rc
 JOIN c ON c.dateTime=rc.target_time
 WHERE rc.variable IN ('rain','rainRate')
)
SELECT MAX(UTC_TIMESTAMP()) AS query_time_utc,
       c.dateTime,c.rain,c.rainRate,c.interval_min,c.usUnits,
       o.rain AS old_rain,o.rainRate AS old_rate,w.rain AS wh_rain,w.rainRate AS wh_rate,
       g.rain AS gw_rain,g.rainRate AS gw_rate,
       op.source_time AS old_prev_time,op.rain AS old_prev_counter,
       MAX(CASE WHEN h.variable='rain' AND h.rn=1 THEN h.state END) AS rain_latest_state,
       MAX(CASE WHEN h.variable='rainRate' AND h.rn=1 THEN h.state END) AS rate_latest_state,
       MAX(CASE WHEN h.variable='rainRate' AND h.rn=1 THEN h.batch_key END) AS rate_latest_batch,
       MAX(CASE WHEN h.variable='rainRate' AND h.rn=1 THEN h.old_value END) AS rate_latest_old,
       MAX(CASE WHEN h.variable='rainRate' AND h.rn=1 THEN h.new_value END) AS rate_latest_new,
       MAX(CASE WHEN h.variable='rainRate' AND h.rn=1 THEN h.source_database END) AS rate_history_source,
       MAX(CASE WHEN h.variable='rainRate' AND h.rn=1 THEN h.source_time END) AS rate_history_source_time,
       MAX(CASE WHEN h.variable='rainRate' AND h.rn=1 THEN h.source_value END) AS rate_history_source_value
FROM c
LEFT JOIN old_weewx.archive o ON o.dateTime=c.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=c.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=c.dateTime
LEFT JOIN op ON op.target_time=c.dateTime AND op.rn=1
LEFT JOIN h ON h.target_time=c.dateTime AND h.rn=1
GROUP BY c.dateTime,c.rain,c.rainRate,c.interval_min,c.usUnits,
 o.rain,o.rainRate,w.rain,w.rainRate,g.rain,g.rainRate,op.source_time,op.rain
ORDER BY c.dateTime
