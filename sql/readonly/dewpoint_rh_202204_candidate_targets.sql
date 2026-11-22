-- Issue #15: strictly read-only, per-target diagnostic export (UTC April 2022).
-- Does NOT assert the historical WeeWX dewpoint algorithm or propose new values.
-- No UPDATE, INSERT, DDL, or automatic reconstruction; keep result files private.
-- DateTime is the UTC end of the WeeWX archive interval; sensor units=16.
WITH latest_rh AS (
  SELECT c.target_time,c.old_value,c.new_value,c.batch_key,c.id,c.created_at,
         ROW_NUMBER() OVER (
           PARTITION BY c.target_time ORDER BY c.created_at DESC,c.id DESC
         ) AS rn
  FROM `loucka_reconstruction`.`reconstruction_changes` c
  WHERE c.variable='outHumidity' AND c.state='applied'
    AND c.target_time>=1648771200 AND c.target_time<1651363200
), basis AS (
  SELECT a.dateTime AS target_time_utc, a.outTemp AS temp_c,
         a.outHumidity AS current_rh_pct, a.dewpoint AS stored_dewpoint_c,
         l.old_value AS old_rh_pct, l.new_value AS approved_rh_pct,
         l.batch_key AS rh_batch_key, l.id AS rh_history_event_id,
         a.heatindex AS stored_heatindex_c,
         a.appTemp AS stored_apptemp_c, a.humidex AS stored_humidex_c,
         LN(a.outHumidity/100)+17.625*a.outTemp/(243.04+a.outTemp) AS gamma_current,
         LN(l.old_value/100)+17.625*a.outTemp/(243.04+a.outTemp) AS gamma_old
  FROM latest_rh l
  JOIN `loucka_reconstruction`.`archive` a ON a.dateTime=l.target_time
  WHERE l.rn=1 AND a.usUnits=16 AND a.outTemp IS NOT NULL
    AND a.outHumidity BETWEEN 1 AND 100 AND l.old_value BETWEEN 1 AND 100
    AND a.dewpoint IS NOT NULL
), diagnostics AS (
  SELECT b.*,
         243.04*gamma_current/(17.625-gamma_current) AS current_rh_magnus_screen_c,
         243.04*gamma_old/(17.625-gamma_old) AS old_rh_magnus_screen_c
  FROM basis b
)
SELECT d.target_time_utc, 'dewpoint' AS variable,
       d.stored_dewpoint_c AS original_value,
       NULL AS proposed_value,
       d.temp_c,d.old_rh_pct,d.current_rh_pct,d.approved_rh_pct,
       d.current_rh_magnus_screen_c,d.old_rh_magnus_screen_c,
       ABS(d.stored_dewpoint_c-d.current_rh_magnus_screen_c) AS current_rh_abs_delta_c,
       ABS(d.stored_dewpoint_c-d.old_rh_magnus_screen_c) AS old_rh_abs_delta_c,
       (d.current_rh_pct <=> d.approved_rh_pct) AS rh_matches_applied,
       (ABS(d.stored_dewpoint_c-d.old_rh_magnus_screen_c)<=0.1) AS stored_matches_old_screen,
       d.stored_heatindex_c,d.stored_apptemp_c,d.stored_humidex_c,
       d.rh_batch_key,d.rh_history_event_id,
       (SELECT COUNT(*) FROM `loucka_reconstruction`.`reconstruction_changes` h
          WHERE h.target_time=d.target_time_utc AND h.variable='dewpoint'
       ) AS existing_dewpoint_history,
       'MAGNUS_17_625_243_04_DIAGNOSTIC_ONLY' AS screening_formula,
       'UNRESOLVED_HISTORICAL_WEEWX_FORMULA' AS qc_state
FROM diagnostics d
WHERE ABS(d.stored_dewpoint_c-d.current_rh_magnus_screen_c)>2
ORDER BY d.target_time_utc;
