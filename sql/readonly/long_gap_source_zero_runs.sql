-- Read-only contiguous zero-run summary in the five >=7-day source windows.
-- A run continues only across exact 300-second neighbors with outTemp=0 on both rows.
-- This is a pattern screen, not proof that zero is an invalid/sentinel value.
SELECT gap_id, COUNT(*) AS zero_runs, SUM(run_rows) AS zero_rows,
       MAX(run_rows) AS max_run_rows, MAX(elapsed_s) AS max_run_elapsed_s
FROM (
  SELECT gap_id, grp, COUNT(*) AS run_rows, MAX(dateTime)-MIN(dateTime) AS elapsed_s
  FROM (
    SELECT gap_id,dateTime,outTemp,
      SUM(CASE WHEN prev_outTemp=0 AND delta=300 AND outTemp=0 THEN 0 ELSE 1 END)
        OVER(PARTITION BY gap_id ORDER BY dateTime) AS grp
    FROM (
      SELECT gap_id,dateTime,outTemp,
        LAG(outTemp) OVER(PARTITION BY gap_id ORDER BY dateTime) AS prev_outTemp,
        dateTime-LAG(dateTime) OVER(PARTITION BY gap_id ORDER BY dateTime) AS delta
      FROM (
        SELECT 1 AS gap_id,dateTime,outTemp FROM `weewx_WH1080`.`archive` WHERE dateTime BETWEEN 1313438700 AND 1330593900
        UNION ALL SELECT 2,dateTime,outTemp FROM `weewx_WH1080`.`archive` WHERE dateTime BETWEEN 1453156500 AND 1454764200
        UNION ALL SELECT 3,dateTime,outTemp FROM `weewx_WH1080`.`archive` WHERE dateTime BETWEEN 1494564600 AND 1496007900
        UNION ALL SELECT 5,dateTime,outTemp FROM `weewx_WH1080`.`archive` WHERE dateTime BETWEEN 1483966800 AND 1484645400
      ) source_rows
    ) lagged
  ) grouped
  WHERE outTemp=0
  GROUP BY gap_id,grp
) runs
GROUP BY gap_id
ORDER BY gap_id;
