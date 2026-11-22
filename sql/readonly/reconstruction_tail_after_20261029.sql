-- Read-only confirmation whether loucka_reconstruction.archive advanced
-- beyond the established 2026-10-29 15:10 UTC high-water mark.
-- 1793286600 = 2026-10-29 15:10:00 UTC.
SELECT COUNT(*) AS rows_after_checkpoint,
       MAX(dateTime) AS latest_epoch
FROM loucka_reconstruction.archive
WHERE dateTime > 1793286600;
