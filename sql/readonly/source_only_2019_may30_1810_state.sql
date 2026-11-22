-- READ-ONLY bounded source/target state for 2019-05-30 18:10 UTC (1559239800).
SELECT 'loucka_reconstruction' AS db, dateTime, usUnits, `interval`, outTemp, outHumidity, rain, rainRate, windSpeed
FROM loucka_reconstruction.archive WHERE dateTime BETWEEN 1559239200 AND 1559240400
UNION ALL SELECT 'old_weewx', dateTime, usUnits, `interval`, outTemp, outHumidity, rain, rainRate, windSpeed
FROM old_weewx.archive WHERE dateTime BETWEEN 1559239200 AND 1559240400
UNION ALL SELECT 'weewx_WH1080', dateTime, usUnits, `interval`, outTemp, outHumidity, rain, rainRate, windSpeed
FROM weewx_WH1080.archive WHERE dateTime BETWEEN 1559239200 AND 1559240400
UNION ALL SELECT 'pocasi-loucka.eu_old', dateTime, usUnits, `interval`, outTemp, outHumidity, rain, rainRate, windSpeed
FROM `pocasi-loucka.eu_old`.archive WHERE dateTime BETWEEN 1559239200 AND 1559240400
UNION ALL SELECT 'pocasi-loucka.eu', dateTime, usUnits, `interval`, outTemp, outHumidity, rain, rainRate, windSpeed
FROM `pocasi-loucka.eu`.archive WHERE dateTime BETWEEN 1559239200 AND 1559240400
UNION ALL SELECT 'pocasi-loucka.eu_GW1000', dateTime, usUnits, `interval`, outTemp, outHumidity, rain, rainRate, windSpeed
FROM `pocasi-loucka.eu_GW1000`.archive WHERE dateTime BETWEEN 1559239200 AND 1559240400
ORDER BY dateTime, db;

-- Exact target history; expected no rows.
SELECT variable, state, COUNT(*) AS events
FROM loucka_reconstruction.reconstruction_changes
WHERE target_time = 1559239800
GROUP BY variable, state ORDER BY variable, state;
