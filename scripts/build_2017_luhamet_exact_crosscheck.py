#!/usr/bin/env python3
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
ref=json.loads((R/'data/2017_strict_source_luhamet_exact_crosscheck.json').read_text())['rows']
source={int(r['ts']):r for r in csv.DictReader((R/'reports/2026-11-13-source-only-strict-2017-row-evidence.csv').open())}
assert len(source)==10 and len(ref)==10
out=[]
for x in ref:
 t=x['target_time']; s=source[t]
 assert float(s['old_outTemp'])==0 and float(s['wh_outTemp'])==0
 delta=float(x['temperature_c'])
 out.append({'target_time':t,'utc':s['utc'],'source_outTemp':0,'previous_source_outTemp':s['previous_outTemp'],'next_source_outTemp':s['next_outTemp'],'luhamet_temperature_c':delta,'luhamet_rh':x['relative_humidity_pct'],'luhamet_resolution':x['source_resolution'],'luhamet_quality':x['quality_status'],'context_class':'REFERENCE_ZERO_AND_RH_ZERO_REVIEW' if delta==0 and x['relative_humidity_pct']==0 else 'REGIONAL_TEMPERATURE_DISAGREEMENT_REVIEW' if delta!=0 else 'REGIONAL_TEMPERATURE_AGREES'})
with (R/'reports/2026-11-13-2017-strict-cohort-luhamet-crosscheck.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
summary={'rows':len(out),'source_zero':sum(r['source_outTemp']==0 for r in out),'luhamet_nonzero':sum(r['luhamet_temperature_c']!=0 for r in out),'luhamet_zero_and_rh_zero':sum(r['luhamet_temperature_c']==0 and r['luhamet_rh']==0 for r in out),'regional_conflict_review':sum(r['context_class']=='REGIONAL_TEMPERATURE_DISAGREEMENT_REVIEW' for r in out),'minimum_luhamet_temperature_nonzero':min(r['luhamet_temperature_c'] for r in out if r['luhamet_temperature_c']!=0),'maximum_luhamet_temperature':max(r['luhamet_temperature_c'] for r in out),'mean_luhamet_temperature_nonzero':sum(r['luhamet_temperature_c'] for r in out if r['luhamet_temperature_c']!=0)/sum(r['luhamet_temperature_c']!=0 for r in out),'disposition':'All 10 remain REVIEW_REQUIRED; source copies are not authenticated independent sensor captures and LuhaMet is regional context only.'}
(R/'data/2017_strict_source_luhamet_exact_crosscheck_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
