-- READ-ONLY per-field audit of the bounded 120-row June 2014 episode.
WITH x AS (
 SELECT a.dateTime,
        a.outTemp old_outTemp,b.outTemp wh_outTemp,
        a.outHumidity old_outHumidity,b.outHumidity wh_outHumidity,
        a.rain old_rain,b.rain wh_rain,a.rainRate old_rainRate,b.rainRate wh_rainRate,
        a.windSpeed old_windSpeed,b.windSpeed wh_windSpeed,
        a.windGust old_windGust,b.windGust wh_windGust,
        a.windDir old_windDir,b.windDir wh_windDir,
        a.barometer old_barometer,b.barometer wh_barometer,
        a.pressure old_pressure,b.pressure wh_pressure,
        a.altimeter old_altimeter,b.altimeter wh_altimeter,
        a.inTemp old_inTemp,b.inTemp wh_inTemp,
        a.inHumidity old_inHumidity,b.inHumidity wh_inHumidity
 FROM old_weewx.archive a
 JOIN weewx_WH1080.archive b ON b.dateTime=a.dateTime
 LEFT JOIN `pocasi-loucka.eu_old`.archive z ON z.dateTime=a.dateTime
 WHERE a.dateTime>=1402940340 AND a.dateTime<=1403011740
   AND z.dateTime IS NULL AND a.outTemp=0 AND b.outTemp=0
)
SELECT 'outTemp' variable,COUNT(old_outTemp) old_nonnull,COUNT(wh_outTemp) wh_nonnull,
       SUM(old_outTemp=wh_outTemp) equal_n,COUNT(DISTINCT old_outTemp) old_distinct,
       MIN(old_outTemp) old_min,MAX(old_outTemp) old_max FROM x
UNION ALL SELECT 'outHumidity',COUNT(old_outHumidity),COUNT(wh_outHumidity),SUM(old_outHumidity=wh_outHumidity),COUNT(DISTINCT old_outHumidity),MIN(old_outHumidity),MAX(old_outHumidity) FROM x
UNION ALL SELECT 'rain',COUNT(old_rain),COUNT(wh_rain),SUM(old_rain=wh_rain),COUNT(DISTINCT old_rain),MIN(old_rain),MAX(old_rain) FROM x
UNION ALL SELECT 'rainRate',COUNT(old_rainRate),COUNT(wh_rainRate),SUM(old_rainRate=wh_rainRate),COUNT(DISTINCT old_rainRate),MIN(old_rainRate),MAX(old_rainRate) FROM x
UNION ALL SELECT 'windSpeed',COUNT(old_windSpeed),COUNT(wh_windSpeed),SUM(old_windSpeed=wh_windSpeed),COUNT(DISTINCT old_windSpeed),MIN(old_windSpeed),MAX(old_windSpeed) FROM x
UNION ALL SELECT 'windGust',COUNT(old_windGust),COUNT(wh_windGust),SUM(old_windGust=wh_windGust),COUNT(DISTINCT old_windGust),MIN(old_windGust),MAX(old_windGust) FROM x
UNION ALL SELECT 'windDir',COUNT(old_windDir),COUNT(wh_windDir),SUM(old_windDir=wh_windDir),COUNT(DISTINCT old_windDir),MIN(old_windDir),MAX(old_windDir) FROM x
UNION ALL SELECT 'barometer',COUNT(old_barometer),COUNT(wh_barometer),SUM(old_barometer=wh_barometer),COUNT(DISTINCT old_barometer),MIN(old_barometer),MAX(old_barometer) FROM x
UNION ALL SELECT 'pressure',COUNT(old_pressure),COUNT(wh_pressure),SUM(old_pressure=wh_pressure),COUNT(DISTINCT old_pressure),MIN(old_pressure),MAX(old_pressure) FROM x
UNION ALL SELECT 'altimeter',COUNT(old_altimeter),COUNT(wh_altimeter),SUM(old_altimeter=wh_altimeter),COUNT(DISTINCT old_altimeter),MIN(old_altimeter),MAX(old_altimeter) FROM x
UNION ALL SELECT 'inTemp',COUNT(old_inTemp),COUNT(wh_inTemp),SUM(old_inTemp=wh_inTemp),COUNT(DISTINCT old_inTemp),MIN(old_inTemp),MAX(old_inTemp) FROM x
UNION ALL SELECT 'inHumidity',COUNT(old_inHumidity),COUNT(wh_inHumidity),SUM(old_inHumidity=wh_inHumidity),COUNT(DISTINCT old_inHumidity),MIN(old_inHumidity),MAX(old_inHumidity) FROM x;
