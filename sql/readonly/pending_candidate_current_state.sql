-- Read-only candidate reconciliation. Run the first two SELECT templates once
-- per (variable, archive column) listed below. Never stage/apply/cancel here.
-- Variables: barometer, outHumidity, outTemp, pm25_1, radiation, rain,
-- rainRate, soilTemp1, windSpeed. Replace {{VARIABLE}} and {{ARCHIVE_COLUMN}}.

-- A: Candidate target to current archive, source and proposal.
WITH p AS (
 SELECT c.*,b.created_at AS batch_created
 FROM loucka_reconstruction.reconstruction_candidates c
 JOIN loucka_reconstruction.reconstruction_batches b ON b.batch_id=c.batch_id
 WHERE b.state='pending' AND c.variable='{{VARIABLE}}'
)
SELECT '{{VARIABLE}}' AS variable,COUNT(*) AS candidates,
       SUM(a.dateTime IS NULL) AS missing_archive,
       SUM(a.dateTime IS NOT NULL AND a.`{{ARCHIVE_COLUMN}}` <=> p.proposed_value) AS current_matches_proposal,
       SUM(a.dateTime IS NOT NULL AND a.`{{ARCHIVE_COLUMN}}` <=> p.source_value) AS current_matches_source,
       SUM(a.dateTime IS NOT NULL AND EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes h
           WHERE h.target_time=p.target_time AND h.variable='{{VARIABLE}}')
           AND a.`{{ARCHIVE_COLUMN}}` <=> (SELECT CASE h.state WHEN 'applied' THEN h.new_value
             WHEN 'reverted' THEN h.old_value ELSE NULL END
             FROM loucka_reconstruction.reconstruction_changes h
             WHERE h.target_time=p.target_time AND h.variable='{{VARIABLE}}'
             ORDER BY h.created_at DESC,h.id DESC LIMIT 1)) AS current_matches_latest_history_expected
FROM p LEFT JOIN loucka_reconstruction.archive a ON a.dateTime=p.target_time;

-- B: History chronology relative to each candidate's own batch creation.
WITH p AS (
 SELECT c.target_time,b.created_at AS batch_created
 FROM loucka_reconstruction.reconstruction_candidates c
 JOIN loucka_reconstruction.reconstruction_batches b ON b.batch_id=c.batch_id
 WHERE b.state='pending' AND c.variable='{{VARIABLE}}'
)
SELECT '{{VARIABLE}}' AS variable,COUNT(*) AS candidates,
       SUM(EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes h
                  WHERE h.target_time=p.target_time AND h.variable='{{VARIABLE}}')) AS has_any_history,
       SUM(EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes h
                  WHERE h.target_time=p.target_time AND h.variable='{{VARIABLE}}'
                    AND h.state='applied' AND h.created_at>p.batch_created)) AS later_applied_targets,
       SUM((SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes h
            WHERE h.target_time=p.target_time AND h.variable='{{VARIABLE}}'
              AND h.state='applied' AND h.created_at>p.batch_created)) AS later_applied_events,
FROM p;

-- C: The two targets whose current reconstruction archive row is absent.
SELECT c.batch_id,c.ordinal,c.source_database,c.source_time,c.target_time,
       c.variable,c.source_value,c.proposed_value,c.rule,c.reason
FROM loucka_reconstruction.reconstruction_candidates c
JOIN loucka_reconstruction.reconstruction_batches b ON b.batch_id=c.batch_id
LEFT JOIN loucka_reconstruction.archive a ON a.dateTime=c.target_time
WHERE b.state='pending' AND a.dateTime IS NULL
ORDER BY c.variable,c.target_time;

-- D: For the rain case, execute with database_name=information_schema because
-- Weather MCP does not accept this schema name directly; keep the quoted schema.
SELECT dateTime,usUnits,`interval`,rain,rainRate,windSpeed,outTemp
FROM `pocasi-loucka.eu_old`.archive
WHERE dateTime BETWEEN 1663246200 AND 1663246800 ORDER BY dateTime;
-- For the frozen-temperature case, run against database_name=old_weewx.
SELECT dateTime,usUnits,`interval`,outTemp,outHumidity,windSpeed,rain,rainRate
FROM old_weewx.archive
WHERE dateTime BETWEEN 1313639700 AND 1313640300 ORDER BY dateTime;
