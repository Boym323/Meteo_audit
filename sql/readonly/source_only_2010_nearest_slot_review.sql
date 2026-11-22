-- READ-ONLY 2010 source-only timestamp alignment. Run using database_name=old_weewx.
-- Nearest 300-second key is diagnostic only; this query does not authorize a time shift.
SELECT MOD(o.dateTime,300) AS grid_remainder,COUNT(*) AS source_rows,
       SUM(w.dateTime IS NOT NULL) AS wh1080_pairs,
       SUM(w.outTemp<=>o.outTemp) AS exact_source_outTemp_pairs,
       SUM(e.dateTime IS NOT NULL) AS eu_old_exact_rows,
       SUM(e.outTemp<=>o.outTemp) AS eu_old_outTemp_equal,
       SUM(r.dateTime IS NOT NULL) AS nearest_reconstruction_rows,
       SUM(r.usUnits=16 AND r.`interval`=5) AS nearest_interval5_metric_rows,
       SUM(r.outTemp<=>o.outTemp) AS nearest_outTemp_equal,
       SUM(r.outTemp IS NOT NULL AND o.outTemp IS NOT NULL AND ABS(r.outTemp-o.outTemp)<=0.3) AS nearest_outTemp_within_0_3,
       SUM(o.outTemp=0) AS source_outTemp_zero
FROM archive o
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive e ON e.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=o.dateTime
LEFT JOIN loucka_reconstruction.archive r
  ON r.dateTime=CASE WHEN MOD(o.dateTime,300)<=150
                     THEN o.dateTime-MOD(o.dateTime,300)
                     ELSE o.dateTime+(300-MOD(o.dateTime,300)) END
WHERE o.dateTime>=1262304000 AND o.dateTime<1293840000 AND t.dateTime IS NULL
GROUP BY MOD(o.dateTime,300) ORDER BY grid_remainder;

-- Field-specific concordance to the diagnostic nearest target; this tests the
-- observed stored-value relationship, not measurement truth or a restoration rule.
SELECT COUNT(*) AS source_rows,
       SUM(o.windSpeed<>0 AND r.windSpeed IS NOT NULL) AS windSpeed_nonzero_pairs,
       SUM(o.windSpeed<>0 AND r.windSpeed IS NOT NULL AND ABS(r.windSpeed/o.windSpeed-1)<0.001) AS windSpeed_ratio_1,
       SUM(o.windSpeed<>0 AND r.windSpeed IS NOT NULL AND ABS(r.windSpeed/o.windSpeed-3.6)<0.001) AS windSpeed_ratio_3_6,
       SUM(o.windGust<>0 AND r.windGust IS NOT NULL) AS windGust_nonzero_pairs,
       SUM(o.windGust<>0 AND r.windGust IS NOT NULL AND ABS(r.windGust/o.windGust-1)<0.001) AS windGust_ratio_1,
       SUM(o.windGust<>0 AND r.windGust IS NOT NULL AND ABS(r.windGust/o.windGust-3.6)<0.001) AS windGust_ratio_3_6,
       SUM(o.rain<>0 AND r.rain IS NOT NULL AND ABS(r.rain/o.rain-0.1)<0.001) AS rain_ratio_0_1,
       SUM(o.rainRate<>0 AND r.rainRate IS NOT NULL AND ABS(r.rainRate/o.rainRate-0.1)<0.001) AS rainRate_ratio_0_1
FROM archive o
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=o.dateTime
JOIN loucka_reconstruction.archive r
  ON r.dateTime=CASE WHEN MOD(o.dateTime,300)<=150
                     THEN o.dateTime-MOD(o.dateTime,300)
                     ELSE o.dateTime+(300-MOD(o.dateTime,300)) END
WHERE o.dateTime>=1262304000 AND o.dateTime<1293840000 AND t.dateTime IS NULL;

-- Explicit collisions: several distinct off-grid source rows map to one already
-- occupied nearest target key. These must never become duplicate inserts.
SELECT r.dateTime AS projected_target_time,COUNT(*) AS source_rows,
       GROUP_CONCAT(o.dateTime ORDER BY o.dateTime) AS source_timestamps,
       GROUP_CONCAT(o.outTemp ORDER BY o.dateTime) AS source_temperatures,
       GROUP_CONCAT(MOD(o.dateTime,300) ORDER BY o.dateTime) AS source_moduli,
       GROUP_CONCAT(ABS(o.dateTime-r.dateTime) ORDER BY o.dateTime) AS offsets_seconds
FROM archive o
JOIN loucka_reconstruction.archive r
  ON r.dateTime=CASE WHEN MOD(o.dateTime,300)<=150
                     THEN o.dateTime-MOD(o.dateTime,300)
                     ELSE o.dateTime+(300-MOD(o.dateTime,300)) END
LEFT JOIN loucka_reconstruction.archive t ON t.dateTime=o.dateTime
WHERE o.dateTime>=1262304000 AND o.dateTime<1293840000 AND t.dateTime IS NULL
GROUP BY r.dateTime HAVING COUNT(*)>1 ORDER BY r.dateTime;
