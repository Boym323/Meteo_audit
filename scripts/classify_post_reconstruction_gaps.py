#!/usr/bin/env python3
"""Classify live gap edges against an empirical month-specific cadence mode.

The output is a candidate unobserved-grid-slot count, not proof that a sensor
was operating or that a measurement was lost. Cadence confidence is explicit.
"""
import csv, json
from collections import defaultdict, Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
hist=json.loads((ROOT/'data/post_reconstruction_cadence_histogram.json').read_text())
by_month=defaultdict(Counter)
for r in hist:
    by_month[r['utc_month']][int(r['delta_seconds'])]+=int(r['transitions'])
mode={}
for month,counts in by_month.items():
    total=sum(counts.values()); seconds,n=max(counts.items(),key=lambda kv:(kv[1],-kv[0]))
    mode[month]={'cadence_mode_seconds':seconds,'mode_transitions':n,'short_transition_count':total,'mode_share':n/total}
(ROOT/'data/post_reconstruction_cadence_modes.json').write_text(json.dumps(mode,indent=2)+'\n')
rows=list(csv.DictReader((ROOT/'ARCHIVE_GAP_INTERVALS.csv').open()))
by_year=defaultdict(lambda:Counter())
with (ROOT/'ARCHIVE_GAP_INTERVALS.csv').open('w',newline='') as f:
    derived=['utc_month_cadence_mode_seconds','cadence_mode_share','unobserved_grid_slots_candidate','gap_classification']
    base_fields=[x for x in dict.fromkeys(rows[0]) if x not in derived]
    fields=base_fields+derived
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for r in rows:
        month=r['target_utc'][:7]; m=mode.get(month)
        delta=int(r['delta_seconds']); pi=int(r['previous_interval_minutes']);ci=int(r['current_interval_minutes'])
        classification='UNRESOLVED_CADENCE_GAP'; slots=''
        if int(r['utc_year'])==2013:
            classification='UNRESOLVED_CADENCE_GAP_KNOWN_2013_TEN_MINUTE_EXCEPTION'
        elif m and m['mode_share']>=0.90 and m['short_transition_count']>=100 and r['previous_utc'][:7]==month and pi==ci:
            step=m['cadence_mode_seconds']
            if delta%step==0:
                candidate=max(0,delta//step-1);slots=candidate
                classification='OBSERVED_EPOCH_STEP' if candidate==0 else 'UNOBSERVED_CADENCE_SLOTS_CAUSE_UNKNOWN'
                if step!=pi*60: classification += '_ARCHIVE_INTERVAL_DIFFERS'
        r.update({'utc_month_cadence_mode_seconds':m['cadence_mode_seconds'] if m else '',
                  'cadence_mode_share':round(m['mode_share'],6) if m else '',
                  'unobserved_grid_slots_candidate':slots,'gap_classification':classification})
        w.writerow(r)
        year=int(r['utc_year']);by_year[year]['gap_edges']+=1
        if delta>3600:by_year[year]['gaps_over_1h']+=1
        if delta>86400:by_year[year]['gaps_over_24h']+=1
        by_year[year]['max_gap_seconds']=max(by_year[year]['max_gap_seconds'],delta)
        if slots!='':
            by_year[year]['cadence_classified_edges']+=1
            by_year[year]['unobserved_grid_slots_candidate']+=int(slots)
            if int(slots)>0:by_year[year]['edges_with_candidate_slots']+=1
        else:by_year[year]['unresolved_cadence_edges']+=1
with (ROOT/'ARCHIVE_TIME_COVERAGE.csv').open('w',newline='') as f:
    fields=['utc_year','gap_edges','gaps_over_1h','gaps_over_24h','max_gap_seconds','cadence_classified_edges','edges_with_candidate_slots','unobserved_grid_slots_candidate','unresolved_cadence_edges']
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for y,c in sorted(by_year.items()):w.writerow({'utc_year':y,**{k:c.get(k,0) for k in fields if k!='utc_year'}})
unresolved=sum(x['gap_classification'].startswith('UNRESOLVED_CADENCE_GAP') for x in rows)
print('months=%d gap_edges=%d candidate_slots=%d unresolved_edges=%d'%(len(mode),len(rows),sum(int(x['unobserved_grid_slots_candidate']) for x in rows if x['unobserved_grid_slots_candidate']),unresolved))
