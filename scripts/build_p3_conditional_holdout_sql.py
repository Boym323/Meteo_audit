#!/usr/bin/env python3
"""Generate SELECT-only conditional 10-25m P3 masked-block validation SQL."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for gap in (600,900,1200,1500):
    minutes=gap//60;k=gap//300-1
    joins=' '.join(f"JOIN loucka_reconstruction.archive t{j} ON t{j}.dateTime=e.left_t+{j*300} AND t{j}.interval=5 AND t{j}.usUnits=16 AND t{j}.outTemp IS NOT NULL AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=t{j}.dateTime AND c.variable='outTemp')" for j in range(1,k+1))
    ys=', '.join(f't{j}.outTemp y{j}' for j in range(1,k+1))
    vals=' UNION ALL '.join(f"SELECT utc_year,FLOOR(ABS((left_y+(right_y-left_y)*{j*300}/{gap})-y{j})*10)/10 err_bucket FROM complete" for j in range(1,k+1))
    prefix=f"""-- SELECT-only Weather MCP READ-ONLY query. Synthetic complete rows are masked.
-- Deterministic hourly anchors; same P3 endpoint filters; 0.1 C error bins.
WITH episodes AS (
 SELECT CASE WHEN a.dateTime<1577836800 THEN 2019 ELSE 2020 END utc_year,
        a.dateTime left_t,a.outTemp left_y,b.outTemp right_y
 FROM loucka_reconstruction.archive a
 JOIN loucka_reconstruction.archive b ON b.dateTime=a.dateTime+{gap}
 WHERE a.dateTime>=1546300800 AND a.dateTime<1609459200
  AND MOD(a.dateTime-1546300800,3600)=0 AND a.interval=5 AND b.interval=5
  AND a.usUnits=16 AND b.usUnits=16
  AND a.outTemp>0 AND a.outTemp<=35 AND b.outTemp>0 AND b.outTemp<=35
  AND a.outHumidity BETWEEN 20 AND 95 AND b.outHumidity BETWEEN 20 AND 95
  AND a.rain=0 AND b.rain=0 AND a.rainRate=0 AND b.rainRate=0
  AND a.windSpeed>=5 AND b.windSpeed>=5 AND ABS(b.outTemp-a.outTemp)<=2
  AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=a.dateTime AND c.variable='outTemp')
  AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=b.dateTime AND c.variable='outTemp')
), complete AS (
 SELECT e.*,{ys}
 FROM episodes e {joins}
), scores AS (
 {vals}
), hist AS (
 SELECT utc_year,err_bucket,COUNT(*) point_n FROM scores GROUP BY utc_year,err_bucket
), counts AS (
 SELECT utc_year,COUNT(*) episode_n,COUNT(*)*{k} total_points FROM complete GROUP BY utc_year
)
SELECT {minutes} gap_minutes,h.utc_year,h.err_bucket,h.point_n,c.episode_n,c.total_points
FROM hist h JOIN counts c ON c.utc_year=h.utc_year ORDER BY h.utc_year,h.err_bucket;
"""
    (R/f'sql/readonly/p3_conditional_holdout_{minutes}m_2019_2020.sql').write_text(prefix)
    maxe=f'GREATEST({", ".join(f"y{j}" for j in range(1,k+1))})' if k>1 else 'y1'
    mine=f'LEAST({", ".join(f"y{j}" for j in range(1,k+1))})' if k>1 else 'y1'
    ext=f"""-- SELECT-only Weather MCP READ-ONLY query. Hidden interior extrema against endpoints.
WITH episodes AS (
 SELECT CASE WHEN a.dateTime<1577836800 THEN 2019 ELSE 2020 END utc_year,
        a.dateTime left_t,a.outTemp left_y,b.outTemp right_y
 FROM loucka_reconstruction.archive a
 JOIN loucka_reconstruction.archive b ON b.dateTime=a.dateTime+{gap}
 WHERE a.dateTime>=1546300800 AND a.dateTime<1609459200
  AND MOD(a.dateTime-1546300800,3600)=0 AND a.interval=5 AND b.interval=5
  AND a.usUnits=16 AND b.usUnits=16
  AND a.outTemp>0 AND a.outTemp<=35 AND b.outTemp>0 AND b.outTemp<=35
  AND a.outHumidity BETWEEN 20 AND 95 AND b.outHumidity BETWEEN 20 AND 95
  AND a.rain=0 AND b.rain=0 AND a.rainRate=0 AND b.rainRate=0
  AND a.windSpeed>=5 AND b.windSpeed>=5 AND ABS(b.outTemp-a.outTemp)<=2
  AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=a.dateTime AND c.variable='outTemp')
  AND NOT EXISTS(SELECT 1 FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=b.dateTime AND c.variable='outTemp')
), complete AS (
 SELECT e.*,{ys}
 FROM episodes e {joins}
)
SELECT {minutes} gap_minutes,utc_year,COUNT(*) episode_n,
 SUM({maxe}>GREATEST(left_y,right_y)) episodes_hidden_max,
 SUM({mine}<LEAST(left_y,right_y)) episodes_hidden_min,
 MAX(GREATEST({maxe}-GREATEST(left_y,right_y),0)) max_hidden_max_error_c,
 MAX(GREATEST(LEAST(left_y,right_y)-{mine},0)) max_hidden_min_error_c
FROM complete GROUP BY utc_year ORDER BY utc_year;
"""
    (R/f'sql/readonly/p3_extrema_holdout_{minutes}m_2019_2020.sql').write_text(ext)
print('generated 8 SELECT-only SQL files for 10/15/20/25 minute conditional holdout and extrema checks')
