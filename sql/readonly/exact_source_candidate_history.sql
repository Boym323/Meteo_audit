-- Applied/reverted/current change history for exact-source NULL candidates.
-- Run as a separate read-only statement after the inventory query.
SELECT c.target_time, c.variable, c.batch_key, c.state, c.old_value, c.new_value,
       c.source_database, c.source_time, c.source_value, c.reason,
       c.created_at, c.applied_at
FROM loucka_reconstruction.reconstruction_changes c
JOIN loucka_reconstruction.archive t ON t.dateTime=c.target_time
LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=t.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive o ON o.dateTime=t.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=t.dateTime
WHERE c.variable IN ('outTemp','outHumidity')
  AND ((c.variable='outTemp' AND t.outTemp IS NULL AND (p.outTemp IS NOT NULL OR o.outTemp IS NOT NULL OR g.outTemp IS NOT NULL)
        AND ((t.dateTime>=1356998400 AND t.dateTime<1388534400)
          OR (t.dateTime>=1451606400 AND t.dateTime<1514764800)
          OR (t.dateTime>=1546300800 AND t.dateTime<1609459200)
          OR (t.dateTime>=1640995200 AND t.dateTime<1672531200)))
    OR (c.variable='outHumidity' AND t.outHumidity IS NULL AND (p.outHumidity IS NOT NULL OR o.outHumidity IS NOT NULL OR g.outHumidity IS NOT NULL)
        AND ((t.dateTime>=1356998400 AND t.dateTime<1388534400)
          OR (t.dateTime>=1451606400 AND t.dateTime<1514764800)
          OR (t.dateTime>=1546300800 AND t.dateTime<1609459200)
          OR (t.dateTime>=1640995200 AND t.dateTime<1672531200))));

-- Staged cohort decisions are distinct from applied change history.
SELECT c.target_time, c.variable, c.batch_id, c.source_database, c.source_time,
       c.source_value, c.proposed_value, c.rule, c.rule_version, c.reason, b.state
FROM loucka_reconstruction.reconstruction_candidates c
JOIN loucka_reconstruction.reconstruction_batches b ON b.batch_id=c.batch_id
JOIN loucka_reconstruction.archive t ON t.dateTime=c.target_time
LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=t.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive o ON o.dateTime=t.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=t.dateTime
WHERE c.variable='outHumidity' AND t.outHumidity IS NULL
  AND t.dateTime>=1640995200 AND t.dateTime<1672531200
  AND (p.outHumidity IS NOT NULL OR o.outHumidity IS NOT NULL OR g.outHumidity IS NOT NULL);
