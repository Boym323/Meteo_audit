-- SELECT-only four-point boundary sample around the five 2013 frozen windows.
WITH episodes AS (
    SELECT 1 AS episode_id,1359072000 AS start_epoch,1359114900 AS end_epoch UNION ALL
    SELECT 2,1360929600,1360972500 UNION ALL
    SELECT 3,1362182400,1362225300 UNION ALL
    SELECT 4,1364342400,1364385300 UNION ALL
    SELECT 5,1364990400,1365033300
), sample_times AS (
    SELECT episode_id, start_epoch-300 AS sample_epoch, 'before' AS position FROM episodes UNION ALL
    SELECT episode_id, start_epoch AS sample_epoch, 'start' FROM episodes UNION ALL
    SELECT episode_id, end_epoch AS sample_epoch, 'end' FROM episodes UNION ALL
    SELECT episode_id, end_epoch+300 AS sample_epoch, 'after' FROM episodes
)
SELECT s.episode_id, s.position, s.sample_epoch,
       a.outTemp AS recon_temp, a.outHumidity AS recon_rh,
       o.outTemp AS old_temp, o.outHumidity AS old_rh,
       w.outTemp AS wh_temp, w.outHumidity AS wh_rh
FROM sample_times s
LEFT JOIN loucka_reconstruction.archive a ON a.dateTime=s.sample_epoch
LEFT JOIN old_weewx.archive o ON o.dateTime=s.sample_epoch
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=s.sample_epoch
ORDER BY s.episode_id, FIELD(s.position,'before','start','end','after');
