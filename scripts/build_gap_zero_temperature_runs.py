#!/usr/bin/env python3
"""Build read-only episode-level zero-outTemp run screens for relevant gap chunks."""
import glob,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
OUT=R/'sql/readonly/gap_zero_temperature_runs';OUT.mkdir(parents=True,exist_ok=True)
result_files=glob.glob(str(R/'data/gap_source_copy_concordance/chunk_results_*.json'))
zero_chunks=set()
for p in result_files:
 for c in json.loads(Path(p).read_text())['chunks']:
  if any(int(r['wh_outTemp_zero'])>0 for r in c['rows']):zero_chunks.add(int(c['chunk']))
records=[]
for i in sorted(zero_chunks):
 src=R/f'sql/readonly/gap_source_copy_concordance/gap_source_copy_concordance_{i:03d}.sql'
 text=src.read_text();start=text.index('WITH targets AS ');end=text.index('), wh_hits AS (',start)
 targets=text[start:end+1]
 sql=targets+''', wh_rows AS (
 SELECT t.gap_id,t.gap_band,t.left_time,t.right_time,a.dateTime ts,a.outTemp,
        CASE WHEN a.dateTime>=1514764800 AND a.dateTime<1522540800 THEN 'PROTECTED_Q1_2018_DIAGNOSTIC' ELSE 'NORMAL' END protection_scope
 FROM targets t JOIN weewx_WH1080.archive a
   ON a.dateTime>t.left_time AND a.dateTime<t.right_time AND MOD(a.dateTime-t.left_time,300)=0
 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime
 WHERE r.dateTime IS NULL
), lagged AS (
 SELECT *,LAG(ts) OVER(PARTITION BY gap_id ORDER BY ts) prev_ts,
          LAG(outTemp) OVER(PARTITION BY gap_id ORDER BY ts) prev_temp,
          LEAD(ts) OVER(PARTITION BY gap_id ORDER BY ts) next_ts,
          LEAD(outTemp) OVER(PARTITION BY gap_id ORDER BY ts) next_temp
 FROM wh_rows
), marked AS (
 SELECT *,CASE WHEN outTemp=0 AND COALESCE(prev_ts=ts-300 AND prev_temp=0,0)=0 THEN 1 ELSE 0 END zero_run_start
 FROM lagged
), segmented AS (
 SELECT *,SUM(zero_run_start) OVER(PARTITION BY gap_id ORDER BY ts ROWS UNBOUNDED PRECEDING) zero_run_id
 FROM marked
), runs AS (
 SELECT CAST(SUBSTRING_INDEX(gap_id,':',1) AS UNSIGNED) utc_year,gap_band,protection_scope,
        gap_id,zero_run_id,COUNT(*) sample_count,MIN(ts) first_ts,MAX(ts) last_ts,
        MAX(CASE WHEN zero_run_start=1 AND prev_ts=ts-300 THEN prev_temp END) left_neighbor_temp,
        MAX(CASE WHEN next_ts=ts+300 AND next_temp<>0 THEN next_temp END) right_neighbor_temp
 FROM segmented WHERE outTemp=0
 GROUP BY utc_year,gap_band,protection_scope,gap_id,zero_run_id
)
SELECT utc_year,gap_band,protection_scope,COUNT(*) zero_run_count,
       SUM(sample_count) zero_samples,SUM(sample_count=1) singleton_runs,
       SUM(sample_count BETWEEN 2 AND 5) runs_2_to_5,
       SUM(sample_count BETWEEN 6 AND 11) runs_6_to_11,
       SUM(sample_count>=12) runs_12_plus,MAX(sample_count) max_run_samples,
       COUNT(DISTINCT gap_id) gaps_with_zero_run,
       SUM(left_neighbor_temp IS NOT NULL AND right_neighbor_temp IS NOT NULL) runs_bracketed_by_nonzero,
       SUM(left_neighbor_temp IS NOT NULL AND right_neighbor_temp IS NOT NULL AND left_neighbor_temp<>right_neighbor_temp) bracketed_with_change
FROM runs GROUP BY utc_year,gap_band,protection_scope ORDER BY utc_year,gap_band,protection_scope
'''
 out=OUT/f'gap_zero_temperature_runs_{i:03d}.sql';out.write_text('-- READ-ONLY episode-level zero outTemp run-length screen.\n'+sql)
 records.append({'source_chunk':i,'path':str(out.relative_to(R)),'bytes':out.stat().st_size})
manifest={'query_count':len(records),'source_scope':'WH1080 rows with outTemp=0 in the frozen conditional gap slots; only chunks with prior-verified zero rows','zero_source_chunks':records,'read_only':True,'interval_interpretation':'run sample counts are archive-row adjacency at exactly 300 seconds; not proof of expected physical observations'}
(R/'data/gap_zero_temperature_run_query_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'query_count':len(records),'source_zero_rows_in_scope':sum(int(r['wh_outTemp_zero']) for p in result_files for c in json.loads(Path(p).read_text())['chunks'] for r in c['rows'])}))
