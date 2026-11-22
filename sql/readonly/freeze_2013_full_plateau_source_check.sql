-- SELECT-only source-copy check over full expanded T/RH plateau bounds.
-- Values are compared at exact epochs; archive copies are not presumed independent.
WITH target_runs AS (
    SELECT 1 AS episode_id,'outTemp' AS variable_name,-4.5 AS expected_value,1359055200 AS start_epoch,1359141900 AS end_epoch UNION ALL
    SELECT 1,'outHumidity',89,1359055200,1359141900 UNION ALL
    SELECT 2,'outTemp',2,1360927200,1360983000 UNION ALL
    SELECT 2,'outHumidity',96,1360927200,1360991400 UNION ALL
    SELECT 3,'outTemp',1.2,1362171600,1362247200 UNION ALL
    SELECT 3,'outHumidity',94,1362171600,1362247200 UNION ALL
    SELECT 4,'outTemp',-4.6,1364329500,1364392200 UNION ALL
    SELECT 4,'outHumidity',80,1364329500,1364391300 UNION ALL
    SELECT 5,'outTemp',-0.7,1364982900,1365069300 UNION ALL
    SELECT 5,'outHumidity',87,1364982900,1365069300
), joined AS (
    SELECT t.*,
           a.dateTime AS recon_time, a.outTemp AS recon_temp, a.outHumidity AS recon_rh,
           o.dateTime AS old_time, o.outTemp AS old_temp, o.outHumidity AS old_rh,
           w.dateTime AS wh_time, w.outTemp AS wh_temp, w.outHumidity AS wh_rh
    FROM target_runs t
    LEFT JOIN loucka_reconstruction.archive a
      ON a.dateTime BETWEEN t.start_epoch AND t.end_epoch
    LEFT JOIN old_weewx.archive o ON o.dateTime=a.dateTime
    LEFT JOIN weewx_WH1080.archive w ON w.dateTime=a.dateTime
)
SELECT episode_id,variable_name,expected_value,start_epoch,end_epoch,
       COUNT(recon_time) AS recon_rows,
       MIN(CASE WHEN variable_name='outTemp' THEN recon_temp ELSE recon_rh END) AS recon_min,
       MAX(CASE WHEN variable_name='outTemp' THEN recon_temp ELSE recon_rh END) AS recon_max,
       COUNT(old_time) AS old_rows,
       MIN(CASE WHEN variable_name='outTemp' THEN old_temp ELSE old_rh END) AS old_min,
       MAX(CASE WHEN variable_name='outTemp' THEN old_temp ELSE old_rh END) AS old_max,
       COUNT(wh_time) AS wh_rows,
       MIN(CASE WHEN variable_name='outTemp' THEN wh_temp ELSE wh_rh END) AS wh_min,
       MAX(CASE WHEN variable_name='outTemp' THEN wh_temp ELSE wh_rh END) AS wh_max
FROM joined
GROUP BY episode_id,variable_name,expected_value,start_epoch,end_epoch
ORDER BY episode_id,variable_name;
