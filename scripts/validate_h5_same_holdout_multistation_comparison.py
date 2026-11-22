#!/usr/bin/env python3
"""Rebuild H5 aggregate comparison in memory and verify serialized outputs."""
import csv,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='h5-rebuild-') as td:
    # Build outputs to workspace, then load and check invariant counts/metrics; builder is deterministic.
    proc=subprocess.run([sys.executable,str(ROOT/'scripts/build_h5_same_holdout_multistation_comparison.py')],cwd=ROOT,text=True,capture_output=True)
    assert proc.returncode==0,proc.stderr
record=json.loads((ROOT/'data/h5_same_holdout_multistation_comparison.json').read_text())
assert record['target_rows_unique']==2415
assert [x['n_unique_utc_targets'] for x in record['years']]==[1067,1348]
assert record['database_access']=='NONE' and record['database_writes']==0
assert record['mcp_dry_run']=='NOT_RUN' and record['staging'] is False and record['application']=='NOT_APPLIED'
with (ROOT/'data/h5_same_holdout_multistation_comparison.csv').open(newline='') as f: rows=list(csv.DictReader(f))
assert len(rows)==6 and {r['reference'] for r in rows}=={'LuhaMet Sehradice','ČHMÚ Vizovice','ČHMÚ Kladná-Žilín'}
assert all(int(r['n_pairs'])==int(r['n_unique_utc_targets']) for r in rows)
for y in record['years']:
    assert set(y)=={'year','n_unique_utc_targets','luhamet_sehradice','chmi_vizovice','chmi_kladna_zilin'}
    assert len({y[k]['n'] for k in ('luhamet_sehradice','chmi_vizovice','chmi_kladna_zilin')})==1
print(json.dumps({'status':'PASS','unique_common_targets':record['target_rows_unique'],'year_counts':[x['n_unique_utc_targets'] for x in record['years']],'metric_rows':len(rows),'database_access':'NONE'},ensure_ascii=False))
