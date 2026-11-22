-- READ-ONLY: contiguous zero outTemp runs in WH1080 archive, 2016–2017.
-- Runs split on any nonzero/NULL value or timestamp gap >600s. Candidate overlap uses
-- the strict paired-source, reconstruction-absent, usUnits=17, interval=5, 300s-grid filter.
WITH w AS (
 SELECT dateTime,`interval` AS interval_min,usUnits,outTemp,
        LAG(dateTime) OVER (ORDER BY dateTime) AS prev_ts,
        LAG(outTemp) OVER (ORDER BY dateTime) AS prev_temp
 FROM weewx_WH1080.archive
 WHERE dateTime>=1451606400 AND dateTime<1514764800
), marked AS (
 SELECT *,CASE WHEN outTemp=0 AND prev_temp=0 AND dateTime-prev_ts<=600 THEN 0 ELSE 1 END AS starts_new
 FROM w
), grouped AS (
 SELECT *,SUM(starts_new) OVER (ORDER BY dateTime ROWS UNBOUNDED PRECEDING) AS grp
 FROM marked
), runs AS (
 SELECT CASE WHEN dateTime<1483228800 THEN 2016 ELSE 2017 END AS utc_year,grp,
        COUNT(*) AS run_rows,MIN(dateTime) AS first_ts,MAX(dateTime) AS last_ts,
        SUM(dateTime%300=0 AND interval_min=5 AND usUnits=17 AND EXISTS (
          SELECT 1 FROM old_weewx.archive o
          LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=o.dateTime
          WHERE o.dateTime=grouped.dateTime AND r.dateTime IS NULL
            AND o.usUnits=17 AND o.`interval`=5 AND o.dateTime%300=0
        )) AS strict_source_only_rows
 FROM grouped WHERE outTemp=0
 GROUP BY utc_year,grp HAVING run_rows>=2
)
SELECT utc_year,COUNT(*) AS zero_run_episodes,SUM(run_rows) AS zero_rows_in_multirow_runs,
       MAX(run_rows) AS longest_zero_run_rows,MAX(last_ts-first_ts) AS longest_zero_run_span_seconds,
       SUM(strict_source_only_rows) AS strict_source_only_zero_rows_in_multirow_runs,
       MAX(strict_source_only_rows) AS max_strict_rows_in_one_run
FROM runs GROUP BY utc_year ORDER BY utc_year;
