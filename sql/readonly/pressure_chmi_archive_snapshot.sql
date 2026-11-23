-- Run with an already-existing read-only client account.
-- One consistent read-only snapshot; no DDL or data writes.
START TRANSACTION READ ONLY;
SELECT dateTime, usUnits, `interval`, pressure, barometer, outTemp, inTemp
FROM loucka_reconstruction.archive
WHERE dateTime >= 1230768000  -- 2009-01-01T00:00:00Z
  AND dateTime < 1798761600   -- 2027-01-01T00:00:00Z
ORDER BY dateTime;
