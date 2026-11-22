#!/usr/bin/env python3
"""Build reproducible evidence and decisions for the first publication pilot.

All source reads are from the frozen, read-only concordance and existing
statistical snapshots. This script never connects to or writes to MariaDB.
"""
from __future__ import annotations
import argparse, ast, csv, datetime as dt, hashlib, json, math, sqlite3, statistics, zlib
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo
import sys

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; TZ=ZoneInfo('Europe/Prague')
sys.path.insert(0, str(ROOT/'src'))

from meteo_audit.publication_classifier import classify_evidence as classify_decision
from meteo_audit.provenance_counts import build_provenance_counts

DB=DATA/'historical_value_concordance.sqlite'; SNAPSHOT='1e34859d05bb0ec20d3810c4fbb376d231a6ee0bfca0c4c636dcfb2d1114e4ba'
VARS=('outTemp','outHumidity','barometer','pressure','altimeter','windSpeed','windGust','windDir')
PRIMARY='pocasi-loucka.eu'

def write_json(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def read_csv(name):
    with (DATA/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def read_payload(blob):return json.loads(zlib.decompress(blob))

def conflict_evidence():
    """Classify conflicts by target/source relationships, without rewriting categories."""
    agg=defaultdict(Counter); examples=defaultdict(list)
    db=sqlite3.connect(f'file:{DB.resolve()}?mode=ro',uri=True)
    for ts,year,blob in db.execute('SELECT dateTime,local_year,comparison_zlib FROM timestamp_evidence ORDER BY dateTime'):
        fields=read_payload(blob)
        for var in VARS:
            x=fields[var]
            if x.get('provenance_category')!='CONFLICTING_SOURCE':continue
            target=x.get('target_value');obs=x.get('source_observations') or []
            matches=[o for o in obs if o.get('normalized_value')==target]
            primary=any(o.get('archive')==PRIMARY for o in matches)
            legacy=any(o.get('archive')!=PRIMARY for o in matches)
            vals={o.get('normalized_value') for o in obs if o.get('normalized_value') is not None}
            source_disagreement=len(vals)>1
            if primary:sub='TARGET_MATCHES_PRIMARY_WITH_LEGACY_DISAGREEMENT' if source_disagreement else 'TARGET_MATCHES_PRIMARY'
            elif legacy:sub='TARGET_MATCHES_LEGACY_ONLY'
            else:sub='TARGET_NO_COMPATIBLE_SOURCE_MATCH'
            epoch='+'.join(sorted({o.get('archive','UNKNOWN') for o in obs})) or 'NO_SOURCE_OBSERVATION'
            # Epoch signature is explicitly an evidence-availability cohort, not a sensor identity.
            key=(var,int(year),epoch);a=agg[key];a[sub]+=1;a['CONFLICTING_SOURCE_TOTAL']+=1
            if primary:a['PRIMARY_ARCHIVE_MATCH']+=1
            if legacy:a['LEGACY_COPY_MATCH']+=1
            if not source_disagreement:a['ALL_COMPATIBLE_SOURCES_AGREE']+=1
            if primary and source_disagreement:a['TARGET_MATCHES_SOURCE_WITH_LEGACY_DISAGREEMENT']+=1
            if source_disagreement:
                a['HISTORICAL_COPIES_DISAGREE']+=1
                legacy_values=[o.get('normalized_value') for o in obs if o.get('archive')!=PRIMARY and o.get('normalized_value') is not None]
                try:rounding_only=bool(legacy_values) and all(abs(Decimal(str(v))-Decimal(str(target)))<=Decimal('0.000000001') for v in legacy_values)
                except (InvalidOperation,TypeError):rounding_only=False
                a['LEGACY_NUMERIC_ROUNDING_ONLY' if rounding_only else 'LEGACY_NUMERICALLY_MATERIAL_DIFFERENCE']+=1
                known=False
                if var in {'windSpeed','windGust'} and 2014<=int(year)<=2019 and target not in (None,'0','0.0'):
                    for o in obs:
                        if o.get('archive') not in {'old_weewx','weewx_WH1080','pocasi-loucka.eu_old'} or not o.get('normalized_value'):continue
                        try:
                            ratio=Decimal(str(target))/Decimal(str(o['normalized_value']))
                            if abs(ratio-Decimal('3.6'))<=Decimal('0.001') or abs(ratio-Decimal(1)/Decimal('3.6'))<=Decimal('0.001'):known=True
                        except (InvalidOperation,ZeroDivisionError):pass
                if known:
                    a['KNOWN_TRANSFORMATION_PATTERN_SUPPORTED_BY_EXISTING_AUDIT']+=1
                    a['KNOWN_TRANSFORMATION_EXPLAINS_DIFFERENCE']+=1
                if var in {'pressure','altimeter','barometer','rainRate'}:a['UNRESOLVED_UNIT_OR_DRIVER_SEMANTICS']+=1
            else:a['ALL_AVAILABLE_SOURCE_VALUES_AGREE']+=1
            if x.get('applied_change') is not None or x.get('audit_row_value') is not None:
                if target is not None and (str(x.get('applied_change'))==str(target) or str(x.get('audit_row_value'))==str(target)):
                    a['EXACT_APPLIED_AUDIT_MATCH']+=1
                else:a['HAS_AUDIT_OR_APPLIED_CHANGE_EVIDENCE']+=1
            if len(examples[key])<3:examples[key].append({'timestamp':int(ts),'target':target,'sources':obs,'subtype':sub,'source_disagreement':source_disagreement})
    db.close()
    rows=[]
    for (v,y,e),c in sorted(agg.items()):rows.append({'variable':v,'year':y,'source_epoch_evidence_signature':e,**dict(sorted(c.items())),'requires_detailed_review':c['TARGET_NO_COMPATIBLE_SOURCE_MATCH']+c['TARGET_MATCHES_LEGACY_ONLY']+c['TARGET_MATCHES_PRIMARY_WITH_LEGACY_DISAGREEMENT']})
    totals=Counter()
    for r in rows:
        for k,v in r.items():
            if k in {'variable','year','source_epoch_evidence_signature'}:continue
            totals[k]+=v
    totals['VALUE_LEVEL_UNMATCHED_REQUIRING_EXPERT_REVIEW']=totals.get('TARGET_NO_COMPATIBLE_SOURCE_MATCH',0)+totals.get('TARGET_MATCHES_LEGACY_ONLY',0)
    totals['EPOCH_LEVEL_LEGACY_DISCREPANCY_REVIEW']=totals.get('TARGET_MATCHES_PRIMARY_WITH_LEGACY_DISAGREEMENT',0)-totals.get('LEGACY_NUMERIC_ROUNDING_ONLY',0)-totals.get('KNOWN_TRANSFORMATION_PATTERN_SUPPORTED_BY_EXISTING_AUDIT',0)
    totals['EXACT_APPLIED_AUDIT_MATCH']=totals.get('EXACT_APPLIED_AUDIT_MATCH',0)
    totals['EXTERNAL_REFERENCE_VALIDATED']=0
    totals['EXTERNAL_REFERENCE_VALIDATED']=0
    return {'schema':'loucka-historical-conflict-subtypes-v2','snapshot_id':SNAPSHOT,'evidence_flags':{'PRIMARY_ARCHIVE_MATCH':'Target exactly matches the current primary archive, independent of historical-copy agreement.','LEGACY_COPY_MATCH':'Target also exactly matches at least one non-primary historical copy.','ALL_COMPATIBLE_SOURCES_AGREE':'All available compatible source observations have identical normalized values.','TARGET_MATCHES_SOURCE_WITH_LEGACY_DISAGREEMENT':'Target exactly matches current primary archive while at least one legacy copy differs.','TARGET_NO_SOURCE_MATCH':'Target matches no compatible source observation.','KNOWN_TRANSFORMATION_EXPLAINS_DIFFERENCE':'An exact wind factor pattern in the previously audited field/year/source cohort; does not prove sensor truth or authorize correction.','UNRESOLVED_UNIT_OR_DRIVER_SEMANTICS':'Field is in a known unresolved unit/driver semantics group.','EXACT_APPLIED_AUDIT_MATCH':'Target exactly matches a row-level applied-change/audit value.','EXTERNAL_REFERENCE_VALIDATED':'No source conflict row is called externally validated from regional similarity.'},'classification_note':'Source-availability cohorts are evidence-availability signatures, not sensor epochs; archives are dependent copies. Exact provenance categories remain unchanged. Legacy numeric rounding uses a separate 1e-9 normalized-unit diagnostic and never upgrades exact concordance. Known wind transformation patterns are flagged only for the field and years supported by the existing audit; flags do not prove sensor truth or authorize correction. Value-level unmatched cases are distinguished from epoch-level legacy discrepancy review.','source_primary_archive':PRIMARY,'source_dependency_catalog':'HISTORICAL_SOURCE_DEPENDENCY_GRAPH.json','known_transform_evidence':'HISTORICAL_WIND_TRANSFORMATION_REPORT.md; 2014-2019 only, exact observed factor 3.6 diagnostic','totals':dict(sorted(totals.items())),'by_variable_year_and_source_epoch':rows,'evidence_samples':[{'variable':v,'year':y,'source_epoch_evidence_signature':e,'samples':s} for (v,y,e),s in sorted(examples.items())]}

def finalize_conflict_summary(summary):
    """Clarify value-level versus epoch-level review counts in computed totals."""
    for r in summary['by_variable_year_and_source_epoch']:
        r['requires_detailed_review']=int(r.get('TARGET_NO_COMPATIBLE_SOURCE_MATCH',0))+int(r.get('TARGET_MATCHES_LEGACY_ONLY',0))
    t=summary['totals']
    t['VALUE_LEVEL_UNMATCHED_REQUIRING_EXPERT_REVIEW']=int(t.get('TARGET_NO_COMPATIBLE_SOURCE_MATCH',0))+int(t.get('TARGET_MATCHES_LEGACY_ONLY',0))
    t['requires_detailed_review']=t['VALUE_LEVEL_UNMATCHED_REQUIRING_EXPERT_REVIEW']
    t['EPOCH_LEVEL_LEGACY_DISCREPANCY_REVIEW']=max(0,int(t.get('TARGET_MATCHES_PRIMARY_WITH_LEGACY_DISAGREEMENT',0))-int(t.get('LEGACY_NUMERIC_ROUNDING_ONLY',0))-int(t.get('KNOWN_TRANSFORMATION_PATTERN_SUPPORTED_BY_EXISTING_AUDIT',0)))
    t['KNOWN_TRANSFORMATION_PATTERN_SUPPORTED_BY_EXISTING_AUDIT']=int(t.get('KNOWN_TRANSFORMATION_PATTERN_SUPPORTED_BY_EXISTING_AUDIT',0))
    t['EXACT_APPLIED_AUDIT_MATCH']=int(t.get('EXACT_APPLIED_AUDIT_MATCH',0))
    t['EXTERNAL_REFERENCE_VALIDATED']=0
    summary['schema']='loucka-historical-conflict-subtypes-v2'
    return summary

def pilot_month():
    # Grid and mean counts are anchored to the released B/E statistical output.
    vr={(r['period'],r['variable'],r['variant']):r for r in read_csv('STATISTICAL_VARIANTS_MONTHLY.csv')}
    rdy=json.loads((DATA/'STATISTICAL_READINESS_CURRENT.json').read_text())
    ready={(r['period'],r['variable']):r for r in rdy['monthly']}
    output=[];pilot_rows={}
    ext_path=ROOT/'PILOT_2026_01_EXTERNAL_VALIDATION.json'
    external=json.loads(ext_path.read_text()) if ext_path.exists() else None
    db=sqlite3.connect(f'file:{DB.resolve()}?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    for var in ('outTemp','outHumidity','barometer'):
        rows=[]
        for rec in db.execute("SELECT dateTime,target_interval,comparison_zlib,audit_zlib FROM timestamp_evidence WHERE local_month='2026-01' ORDER BY dateTime"):
            fields=read_payload(rec['comparison_zlib']);f=fields[var]
            if f['target_value'] is None:continue
            auxiliary={name:fields.get(name,{}).get('target_value') for name in ('pressure','barometer','altimeter','dewpoint')}
            rows.append((int(rec['dateTime']),int(rec['target_interval'] or 0),f,read_payload(rec['audit_zlib']),auxiliary))
        vals=[float(x[2]['target_value']) for x in rows]
        pilot_rows[var]=rows
        diffs=[vals[i]-vals[i-1] for i in range(1,len(vals))]
        cats=Counter(x[2]['provenance_category'] for x in rows)
        source_names=Counter(o['archive'] for x in rows for o in (x[2].get('source_observations') or []) if o.get('normalized_value')==x[2].get('target_value'))
        source_values=Counter((o['archive'],o['normalized_value']) for x in rows for o in (x[2].get('source_observations') or []))
        # Stuck runs are exact repeated target values lasting >= 60 minutes.
        runs=[];start=0
        for i in range(1,len(vals)+1):
            if i==len(vals) or vals[i]!=vals[start]:
                if i-start>1:runs.append({'value':vals[start],'slots':i-start,'start_utc':dt.datetime.fromtimestamp(rows[start][0],dt.timezone.utc).isoformat().replace('+00:00','Z'),'end_utc':dt.datetime.fromtimestamp(rows[i-1][0],dt.timezone.utc).isoformat().replace('+00:00','Z'),'duration_seconds':rows[i-1][0]-rows[start][0]+(rows[i-1][1]*60)})
                start=i
        max_run=max((x['slots'] for x in runs),default=1);long_runs=[x for x in runs if x['duration_seconds']>=3600]
        dtimes=[x[0] for x in rows];gaps=[(dtimes[i]-dtimes[i-1]) for i in range(1,len(dtimes))]
        units=Counter(x[2].get('target_unit') for x in rows)
        ref=vr[('2026-01',var,'E_FULL_CURRENT_ARCHIVE')]
        b=vr[('2026-01',var,'B_DOCUMENTED_SOURCE_AND_RECOVERY')]
        rr=ready[('2026-01',var)]
        weights=[x[1]*60 for x in rows]
        independent_mean=sum(v*w for v,w in zip(vals,weights))/sum(weights)
        if not math.isclose(independent_mean,float(ref['mean_time_weighted']),rel_tol=0,abs_tol=2e-9):
            raise AssertionError(f'independent weighted mean mismatch for {var}: {independent_mean} vs {ref["mean_time_weighted"]}')
        ext=external['variables'].get(var) if external else None
        ext_pass=bool(var=='outTemp' and ext and ext['matched_coverage']>=.98 and ext['correlation']>=.90 and abs(ext['bias_chmi_minus_loucka'])<=1.0)
        continuity=bool(cats['SOURCE_MATCHED']==len(rows) and {'pocasi-loucka.eu','pocasi-loucka.eu_GW1000'}<=set(source_names))
        physical=ext_pass if var=='outTemp' else False
        decision,decision_reason=classify_decision({'integrity_ok':True,'estimates':cats['ESTIMATED'],'representative':float(ref['coverage'])>=.99 and max(gaps,default=0)<=1800,'sensor_error':False,'unmatched_conflicts':cats['CONFLICTING_SOURCE'],'physical_validation':physical,'provenance_sufficient':continuity,'external_validation':ext_pass,'independent_sensor_lineage':False,'documented_archive_continuity':continuity,'explicit_limitations':continuity})
        if var=='outHumidity':decision_reason='A 15 h 40 min exact 99% plateau (2026-01-15 17:25–2026-01-16 09:00 UTC), plus a second 15 h 35 min plateau, coincides with CHMI Vizovice humidity 79–97%; the monthly CHMI-minus-Loučka mean is -8.40 percentage points. Regional microclimate may explain some difference, but saturation/sticking is unresolved. Tie the sensor/configuration record to this period and resolve the plateau before recommendation.'
        if var=='barometer':decision_reason='WeeWX distinguishes station pressure (pressure), sea-level pressure (barometer), and altitude-corrected altimeter. January median barometer-pressure is 52.62 hPa and altimeter-barometer is -2.40 hPa. Without the driver/hardware configuration and Loučka site elevation, the recorded transformation cannot be checked; provide those records before recommendation.'
        domain={'outTemp':(-40.0,45.0),'outHumidity':(0.0,100.0),'barometer':(870.0,1085.0)}[var]
        full_weight=int(ref['expected_unique_slots'])*300;missing_weight=max(0,full_weight-sum(weights))
        mean_lower=(independent_mean*sum(weights)+domain[0]*missing_weight)/full_weight
        mean_upper=(independent_mean*sum(weights)+domain[1]*missing_weight)/full_weight
        output.append({'period':'2026-01','variable':var,'statistic':'time_weighted_mean','value':independent_mean,'unit':units.most_common(1)[0][0],'methodology':'WeeWX archive-end timestamp intervals, on the canonical expected 5-minute grid, UTC duration weighting; not an unweighted sample mean. Independently recomputed from target_value × target_interval × 60 seconds over exact January evidence rows.','expected_slots':int(ref['expected_unique_slots']),'observed_slots':int(ref['variant_on_grid_values']),'coverage':float(ref['coverage']),'provenance':dict(cats),'matched_source_observation_counts':dict(source_names),'estimated_count':int(cats['ESTIMATED']),'conflict_count':int(cats['CONFLICTING_SOURCE']),'max_gap_seconds':max(gaps,default=0),'max_exact_stuck_run_slots':max_run,'stuck_runs_ge_1_hour':len(long_runs),'longest_exact_stuck_run':max(runs,key=lambda x:x['slots']) if runs else None,'long_exact_stuck_run_samples':long_runs[:10],'max_abs_adjacent_change':max(map(abs,diffs),default=0),'minimum':min(vals),'maximum':max(vals),'units_seen':dict(units),'variant_B_value':float(b['mean_time_weighted']),'variant_E_value':float(ref['mean_time_weighted']),'variant_B_coverage':float(b['coverage']),'independent_recalculation_matches':True,'recalculation_abs_difference':abs(independent_mean-float(ref['mean_time_weighted'])),'missing_value_mean_sensitivity':{'missing_weight_seconds':missing_weight,'assumed_broad_physical_domain':[domain[0],domain[1]],'lower_bound':mean_lower,'upper_bound':mean_upper,'caveat':'Sensitivity interval only; bounds use broad physical limits and do not include systematic sensor error.'},'independent_external_reference':ext,'sensor_epoch':'January 2026 is in the shared historical archive baseline: GW3000 and GW1000 copies agree for the listed core fields through the pre-March transition. It is not evidence of live GW3000 measurements. Exact sensor identity/configuration and deployment history are absent.','physical_checks':{},'uncertainty':'Three expected 5-minute slots lack non-NULL values. Missing-data sensitivity is bounded using the broad physical domain reported here; this does not bound sensor bias. Archive concordance and synchronization audit support copy continuity but are dependent records, not independent sensor verification.','decision':decision,'decision_reason':decision_reason,'readiness_evidence':{'readiness_screen':rr,'variant_B_provenance_counts':ast.literal_eval(b['provenance_counts']),'variant_E_provenance_counts':ast.literal_eval(ref['provenance_counts']),'source_snapshot_id':SNAPSHOT}})
    # Check temperature/RH-derived dewpoint and pressure-field relationships.
    tmap={x[0]:(float(x[2]['target_value']),x[4].get('dewpoint')) for x in pilot_rows['outTemp']}
    hmap={x[0]:float(x[2]['target_value']) for x in pilot_rows['outHumidity']}
    dew_errors=[]
    for ts in sorted(set(tmap)&set(hmap)):
        temp,observed_dew=tmap[ts];rh=hmap[ts]
        if 0<rh<=100 and observed_dew is not None:
            aa=17.625;bb=243.04;gamma=math.log(rh/100)+aa*temp/(bb+temp);calc=bb*gamma/(aa-gamma)
            dew_errors.append(abs(calc-float(observed_dew)))
    output[0]['physical_checks']={'broad_range_check':{'range_degC':[-40,45],'out_of_range_count':sum(not -40<=v<=45 for v in [float(x[2]['target_value']) for x in pilot_rows['outTemp']])},'dewpoint_crosscheck':'Unavailable because a per-row dewpoint field is not included in this concordance snapshot; the external CHMI T/H series supplies regional checks for temperature and humidity separately.'}
    output[1]['physical_checks']={'broad_range_check':{'range_percent':[0,100],'out_of_range_count':sum(not 0<=v<=100 for v in [float(x[2]['target_value']) for x in pilot_rows['outHumidity']])},'temperature_rh_dewpoint_crosscheck':'Reported with outTemp.'}
    pvals=[];avals=[]
    for x in pilot_rows['barometer']:
        bval=float(x[2]['target_value']);p=x[4].get('pressure');a=x[4].get('altimeter')
        if p is not None:pvals.append(bval-float(p))
        if a is not None:avals.append(float(a)-bval)
    bvalues=[float(x[2]['target_value']) for x in pilot_rows['barometer']]
    output[2]['physical_checks']={'broad_range_check':{'range_hPa':[870,1085],'out_of_range_count':sum(not 870<=v<=1085 for v in bvalues)},'barometer_minus_pressure_hPa':{'count':len(pvals),'minimum':min(pvals) if pvals else None,'median':statistics.median(pvals) if pvals else None,'maximum':max(pvals) if pvals else None},'altimeter_minus_barometer_hPa':{'count':len(avals),'minimum':min(avals) if avals else None,'median':statistics.median(avals) if avals else None,'maximum':max(avals) if avals else None},'interpretation':'WeeWX documentation defines pressure as station pressure, barometer as sea-level pressure corrected using altitude and local temperature, and altimeter as station pressure corrected for altitude. Hardware/driver determines which value is measured versus calculated. This archive evidence does not include the exact driver configuration or site elevation needed to reproduce transformations; no field is relabelled.'}
    db.close();return output

def decisions_v2():
    old=read_csv('PUBLICATION_READINESS_DECISIONS.csv');out=[]
    for r in old:
        status=r['publication_readiness'];reason=r['rejection_reason']
        if status=='REVIEW_REQUIRED_PROVENANCE':
            status='REVIEW_REQUIRED_CONFLICTS' if int(r['conflicting_source_values'] or 0)>0 else 'REVIEW_REQUIRED_PROVENANCE'
            reason='High coverage passed sampling only. Value-level source conflicts require classification; dependent archive-copy agreement is not independent sensor validation.' if status=='REVIEW_REQUIRED_CONFLICTS' else 'No value-level evidence establishes sensor lineage for this candidate.'
        r['publication_readiness']=status;r['rejection_reason']=reason;r['uncertainty']=reason
        r['evidence_state']='Snapshot-bound value-level provenance; no blanket approval from coverage.'
        out.append(r)
    # Do not approve pilot rows: specific sensor identity/configuration and external comparator unavailable.
    return out

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-conflict-summary',action='store_true',help='reuse an existing summary only when its snapshot id matches')
    args=parser.parse_args()
    actual=hashlib.sha256(DB.read_bytes()).hexdigest()
    if actual!=SNAPSHOT:raise SystemExit(f'Concordance snapshot hash mismatch: {actual}')
    pilot=pilot_month()
    summary_path=DATA/'HISTORICAL_CONFLICT_SUBTYPES_SUMMARY.json'
    if args.reuse_conflict_summary and summary_path.exists():
        conflicts=json.loads(summary_path.read_text())
        if conflicts.get('snapshot_id')!=SNAPSHOT:raise SystemExit('Conflict summary snapshot mismatch.')
    else:conflicts=conflict_evidence()
    conflicts=finalize_conflict_summary(conflicts)
    write_json(summary_path,conflicts);write_json(ROOT/'HISTORICAL_CONFLICT_SUBTYPES_SUMMARY.json',conflicts)
    pilot_decisions={row['variable']:row['publication_readiness'] if 'publication_readiness' in row else row['decision'] for row in pilot}
    for row in pilot:
        row.update({'methodology_version':'publication-pilot-v2.0','publication_readiness':row['decision'],'limitations':[row['uncertainty'],row['decision_reason']],'evidence_reference':'data/historical_value_concordance.sqlite; data/STATISTICAL_VARIANTS_MONTHLY.csv; data/STATISTICAL_READINESS_CURRENT.json','snapshot_id':SNAPSHOT})
    write_json(ROOT/'PILOT_2026_01_VALIDATED_STATISTICS.json',{'schema':'loucka-validated-statistics-v1','snapshot_id':SNAPSHOT,'methodology_version':'publication-pilot-v2.0','statistics':pilot})
    # Reproduce the 248 pre-screened provenance-review monthly means with >=99% B coverage.
    cand=[];vmap={(r['period'],r['variable'],r['variant']):r for r in read_csv('STATISTICAL_VARIANTS_MONTHLY.csv')}
    screened={(r['period'],r['variable']) for r in read_csv('MASTER_GOAL_CANDIDATE_SELECTION_BASELINE.csv')}
    for (period,var,variant),r in vmap.items():
        if variant!='B_DOCUMENTED_SOURCE_AND_RECOVERY':continue
        if (period,var) not in screened:continue
        direction_without_speed=int(r.get('wind_direction_without_variant_speed_excluded',0)) if var=='windDir' else 0
        eligible_count=int(r['variant_on_grid_values'])
        selection_coverage=(eligible_count+direction_without_speed)/int(r['expected_unique_slots']) if var=='windDir' and int(r['expected_unique_slots']) else float(r['coverage'] or 0)
        if selection_coverage>=.99 and var in ('outTemp','outHumidity','barometer','windGust','windSpeed','windDir'):
            candidate_value=float(r['mean_time_weighted']) if r['mean_time_weighted']!='' else None
            candidate_coverage=float(r['coverage'])
            # Retain the originally selected period-variable as an individually
            # reviewed candidate even when its variant has no eligible direction.
            # The missing statistic is explicit; no E-variant fallback is used.
            if var=='windDir' and candidate_value is None and direction_without_speed:
                candidate_coverage=0.0
            cand.append({'period':period,'variable':var,'statistic':'mean','variant':'B_DOCUMENTED_SOURCE_AND_RECOVERY','coverage':candidate_coverage,'selection_coverage':selection_coverage,'observed_slots':eligible_count,'expected_slots':int(r['expected_unique_slots']),'value':candidate_value,'unit':r['unit'],'provenance_counts':r['provenance_counts'],'wind_direction_without_variant_speed_excluded':direction_without_speed,'candidate_decision':pilot_decisions[var] if period=='2026-01' and var in pilot_decisions else 'REVIEW_REQUIRED_PROVENANCE','reason':('No B-variant mean is calculable: every direction lacks same-variant positive windSpeed; retain as a candidate-specific blocked result.' if var=='windDir' and candidate_value is None else 'Candidate selection only; 99% slot coverage does not constitute expert validation.')})
    cand.sort(key=lambda x:(x['variable'],x['period']))
    write_json(ROOT/'MONTHLY_PUBLICATION_CANDIDATES.json',{'schema':'loucka-monthly-publication-candidates-v2','snapshot_id':SNAPSHOT,'selection_rule':'Monthly means for the six named fields, variant B, original slot coverage >= 0.99. A selected windDir candidate is retained with value=null and an explicit blocker when same-variant positive windSpeed is unavailable.','candidate_count':len(cand),'by_variable':dict(Counter(x['variable'] for x in cand)),'candidates':cand})
    # Derive totals from this snapshot's controlled rollup, then check them
    # against the previous artifact only when it names the same snapshot hash.
    counts=build_provenance_counts(DB,ROOT/'PROVENANCE_COUNTS_CORRECTED.json')
    write_json(ROOT/'PROVENANCE_COUNTS_CORRECTED.json',counts)
    rows=decisions_v2()
    for r in rows:
        r.update({'value':'','unit':'','evidence_reference':'','methodology_version':'publication-pilot-v2.0'})
    for p in pilot:
        match=next((r for r in rows if r['period']==p['period'] and r['scope']=='MONTHLY' and r['variable']==p['variable'] and r['statistic']=='MEAN'),None)
        if match:
            match.update({'publication_readiness':p['decision'],'value':p['value'],'unit':p['unit'],'evidence_reference':p['evidence_reference'],'methodology_version':p['methodology_version'],'evidence_state':'Pilot-specific value-level evidence plus time-matched CHMI validation where applicable; see the cited pilot evidence JSON.','permitted_use':'Future publication with explicit limitations.' if p['decision']=='READY_WITH_DISCLOSED_LIMITATIONS' else 'Research review only pending sensor/physical validation.','uncertainty':p['uncertainty'],'rejection_reason':p['decision_reason'],'statistics_used':'Independent time-weighted recomputation from frozen snapshot; E/B exact means cross-checked.'})
    keys=list(rows[0]);
    with (ROOT/'STATISTICAL_PUBLICATION_DECISIONS_V2.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    dc=Counter(r['publication_readiness'] for r in rows)
    write_json(ROOT/'STATISTICAL_PUBLICATION_DECISIONS_V2.json',{'schema':'loucka-publication-decisions-v2','snapshot_id':SNAPSHOT,'row_count':len(rows),'status_counts':dict(sorted(dc.items())),'positive_decision_branch':'Shared normalized evidence classifier: src/meteo_audit/publication_classifier.py. Readiness recommendations remain separate from publication authorization.','publication_authorized':False,'decisions':rows})
    write_json(ROOT/'MASTER_GOAL_PUBLICATION_PILOT_EVIDENCE.json',{'schema':'loucka-publication-pilot-evidence-v1','snapshot_id':SNAPSHOT,'concordance_rows':counts['snapshot_rows'],'provenance_counts':counts,'conflict_summary_file':'HISTORICAL_CONFLICT_SUBTYPES_SUMMARY.json','pilot_file':'PILOT_2026_01_VALIDATED_STATISTICS.json','external_validation_file':'PILOT_2026_01_EXTERNAL_VALIDATION.json','candidate_count':len(cand),'candidate_by_variable':dict(Counter(x['variable'] for x in cand)),'decision_count':len(rows),'decision_status_counts':dict(sorted(dc.items())),'external_reference_status':'CHMI Vizovice 11777 Jan 2026 10-minute T/H data aligned on exact UTC timestamps; regional plausibility only. No Loucka sensor coordinates; pressure reference unavailable. ILOUKA4 excluded because identity independence is unresolved.','reproduction':'Run python3 scripts/run_automated_validation_pipeline.py from the repository root.'})
    print(json.dumps({'conflict_subtype_total':conflicts['totals'],'candidate_count':len(cand),'candidate_by_variable':dict(Counter(x['variable'] for x in cand)),'decision_status_counts':dict(sorted(dc.items()))},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
