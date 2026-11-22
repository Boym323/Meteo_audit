-- READ-ONLY targeted review of the only two 2011 source-only rows where old_weewx outTemp is NULL and WH1080 is non-NULL.
-- Separate exact source-key evidence from nearest-key context; do not infer a timestamp correction.
SELECT 'old_weewx' AS archive,dateTime,usUnits,`interval`,outTemp,outHumidity,rain,rainRate,windSpeed,windGust,barometer
FROM old_weewx.archive
WHERE dateTime BETWEEN 1307450940 AND 1307452740 OR dateTime BETWEEN 1307455140 AND 1307456940
UNION ALL SELECT 'weewx_WH1080',dateTime,usUnits,`interval`,outTemp,outHumidity,rain,rainRate,windSpeed,windGust,barometer FROM weewx_WH1080.archive
WHERE dateTime BETWEEN 1307450940 AND 1307452740 OR dateTime BETWEEN 1307455140 AND 1307456940
UNION ALL SELECT 'pocasi-loucka.eu_old',dateTime,usUnits,`interval`,outTemp,outHumidity,rain,rainRate,windSpeed,windGust,barometer FROM `pocasi-loucka.eu_old`.archive
WHERE dateTime BETWEEN 1307450940 AND 1307452740 OR dateTime BETWEEN 1307455140 AND 1307456940
UNION ALL SELECT 'pocasi-loucka.eu',dateTime,usUnits,`interval`,outTemp,outHumidity,rain,rainRate,windSpeed,windGust,barometer FROM `pocasi-loucka.eu`.archive
WHERE dateTime BETWEEN 1307450940 AND 1307452740 OR dateTime BETWEEN 1307455140 AND 1307456940
UNION ALL SELECT 'pocasi-loucka.eu_GW1000',dateTime,usUnits,`interval`,outTemp,outHumidity,rain,rainRate,windSpeed,windGust,barometer FROM `pocasi-loucka.eu_GW1000`.archive
WHERE dateTime BETWEEN 1307450940 AND 1307452740 OR dateTime BETWEEN 1307455140 AND 1307456940
UNION ALL SELECT 'loucka_reconstruction',dateTime,usUnits,`interval`,outTemp,outHumidity,rain,rainRate,windSpeed,windGust,barometer FROM loucka_reconstruction.archive
WHERE dateTime BETWEEN 1307450940 AND 1307452740 OR dateTime BETWEEN 1307455140 AND 1307456940
ORDER BY dateTime,archive;

-- READ-ONLY current audit history for exact off-grid timestamps and projected archive keys.
SELECT * FROM loucka_reconstruction.reconstruction_changes
WHERE target_time IN (1307451840,1307451900,1307456040,1307456100)
ORDER BY target_time,variable;
