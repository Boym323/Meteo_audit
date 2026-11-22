-- Bounded target evidence for exact source/target outTemp rows in 2017 where
-- a separate LuhaMet exact-time RH observation differs by >35 percentage
-- points. READ-ONLY SELECT only; no Q1 2018 or 2021 data are included.
SELECT o.dateTime,
 o.outHumidity source_rh, ref.relative_humidity_pct luhamet_rh,
 ref.temperature_c luhamet_temp, o.outTemp source_temp, r.outTemp target_temp,
 rp.outHumidity prev_rh, rn.outHumidity next_rh,
 rp.outTemp prev_temp, rn.outTemp next_temp,
 o.rain source_rain, w.rain wh_rain, o.rainRate source_rainRate,
 w.rainRate wh_rainRate, o.windSpeed source_wind, w.windSpeed wh_wind,
 ABS(ref.relative_humidity_pct-o.outHumidity) rh_difference_pp,
 (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c
  WHERE c.target_time=o.dateTime) all_events,
 (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c
  WHERE c.target_time=o.dateTime AND c.variable='outHumidity') rh_events,
 EXISTS(SELECT 1 FROM `pocasi-loucka.eu_old`.archive x WHERE x.dateTime=o.dateTime) euold_row,
 EXISTS(SELECT 1 FROM `pocasi-loucka.eu`.archive x WHERE x.dateTime=o.dateTime) eu_row,
 EXISTS(SELECT 1 FROM `pocasi-loucka.eu_GW1000`.archive x WHERE x.dateTime=o.dateTime) gw_row,
 EXISTS(SELECT 1 FROM old_weewx.archive x WHERE x.dateTime=o.dateTime) old_row,
 EXISTS(SELECT 1 FROM weewx_WH1080.archive x WHERE x.dateTime=o.dateTime) wh_row
FROM old_weewx.archive o
JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
 AND w.outHumidity=o.outHumidity AND w.outTemp=o.outTemp
JOIN loucka_reconstruction.archive r ON r.dateTime=o.dateTime
 AND r.outHumidity IS NULL AND r.outTemp=o.outTemp
JOIN loucka_reconstruction.archive rp ON rp.dateTime=o.dateTime-300
 AND rp.outHumidity IS NOT NULL
JOIN loucka_reconstruction.archive rn ON rn.dateTime=o.dateTime+300
 AND rn.outHumidity IS NOT NULL
JOIN loucka_reconstruction.reference_observations ref
 ON ref.station_id='luhamet_sehradice' AND ref.observed_at_utc=o.dateTime
WHERE o.dateTime>=1483228800 AND o.dateTime<1514764800
 AND o.outHumidity IS NOT NULL
 AND o.usUnits=17 AND w.usUnits=17 AND o.interval=5 AND w.interval=5
 AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c
                WHERE c.target_time=o.dateTime AND c.variable='outHumidity')
 AND ABS(ref.relative_humidity_pct-o.outHumidity)>35
ORDER BY o.dateTime;
