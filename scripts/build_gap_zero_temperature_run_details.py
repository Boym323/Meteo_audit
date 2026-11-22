#!/usr/bin/env python3
"""Generate top-run SELECTs for the largest year/protection zero-run groups."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];src=R/'sql/readonly/gap_zero_temperature_runs';out=src/'details';out.mkdir(parents=True,exist_ok=True)
# Chunks selected by the complete 21-chunk aggregate: longest gap-catalog-year
# runs for 2012, 2016 and 2017, plus protected Q1 2018.
selected=[4,91,95,101]
items=[]
for i in selected:
 p=src/f'gap_zero_temperature_runs_{i:03d}.sql';text=p.read_text()
 marker='\nSELECT utc_year,gap_band,protection_scope,COUNT(*) zero_run_count'
 idx=text.rfind(marker)
 if idx<0:raise ValueError(f'final summary SELECT not found: {p}')
 detail=text[:idx]+'''\nSELECT utc_year,gap_band,protection_scope,gap_id,zero_run_id,sample_count,
       first_ts,last_ts,left_neighbor_temp,right_neighbor_temp
FROM runs ORDER BY sample_count DESC LIMIT 5\n'''
 q=out/f'gap_zero_temperature_run_details_{i:03d}.sql';q.write_text('-- READ-ONLY largest zero runs for evidence targeting.\n'+detail)
 items.append({'source_chunk':i,'path':str(q.relative_to(R)),'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
m={'query_count':len(items),'selection_rationale':'Largest run by gap catalog year among all 21 zero-bearing chunks; includes protected Q1 2018 as diagnostic-only.','queries':items,'read_only':True}
(R/'data/gap_zero_temperature_run_detail_query_manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print(json.dumps({'queries':len(items)}))
