-- READ-ONLY: 2010 source-only off-grid cohort, signed nearest 300s offset,
-- same-time copy equality, and fieldwise comparison to the existing nearest target.
-- METRICWX -> METRIC conversions shown only as diagnostic hypotheses.
WITH cohort AS (
 SELECT s.dateTime,s.outTemp,s.outHumidity,s.rain,s.rainRate,s.windSpeed,
        o.outTemp oT,o.outHumidity oRH,o.rain oRain,o.rainRate oRate,o.windSpeed oWind
 FROM weewx_WH1080.archive s JOIN old_weewx.archive o ON o.dateTime=s.dateTime
 LEFT JOIN loucka_reconstruction.archive exactrow ON exactrow.dateTime=s.dateTime
 WHERE s.dateTime>=1262304000 AND s.dateTime<1293840000
  AND s.`interval`=5 AND o.`interval`=5 AND s.usUnits=17 AND o.usUnits=17
  AND MOD(s.dateTime,300)<>0 AND exactrow.dateTime IS NULL
), mapped AS (
 SELECT c.*,FLOOR((c.dateTime+150)/300)*300 nearest_dt,
        t.dateTime target_time,t.outTemp target_temp,t.outHumidity target_rh,
        t.rain target_rain,t.rainRate target_rate,t.windSpeed target_wind,
        c.dateTime-FLOOR((c.dateTime+150)/300)*300 signed_offset
 FROM cohort c LEFT JOIN loucka_reconstruction.archive t
  ON t.dateTime=FLOOR((c.dateTime+150)/300)*300
)
SELECT signed_offset,COUNT(*) n,
 SUM(target_time IS NOT NULL) nearest_target_rows,
 SUM(target_time IS NOT NULL AND outTemp=target_temp) temp_exact_match,
 SUM(target_time IS NOT NULL AND outHumidity=target_rh) rh_exact_match,
 SUM(target_time IS NOT NULL AND ABS(rain*0.1-target_rain)<0.000001) rain_converted_match,
 SUM(target_time IS NOT NULL AND ABS(rainRate*0.1-target_rate)<0.000001) rainRate_converted_match,
 SUM(target_time IS NOT NULL AND ABS(windSpeed*3.6-target_wind)<0.000001) wind_converted_match,
 SUM(target_time IS NOT NULL AND outTemp=target_temp AND outHumidity=target_rh
     AND ABS(rain*0.1-target_rain)<0.000001 AND ABS(rainRate*0.1-target_rate)<0.000001
     AND ABS(windSpeed*3.6-target_wind)<0.000001) all5_converted_value_matches,
 SUM(oT=outTemp AND oRH=outHumidity AND oRain=rain AND oRate=rainRate AND oWind=windSpeed) source_copy_all5_equal
FROM mapped GROUP BY signed_offset ORDER BY signed_offset;

-- Mapping collisions: count distinct nearest grid slots, source rows per slot,
-- whether the target row is already present. This is not an approved time shift.
WITH source_rows AS (
 SELECT s.dateTime,FLOOR((s.dateTime+150)/300)*300 nearest_dt
 FROM weewx_WH1080.archive s
 LEFT JOIN loucka_reconstruction.archive exactrow ON exactrow.dateTime=s.dateTime
 WHERE s.dateTime>=1262304000 AND s.dateTime<1293840000
  AND s.`interval`=5 AND s.usUnits=17 AND MOD(s.dateTime,300)<>0
  AND exactrow.dateTime IS NULL
), mapped AS (
 SELECT nearest_dt,COUNT(*) source_n FROM source_rows GROUP BY nearest_dt
)
SELECT COUNT(*) AS nearest_slots, SUM(source_n) AS source_rows,
       SUM(source_n>1) AS collision_slots, MAX(source_n) AS max_sources_per_slot,
       SUM(t.dateTime IS NOT NULL) AS nearest_slots_with_existing_target_row,
       SUM(t.dateTime IS NULL) AS nearest_slots_without_target_row
FROM mapped m LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=m.nearest_dt;


-- Variable completeness at the nearest existing target rows (not restoration approval).
SELECT COUNT(*) AS source_rows,SUM(t.dateTime IS NOT NULL) AS nearest_target_rows,
 SUM(t.outTemp IS NULL) AS target_outTemp_null,
 SUM(t.outHumidity IS NULL) AS target_outHumidity_null,
 SUM(t.rain IS NULL) AS target_rain_null,
 SUM(t.rainRate IS NULL) AS target_rainRate_null,
 SUM(t.windSpeed IS NULL) AS target_windSpeed_null
FROM weewx_WH1080.archive s
LEFT JOIN loucka_reconstruction.archive exactrow ON exactrow.dateTime=s.dateTime
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=FLOOR((s.dateTime+150)/300)*300
WHERE s.dateTime>=1262304000 AND s.dateTime<1293840000 AND s.`interval`=5 AND s.usUnits=17
 AND MOD(s.dateTime,300)<>0 AND exactrow.dateTime IS NULL;
