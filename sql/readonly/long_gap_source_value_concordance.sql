-- SELECT-only aggregate for the longest >=90-day reconstruction gap.
-- Compare archive copies at exact shared source timestamps; not independent truth.
SELECT COUNT(*) AS shared_rows,
       SUM(a.outTemp <=> b.outTemp) AS outTemp_equal,
       SUM(a.outHumidity <=> b.outHumidity) AS outHumidity_equal,
       SUM(a.rain <=> b.rain) AS rain_equal,
       SUM(a.rainRate <=> b.rainRate) AS rainRate_equal,
       SUM(a.usUnits=b.usUnits) AS units_equal,
       SUM(a.interval=b.interval) AS interval_equal,
       SUM(a.outTemp IS NOT NULL AND b.outTemp IS NOT NULL) AS both_outTemp,
       SUM(a.outHumidity IS NOT NULL AND b.outHumidity IS NOT NULL) AS both_outHumidity,
       SUM(a.rain IS NOT NULL AND b.rain IS NOT NULL) AS both_rain,
       SUM(a.rainRate IS NOT NULL AND b.rainRate IS NOT NULL) AS both_rainRate
FROM `old_weewx`.`archive` a
JOIN `weewx_WH1080`.`archive` b USING(dateTime)
WHERE a.dateTime BETWEEN 1313438700 AND 1330593900;

-- Distinguish matching NULLs, one-sided NULLs, and non-NULL disagreements in RH.
SELECT COUNT(*) AS shared_rows,
       SUM(a.outHumidity IS NULL AND b.outHumidity IS NULL) AS both_null,
       SUM(a.outHumidity IS NULL AND b.outHumidity IS NOT NULL) AS old_null_only,
       SUM(a.outHumidity IS NOT NULL AND b.outHumidity IS NULL) AS wh1080_null_only,
       SUM(a.outHumidity IS NOT NULL AND b.outHumidity IS NOT NULL AND a.outHumidity=b.outHumidity) AS both_value_equal,
       SUM(a.outHumidity IS NOT NULL AND b.outHumidity IS NOT NULL AND a.outHumidity<>b.outHumidity) AS both_value_different,
       MAX(CASE WHEN a.outHumidity IS NOT NULL AND b.outHumidity IS NOT NULL THEN ABS(a.outHumidity-b.outHumidity) END) AS max_abs_diff
FROM `old_weewx`.`archive` a
JOIN `weewx_WH1080`.`archive` b USING(dateTime)
WHERE a.dateTime BETWEEN 1313438700 AND 1330593900;
