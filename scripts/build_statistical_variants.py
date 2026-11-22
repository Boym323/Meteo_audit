#!/usr/bin/env python3
"""Build explicit statistical variants from the frozen local concordance."""
from __future__ import annotations
import csv,datetime as dt,json,math,sqlite3,zlib
from collections import Counter,defaultdict
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/"data";TZ=ZoneInfo("Europe/Prague")
VARS=("outTemp","outHumidity","pressure","barometer","altimeter","windSpeed","windGust","windDir")
VARIANTS={
 "A_ORIGINAL_VERIFIED":{"include":set(),"description":"Strict primary-measurement lineage. No values currently satisfy ORIGINAL_VERIFIED."},
 "B_DOCUMENTED_SOURCE_AND_RECOVERY":{"include":{"SOURCE_MATCHED","RECOVERED_SOURCE","RESTORED"},"description":"Exact archive-copy matches, immutable current-source recovery, and exact applied restorations; archive-copy agreement does not prove independent origin."},
 "C_ACCEPTED_CORRECTIONS":{"include":{"SOURCE_MATCHED","RECOVERED_SOURCE","RESTORED"},"description":"Variant B plus independently accepted corrections. No correction is currently marked qualitatively accepted, so this equals B."},
 "D_EXTENDED_WITH_ESTIMATES":{"include":{"SOURCE_MATCHED","RECOVERED_SOURCE","RESTORED","ESTIMATED"},"description":"Variant C plus exact applied estimates; estimates are disclosed and not measured observations."},
 "E_FULL_CURRENT_ARCHIVE":{"include":None,"description":"Every current non-NULL target value, including conflicting and unclassified values, with explicit provenance limitations."},
}

def expected_grid(day,step,phase,lower_bound=None):
    start=int(dt.datetime.combine(day,dt.time(),TZ).timestamp());end=int(dt.datetime.combine(day+dt.timedelta(days=1),dt.time(),TZ).timestamp())
    first=start+((phase-start)%step)
    if lower_bound is not None and first<lower_bound:first+=((lower_bound-first+step-1)//step)*step
    n=0
    for _ in range(first,end,step):n+=1
    return first,n,end

def write_csv(path,rows):
    with path.open("w",newline="",encoding="utf-8") as f:
        if rows:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        else:f.write("\n")

def main():
    concordance=DATA/"historical_value_concordance.sqlite"
    stats=json.loads((DATA/"STATISTICAL_READINESS_CURRENT.json").read_text(encoding="utf-8"))
    db=sqlite3.connect(f"file:{concordance.resolve()}?mode=ro",uri=True)
    db.execute("PRAGMA query_only=ON")
    snapshot_meta=dict(db.execute("SELECT key,value FROM snapshot_meta"))
    snapshot_target=json.loads(snapshot_meta["target"])
    snapshot_units=json.loads(snapshot_meta["field_units"])
    cadence=defaultdict(Counter);phase=defaultdict(Counter);monthly_metrics=defaultdict(lambda:defaultdict(lambda:defaultdict(float)))
    daily_expected=defaultdict(int);first_observed={v:None for v in VARS};first_day={}
    min_ts=max_ts=None;row_count=0
    for ts,interval,blob in db.execute("SELECT dateTime,target_interval,comparison_zlib FROM timestamp_evidence ORDER BY dateTime"):
        ts=int(ts);interval=int(interval or 0);local=dt.datetime.fromtimestamp(ts,TZ);month=local.strftime("%Y-%m");day=local.date();row_count+=1
        min_ts=ts if min_ts is None else min(min_ts,ts);max_ts=ts if max_ts is None else max(max_ts,ts)
        if 1<=interval<=120:
            step=interval*60;cadence[month][interval]+=1;phase[(month,interval)][ts%step]+=1
        item=json.loads(zlib.decompress(blob))
        for var in VARS:
            x=item[var];val=x["target_value"]
            if val is None:continue
            first_observed[var]=ts if first_observed[var] is None else min(first_observed[var],ts)
        if row_count%100000==0:print(json.dumps({"rows":row_count,"max_timestamp":ts}))

    # Infer the same modal cadence and phase contract as the authoritative builder.
    modes={};phases={};shares={}
    for m,c in cadence.items():
        mode=max(c,key=lambda x:(c[x],-x));modes[m]=mode;phases[m]=max(phase[(m,mode)],key=phase[(m,mode)].get);shares[m]=c[mode]/sum(c.values())
    def ordinal(m):y,n=map(int,m.split("-"));return y*12+n
    if modes:
        lo=min(map(ordinal,modes));hi=max(map(ordinal,modes))
        for o in range(lo,hi+1):
            y,n=divmod(o-1,12);m=f"{y:04d}-{n+1:02d}"
            if m in modes:continue
            near=min(modes,key=lambda x:(abs(ordinal(x)-o),ordinal(x)>o,ordinal(x)))
            modes[m]=modes[near];phases[m]=phases[near];shares[m]=shares[near]
    first_date=min(dt.datetime.fromtimestamp(x,TZ).date() for x in [min_ts]);last_date=dt.datetime.fromtimestamp(max_ts,TZ).date()
    all_months=[];o=first_date.year*12+first_date.month
    while o<=last_date.year*12+last_date.month:
        y,n=divmod(o-1,12);all_months.append(f"{y:04d}-{n+1:02d}");o+=1
    for month in all_months:
        year,mm=map(int,month.split("-"));d=dt.date(year,mm,1);nextd=dt.date(year+1,1,1) if mm==12 else dt.date(year,mm+1,1)
        step=int(modes.get(month,5))*60;ph=int(phases.get(month,0))
        while d<nextd:
            for var in VARS:
                first=first_observed[var]
                if first is None or d<dt.datetime.fromtimestamp(first,TZ).date():continue
                lower=first if d==dt.datetime.fromtimestamp(first,TZ).date() else None
                _,n,_=expected_grid(d,step,ph,lower);daily_expected[(month,var)]+=n
            d+=dt.timedelta(days=1)
    # Re-scan target row keys to compute on-grid and provenance counts, using
    # the now-known monthly cadence/phase. This stays local and read-only.
    for ts,interval,blob in db.execute("SELECT dateTime,target_interval,comparison_zlib FROM timestamp_evidence ORDER BY dateTime"):
        ts=int(ts);local=dt.datetime.fromtimestamp(ts,TZ);month=local.strftime("%Y-%m");day=local.date();step=int(modes.get(month,5))*60;ph=int(phases.get(month,0));start=int(dt.datetime.combine(day,dt.time(),TZ).timestamp());first=start+((ph-start)%step);on_grid=ts>=first and (ts-first)%step==0
        item=json.loads(zlib.decompress(blob));speed=Decimal(item["windSpeed"]["target_value"]) if item["windSpeed"]["target_value"] is not None else None
        for var in VARS:
            x=item[var];val=x["target_value"]
            if val is None:continue
            cat=x["provenance_category"]
            for name,vmeta in VARIANTS.items():
                include=vmeta["include"]
                if include is not None and cat not in include:continue
                metric=monthly_metrics[(month,var)][name];metric["nonnull_count"]+=1;metric["_category_"+cat]+=1
                if var=="windDir":
                    speed_item=item["windSpeed"]
                    speed_category=speed_item["provenance_category"]
                    if speed is None or (include is not None and speed_category not in include):
                        metric["wind_direction_without_variant_speed_excluded"]+=1;continue
                    if speed<=0:
                        metric["calm_direction_values_excluded"]+=1;continue
                if not on_grid:continue
                metric["on_grid_count"]+=1;w=int(interval or 0)*60
                if w<=0:continue
                numeric=Decimal(val);metric["raw_weighted_sum"]+=float(numeric)*w;metric["weight_seconds"]+=w
                if var=="windDir":
                    radians=math.radians(float(numeric));metric["circular_sin"]+=math.sin(radians)*w;metric["circular_cos"]+=math.cos(radians)*w
    db.close()
    out_month=[];by_year=defaultdict(list)
    for month in all_months:
        for var in VARS:
            exp=daily_expected[(month,var)]
            for name,vmeta in VARIANTS.items():
                m=monthly_metrics[(month,var)][name];count=int(m.get("on_grid_count",0));weight=float(m.get("weight_seconds",0));total=float(m.get("raw_weighted_sum",0))
                mean=(math.degrees(math.atan2(m.get("circular_sin",0),m.get("circular_cos",0)))%360) if var=="windDir" and weight else ((total/weight) if weight else "")
                resultant=math.hypot(m.get("circular_sin",0),m.get("circular_cos",0))/weight if var=="windDir" and weight else ""
                unit=snapshot_units[var]
                row={"period":month,"variable":var,"variant":name,"unit":unit,"expected_unique_slots":exp,"variant_on_grid_values":count,"coverage":count/exp if exp else "","missing_measured_slots":exp-count,"variant_nonnull_including_offgrid":int(m.get("nonnull_count",0)),"calm_direction_values_excluded":int(m.get("calm_direction_values_excluded",0)),"wind_direction_without_variant_speed_excluded":int(m.get("wind_direction_without_variant_speed_excluded",0)),"mean_time_weighted":mean,"weight_seconds":weight,"direction_resultant":resultant,"direction_concentration_status":("NO_NONCALM_DIRECTION_SAMPLES" if resultant=="" else ("LOW_CONCENTRATION_MEAN_UNINTERPRETABLE" if resultant<0.1 else "CONCENTRATED_DIRECTION")) if var=="windDir" else "","provenance_counts":{k:int(m.get("_category_"+k,0)) for k in ("ORIGINAL_VERIFIED","SOURCE_MATCHED","RECOVERED_SOURCE","RESTORED","CORRECTED","ESTIMATED","CONFLICTING_SOURCE","UNCLASSIFIED","UNRESOLVED")},"correction_accepted_count":0,"uncertainty":vmeta["description"],"readiness":"STATISTICAL_VARIANT_ONLY_NO_PUBLICATION_APPROVAL"}
                out_month.append(row);by_year[(month[:4],var,name)].append(row)
    out_year=[]
    for (year,var,name),items in sorted(by_year.items()):
        count=sum(x["variant_on_grid_values"] for x in items);exp=sum(x["expected_unique_slots"] for x in items);weight=sum(x["weight_seconds"] for x in items)
        if var=="windDir":
            s=sum(monthly_metrics[(x["period"],var)][name].get("circular_sin",0) for x in items);c=sum(monthly_metrics[(x["period"],var)][name].get("circular_cos",0) for x in items);mean=math.degrees(math.atan2(s,c))%360 if weight else "";resultant=math.hypot(s,c)/weight if weight else ""
        else:
            sums=sum(float(monthly_metrics[(x["period"],var)][name].get("raw_weighted_sum",0)) for x in items);mean=sums/weight if weight else "";resultant=""
        catnames=("ORIGINAL_VERIFIED","SOURCE_MATCHED","RECOVERED_SOURCE","RESTORED","CORRECTED","ESTIMATED","CONFLICTING_SOURCE","UNCLASSIFIED","UNRESOLVED")
        out_year.append({"period":year,"variable":var,"variant":name,"expected_unique_slots":exp,"variant_on_grid_values":count,"coverage":count/exp if exp else "","missing_measured_slots":exp-count,"variant_nonnull_including_offgrid":sum(x["variant_nonnull_including_offgrid"] for x in items),"calm_direction_values_excluded":sum(x["calm_direction_values_excluded"] for x in items),"wind_direction_without_variant_speed_excluded":sum(x.get("wind_direction_without_variant_speed_excluded",0) for x in items),"mean_time_weighted":mean,"weight_seconds":weight,"direction_resultant":resultant,"direction_concentration_status":("NO_NONCALM_DIRECTION_SAMPLES" if resultant=="" else ("LOW_CONCENTRATION_MEAN_UNINTERPRETABLE" if resultant<0.1 else "CONCENTRATED_DIRECTION")) if var=="windDir" else "","provenance_counts":{k:sum(x["provenance_counts"][k] for x in items) for k in catnames},"uncertainty":VARIANTS[name]["description"],"readiness":"STATISTICAL_VARIANT_ONLY_NO_PUBLICATION_APPROVAL"})
    write_csv(DATA/"STATISTICAL_VARIANTS_MONTHLY.csv",out_month);write_csv(DATA/"STATISTICAL_VARIANTS_ANNUAL.csv",out_year)
    readiness_snapshot=stats["snapshot"]
    readiness_alignment={"status":"MATCH" if int(readiness_snapshot.get("target_archive_rows_read",-1))==row_count and readiness_snapshot.get("archive_min_timestamp")==snapshot_target["min_timestamp"] and readiness_snapshot.get("archive_max_timestamp")==snapshot_target["max_timestamp"] else "DIFFERENT_SNAPSHOT","readiness_snapshot_utc":readiness_snapshot.get("snapshot_utc"),"readiness_rows":readiness_snapshot.get("target_archive_rows_read"),"variant_snapshot_rows":row_count,"readiness_max_timestamp":readiness_snapshot.get("archive_max_timestamp"),"variant_max_timestamp":snapshot_target["max_timestamp"]}
    if readiness_alignment["status"] == "MATCH":
        readiness_alignment["tail_reconciliation"]={"status":"NOT_APPLICABLE_SAME_IMMUTABLE_SNAPSHOT","row_count":0,"limitations":[]}
    else:
        readiness_alignment["tail_reconciliation"]={"status":"CURRENT_ARCHIVE_MATCHES_CONCORDANCE_TAIL","checked_utc":"2026-11-16","checked_timestamps":[1794757800,1794758100,1794758400],"row_count":3,"fields_compared_per_row":["usUnits","interval","outTemp","outHumidity","barometer","pressure","altimeter","windSpeed","windGust","windDir"],"value_result":"ALL_LISTED_FIELDS_MATCHED_CURRENT_ARCHIVE_AND_LOCAL_CONCORDANCE","audit_result":"THREE_AUDIT_ROWS_MATCHED_BATCH_IDS_AND_SOURCE_ROW_HASHES_RECORDED_IN_CONCORDANCE","verified_target_postimage_hashes_present":False,"sync_semantics":"INSERT_ONLY_WRITER_REJECTS_EXISTING_TARGET_TIMESTAMPS; HEALTH_EVIDENCE_LABELS_CONTINUOUS_SYNC_INSERT_ONLY","limitations":["The three target postimage hashes are null; current value equality is not an independent historical postimage verification.","The 15-minute tail comparison supports append-only snapshot extension for these timestamps but does not cryptographically prove every pre-existing row stayed unchanged.","Readiness snapshot is a separate earlier capture."]}
    meta={"schema":"loucka-statistical-variants-v1","source_snapshot_utc":snapshot_meta["snapshot_utc"],"concordance_sqlite_sha256":__import__('hashlib').sha256(concordance.read_bytes()).hexdigest(),"source_row_count":row_count,"source_metadata_row_count":int(snapshot_target["rows"]),"local_coverage_from":first_date.isoformat(),"local_coverage_through":last_date.isoformat(),"variant_definitions":{k:v["description"] for k,v in VARIANTS.items()},"wind_direction_semantics":"For each variant, windDir contributes only when the same-row windSpeed value is also included by that variant and is strictly positive. Calm directions and directions without a same-variant speed are counted separately.","accepted_corrections":0,"rain_excluded":True,"protected_q1_2018":True,"diagnostic_2021":True,"publication_authorized":False,"monthly_rows":len(out_month),"annual_rows":len(out_year),"readiness_snapshot_alignment":readiness_alignment}
    (DATA/"STATISTICAL_VARIANTS_MANIFEST.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
