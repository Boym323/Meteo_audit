#!/usr/bin/env python3
"""Time-blocked ERA5/CHMI/local pressure model audit; no writes to SQL."""
from __future__ import annotations
import argparse, configparser, csv, hashlib, json, math, statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from validate_pressure_station_field import STATIONS, metrics, transport_station_pressure

G,RD=9.80665,287.05
SITE_HEIGHT=425.0
CHMI_IDS={"H":"0-20000-0-11774","M":"0-20000-0-11782"}
START=int(datetime(2018,1,1,tzinfo=timezone.utc).timestamp())
END=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp())
Q1_2018_START=int(datetime(2018,1,1,tzinfo=timezone.utc).timestamp())
Q1_2018_END=int(datetime(2018,4,1,tzinfo=timezone.utc).timestamp())


def load_era5(folder):
    manifest=json.loads((folder/"manifest.json").read_text())
    bypoint={k:{} for k in manifest["points"]}; elevations={}
    for rec in manifest["responses"]:
        path=folder/rec["file"]
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=rec["sha256"]: raise ValueError("ERA5 SHA mismatch: "+rec["file"])
        obj=json.loads(raw); point=Path(rec["file"]).stem.rsplit("-",1)[0]
        elevations[point]=float(obj["elevation"])
        h=obj["hourly"]
        for i,stamp in enumerate(h["time"]):
            ts=int(datetime.strptime(stamp,"%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc).timestamp())
            bypoint[point][ts]=(h["pressure_msl"][i],h["surface_pressure"][i],h["temperature_2m"][i])
    return bypoint,elevations,manifest


def load_chmi(cache):
    manifest=json.loads((cache/"manifest.json").read_text()); refs=defaultdict(dict);files=0
    for item in manifest["items"]:
        if item.get("availability")!="available" or item.get("kind")!="hourly_csv" or item.get("element") not in ("P","P_hm") or item.get("station_id") not in CHMI_IDS.values(): continue
        f=cache/"raw"/item["path"];raw=f.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=item["sha256"]:raise ValueError("CHMI SHA mismatch: "+item["path"])
        files+=1
        with f.open(encoding="utf-8-sig",newline="") as stream:
            for r in csv.DictReader(stream):
                if r["STATION"]!=item["station_id"] or r["ELEMENT"]!=item["element"]:raise ValueError("CHMI reference mismatch")
                if r["QUALITY"] not in ("0","0.0") or not r["VALUE"]:continue
                ts=int(datetime.fromisoformat(r["DT"].replace("Z","+00:00")).timestamp())
                refs[(r["STATION"],r["ELEMENT"])][ts]=float(r["VALUE"])
    return refs,{"manifest_sha256":hashlib.sha256((cache/"manifest.json").read_bytes()).hexdigest(),"sha256_files_verified":files}


def read_local(cnf, db, start, end, missing_only=False):
    import pymysql
    from pymysql.cursors import DictCursor
    cfg=configparser.ConfigParser(interpolation=None)
    if not cfg.read(cnf) or cfg.get("client","user",fallback="")!="loucka_web_ro":raise PermissionError("Use existing read-only account")
    conn=pymysql.connect(read_default_file=str(cnf),read_default_group="client",database="loucka_reconstruction",cursorclass=DictCursor,autocommit=False,connect_timeout=15,read_timeout=180)
    try:
        with conn.cursor() as c:
            c.execute("START TRANSACTION READ ONLY")
            c.execute("SELECT @@hostname host,@@server_id server_id,CURRENT_USER() account")
            ident=c.fetchone()
            if (ident["host"],int(ident["server_id"]),ident["account"])!=("lo-infra-db-mariadb01",1,"loucka_web_ro@192.168.0.131"):raise RuntimeError("Unexpected SQL server")
            missing=" AND pressure IS NULL" if missing_only else ""
            c.execute(f"""SELECT dateTime,usUnits,pressure,barometer,outTemp FROM `{db}`.`archive`
                        WHERE dateTime >= %s AND dateTime < %s AND MOD(dateTime,3600)=0 {missing}
                        ORDER BY dateTime""",(start,end))
            rows=c.fetchall()
            if any(int(r["usUnits"])!=16 for r in rows):raise ValueError("Unexpected local usUnits")
            return rows,ident
    finally:conn.rollback();conn.close()


def q95(xs):
    if not xs:return None
    a=sorted(xs);x=(len(a)-1)*.95;i=int(x);return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(x-i)


def era5_base(ts,era,lou_elev):
    v=era.get(ts)
    if v is None or v[1] is None or v[2] is None:return None
    # Reanalysis grid surface pressure -> Loucka 425 m, with ERA5 grid 2m T proxy.
    return v[1]*math.exp(G*(lou_elev-SITE_HEIGHT)/(RD*(v[2]+273.15)))


def v1_predict(row,model):
    b,t=row["barometer"],row["outTemp"]
    if b is None or t is None:return None
    d=model["training_domain"]
    if not(d["barometer_hpa"][0]<=float(b)<=d["barometer_hpa"][1] and d["outTemp_c"][0]<=float(t)<=d["outTemp_c"][1]):return None
    p=model["parameters"]
    raw=float(b)*math.exp(-G*SITE_HEIGHT/(RD*(float(t)+273.15)))
    return raw+p["offset_hpa"]+p["temperature_slope_hpa_per_c"]*(float(t)-p["temperature_center_c"])


def model_scores(rows,era,era_elev,v1,offset,refs,gate,flagged,month_filter=None):
    stats=defaultdict(lambda:{"n_eligible":0,"n_common":0,"errors":defaultdict(list)})
    preds=[]
    for row in rows:
        ts=int(row["dateTime"]);dt=datetime.fromtimestamp(ts,timezone.utc);ym=dt.strftime("%Y-%m")
        if month_filter is not None and ym not in month_filter:continue
        pred_era=era5_base(ts,era,era_elev)
        pred_v1=v1_predict(row,v1)
        if pred_era is None:continue
        # ERA5 is its own model variant. The blend and local V1 are fixed definitions.
        cand={"era5_surface":pred_era,"era5_bias_corrected":pred_era+offset}
        if pred_v1 is not None and ts not in flagged:
            cand["v1_frozen_temp"]=pred_v1
            cand["blend_50"]=0.5*(pred_v1+pred_era)
        s=stats[ym];s["n_eligible"]+=1
        if any((ts in refs[(sid,"P")]) is False for sid in CHMI_IDS.values()):continue
        s["n_common"]+=1
        for name,pred in cand.items():
            temp=row["outTemp"]
            if temp is None: temp=era[ts][2]
            for key,sid in CHMI_IDS.items():
                h=STATIONS[key][1]
                err=transport_station_pressure(pred,float(temp),h)-refs[(sid,"P")][ts]
                s["errors"][name+key].append(err)
        preds.append((row,cand))
    result={}
    for ym,s in sorted(stats.items()):
        coverage=s["n_common"]/s["n_eligible"] if s["n_eligible"] else 0
        result[ym]={"eligible_exact_missing_hours":s["n_eligible"],"common_dual_station_hours":s["n_common"],"common_coverage":coverage,"models":{}}
        for name in ("era5_surface","era5_bias_corrected","v1_frozen_temp","blend_50"):
            scores={k:metrics(s["errors"][name+k]) for k in ("H","M")}
            # Keep the fixed PR97 gate; evidence must exist at both stations.
            passes=(s["n_common"]>=gate["min_common_hours_per_month"] and coverage>=gate["min_common_coverage"] and all(x["mae_hpa"] is not None and x["mae_hpa"]<=gate["max_mae_hpa"] and x["p95_abs_error_hpa"]<=gate["max_p95_absolute_hpa"] and abs(x["median_bias_hpa"])<=gate["max_abs_median_bias_hpa"] for x in scores.values()))
            result[ym]["models"][name]={"scores":scores,"gate":"PASS_DIAGNOSTIC_PREVIEW_ONLY" if passes else "FAIL_OR_INSUFFICIENT"}
    return result,preds


def regional_loo_scores(rows,era,refs,gate):
    """Transfer pressure from the other station; target station is never an input."""
    heights={"H":222.25,"M":252.8}
    stats=defaultdict(lambda:{"eligible":0,"common":0,"errors":{"H":[],"M":[]}})
    for row in rows:
        ts=int(row["dateTime"]);ym=datetime.fromtimestamp(ts,timezone.utc).strftime("%Y-%m")
        temps={k:era["holesov_era5" if k=="H" else "mosnov_era5"].get(ts,(None,None,None))[2] for k in ("H","M")}
        if any(t is None for t in temps.values()): continue
        s=stats[ym];s["eligible"]+=1
        if any(ts not in refs[(CHMI_IDS[k],"P")] for k in ("H","M")): continue
        s["common"]+=1
        for target,source in (("H","M"),("M","H")):
            source_p=refs[(CHMI_IDS[source],"P")][ts]
            pred=source_p*math.exp(G*(heights[source]-heights[target])/(RD*(temps[target]+273.15)))
            s["errors"][target].append(pred-refs[(CHMI_IDS[target],"P")][ts])
    out={}
    for ym,s in sorted(stats.items()):
        coverage=s["common"]/s["eligible"] if s["eligible"] else 0
        scores={k:metrics(s["errors"][k]) for k in ("H","M")}
        passed=(s["common"]>=gate["min_common_hours_per_month"] and coverage>=gate["min_common_coverage"] and all(m["mae_hpa"] is not None and m["mae_hpa"]<=gate["max_mae_hpa"] and m["p95_abs_error_hpa"]<=gate["max_p95_absolute_hpa"] and abs(m["median_bias_hpa"])<=gate["max_abs_median_bias_hpa"] for m in scores.values()))
        out[ym]={"eligible_exact_missing_hours":s["eligible"],"common_dual_station_hours":s["common"],"common_coverage":coverage,"scores":scores,"gate":"PASS_DIAGNOSTIC_PREVIEW_ONLY" if passed else "FAIL_OR_INSUFFICIENT"}
    return out


def regional_loucka_prediction(ts,refs,era):
    """Average the two measured station pressures after transfer to Loučka 425 m."""
    values=[]
    for key in ("H","M"):
        station_pressure=refs[(CHMI_IDS[key],"P")].get(ts)
        point="holesov_era5" if key=="H" else "mosnov_era5";v=era[point].get(ts)
        if station_pressure is None or v is None or v[2] is None:return None
        values.append(transport_station_pressure(station_pressure,v[2],SITE_HEIGHT,STATIONS[key][1]))
    return statistics.fmean(values)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--cnf",required=True,type=Path);ap.add_argument("--era5-dir",required=True,type=Path);ap.add_argument("--chmi-cache",required=True,type=Path);ap.add_argument("--model",type=Path,default=ROOT/"models/pressure-shadow-2022-v1.json");ap.add_argument("--qc",required=True,type=Path);ap.add_argument("--out-dir",required=True,type=Path)
    a=ap.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    era,elev,era_manifest=load_era5(a.era5_dir);refs,chmi_meta=load_chmi(a.chmi_cache);v1=json.loads(a.model.read_text());gate=v1["preview"]["gate"]
    qc=json.loads(a.qc.read_text());flagrows=[]
    for db in ("pocasi-loucka.eu","loucka_reconstruction"):
        path=a.qc.parent/(db.replace(".","_")+"-suspected-spikes.csv")
        with path.open() as f:flagrows.extend(csv.DictReader(f))
    flagged={int(r["dateTime_utc"]) for r in flagrows}
    # Fit a single ERA5->local-pressure residual offset only on measured 2019-2020 rows.
    tr0=int(datetime(2019,1,1,tzinfo=timezone.utc).timestamp());tr1=int(datetime(2021,1,1,tzinfo=timezone.utc).timestamp())
    train,ident=read_local(a.cnf,"pocasi-loucka.eu",tr0,tr1)
    residuals=[]
    for r in train:
        if r["pressure"] is None or r["outTemp"] is None:continue
        base=era5_base(int(r["dateTime"]),era["loucka_era5_nearest"],elev["loucka_era5_nearest"])
        if base is not None:residuals.append(float(r["pressure"])-base)
    if not residuals:raise RuntimeError("No ERA5/local 2019-2020 training pairs")
    offset=statistics.median(residuals)
    # Chronological external validation: missing exact hours in 2021 select one fixed model family.
    v0=int(datetime(2021,1,1,tzinfo=timezone.utc).timestamp());v1end=int(datetime(2022,1,1,tzinfo=timezone.utc).timestamp())
    validation,_=read_local(a.cnf,"loucka_reconstruction",v0,v1end,missing_only=True)
    validation_scores,_=model_scores(validation,era["loucka_era5_nearest"],elev["loucka_era5_nearest"],v1,offset,refs,gate,flagged)
    validation_chmi_loo=regional_loo_scores(validation,era,refs,gate)
    for ym,d in validation_chmi_loo.items():
        if ym in validation_scores: validation_scores[ym]["models"]["chmi_regional_loo"]={"scores":d["scores"],"gate":d["gate"]}
    modelnames=("era5_surface","era5_bias_corrected","v1_frozen_temp","blend_50","chmi_regional_loo")
    def rank(name):
        passed=sum(m["models"][name]["gate"]=="PASS_DIAGNOSTIC_PREVIEW_ONLY" for m in validation_scores.values())
        errs=[x["mae_hpa"] for m in validation_scores.values() for x in m["models"][name]["scores"].values() if x["mae_hpa"] is not None]
        return (passed,-statistics.fmean(errs) if errs else -999)
    selected=max(modelnames,key=rank)
    # Untouched chronological block: missing pressure hours in Jan-Jul 2022.
    t0=int(datetime(2022,1,1,tzinfo=timezone.utc).timestamp());t1=int(datetime(2022,8,1,tzinfo=timezone.utc).timestamp())
    test,ident=read_local(a.cnf,"loucka_reconstruction",t0,t1,missing_only=True)
    test_scores,test_preds=model_scores(test,era["loucka_era5_nearest"],elev["loucka_era5_nearest"],v1,offset,refs,gate,flagged)
    test_chmi_loo=regional_loo_scores(test,era,refs,gate)
    for ym,d in test_chmi_loo.items():
        if ym in test_scores: test_scores[ym]["models"]["chmi_regional_loo"]={"scores":d["scores"],"gate":d["gate"]}
    # Independent reanalysis validation against complete quality-zero CHMI hours, split by year.
    station_scores=defaultdict(lambda:defaultdict(list));mslp_scores=defaultdict(lambda:defaultdict(list))
    station_heights={"H":222.25,"M":252.8}
    for key,sid in CHMI_IDS.items():
        point="holesov_era5" if key=="H" else "mosnov_era5"; refp=refs[(sid,"P")];refm=refs[(sid,"P_hm")]
        for ts,pref in refp.items():
            if not START<=ts<END:continue
            d=datetime.fromtimestamp(ts,timezone.utc);yr=str(d.year);v=era[point].get(ts)
            if not v or v[1] is None or v[2] is None:continue
            p_station=transport_station_pressure(v[1],v[2],station_heights[key],elev[point])
            station_scores[yr][key].append(p_station-pref)
            if ts in refm:mslp_scores[yr][key].append(float(v[0])-refm[ts])
    chmi_results={}
    for yr in sorted(station_scores):chmi_results[yr]={"station_pressure_surface_vs_CHMI_P":{k:metrics(v) for k,v in station_scores[yr].items()},"sea_level_pressure_vs_CHMI_P_hm":{k:metrics(v) for k,v in mslp_scores[yr].items()}}
    # ERA5 grid sensitivity at Loucka, not an uncertainty bound.
    sensitivity={}
    for yr in ("2018","2019","2020","2021","2022","2023","2024"):
        diffs=[]
        for ts,v in era["loucka_era5_nearest"].items():
            if datetime.fromtimestamp(ts,timezone.utc).strftime("%Y")==yr and ts in era["loucka_era5_adjacent"]:
                w=era["loucka_era5_adjacent"][ts]
                if v[1] is not None and w[1] is not None:diffs.append(v[1]-w[1])
        sensitivity[yr]=metrics(diffs)
    # Save an hourly-only candidate file only for the frozen model selected in 2021 and months passing 2022 test.
    candidate_path=a.out_dir/"era5-hourly-estimates-unapproved.csv";fields=["dateTime_utc","field","original_value","estimated_value_hpa","classification","approval_status","method","source_model","reference_manifest_sha256","era5_manifest_sha256","barometer_qc","uncertainty_note","reason"]
    with candidate_path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();count=0
        for row,cands in test_preds:
            ts=int(row["dateTime"]);ym=datetime.fromtimestamp(ts,timezone.utc).strftime("%Y-%m");gate_row=test_scores.get(ym,{}).get("models",{}).get(selected,{})
            if Q1_2018_START <= ts < Q1_2018_END: continue
            if gate_row.get("gate")!="PASS_DIAGNOSTIC_PREVIEW_ONLY":continue
            if ts not in refs[(CHMI_IDS["H"],"P")] or ts not in refs[(CHMI_IDS["M"],"P")]:continue
            p=regional_loucka_prediction(ts,refs,era) if selected=="chmi_regional_loo" else cands.get(selected)
            if p is None:continue
            absolute_errors=[]
            for month in validation_scores.values():
                for station in ("H","M"):
                    metric=month["models"][selected]["scores"][station]
                    if metric["p95_abs_error_hpa"] is not None: absolute_errors.append(metric["p95_abs_error_hpa"])
            empirical_p95=max(absolute_errors) if absolute_errors else None
            w.writerow({"dateTime_utc":ts,"field":"pressure","original_value":"","estimated_value_hpa":f"{p:.4f}","classification":"ESTIMATED","approval_status":"UNAPPROVED","method":selected,"source_model":"ERA5 hourly surface pressure + 2021-selected model; no sub-hour interpolation","reference_manifest_sha256":chmi_meta["manifest_sha256"],"era5_manifest_sha256":hashlib.sha256((a.era5_dir/"manifest.json").read_bytes()).hexdigest(),"barometer_qc":"local-input variants exclude flagged values; ERA5-only model does not use barometer","uncertainty_note":f"2021 validation max monthly station P95 absolute error: {empirical_p95} hPa; empirical group uncertainty, not per-row interval","reason":"hourly only; regional diagnostic gate passed; does not validate 5-minute values"});count+=1
    result={"schema":"pressure-reanalysis-validation-v2","state":"READ_ONLY_DIAGNOSTIC_UNAPPROVED_ONLY","database_identity":ident,"periods":{"training":"2019-01-01/2021-01-01 measured local pressure; fit median ERA5 residual offset for comparison only","model_selection":"2021 missing exact UTC hours; regional transfer scored reciprocal leave-one-station-out","untouched_test":"2022-01-01/2022-08-01 missing exact UTC hours"},"era5_manifest_sha256":hashlib.sha256((a.era5_dir/"manifest.json").read_bytes()).hexdigest(),"chmi":chmi_meta,"era5_grid_elevations_m":elev,"local_training_rows":len(train),"training_valid_pairs":len(residuals),"era5_bias_correction_median_hpa":offset,"validation_selected_model":selected,"validation_monthly":validation_scores,"validation_chmi_leave_one_out_monthly":validation_chmi_loo,"test_chmi_leave_one_out_monthly":test_chmi_loo,"test_monthly":test_scores,"test_hourly_unapproved_rows":count,"station_year_scores":chmi_results,"loucka_adjacent_era5_grid_sensitivity_hpa":sensitivity,"limitations":["ERA5 is a gridded reanalysis with assimilated observations, not an independent point sensor.","ERA5 hourly values are never interpolated or presented as 5-minute observations.","ERA5-Land hourly surface-pressure series could not be retrieved from the public API; CDS ARCO requires a CDS token.","Model-height transport uses dry-air hypsometric relation and ERA5 2m temperature proxy.","All created candidate values are separate ESTIMATED/UNAPPROVED rows."]}
    (a.out_dir/"pressure-reanalysis-validation-v2.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":"READ_ONLY_DONE","selected_model":selected,"training_offset_hpa":offset,"validation_months":len(validation_scores),"test_months":len(test_scores),"new_hourly_unapproved_rows":count,"report":str(a.out_dir/"pressure-reanalysis-validation-v2.json")}))

if __name__=="__main__":main()
