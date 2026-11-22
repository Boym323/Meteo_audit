-- READ-ONLY annual ratio screen; execute once per UTC year with fixed [start,end) epochs.
-- Replace the two epoch placeholders. Ratio groups exclude NULL/zero pairs.
START TRANSACTION READ ONLY;
SELECT
  COUNT(*) AS exact_timestamp_pairs,
  SUM(w.usUnits<>s.usUnits) AS unit_mismatch_pairs,
  SUM(w.`interval`<>s.`interval`) AS interval_mismatch_pairs,
  SUM(w.windSpeed IS NOT NULL AND s.windSpeed IS NOT NULL AND w.windSpeed<>0 AND s.windSpeed<>0) AS windSpeed_nonzero_pairs,
  SUM(w.windSpeed IS NOT NULL AND s.windSpeed IS NOT NULL AND w.windSpeed<>0 AND s.windSpeed<>0 AND ABS(s.windSpeed/w.windSpeed-1)<0.001) AS windSpeed_ratio_1,
  SUM(w.windSpeed IS NOT NULL AND s.windSpeed IS NOT NULL AND w.windSpeed<>0 AND s.windSpeed<>0 AND ABS(s.windSpeed/w.windSpeed-3.6)<0.001) AS windSpeed_ratio_3_6,
  SUM(w.windGust IS NOT NULL AND s.windGust IS NOT NULL AND w.windGust<>0 AND s.windGust<>0) AS windGust_nonzero_pairs,
  SUM(w.windGust IS NOT NULL AND s.windGust IS NOT NULL AND w.windGust<>0 AND s.windGust<>0 AND ABS(s.windGust/w.windGust-1)<0.001) AS windGust_ratio_1,
  SUM(w.windGust IS NOT NULL AND s.windGust IS NOT NULL AND w.windGust<>0 AND s.windGust<>0 AND ABS(s.windGust/w.windGust-3.6)<0.001) AS windGust_ratio_3_6,
  SUM(w.windrun IS NOT NULL AND s.windrun IS NOT NULL AND w.windrun<>0 AND s.windrun<>0) AS windrun_nonzero_pairs,
  SUM(w.windrun IS NOT NULL AND s.windrun IS NOT NULL AND w.windrun<>0 AND s.windrun<>0 AND ABS(s.windrun/w.windrun-1)<0.001) AS windrun_ratio_1,
  SUM(w.windrun IS NOT NULL AND s.windrun IS NOT NULL AND w.windrun<>0 AND s.windrun<>0 AND ABS(s.windrun/w.windrun-1/3.6)<0.001) AS windrun_ratio_1_over_3_6
FROM `weewx_WH1080`.archive w
JOIN `pocasi-loucka.eu_old`.archive s ON s.dateTime=w.dateTime
WHERE w.dateTime>=<UTC_YEAR_START_EPOCH> AND w.dateTime < <UTC_YEAR_END_EPOCH>;
