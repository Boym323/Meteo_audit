-- SELECT-only: ten positive source rain rows at Q1-2018 rain=NULL targets, with exact neighbors.
WITH old_lag AS (
 SELECT dateTime,rain,rainRate,`interval` AS interval_min,usUnits,
        LAG(dateTime) OVER(ORDER BY dateTime) AS prev_time,
        LAG(rain) OVER(ORDER BY dateTime) AS prev_rain,
        LEAD(dateTime) OVER(ORDER BY dateTime) AS next_time,
        LEAD(rain) OVER(ORDER BY dateTime) AS next_rain
 FROM old_weewx.archive WHERE dateTime>=1514764800 AND dateTime<1522540800
)
SELECT UTC_TIMESTAMP() AS query_time_utc,
       s.dateTime,s.rain,s.rainRate,s.interval_min,s.usUnits,
       s.prev_time,s.prev_rain,s.rain-s.prev_rain AS delta_from_prev,
       s.next_time,s.next_rain,s.next_rain-s.rain AS delta_to_next,
       r.rain AS recon_rain,r.rainRate AS recon_rate,
       w.rain AS wh_rain,w.rainRate AS wh_rate,
       (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes h WHERE h.target_time=s.dateTime AND h.variable='rain') AS rain_history_events,
       (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes h WHERE h.target_time=s.dateTime AND h.variable='rainRate') AS rate_history_events
FROM old_lag s
JOIN loucka_reconstruction.archive r ON r.dateTime=s.dateTime
JOIN weewx_WH1080.archive w ON w.dateTime=s.dateTime
WHERE r.dateTime>=1514764800 AND r.dateTime<1522540800
  AND r.rain IS NULL AND s.rain>0
ORDER BY s.dateTime
