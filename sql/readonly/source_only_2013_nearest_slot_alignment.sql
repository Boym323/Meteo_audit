-- READ-ONLY diagnostic alignment of all 2013 shared old/WH1080 source-only rows.
-- Nearest 300-second projection is descriptive only; it does not authorize a shift.
WITH aligned AS (
  SELECT o.dateTime AS source_time,
         CASE WHEN MOD(o.dateTime,300)<=150
              THEN o.dateTime-MOD(o.dateTime,300)
              ELSE o.dateTime+(300-MOD(o.dateTime,300)) END AS projected_time,
         CASE WHEN MOD(o.dateTime,300)<150 THEN MOD(o.dateTime,300)
              WHEN MOD(o.dateTime,300)>150 THEN MOD(o.dateTime,300)-300
              ELSE 0 END AS signed_offset_seconds,
         o.usUnits AS old_units,w.usUnits AS wh_units,
         o.`interval` AS old_interval,w.`interval` AS wh_interval,r.usUnits AS target_units,
         o.outTemp AS old_temp,w.outTemp AS wh_temp,o.outHumidity AS old_rh,w.outHumidity AS wh_rh,
         o.rain AS old_rain,w.rain AS wh_rain,o.rainRate AS old_rate,w.rainRate AS wh_rate,
         o.windSpeed AS old_wind,w.windSpeed AS wh_wind,
         r.dateTime AS reconstruction_time,r.outTemp AS target_temp,r.outHumidity AS target_rh,
         r.rain AS target_rain,r.rainRate AS target_rate,r.windSpeed AS target_wind,
         e.dateTime AS eu_time,g.dateTime AS gw_time,eo.dateTime AS eu_old_time
  FROM old_weewx.archive o
  JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
  LEFT JOIN loucka_reconstruction.archive exact_r ON exact_r.dateTime=o.dateTime
  LEFT JOIN loucka_reconstruction.archive r
    ON r.dateTime=CASE WHEN MOD(o.dateTime,300)<=150
                       THEN o.dateTime-MOD(o.dateTime,300)
                       ELSE o.dateTime+(300-MOD(o.dateTime,300)) END
  LEFT JOIN `pocasi-loucka.eu`.archive e ON e.dateTime=CASE WHEN MOD(o.dateTime,300)<=150 THEN o.dateTime-MOD(o.dateTime,300) ELSE o.dateTime+(300-MOD(o.dateTime,300)) END
  LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=CASE WHEN MOD(o.dateTime,300)<=150 THEN o.dateTime-MOD(o.dateTime,300) ELSE o.dateTime+(300-MOD(o.dateTime,300)) END
  LEFT JOIN `pocasi-loucka.eu_old`.archive eo ON eo.dateTime=CASE WHEN MOD(o.dateTime,300)<=150 THEN o.dateTime-MOD(o.dateTime,300) ELSE o.dateTime+(300-MOD(o.dateTime,300)) END
  WHERE o.dateTime>=1356998400 AND o.dateTime<1388534400
    AND exact_r.dateTime IS NULL
)
SELECT COUNT(*) AS source_rows,COUNT(DISTINCT projected_time) AS projected_slots,
       SUM(source_time%300<>0) AS offgrid_rows,
       SUM(reconstruction_time IS NOT NULL) AS projected_reconstruction_rows,
       SUM(eu_time IS NOT NULL) AS projected_eu_rows,
       SUM(gw_time IS NOT NULL) AS projected_gw_rows,
       SUM(eu_old_time IS NOT NULL) AS projected_eu_old_rows,
       SUM(reconstruction_time IS NULL) AS projected_reconstruction_absent,
       SUM(old_units=17 AND wh_units=17 AND old_interval=5 AND wh_interval=5) AS source_unit_interval_rows,
       SUM(target_units=16) AS metric_target_rows
FROM aligned;

WITH aligned AS (
  SELECT o.dateTime AS source_time,
         CASE WHEN MOD(o.dateTime,300)<=150 THEN o.dateTime-MOD(o.dateTime,300)
              ELSE o.dateTime+(300-MOD(o.dateTime,300)) END AS projected_time,
         CASE WHEN MOD(o.dateTime,300)<150 THEN MOD(o.dateTime,300)
              WHEN MOD(o.dateTime,300)>150 THEN MOD(o.dateTime,300)-300
              ELSE 0 END AS signed_offset_seconds,
         o.outTemp old_temp,w.outTemp wh_temp,o.outHumidity old_rh,w.outHumidity wh_rh,
         o.rain old_rain,w.rain wh_rain,o.rainRate old_rate,w.rainRate wh_rate,
         o.windSpeed old_wind,w.windSpeed wh_wind,r.dateTime target_time,
         r.outTemp target_temp,r.outHumidity target_rh,r.rain target_rain,
         r.rainRate target_rate,r.windSpeed target_wind
  FROM old_weewx.archive o
  JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
  LEFT JOIN loucka_reconstruction.archive exact_r ON exact_r.dateTime=o.dateTime
  LEFT JOIN loucka_reconstruction.archive r
    ON r.dateTime=CASE WHEN MOD(o.dateTime,300)<=150
                       THEN o.dateTime-MOD(o.dateTime,300)
                       ELSE o.dateTime+(300-MOD(o.dateTime,300)) END
  WHERE o.dateTime>=1356998400 AND o.dateTime<1388534400
    AND exact_r.dateTime IS NULL
)
SELECT signed_offset_seconds,COUNT(*) AS source_rows,
       COUNT(DISTINCT projected_time) AS projected_slots,
       SUM(target_time IS NOT NULL) AS target_rows,
       SUM(old_temp<=>wh_temp) AS source_temp_copy_equal,
       SUM(old_rh<=>wh_rh) AS source_rh_copy_equal,
       SUM(old_rain<=>wh_rain) AS source_rain_copy_equal,
       SUM(old_rate<=>wh_rate) AS source_rate_copy_equal,
       SUM(old_wind<=>wh_wind) AS source_wind_copy_equal,
       SUM(target_temp<=>old_temp) AS target_temp_direct_equal,
       SUM(target_rh<=>old_rh) AS target_rh_direct_equal,
       SUM(ABS(target_rain-old_rain/10)<0.000001) AS target_rain_metric_equal,
       SUM(ABS(target_rate-old_rate/10)<0.000001) AS target_rate_metric_equal,
       SUM(ABS(target_wind-old_wind*3.6)<0.000001) AS target_wind_metric_equal
FROM aligned
GROUP BY signed_offset_seconds ORDER BY signed_offset_seconds;
