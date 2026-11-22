-- READ ONLY exact-membership check of the old SYSTEM/CET window and fixed UTC
-- window. The prior SQL evaluated these UNIX_TIMESTAMP bounds in the live
-- SYSTEM timezone; fixed UTC boundaries are Unix epochs.
WITH bounds AS (
 SELECT UNIX_TIMESTAMP('2009-01-01 00:00:00') prior_start,1230768000 utc_start,
        UNIX_TIMESTAMP('2021-01-01 00:00:00') prior_end,1609459200 utc_end
)
SELECT 'old_weewx' source_archive,'prior_only_start_band' band,COUNT(*) rows_in_band
FROM old_weewx.archive a JOIN bounds b WHERE a.dateTime>=b.prior_start AND a.dateTime<b.utc_start
UNION ALL
SELECT 'weewx_WH1080','prior_only_start_band',COUNT(*)
FROM weewx_WH1080.archive a JOIN bounds b WHERE a.dateTime>=b.prior_start AND a.dateTime<b.utc_start
UNION ALL
SELECT 'old_weewx','utc_only_end_band',COUNT(*)
FROM old_weewx.archive a JOIN bounds b WHERE a.dateTime>=b.prior_end AND a.dateTime<b.utc_end
UNION ALL
SELECT 'weewx_WH1080','utc_only_end_band',COUNT(*)
FROM weewx_WH1080.archive a JOIN bounds b WHERE a.dateTime>=b.prior_end AND a.dateTime<b.utc_end
UNION ALL
SELECT 'session','boundary_epoch_seconds',b.prior_start-b.utc_start
FROM bounds b;
