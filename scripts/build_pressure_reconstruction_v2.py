#!/usr/bin/env python3
"""Build a separate UNAPPROVED candidate catalog and read-only annual inventory."""
from __future__ import annotations
import argparse,csv,configparser,hashlib,json
import gzip,io
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

Q1_START=int(datetime(2018,1,1,tzinfo=timezone.utc).timestamp())
Q1_END=int(datetime(2018,4,1,tzinfo=timezone.utc).timestamp())

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def combine(v1_path,era_path,qc_path,validation):
    flags=set()
    with qc_path.open(newline='') as f:
        for r in csv.DictReader(f): flags.add(int(r['dateTime_utc']))
    rows={}
    with v1_path.open(newline='') as f:
        for r in csv.DictReader(f):
            ts=int(r['dateTime_utc'])
            if Q1_START<=ts<Q1_END: continue
            if ts in flags:
                rows[ts]={'dateTime_utc':ts,'field':'pressure','original_value':'','estimated_value_hpa':'','withheld_candidate_value_hpa':r['estimated_value_hpa'],'classification':'UNRESOLVED','approval_status':'UNAPPROVED','method':'none','temporal_resolution':'5-minute source row','source_barometer_hpa':r['source_barometer_hpa'],'source_outTemp_c':r['source_outTemp_c'],'empirical_uncertainty_hpa':'','precision_class':'REJECTED_INPUT_QC','model_sha256':r['model_sha256'],'reference_manifest_sha256':r['reference_manifest_sha256'],'era5_manifest_sha256':'','qc_evidence_sha256':sha(qc_path),'provenance':r['source'],'reason':'suspected isolated barometer spike; input value withheld'}
            else:
                rows[ts]={'dateTime_utc':ts,'field':'pressure','original_value':r['original_value'],'estimated_value_hpa':r['estimated_value_hpa'],'withheld_candidate_value_hpa':'','classification':'ESTIMATED','approval_status':'UNAPPROVED','method':'pressure-shadow-2022-v1 barometer+outTemp','temporal_resolution':'archive row (not independently validated at 5-minute resolution)','source_barometer_hpa':r['source_barometer_hpa'],'source_outTemp_c':r['source_outTemp_c'],'empirical_uncertainty_hpa':max(float(r['reference_hourly_p95_max_hpa']),float(r['local_holdout_p95_hpa'])),'precision_class':'DUAL_STATION_MONTHLY_GATE_PASS; 5-MINUTE_ACCURACY_UNVERIFIED','model_sha256':r['model_sha256'],'reference_manifest_sha256':r['reference_manifest_sha256'],'era5_manifest_sha256':'','qc_evidence_sha256':'','provenance':r['source'],'reason':'V1 regional monthly gate passed; empirical p95 is group diagnostic only'}
    with era_path.open(newline='') as f:
        for r in csv.DictReader(f):
            ts=int(r['dateTime_utc'])
            if Q1_START<=ts<Q1_END: raise ValueError('Q1 2018 protection violated')
            if ts in flags: continue
            model=r['method'];vmonth=validation['test_monthly'].get(datetime.fromtimestamp(ts,timezone.utc).strftime('%Y-%m'),{})
            score=vmonth.get('models',{}).get(model,{})
            # This CSV contains only rows admitted by the independent frozen test gate.
            if score.get('gate')!='PASS_DIAGNOSTIC_PREVIEW_ONLY': raise ValueError('ERA5 candidate failed frozen gate')
            prior=rows.get(ts)
            rows[ts]={'dateTime_utc':ts,'field':'pressure','original_value':'','estimated_value_hpa':r['estimated_value_hpa'],'withheld_candidate_value_hpa':'','classification':'ESTIMATED','approval_status':'UNAPPROVED','method':model,'temporal_resolution':'hourly ERA5 model value; never a 5-minute observation','source_barometer_hpa':'','source_outTemp_c':'','empirical_uncertainty_hpa':max(score['scores'][s]['p95_abs_error_hpa'] for s in ('H','M')),'precision_class':'DUAL_STATION_HELDOUT_GATE_PASS; HOURLY_ONLY','model_sha256':'','reference_manifest_sha256':r['reference_manifest_sha256'],'era5_manifest_sha256':r['era5_manifest_sha256'],'qc_evidence_sha256':sha(qc_path),'provenance':'ERA5 surface_pressure + returned grid-height transport; 2021 selection, untouched 2022 test','reason':'independent dual-station hourly gate passed; replaces same-time V1 candidate' if prior else 'independent dual-station hourly gate passed; no temporal interpolation'}
    fields=['dateTime_utc','field','original_value','estimated_value_hpa','withheld_candidate_value_hpa','classification','approval_status','method','temporal_resolution','source_barometer_hpa','source_outTemp_c','empirical_uncertainty_hpa','precision_class','model_sha256','reference_manifest_sha256','era5_manifest_sha256','qc_evidence_sha256','provenance','reason']
    return [rows[t] for t in sorted(rows)],fields

def write_unified_series(cnf,candidates,path):
    """Stream every archive timestamp to a separate compressed file; SELECT only."""
    import pymysql
    from pymysql.cursors import SSCursor
    cfg=configparser.ConfigParser(interpolation=None)
    if not cfg.read(cnf) or cfg.get('client','user',fallback='')!='loucka_web_ro':raise PermissionError('read-only account required')
    con=pymysql.connect(read_default_file=str(cnf),read_default_group='client',database='loucka_reconstruction',cursorclass=SSCursor,autocommit=False,connect_timeout=15,read_timeout=300)
    bytime={r['dateTime_utc']:r for r in candidates};counts=Counter();annual=__import__('collections').defaultdict(Counter);rows=0;candidate_seen=set();stale_collisions=0
    try:
        with con.cursor() as c:
            c.execute('START TRANSACTION READ ONLY')
            c.execute('SELECT @@hostname,@@server_id,CURRENT_USER()');ident=c.fetchone()
            c.fetchall()  # drain the unbuffered identity result before the archive scan
            if ident!=('lo-infra-db-mariadb01',1,'loucka_web_ro@192.168.0.131'):raise RuntimeError('unexpected SQL endpoint')
            c.execute('SELECT dateTime,usUnits,pressure FROM loucka_reconstruction.archive ORDER BY dateTime')
            with path.open('wb') as raw:
                with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as zipped:
                    with io.TextIOWrapper(zipped,encoding='utf-8',newline='',write_through=True) as text:
                        w=csv.writer(text);w.writerow(['dateTime_utc','field','original_value_hpa','series_value_hpa','classification','approval_status','method','empirical_uncertainty_hpa','model_sha256','reference_manifest_sha256','era5_manifest_sha256','qc_evidence_sha256','provenance','reason'])
                        while True:
                            batch=c.fetchmany(20000)
                            if not batch:break
                            for ts,units,p in batch:
                                ts=int(ts);rows+=1;candidate=bytime.get(ts)
                                if candidate is not None:candidate_seen.add(ts)
                                if int(units)!=16:raise ValueError(f'unexpected units at {ts}')
                                year=datetime.fromtimestamp(ts,timezone.utc).year;annual[year]['archive_rows']+=1
                                if p is not None:
                                    if candidate and candidate['classification']=='ESTIMATED':stale_collisions+=1
                                    counts['MEASURED']+=1;annual[year]['MEASURED']+=1;w.writerow([ts,'pressure',p,p,'MEASURED','SOURCE_VALUE','existing loucka_reconstruction.archive.pressure','','','','','','archive snapshot: loucka_reconstruction.archive','source record preserved unchanged'])
                                elif candidate and candidate['classification']=='ESTIMATED':
                                    counts['ESTIMATED_UNAPPROVED']+=1;annual[year]['ESTIMATED_UNAPPROVED']+=1;w.writerow([ts,'pressure','',candidate['estimated_value_hpa'],'ESTIMATED','UNAPPROVED',candidate['method'],candidate['empirical_uncertainty_hpa'],candidate['model_sha256'],candidate['reference_manifest_sha256'],candidate['era5_manifest_sha256'],candidate['qc_evidence_sha256'],candidate['provenance'],candidate['reason']])
                                else:
                                    counts['UNRESOLVED']+=1;annual[year]['UNRESOLVED']+=1;w.writerow([ts,'pressure',p or '','','UNRESOLVED','UNAPPROVED','', '', '', '', '',candidate['qc_evidence_sha256'] if candidate else '',candidate['provenance'] if candidate else 'no accepted candidate',candidate['reason'] if candidate else 'source pressure is NULL; no approved replacement'])
        annual_rows=[{'year':y,'archive_rows':c['archive_rows'],'MEASURED':c['MEASURED'],'CALIBRATED':0,'ESTIMATED_UNAPPROVED':c['ESTIMATED_UNAPPROVED'],'UNRESOLVED':c['UNRESOLVED'],'candidate_rows_rejected_by_input_qc':sum(1 for r in candidates if r['classification']=='UNRESOLVED' and datetime.fromtimestamp(r['dateTime_utc'],timezone.utc).year==y)} for y,c in sorted(annual.items())]
        return {'rows':rows,'counts':dict(counts),'annual_status':annual_rows,'candidate_timestamp_collisions':stale_collisions,'candidate_rows_missing_from_archive':len(bytime)-len(candidate_seen),'sha256':sha(path),'file':str(path),'database_identity':{'host':ident[0],'server_id':ident[1],'account':ident[2]}}
    finally:con.rollback();con.close()

def main():
    p=argparse.ArgumentParser();p.add_argument('--cnf',type=Path,required=True);p.add_argument('--v1',type=Path,required=True);p.add_argument('--era5-csv',type=Path,required=True);p.add_argument('--qc-csv',type=Path,required=True);p.add_argument('--validation',type=Path,required=True);p.add_argument('--out-dir',type=Path,required=True);a=p.parse_args()
    validation=json.loads(a.validation.read_text());rows,fields=combine(a.v1,a.era5_csv,a.qc_csv,validation);a.out_dir.mkdir(parents=True,exist_ok=True)
    out=a.out_dir/'pressure-reconstruction-v2-unapproved.csv'
    with out.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    unified=write_unified_series(a.cnf,rows,a.out_dir/'pressure-series-unified-v2.csv.gz')
    if unified['candidate_timestamp_collisions'] or unified['candidate_rows_missing_from_archive']:
        raise RuntimeError('Candidate/archive snapshot mismatch; refusing to finalize unified series')
    (a.out_dir/'annual-status-inventory-v2.json').write_text(json.dumps({'schema':'pressure-series-status-inventory-v2','state':'READ_ONLY_SNAPSHOT_ALL_MODELED_VALUES_UNAPPROVED','database_identity':unified['database_identity'],'unified_series_sha256':unified['sha256'],'years':unified['annual_status']},indent=2,ensure_ascii=False)+'\n')
    methods=Counter((r['method'],r['classification'],r['precision_class']) for r in rows)
    report={'schema':'pressure-reconstruction-v2-artifact-manifest','state':'UNAPPROVED_ONLY','rows':len(rows),'sha256':sha(out),'unified_series':unified,'inputs_sha256':{str(p):sha(p) for p in (a.v1,a.era5_csv,a.qc_csv,a.validation)},'counts_by_method_class_precision':[{'method':k[0],'classification':k[1],'precision_class':k[2],'count':n} for k,n in sorted(methods.items())],'q1_2018_rows':sum(Q1_START<=r['dateTime_utc']<Q1_END for r in rows),'candidate_series_path':str(out)}
    (a.out_dir/'manifest-v2.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
