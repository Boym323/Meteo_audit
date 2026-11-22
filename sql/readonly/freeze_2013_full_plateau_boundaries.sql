-- SELECT-only boundary check for the ten expanded 2013 T/RH runs.
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
)
SELECT t.episode_id,t.variable_name,t.expected_value,t.start_epoch,t.end_epoch,
       CASE WHEN t.variable_name='outTemp' THEN p.outTemp ELSE p.outHumidity END AS previous_value,
       p.`interval` AS previous_interval,
       CASE WHEN t.variable_name='outTemp' THEN s.outTemp ELSE s.outHumidity END AS first_value,
       s.`interval` AS first_interval,
       CASE WHEN t.variable_name='outTemp' THEN e.outTemp ELSE e.outHumidity END AS last_value,
       e.`interval` AS last_interval,
       CASE WHEN t.variable_name='outTemp' THEN n.outTemp ELSE n.outHumidity END AS next_value,
       n.`interval` AS next_interval
FROM target_runs t
LEFT JOIN loucka_reconstruction.archive p ON p.dateTime=t.start_epoch-300
LEFT JOIN loucka_reconstruction.archive s ON s.dateTime=t.start_epoch
LEFT JOIN loucka_reconstruction.archive e ON e.dateTime=t.end_epoch
LEFT JOIN loucka_reconstruction.archive n ON n.dateTime=t.end_epoch+300
ORDER BY t.episode_id,t.variable_name;
