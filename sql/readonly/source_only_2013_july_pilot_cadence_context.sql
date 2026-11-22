-- READ-ONLY source/reconstruction cadence boundary, 2013-07-08 20:40–22:50 UTC.
START TRANSACTION READ ONLY;
SELECT w.dateTime,w.`interval` AS source_interval,w.outTemp AS source_outTemp,w.outHumidity AS source_outHumidity,
 t.dateTime IS NOT NULL AS target_row_present,t.`interval` AS target_interval,t.outTemp AS target_outTemp,t.outHumidity AS target_outHumidity
FROM `weewx_WH1080`.archive w
LEFT JOIN `loucka_reconstruction`.archive t ON t.dateTime=w.dateTime
WHERE w.dateTime>=1373316000 AND w.dateTime<=1373323800
ORDER BY w.dateTime;
