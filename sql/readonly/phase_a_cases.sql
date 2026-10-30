-- Read-only incident review. Execute only as a SELECT-only account.
-- dateTime predicates use UTC Unix seconds; local display is Europe/Prague.
START TRANSACTION READ ONLY;
SELECT dateTime, usUnits, `interval`, rain, rainRate, outTemp, outHumidity, windSpeed
FROM `pocasi-loucka.eu`.archive
WHERE dateTime BETWEEN 1275387000 AND 1275391800
   OR dateTime BETWEEN 1301294100 AND 1301295900
   OR dateTime BETWEEN 1740686400 AND 1740688200
ORDER BY dateTime;

-- 2010-06-01/02/03 local civil-day boundaries (Europe/Prague DST-aware UTC epochs).
SELECT '2010-06-01',COUNT(*),SUM(rain),SUM(rain IS NULL),MAX(rain)
FROM `pocasi-loucka.eu`.archive WHERE dateTime>=1275343200 AND dateTime<1275429600;
SELECT '2010-06-02',COUNT(*),SUM(rain),SUM(rain IS NULL),MAX(rain)
FROM `pocasi-loucka.eu`.archive WHERE dateTime>=1275429600 AND dateTime<1275516000;
SELECT '2010-06-03',COUNT(*),SUM(rain),SUM(rain IS NULL),MAX(rain)
FROM `pocasi-loucka.eu`.archive WHERE dateTime>=1275516000 AND dateTime<1275602400;

SELECT batch_id, ordinal, source_database, source_time, target_time, variable,
       source_value, proposed_value, rule, rule_version, reason
FROM loucka_reconstruction.reconstruction_candidates
WHERE target_time IN (1301295000, 1740687300)
ORDER BY batch_id, ordinal;

SELECT batch_key, target_time, variable, old_value, new_value, state, created_at, applied_at
FROM loucka_reconstruction.reconstruction_changes
WHERE target_time IN (1301295000, 1740687300)
ORDER BY id;
ROLLBACK;
