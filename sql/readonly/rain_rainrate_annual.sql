-- SELECT-only snapshot. Year grouping follows the SQL session timezone.
SELECT YEAR(FROM_UNIXTIME(a.dateTime)) AS local_year,
       COUNT(*) AS archive_rows,
       SUM(a.rain IS NULL) AS rain_null,
       SUM(a.rain = 0) AS rain_zero,
       SUM(a.rain > 0) AS rain_positive,
       ROUND(SUM(a.rain), 4) AS rain_sum_stored,
       SUM(a.rainRate IS NULL) AS rainRate_null,
       SUM(a.rainRate = 0) AS rainRate_zero,
       SUM(a.rainRate > 0) AS rainRate_positive,
       ROUND(SUM(a.rainRate), 4) AS rainRate_sum_stored,
       SUM(a.rain > 0 AND a.rainRate = 0) AS wet_rate_zero,
       SUM(a.rain = 0 AND a.rainRate > 0) AS ratepos_rainzero,
       SUM(a.rain IS NULL AND a.rainRate > 0) AS ratepos_rainnull
FROM archive AS a
GROUP BY YEAR(FROM_UNIXTIME(a.dateTime))
ORDER BY local_year;
