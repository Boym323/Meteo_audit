-- READ ONLY source-only cohort: exact-copy primary fields, RH NULL in both copies.
SELECT o.dateTime,o.outTemp,o.outHumidity,o.rain,o.rainRate,o.windSpeed,
 p.dateTime AS target_prev_time,p.outTemp AS target_prev_temp,n.dateTime AS target_next_time,n.outTemp AS target_next_temp
FROM old_weewx.archive o JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive x ON x.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive p ON p.dateTime=o.dateTime-300
LEFT JOIN loucka_reconstruction.archive n ON n.dateTime=o.dateTime+300
WHERE o.dateTime>=1546300800 AND o.dateTime<1577836800 AND o.`interval`=5 AND w.`interval`=5
 AND o.usUnits=17 AND w.usUnits=17 AND MOD(o.dateTime,300)=0 AND x.dateTime IS NULL
 AND o.outTemp IS NOT NULL AND w.outTemp=o.outTemp
 AND o.outHumidity IS NULL AND w.outHumidity IS NULL
 AND o.rain IS NOT NULL AND w.rain=o.rain AND o.rainRate IS NOT NULL AND w.rainRate=o.rainRate
 AND o.windSpeed IS NOT NULL AND w.windSpeed=o.windSpeed ORDER BY o.dateTime;
