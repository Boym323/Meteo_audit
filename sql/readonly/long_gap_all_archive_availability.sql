-- SELECT-only bounded archive inventory strictly inside the 2011-08-15 to
-- 2012-03-01 reconstruction gap. Epochs are UTC; do not widen to endpoints.
SELECT 'loucka_reconstruction' archive,COUNT(*) rows_n,MIN(dateTime) first_ts,
       MAX(dateTime) last_ts,SUM(outTemp IS NOT NULL) outTemp_nonnull,
       SUM(outTemp=0) outTemp_zero,MIN(`interval`) min_interval,MAX(`interval`) max_interval
FROM loucka_reconstruction.archive WHERE dateTime>1313438700 AND dateTime<1330593900
UNION ALL
SELECT 'old_weewx',COUNT(*),MIN(dateTime),MAX(dateTime),SUM(outTemp IS NOT NULL),
       SUM(outTemp=0),MIN(`interval`),MAX(`interval`)
FROM old_weewx.archive WHERE dateTime>1313438700 AND dateTime<1330593900
UNION ALL
SELECT 'weewx_WH1080',COUNT(*),MIN(dateTime),MAX(dateTime),SUM(outTemp IS NOT NULL),
       SUM(outTemp=0),MIN(`interval`),MAX(`interval`)
FROM weewx_WH1080.archive WHERE dateTime>1313438700 AND dateTime<1330593900
UNION ALL
SELECT 'pocasi-loucka.eu',COUNT(*),MIN(dateTime),MAX(dateTime),SUM(outTemp IS NOT NULL),
       SUM(outTemp=0),MIN(`interval`),MAX(`interval`)
FROM `pocasi-loucka.eu`.archive WHERE dateTime>1313438700 AND dateTime<1330593900
UNION ALL
SELECT 'pocasi-loucka.eu_old',COUNT(*),MIN(dateTime),MAX(dateTime),SUM(outTemp IS NOT NULL),
       SUM(outTemp=0),MIN(`interval`),MAX(`interval`)
FROM `pocasi-loucka.eu_old`.archive WHERE dateTime>1313438700 AND dateTime<1330593900
UNION ALL
SELECT 'pocasi-loucka.eu_GW1000',COUNT(*),MIN(dateTime),MAX(dateTime),SUM(outTemp IS NOT NULL),
       SUM(outTemp=0),MIN(`interval`),MAX(`interval`)
FROM `pocasi-loucka.eu_GW1000`.archive WHERE dateTime>1313438700 AND dateTime<1330593900;

-- Exact shared-row core field concordance for the two historical copies.
SELECT COUNT(*) paired_rows,
       SUM(a.outTemp <=> b.outTemp) outTemp_equal,
       SUM(a.outHumidity <=> b.outHumidity) outHumidity_equal,
       SUM(a.rain <=> b.rain) rain_equal,
       SUM(a.rainRate <=> b.rainRate) rainRate_equal,
       SUM(a.usUnits=b.usUnits) usUnits_equal,
       SUM(a.interval=b.interval) interval_equal,
       SUM(a.outHumidity IS NULL) old_RH_null,
       SUM(b.outHumidity IS NULL) WH1080_RH_null,
       SUM(a.outHumidity=0) old_RH_zero,
       SUM(b.outHumidity=0) WH1080_RH_zero
FROM old_weewx.archive a JOIN weewx_WH1080.archive b ON b.dateTime=a.dateTime
WHERE a.dateTime>1313438700 AND a.dateTime<1330593900;
