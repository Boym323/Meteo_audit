-- READ-ONLY residual exact-bracket RH candidates after excluding prior row-level reviews.
-- Q1 2018 is excluded. This query is a source/availability review, not a correction generator.
WITH p AS (
 SELECT o.dateTime,o.outHumidity source_rh,w.outHumidity wh_rh,o.outTemp old_temp,w.outTemp wh_temp,
        o.usUnits old_units,w.usUnits wh_units,o.`interval` old_interval,w.`interval` wh_interval,
        r.outHumidity target_rh,r.outTemp target_temp,r.usUnits target_units,r.`interval` target_interval,
        rp.outHumidity prev_rh,rn.outHumidity next_rh,rp.outTemp prev_temp,rn.outTemp next_temp,
        e.dateTime eu_row,e.outHumidity eu_rh,g.dateTime gw_row,g.outHumidity gw_rh,
        eo.dateTime euold_row,eo.outHumidity euold_rh,l.relative_humidity_pct luhamet_rh,l.temperature_c luhamet_temp,
        CASE WHEN o.dateTime<1483228800 THEN 2016 WHEN o.dateTime<1514764800 THEN 2017 WHEN o.dateTime<1546300800 THEN 2018 ELSE 2019 END utc_year
 FROM old_weewx.archive o JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
 JOIN loucka_reconstruction.archive r ON r.dateTime=o.dateTime
 JOIN loucka_reconstruction.archive rp ON rp.dateTime=o.dateTime-300
 JOIN loucka_reconstruction.archive rn ON rn.dateTime=o.dateTime+300
 LEFT JOIN `pocasi-loucka.eu_old`.archive eo ON eo.dateTime=o.dateTime
 LEFT JOIN `pocasi-loucka.eu`.archive e ON e.dateTime=o.dateTime
 LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=o.dateTime
 LEFT JOIN loucka_reconstruction.reference_observations l ON l.station_id='luhamet_sehradice' AND l.observed_at_utc=o.dateTime
 WHERE o.dateTime>=1451606400 AND o.dateTime<1577836800
   AND NOT (o.dateTime>=1514764800 AND o.dateTime<1522540800)
   AND o.outHumidity IS NOT NULL AND w.outHumidity IS NOT NULL AND o.outHumidity=w.outHumidity AND r.outHumidity IS NULL
   AND rp.outHumidity IS NOT NULL AND rn.outHumidity IS NOT NULL
   AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=o.dateTime AND c.variable='outHumidity')
   AND o.dateTime NOT IN (1458239400,1474061400,1484989500,1487911800,1489737000,1490743800,1490746500,1490754900,1491762900,1492381500,1494477900,1496823600,1500240900,1504517100,1505497500,1505498700,1506765600,1509272700,1509367200,1509449700,1511014500,1512155700,1512163800,1512164400,1512227100,1512234000,1524948000,1529639100,1530398700,1535359800,1538482200,1544274600,1544714100,1546297200,1547200200,1547744700,1548606300,1548866100,1549596600,1553517000)
)
SELECT dateTime target_time,utc_year,source_rh,wh_rh,old_temp,wh_temp,target_rh,target_temp,prev_rh,next_rh,prev_temp,next_temp,
       old_units,wh_units,target_units,old_interval,wh_interval,target_interval,eu_row,eu_rh,gw_row,gw_rh,euold_row,euold_rh,
       luhamet_rh,luhamet_temp,(source_rh BETWEEN LEAST(prev_rh,next_rh) AND GREATEST(prev_rh,next_rh)) within_range,
       ABS(source_rh-(prev_rh+next_rh)/2) midpoint_delta,
       IF(luhamet_rh IS NULL,NULL,ABS(source_rh-luhamet_rh)) luhamet_delta_pp
FROM p ORDER BY utc_year,target_time;
