-- SELECT-only incremental inventory for main production archive after the 21:15Z snapshot.
-- Wide triage limits and fields match the existing post-reconstruction screen.
SELECT COUNT(*) rows_n,MIN(dateTime) first_epoch,MAX(dateTime) last_epoch,
       MIN(`interval`) min_interval,MAX(`interval`) max_interval,
       MIN(usUnits) min_usUnits,MAX(usUnits) max_usUnits,
       COUNT(outTemp) outTemp_n,MIN(outTemp) outTemp_min,MAX(outTemp) outTemp_max,SUM(outTemp < -50 OR outTemp > 60) outTemp_outside,
       COUNT(outHumidity) RH_n,MIN(outHumidity) RH_min,MAX(outHumidity) RH_max,SUM(outHumidity < 0 OR outHumidity > 100) RH_outside,
       COUNT(rain) rain_n,MIN(rain) rain_min,MAX(rain) rain_max,SUM(rain<0) negative_rain,
       COUNT(rainRate) rainRate_n,MIN(rainRate) rainRate_min,MAX(rainRate) rainRate_max,SUM(rainRate<0) negative_rainRate,
       COUNT(windSpeed) windSpeed_n,MIN(windSpeed) windSpeed_min,MAX(windSpeed) windSpeed_max,SUM(windSpeed<0) negative_windSpeed,
       COUNT(windGust) windGust_n,MIN(windGust) windGust_min,MAX(windGust) windGust_max,SUM(windGust<0) negative_windGust,
       COUNT(windDir) windDir_n,MIN(windDir) windDir_min,MAX(windDir) windDir_max,SUM(windDir<0 OR windDir>=360) windDir_outside,
       COUNT(radiation) radiation_n,MIN(radiation) radiation_min,MAX(radiation) radiation_max,SUM(radiation<0) negative_radiation,
       COUNT(UV) UV_n,MIN(UV) UV_min,MAX(UV) UV_max,SUM(UV<0) negative_UV,
       COUNT(pm25_1) pm25_n,MIN(pm25_1) pm25_min,MAX(pm25_1) pm25_max,SUM(pm25_1>=999.8) pm25_sentinel,
       COUNT(pressure) pressure_n,MIN(pressure) pressure_min,MAX(pressure) pressure_max,
       COUNT(barometer) barometer_n,MIN(barometer) barometer_min,MAX(barometer) barometer_max
FROM `pocasi-loucka.eu`.`archive` WHERE dateTime>1794518100;

SELECT COUNT(*) AS adjacent_pairs,SUM(delta=300) AS delta_300s,
       SUM(delta<>300) AS delta_not_300s,MIN(delta) AS min_delta_s,MAX(delta) AS max_delta_s
FROM (SELECT dateTime-LAG(dateTime) OVER(ORDER BY dateTime) AS delta
      FROM `pocasi-loucka.eu`.`archive` WHERE dateTime>1794518100) q
WHERE delta IS NOT NULL;
