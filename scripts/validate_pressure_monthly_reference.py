#!/usr/bin/env python3
"""Compare 2026 pressure fields to official CHMI hourly SYNOP P_hm context."""
from __future__ import annotations
import hashlib,json,math,sqlite3,statistics,zlib
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1];DB=ROOT/'data/historical_value_concordance.sqlite'
MANIFEST=ROOT/'data/chmi-2026-synop-pressure/manifest.json';TZ=ZoneInfo('Europe/Prague');STEP=3600

def bounds(period):
    y,m=map(int,period.split('-'));lo=int(datetime(y,m,1,tzinfo=TZ).timestamp());y,m=(y+1,1) if m==12 else (y,m+1)
    return lo,int(datetime(y,m,1,tzinfo=TZ).timestamp())

def quantile(xs,q):
    if not xs:return None
    ys=sorted(xs);p=(len(ys)-1)*q;i=int(p);j=min(i+1,len(ys)-1)
    return ys[i]+(ys[j]-ys[i])*(p-i)

def main():
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'));candidate_doc=json.loads((ROOT/'MONTHLY_PUBLICATION_CANDIDATES.json').read_text())
    candidates={(r['period'],r['variable']):r for r in candidate_doc['candidates']}
    by_period={r['period']:r for r in manifest['files']};db=sqlite3.connect(f'file:{DB.resolve()}?mode=ro',uri=True);results=[]
    for period in ('2026-01','2026-02'):
        lo,hi=bounds(period);expected=set(range(((lo//STEP)+1)*STEP,hi+1,STEP));item=by_period[period]
        raw=json.loads((ROOT/item['path']).read_text(encoding='utf-8'));ref_all={};qc=Counter();flags=Counter()
        for sid,element,stamp,value,flag,quality in raw['data']['data']['values']:
            if sid!=item['station']['station_id'] or element!='P_hm':continue
            try:ts=int(datetime.fromisoformat(stamp.replace('Z','+00:00')).timestamp());v=float(value)
            except (ValueError,TypeError):continue
            q=str(quality);qc[q]+=1;flags[str(flag or '')]+=1
            if ts in expected:ref_all[ts]={'value':v,'quality':q,'flag':str(flag or '')}
        valid={ts:r['value'] for ts,r in ref_all.items() if r['quality'] in ('0','0.0') and math.isfinite(r['value'])}
        local={}
        for ts,blob in db.execute('SELECT dateTime,comparison_zlib FROM timestamp_evidence WHERE dateTime>? AND dateTime<=? ORDER BY dateTime',(lo,hi)):
            x=json.loads(zlib.decompress(blob));local[int(ts)]={k:(float(x[k]['target_value']) if x.get(k,{}).get('target_value') is not None else None) for k in ('barometer','pressure','altimeter')}
        paired={field:[] for field in ('barometer','pressure','altimeter')}
        for ts,rv in sorted(valid.items()):
            if ts not in local:continue
            for field in paired:
                value=local[ts].get(field)
                if value is not None:paired[field].append((ts,value,rv))
        field_metrics={}
        for field,pairs in paired.items():
            n=len(pairs);lx=[x[1] for x in pairs];rx=[x[2] for x in pairs];diff=[r-l for l,r in zip(lx,rx)]
            if n:
                bias=statistics.mean(diff);mae=statistics.mean(abs(x) for x in diff);rmse=math.sqrt(statistics.mean(x*x for x in diff));mx,my=statistics.mean(lx),statistics.mean(rx)
                den=math.sqrt(sum((x-mx)**2 for x in lx)*sum((y-my)**2 for y in rx));corr=sum((x-mx)*(y-my) for x,y in zip(lx,rx))/den if den else None
            else:bias=mae=rmse=corr=None
            field_metrics[field]={'paired_timestamp_count':n,'matched_coverage_of_valid_reference':n/len(valid) if valid else 0.0,'loucka_hourly_archive_sample_mean_hpa':statistics.mean(lx) if n else None,'chmi_p_hm_paired_mean_hpa':statistics.mean(rx) if n else None,'chmi_minus_loucka_bias_hpa':bias,'mae_hpa':mae,'rmse_hpa':rmse,'correlation':corr,'difference_quantiles_hpa':{'p05':quantile(diff,.05),'p50':quantile(diff,.5),'p95':quantile(diff,.95)}}
        bp=[r-l for _,b,r in paired['barometer'] for l in [b]]
        altminusbar=[local[ts]['altimeter']-local[ts]['barometer'] for ts,_,_ in paired['barometer'] if local[ts]['altimeter'] is not None]
        bar=field_metrics['barometer']
        results.append({'period':period,'station_id':item['station']['station_id'],'reference_station':item['station'],'reference_file':{'path':item['path'],'source_url':item['source_url'],'sha256':item['sha256']},
            'matched_pairs':bar['paired_timestamp_count'],'matched_coverage_of_valid_reference':bar['matched_coverage_of_valid_reference'],'bias_reference_minus_loucka_hPa':bar['chmi_minus_loucka_bias_hpa'],'mae_hPa':bar['mae_hpa'],'rmse_hPa':bar['rmse_hpa'],'correlation':bar['correlation'],'unit':'hPa',
            'expected_hourly_utc_slots_in_local_civil_month':len(expected),'reference_rows_in_expected_range':len(ref_all),'valid_p_hm_slots':len(valid),'quality_counts_all_file':dict(qc),'quality_counts_in_period':dict(Counter(r['quality'] for r in ref_all.values())),'flag_counts_all_file':dict(flags),
            'monthly_barometer_candidate_mean_hpa':candidates.get((period,'barometer'),{}).get('value'),'timestamp_coincident_field_metrics_vs_chmi_p_hm':field_metrics,
            'coincident_archive_field_offsets_hpa':{'barometer_minus_pressure_median':statistics.median(local[ts]['barometer']-local[ts]['pressure'] for ts,_,_ in paired['barometer'] if local[ts]['pressure'] is not None) if any(local[ts]['pressure'] is not None for ts,_,_ in paired['barometer']) else None,'altimeter_minus_barometer_median':statistics.median(altminusbar) if altminusbar else None},
            'time_method':'Only identical UTC hourly timestamps are paired. CHMI P_hm is a one-hour SYNOP record; WeeWX values are archive records at the same timestamps. Equal timestamps do not establish equal measurement functions or averaging windows.',
            'interpretation':'Regional pressure plausibility only. P_hm is sea-level-reduced reference pressure; this is a potential comparator for local barometer only if that field has the corresponding semantics, which are not established. Site separation, Loucka sensor elevation and local configuration remain unresolved.'})
    db.close()
    out={'schema':'loucka-monthly-pressure-reference-validation-v1','snapshot_id':hashlib.sha256(DB.read_bytes()).hexdigest(),'reference_manifest_sha256':hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),'source_documentation_urls':['https://opendata.chmi.cz/meteorology/climate/Klimatologicka_data_popis.pdf','https://data.gov.cz/dataset?iri=https%3A%2F%2Fdata.gov.cz%2Fzdroj%2Fdatov%C3%A9-sady%2F00020699%2Ff851e0fbe050a4d841a587e69efef918'],'license':'CC BY 4.0 per the National Data Catalog; attribution to ČHMÚ.','station_month_results':results,
         'method_limits':['CHMI Holešov station metadata states 49.320556 N, 17.570000 E, 222.25 m; the Loucka sensor coordinates/elevation are not verified, so no distance/elevation correction is inferred.','CHMI P_hm is a sea-level-reduced pressure code from hourly SYNOP data; it is not assumed equivalent to WeeWX pressure, barometer or altimeter without local configuration evidence.','Only CHMI quality code 0 is used in paired statistics; quality and flag counts are retained.','No pressure field is relabeled, substituted or corrected.']}
    (ROOT/'MONTHLY_PRESSURE_REFERENCE_VALIDATION.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'station_month_results':len(results),'valid_reference_slots':[r['valid_p_hm_slots'] for r in results],'barometer_pairs':[r['timestamp_coincident_field_metrics_vs_chmi_p_hm']['barometer']['paired_timestamp_count'] for r in results]},indent=2))

if __name__=='__main__':main()
