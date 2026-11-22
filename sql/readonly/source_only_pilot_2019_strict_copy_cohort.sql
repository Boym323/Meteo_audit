-- Next-best source-only pilot lane: exact-copy, complete 5-variable records from 2019.
-- READ-ONLY SELECT. No target row is inserted and no proposal is generated.
SELECT o.dateTime,o.usUnits AS old_units,w.usUnits AS wh_units,
       o.interval AS old_interval,w.interval AS wh_interval,
       o.outTemp AS old_temp,w.outTemp AS wh_temp,
       o.outHumidity AS old_rh,w.outHumidity AS wh_rh,
       o.rain AS old_rain,w.rain AS wh_rain,
       o.rainRate AS old_rainrate,w.rainRate AS wh_rainrate,
       o.windSpeed AS old_wind,w.windSpeed AS wh_wind,
       prev.dateTime AS prev_time,prev.outTemp AS prev_temp,prev.outHumidity AS prev_rh,prev.rain AS prev_rain,
       nxt.dateTime AS next_time,nxt.outTemp AS next_temp,nxt.outHumidity AS next_rh,nxt.rain AS next_rain
FROM old_weewx.archive o
JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive a ON a.dateTime=o.dateTime
LEFT JOIN old_weewx.archive prev ON prev.dateTime=o.dateTime-300
LEFT JOIN old_weewx.archive nxt ON nxt.dateTime=o.dateTime+300
WHERE o.dateTime>=1546300800 AND o.dateTime<1577836800
  AND o.interval=5 AND w.interval=5 AND o.usUnits=17 AND w.usUnits=17
  AND MOD(o.dateTime,300)=0 AND a.dateTime IS NULL
  AND o.outTemp IS NOT NULL AND w.outTemp IS NOT NULL
  AND o.outHumidity IS NOT NULL AND w.outHumidity IS NOT NULL
  AND o.rain IS NOT NULL AND w.rain IS NOT NULL
  AND o.rainRate IS NOT NULL AND w.rainRate IS NOT NULL
  AND o.windSpeed IS NOT NULL AND w.windSpeed IS NOT NULL
  AND o.outTemp=w.outTemp AND o.outHumidity=w.outHumidity
  AND o.rain=w.rain AND o.rainRate=w.rainRate AND o.windSpeed=w.windSpeed
ORDER BY o.dateTime;
