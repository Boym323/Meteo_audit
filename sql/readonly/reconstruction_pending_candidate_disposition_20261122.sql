-- Audit 2026-11-22: outstanding historic proposals.
-- All statements below are SELECT only. Execute independently in MariaDB.
-- Case-sensitive BINARY collation is necessary because legacy staging tables
-- and reconstruction_changes have differing utf8mb4 collations.
-- Deliberately no INSERT/UPDATE/DELETE/DDL, no auto-apply of 272 pending.

-- A. Snapshot of staged decisions, including numeric proposal availability.
SELECT b.state, c.rule,
       COUNT(*) AS candidates,
       SUM(c.proposed_value IS NULL) AS no_numeric_replacement,
       SUM(c.proposed_value IS NOT NULL) AS with_numeric_replacement,
       COUNT(DISTINCT c.batch_id) AS batches
FROM loucka_reconstruction.reconstruction_candidates c
JOIN loucka_reconstruction.reconstruction_batches b
 ON BINARY b.batch_id=BINARY c.batch_id
GROUP BY b.state,c.rule ORDER BY b.state,candidates DESC;

-- B. Review every pending numeric candidate against CURRENT target and audit.
-- Exact timestamp/source units are necessary but never sufficient for approval.
WITH proposed AS (
 SELECT c.batch_id,c.ordinal,c.rule,c.source_database,c.target_time,
        c.variable,c.proposed_value,c.reason,
        r.dateTime IS NOT NULL AS target_exists,
        CASE BINARY c.variable
         WHEN BINARY 'outTemp' THEN r.outTemp
         WHEN BINARY 'outHumidity' THEN r.outHumidity
         WHEN BINARY 'rain' THEN r.rain
         WHEN BINARY 'rainRate' THEN r.rainRate
         WHEN BINARY 'pressure' THEN r.pressure
         WHEN BINARY 'barometer' THEN r.barometer
         WHEN BINARY 'windSpeed' THEN r.windSpeed
         WHEN BINARY 'windGust' THEN r.windGust
         ELSE NULL END AS current_value,
        (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes h
          WHERE h.target_time=c.target_time
          AND BINARY h.variable=BINARY c.variable
          AND h.state='applied'
          AND h.new_value <=> c.proposed_value) AS applied_exact_value_audits
 FROM loucka_reconstruction.reconstruction_candidates c
 JOIN loucka_reconstruction.reconstruction_batches b
  ON BINARY b.batch_id=BINARY c.batch_id
 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=c.target_time
 WHERE b.state='pending' AND c.proposed_value IS NOT NULL
)
SELECT batch_id,ordinal,rule,source_database,target_time,variable,
       proposed_value,target_exists,current_value,applied_exact_value_audits,
       CASE WHEN target_exists=1 AND current_value <=> proposed_value
                 AND applied_exact_value_audits>0
            THEN 'ALREADY_APPLIED_NO_REPEAT'
            WHEN target_exists=0 THEN 'HOLD_MISSING_TARGET_NO_INDEPENDENT_PROOF'
            ELSE 'HOLD_NOT_VERIFIED_NO_APPROVED_BATCH' END AS disposition
FROM proposed ORDER BY batch_id,ordinal;

-- C. 2020 physical temperature source conflict: the old DB has suspicious
-- 4.25/0 degree plateaus, while old_weewx and weewx_WH1080 agree with EACH OTHER,
-- not the old DB. Their common origin is NOT independent confirmation.
SELECT COUNT(*) AS old_source_candidate_count,
       COUNT(DISTINCT s.outTemp) AS distinct_old_source_values,
       MIN(s.outTemp) AS old_source_min, MAX(s.outTemp) AS old_source_max,
       SUM(w.outTemp IS NOT NULL) AS wh_available,
       COUNT(DISTINCT w.outTemp) AS distinct_wh_values,
       SUM(w.outTemp IS NOT NULL AND ABS(w.outTemp-s.outTemp)<0.001)
        AS old_archive_agrees_with_wh,
       SUM(w.outTemp IS NOT NULL AND o.outTemp IS NOT NULL
           AND ABS(w.outTemp-o.outTemp)<0.001)
        AS wh_copies_agree,
       MIN(t.dateTime) AS first_epoch, MAX(t.dateTime) AS last_epoch
FROM loucka_reconstruction.archive t
JOIN `pocasi-loucka.eu_old`.archive s ON s.dateTime=t.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=t.dateTime
LEFT JOIN old_weewx.archive o ON o.dateTime=t.dateTime
WHERE t.dateTime>=1577836800 AND t.dateTime<1609459200
 AND t.outTemp IS NULL AND s.outTemp IS NOT NULL;

-- D. Candidate from September 2022: verify historical missing slot and
-- nearest-slot rain disagreement. Do not synthesize or automatically insert
-- the missing original timestamp 1663246500.
SELECT src,'2022-09-15-gap' AS cohort, COUNT(*) AS records_found,
       SUM(dateTime=1663246500) AS matching_exact_gap_ts,
       SUM(rain IS NOT NULL) AS known_rain_intervals,
       SUM(rainRate IS NOT NULL) AS known_rainrate_intervals,
       SUM(rain>0) AS positive_rain_intervals
FROM (
 SELECT 'production' AS src,dateTime,rain,rainRate FROM `pocasi-loucka.eu`.archive
  WHERE dateTime BETWEEN 1663245300 AND 1663247700
 UNION ALL
 SELECT 'reconstruction',dateTime,rain,rainRate FROM loucka_reconstruction.archive
  WHERE dateTime BETWEEN 1663245300 AND 1663247700
 UNION ALL
 SELECT 'old_archive',dateTime,rain,rainRate FROM `pocasi-loucka.eu_old`.archive
  WHERE dateTime BETWEEN 1663245300 AND 1663247700
 UNION ALL
 SELECT 'gw1000',dateTime,rain,rainRate FROM `pocasi-loucka.eu_GW1000`.archive
  WHERE dateTime BETWEEN 1663245300 AND 1663247700
) x GROUP BY src ORDER BY src;
