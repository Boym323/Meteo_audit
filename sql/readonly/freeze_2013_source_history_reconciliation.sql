-- SELECT-only exact-time reconciliation of five previously documented 2013
-- 12-hour T/RH plateau episodes. Source copies are not presumed independent.
WITH episodes AS (
    SELECT 1 AS episode_id, '2013-01-25T00:00Z' AS label, 1359072000 AS start_epoch, 1359114900 AS end_epoch UNION ALL
    SELECT 2, '2013-02-15T12:00Z', 1360929600, 1360972500 UNION ALL
    SELECT 3, '2013-03-02T00:00Z', 1362182400, 1362225300 UNION ALL
    SELECT 4, '2013-03-27T00:00Z', 1364342400, 1364385300 UNION ALL
    SELECT 5, '2013-04-03T12:00Z', 1364990400, 1365033300
), joined AS (
    SELECT e.episode_id, e.label, e.start_epoch, e.end_epoch,
           a.dateTime, a.`interval` AS recon_interval, a.usUnits AS recon_units,
           a.outTemp AS recon_temp, a.outHumidity AS recon_rh,
           o.dateTime AS old_time, o.outTemp AS old_temp, o.outHumidity AS old_rh,
           o.`interval` AS old_interval, o.usUnits AS old_units,
           w.dateTime AS wh_time, w.outTemp AS wh_temp, w.outHumidity AS wh_rh,
           w.`interval` AS wh_interval, w.usUnits AS wh_units
    FROM episodes AS e
    LEFT JOIN loucka_reconstruction.archive AS a
      ON a.dateTime BETWEEN e.start_epoch AND e.end_epoch
    LEFT JOIN old_weewx.archive AS o ON o.dateTime = a.dateTime
    LEFT JOIN weewx_WH1080.archive AS w ON w.dateTime = a.dateTime
)
SELECT j.episode_id, j.label, j.start_epoch, j.end_epoch,
       COUNT(j.dateTime) AS recon_rows,
       MIN(j.recon_temp) AS recon_temp_min, MAX(j.recon_temp) AS recon_temp_max,
       COUNT(DISTINCT j.recon_temp) AS recon_temp_distinct,
       MIN(j.recon_rh) AS recon_rh_min, MAX(j.recon_rh) AS recon_rh_max,
       COUNT(DISTINCT j.recon_rh) AS recon_rh_distinct,
       MIN(j.recon_interval) AS recon_interval_min, MAX(j.recon_interval) AS recon_interval_max,
       MIN(j.recon_units) AS recon_units_min, MAX(j.recon_units) AS recon_units_max,
       COUNT(j.old_time) AS old_rows,
       MIN(j.old_temp) AS old_temp_min, MAX(j.old_temp) AS old_temp_max,
       COUNT(DISTINCT j.old_temp) AS old_temp_distinct,
       MIN(j.old_rh) AS old_rh_min, MAX(j.old_rh) AS old_rh_max,
       COUNT(DISTINCT j.old_rh) AS old_rh_distinct,
       MIN(j.old_interval) AS old_interval_min, MAX(j.old_interval) AS old_interval_max,
       MIN(j.old_units) AS old_units_min, MAX(j.old_units) AS old_units_max,
       COUNT(j.wh_time) AS wh_rows,
       MIN(j.wh_temp) AS wh_temp_min, MAX(j.wh_temp) AS wh_temp_max,
       COUNT(DISTINCT j.wh_temp) AS wh_temp_distinct,
       MIN(j.wh_rh) AS wh_rh_min, MAX(j.wh_rh) AS wh_rh_max,
       COUNT(DISTINCT j.wh_rh) AS wh_rh_distinct,
       MIN(j.wh_interval) AS wh_interval_min, MAX(j.wh_interval) AS wh_interval_max,
       MIN(j.wh_units) AS wh_units_min, MAX(j.wh_units) AS wh_units_max,
       (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c
        WHERE c.target_time BETWEEN j.start_epoch AND j.end_epoch
          AND c.variable='outTemp') AS outtemp_history_events,
       (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c
        WHERE c.target_time BETWEEN j.start_epoch AND j.end_epoch
          AND c.variable='outHumidity') AS rh_history_events
FROM joined j
GROUP BY j.episode_id,j.label,j.start_epoch,j.end_epoch
ORDER BY j.episode_id;
