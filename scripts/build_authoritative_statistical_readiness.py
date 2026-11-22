#!/usr/bin/env python3
"""Build current local statistical-readiness tables from a read-only DB snapshot.

The denominator is the actual unique local-civil expected slot grid inferred
from the observed monthly archive cadence and epoch phase. Off-grid rows are
kept as a separate count and never inflate coverage.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import math
import os
import tempfile
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import pymysql
    from pymysql.cursors import SSCursor
except ImportError:  # Concordance snapshot mode has no MariaDB dependency.
    pymysql=None
    SSCursor=None

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Europe/Prague")
VARS = ("outTemp", "outHumidity", "windSpeed", "windGust", "windDir", "barometer", "pressure", "altimeter")
UNITS = {"outTemp":"degC", "outHumidity":"percent", "windSpeed":"km_per_hour", "windGust":"km_per_hour", "windDir":"degrees_from_north", "barometer":"hPa", "pressure":"hPa", "altimeter":"hPa"}
MEAS_FIELDS = set(VARS)


def connect_readonly():
    snapshot_path = os.environ.get("METEO_AUDIT_CONCORDANCE_READONLY")
    if snapshot_path:
        import sys
        sys.path.insert(0, str(ROOT / "src"))
        from meteo_audit.readiness_snapshot_adapter import ConcordanceReadOnlyConnection
        return ConcordanceReadOnlyConnection(snapshot_path)
    if pymysql is None:
        raise RuntimeError("PyMySQL is required only for live read-only database mode")
    required = ("TARGET_DB_HOST", "TARGET_DB_PORT", "TARGET_DB_USER", "TARGET_DB_PASSWORD")
    missing = [x for x in required if not os.environ.get(x)]
    if missing:
        raise RuntimeError("missing protected database environment settings: " + ", ".join(missing))
    c = pymysql.connect(host=os.environ["TARGET_DB_HOST"], port=int(os.environ["TARGET_DB_PORT"]),
                        user=os.environ["TARGET_DB_USER"], password=os.environ["TARGET_DB_PASSWORD"],
                        database="loucka_reconstruction", charset="utf8mb4", autocommit=False,
                        cursorclass=SSCursor)
    q = c.cursor(); q.execute("SET SESSION TRANSACTION READ ONLY"); q.close()
    c.begin()
    return c


def local_day(ts: int) -> dt.date:
    return dt.datetime.fromtimestamp(ts, TZ).date()


def expected_grid(day: dt.date, step_seconds: int, phase_seconds: int, lower_bound: int | None = None) -> tuple[int, int, int, int, int]:
    """Return first epoch, expected slots, day slots, night slots, exclusive end."""
    start = int(dt.datetime.combine(day, dt.time(), TZ).timestamp())
    end = int(dt.datetime.combine(day + dt.timedelta(days=1), dt.time(), TZ).timestamp())
    first = start + ((phase_seconds - start) % step_seconds)
    if lower_bound is not None and first < lower_bound:
        first += ((lower_bound-first+step_seconds-1)//step_seconds)*step_seconds
    stamps = range(first, end, step_seconds)
    n = 0; day_n = 0
    for ts in stamps:
        n += 1
        if 6 <= dt.datetime.fromtimestamp(ts, TZ).hour < 18:
            day_n += 1
    return first, n, day_n, n-day_n, end


def classify(ts: int, variable: str, value, verified_source: dict, estimates: dict,
             changes: dict) -> str:
    key = (ts, variable)
    est = estimates.get(key)
    if key in estimates:
        return "ESTIMATED" if value is not None and numeric_equal(value, est) else "UNCLASSIFIED"
    change = changes.get(key)
    if change and value is not None and numeric_equal(value, change["new_value"]):
        return change["class"]
    evidence = verified_source.get(ts)
    if evidence and value is not None and variable in evidence and numeric_equal(value, evidence[variable]):
        return "RECOVERED_SOURCE"
    return "UNCLASSIFIED"


def numeric_equal(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except Exception:
        return a == b


def empty_day():
    return {"raw_nonnull":0,"on_grid":0,"nonestimated":0,"estimated":0,"offgrid":0,
            "day_nonestimated":0,"night_nonestimated":0,"invalid_interval":0,
            "source":0,"restored":0,"corrected":0,"unclassified":0,
            "source_on_grid":0,"restored_on_grid":0,"source_restored":0,"source_restored_mean":0,"source_restored_weight":0,
            "source_mean":0,"source_weight":0,"without_est_mean":0,"without_est_weight":0,
            "all_mean":0,"all_weight":0,"without_est_sin":0,"without_est_cos":0,
            "source_sin":0,"source_cos":0,
            "source_restored_sin":0,"source_restored_cos":0,"all_sin":0,"all_cos":0,
            "dir_weight_current":0,"dir_weight_without_estimates":0,
            "dir_weight_source":0,"dir_weight_source_restored":0,
            "calm_wind_samples":0,
            "min":None,"max":None,"offgrid_min":None,"offgrid_max":None,
            "last_slot":None,"first_slot":None,"max_gap":0,"bucket_counts":Counter()}


def add_value(a, value, weight_seconds, category, ts, slot_index, on_grid, day_hour):
    if value is None:
        return
    a["raw_nonnull"] += 1
    numeric = float(value)
    if slot_index is not None:a["bucket_counts"][slot_index] += 1
    if weight_seconds <= 0:
        a["invalid_interval"] += 1
        return
    if on_grid:
        a["on_grid"] += 1
        if category != "ESTIMATED":
            a["nonestimated"] += 1
            a["day_nonestimated" if 6 <= day_hour < 18 else "night_nonestimated"] += 1
        a["all_mean"] += numeric * weight_seconds; a["all_weight"] += weight_seconds
        a["min"] = numeric if a["min"] is None else min(a["min"], numeric)
        a["max"] = numeric if a["max"] is None else max(a["max"], numeric)
        if category != "ESTIMATED":
            a["without_est_mean"] += numeric * weight_seconds; a["without_est_weight"] += weight_seconds
        if category in {"RECOVERED_SOURCE","RESTORED"}:
            a["source_restored_mean"] += numeric * weight_seconds; a["source_restored_weight"] += weight_seconds
        if category == "RECOVERED_SOURCE":
            a["source_mean"] += numeric * weight_seconds; a["source_weight"] += weight_seconds
        if category == "RECOVERED_SOURCE":a["source_on_grid"]+=1
        if category == "RESTORED":a["restored_on_grid"]+=1
        if category in {"RECOVERED_SOURCE","RESTORED"}:a["source_restored"]+=1
        if a["first_slot"] is None:a["first_slot"] = slot_index
        if a["last_slot"] is not None:a["max_gap"] = max(a["max_gap"],(slot_index-a["last_slot"]))
        a["last_slot"] = slot_index
    else:
        a["offgrid"] += 1
        a["offgrid_min"] = numeric if a["offgrid_min"] is None else min(a["offgrid_min"],numeric)
        a["offgrid_max"] = numeric if a["offgrid_max"] is None else max(a["offgrid_max"],numeric)


def write_csv(path: Path, rows: list[dict]):
    fd, temp_name = tempfile.mkstemp(prefix=path.name+".", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp_path=Path(temp_name)
    try:
        if not rows:
            temp_path.write_text("\n", encoding="utf-8")
        else:
            with temp_path.open("w", newline="", encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        os.replace(temp_path,path)
    finally:
        temp_path.unlink(missing_ok=True)


def main():
    estimate_docs=json.loads((ROOT/"data/applied_estimated_operations.json").read_text(encoding="utf-8"))
    estimates={(int(x["target_time"]),x["variable"]):x.get("new_value") for x in estimate_docs if x.get("state")=="applied"}
    conn=connect_readonly()
    from_concordance = hasattr(conn, "meta") and hasattr(conn, "sha256")
    daily=[]; cadence=defaultdict(Counter); phase=defaultdict(Counter); verified_source=set(); changes={}
    snapshot_id={}
    try:
        q=conn.cursor();q.execute("SELECT VERSION(),@@hostname,@@server_id,CURRENT_USER()")
        ident=q.fetchone();snapshot_id={"version":ident[0],"host":ident[1],"server_id":int(ident[2]),"account":ident[3]};q.close()
        total_rows=0; first_archive_ts=None; last_archive_ts=None
        q=conn.cursor();q.execute("SELECT `dateTime`,`interval` FROM `loucka_reconstruction`.`archive` ORDER BY `dateTime`")
        while True:
            batch=q.fetchmany(10000)
            if not batch:break
            for ts,interval in batch:
                total_rows+=1
                first_archive_ts=int(ts) if first_archive_ts is None else first_archive_ts
                last_archive_ts=int(ts)
                day=local_day(int(ts)); month=day.strftime("%Y-%m"); interval=int(interval or 0)
                if 1<=interval<=120:
                    cadence[month][interval]+=1;phase[(month,interval)][int(ts)%(interval*60)]+=1
        q.close()
        if from_concordance and total_rows != int(conn.target["rows"]):
            raise RuntimeError(f"selected concordance row count mismatch: read={total_rows} metadata={conn.target['rows']}")
        if from_concordance and (first_archive_ts != int(conn.target["min_timestamp"]) or last_archive_ts != int(conn.target["max_timestamp"])):
            raise RuntimeError("selected concordance timestamp range does not match its snapshot metadata")
        modes={}; phases={}; cadence_share={}
        for month,count in cadence.items():
            mode=max(count,key=lambda x:(count[x],-x));modes[month]=mode
            phases[month]=max(phase[(month,mode)],key=phase[(month,mode)].get)
            cadence_share[month]=count[mode]/sum(count.values())
        cadence_inferred_months=[]
        if modes:
            def month_ordinal(value):
                year,month=map(int,value.split("-"));return year*12+month
            first_month=min(modes,key=month_ordinal);last_month=max(modes,key=month_ordinal)
            start_ord=month_ordinal(first_month);end_ord=month_ordinal(last_month)
            for ordinal in range(start_ord,end_ord+1):
                year,month=divmod(ordinal-1,12);label=f"{year:04d}-{month+1:02d}"
                if label in modes:continue
                nearest=min(modes,key=lambda existing:(abs(month_ordinal(existing)-ordinal),month_ordinal(existing)>ordinal,month_ordinal(existing)))
                modes[label]=modes[nearest];phases[label]=phases[nearest];cadence_share[label]=cadence_share[nearest]
                cadence_inferred_months.append(label)
        # A timestamp alone proves nothing about a particular field. Require a
        # committed verification batch and exact field equality to its immutable
        # source row_json; later reconstruction events take precedence above.
        q=conn.cursor();q.execute("SELECT batch_id,row_count,source_payload_sha256,verified_target_postimage_sha256 FROM `loucka_reconstruction`.`archive_sync_verification`")
        verified_batches={str(batch):(int(count),str(payload),str(postimage)) for batch,count,payload,postimage in q.fetchall()
                          if int(count)>0 and payload and postimage};q.close()
        q=conn.cursor();q.execute("SELECT dateTime,batch_id,source_schema,target_schema,source_row_sha256,row_json FROM `loucka_reconstruction`.`archive_sync_audit`")
        batch_rows=Counter()
        audit_candidates=defaultdict(list)
        for ts,batch,source_schema,target_schema,row_hash,row_json in q:
            batch=str(batch)
            if batch not in verified_batches or source_schema!="pocasi-loucka.eu" or target_schema!="loucka_reconstruction":continue
            try: payload=json.loads(row_json) if isinstance(row_json,(str,bytes,bytearray)) else row_json
            except (TypeError,ValueError):continue
            if not isinstance(payload,dict) or not row_hash:continue
            canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False,default=str)
            if hashlib.sha256(canonical.encode("utf-8")).hexdigest()!=str(row_hash):continue
            audit_candidates[batch].append((int(ts),payload));batch_rows[batch]+=1
        q.close()
        verified_source={}
        for batch,items in audit_candidates.items():
            if batch not in verified_batches:continue
            expected_count,expected_payload_hash,_=verified_batches[batch]
            items.sort(key=lambda x:x[0])
            payload_hash=hashlib.sha256(json.dumps([payload for _,payload in items],sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False,default=str).encode("utf-8")).hexdigest()
            if batch_rows[batch]==expected_count and payload_hash==expected_payload_hash:
                verified_source.update({ts:payload for ts,payload in items})
        q=conn.cursor();q.execute("SELECT `id`,`target_time`,`variable`,`new_value`,`reason` FROM `loucka_reconstruction`.`reconstruction_changes` WHERE `state`='applied' ORDER BY `id`")
        for event_id,ts,var,new_value,reason in q:
            text=str(reason or "").upper();cls="UNCLASSIFIED"
            if "ESTIMATED" in text:cls="ESTIMATED"
            elif "RECOVERED_SOURCE" in text or "RECOVERED SOURCE" in text:cls="RECOVERED_SOURCE"
            elif "RESTORED" in text or "RESTORE" in text:cls="RESTORED"
            elif "CORRECTED" in text:cls="CORRECTED"
            changes[(int(ts),var)]={"id":int(event_id),"new_value":new_value,"class":cls}
        q.close()
        colnames=("dateTime","usUnits","interval",*VARS)
        q=conn.cursor();q.execute("SELECT "+",".join(f"`{x}`" for x in colnames)+" FROM `loucka_reconstruction`.`archive` ORDER BY `dateTime`")
        day_state={};current_day=None;first_observed={};last_local=None;min_epoch=None;max_epoch=None

        def flush_day(day, state):
            if day is None:return
            month=day[:7];step=int(modes.get(month,5))*60;phase_s=int(phases.get(month,0))
            d=dt.date.fromisoformat(day);first,nexp,dayexp,nightexp,end=expected_grid(d,step,phase_s)
            for var in VARS:
                a=state.get(var,empty_day())
                first_ts=first_observed.get(var)
                if first_ts is not None and day==local_day(first_ts).isoformat():
                    first,nexp,dayexp,nightexp,end=expected_grid(d,step,phase_s,first_ts)
                exp=nexp if first_ts is not None and day>=local_day(first_ts).isoformat() else 0
                day_exp=dayexp if exp else 0;night_exp=nightexp if exp else 0
                # Exclude edge gaps from the reported longest observed step but include them in missing-run quality.
                max_gap_slots=a["max_gap"]
                if exp:
                    if a["first_slot"] is not None:
                        max_gap_slots=max(max_gap_slots,a["first_slot"],nexp-1-a["last_slot"])
                    else:max_gap_slots=nexp
                max_gap_seconds=max_gap_slots*step
                measured=a["nonestimated"];coverage=measured/exp if exp else None
                day_cov=a["day_nonestimated"]/day_exp if day_exp else None
                night_cov=a["night_nonestimated"]/night_exp if night_exp else None
                dup=sum(n-1 for n in a["bucket_counts"].values() if n>1)
                meanpass=bool(exp and coverage>=.95 and day_cov>=.90 and night_cov>=.90 and max_gap_seconds<=3600 and not a["estimated"])
                extempass=bool(exp and coverage>=.99 and day_cov>=.98 and night_cov>=.98 and max_gap_seconds<=1800 and not a["estimated"])
                # The latest snapshot day is marked partial after the complete
                # ordered scan. At this point last_local still refers to the
                # day being flushed, so consulting it here would incorrectly
                # mark every completed day as partial.
                status="NOT_AVAILABLE_BEFORE_FIRST_OBSERVED_EPOCH" if not exp else ("REVIEW_REQUIRED_ESTIMATED_VALUES" if a["estimated"] else ("REVIEW_REQUIRED_PROVENANCE_UNKNOWN" if a["unclassified"] else ("READY_WITH_LIMITATIONS" if meanpass else "NOT_REPRESENTATIVE_COVERAGE_OR_GAP")))
                if day.startswith("2018-") and day[5:7] in {"01","02","03"}:status="PROTECTED_Q1_2018_REVIEW_REQUIRED"
                if day.startswith("2021-"):status="DIAGNOSTIC_2021_NO_PRODUCTION_DECISION"
                current_mean=(math.degrees(math.atan2(a["all_sin"],a["all_cos"]))%360) if var=="windDir" and a["dir_weight_current"] else (a["all_mean"]/a["all_weight"] if a["all_weight"] else "")
                without_mean=(math.degrees(math.atan2(a["without_est_sin"],a["without_est_cos"]))%360) if var=="windDir" and a["dir_weight_without_estimates"] else (a["without_est_mean"]/a["without_est_weight"] if a["without_est_weight"] else "")
                source_mean=(math.degrees(math.atan2(a["source_sin"],a["source_cos"]))%360) if var=="windDir" and a["dir_weight_source"] else (a["source_mean"]/a["source_weight"] if a["source_weight"] else "")
                source_restored_mean=(math.degrees(math.atan2(a["source_restored_sin"],a["source_restored_cos"]))%360) if var=="windDir" and a["dir_weight_source_restored"] else (a["source_restored_mean"]/a["source_restored_weight"] if a["source_restored_weight"] else "")
                item={"local_day":day,"variable":var,"unit":UNITS[var],"expected_unique_slots":exp,"available_unique_on_grid_slots":a["on_grid"],"non_estimated_on_grid_slots":measured,"missing_measured_slots":max(0,exp-measured),"coverage_measured":f"{coverage:.8f}" if coverage is not None else "","day_slots_expected":day_exp,"day_slots_measured":a["day_nonestimated"],"day_coverage":f"{day_cov:.8f}" if day_cov is not None else "","night_slots_expected":night_exp,"night_slots_measured":a["night_nonestimated"],"night_coverage":f"{night_cov:.8f}" if night_cov is not None else "","offgrid_nonnull_values":a["offgrid"],"duplicate_nearest_slot_values":dup,"raw_nonnull_including_offgrid":a["raw_nonnull"],"estimated_values":a["estimated"],"restored_values":a["restored"],"recovered_source_values":a["source"],"corrected_values":a["corrected"],"unclassified_values":a["unclassified"],"original_verified_values":0,"calm_wind_samples_exact_zero_speed_with_direction":a["calm_wind_samples"] if var=="windDir" else "","modal_interval_minutes":modes.get(month,""),"modal_cadence_share":f"{cadence_share.get(month,0):.8f}","max_observed_or_edge_gap_seconds":max_gap_seconds,"mean_current_archive_on_grid":f"{current_mean:.8f}" if current_mean!="" else "","mean_excluding_known_estimates":f"{without_mean:.8f}" if without_mean!="" else "","mean_verified_source_only":f"{source_mean:.8f}" if source_mean!="" else "","mean_verified_source_plus_restored":f"{source_restored_mean:.8f}" if source_restored_mean!="" else "","sum_weighted_current":a["all_mean"],"weight_seconds_current":a["all_weight"],"sum_weighted_without_estimates":a["without_est_mean"],"weight_seconds_without_estimates":a["without_est_weight"],"sum_weighted_verified_source":a["source_mean"],"weight_seconds_verified_source":a["source_weight"],"sum_weighted_source_restored":a["source_restored_mean"],"weight_seconds_source_restored":a["source_restored_weight"],"circular_sin_current":a["all_sin"],"circular_cos_current":a["all_cos"],"circular_sin_without_estimates":a["without_est_sin"],"circular_cos_without_estimates":a["without_est_cos"],"circular_sin_verified_source":a["source_sin"],"circular_cos_verified_source":a["source_cos"],"circular_sin_source_restored":a["source_restored_sin"],"circular_cos_source_restored":a["source_restored_cos"],"minimum_on_grid":a["min"] if a["min"] is not None else "","maximum_on_grid":a["max"] if a["max"] is not None else "","offgrid_minimum":a["offgrid_min"] if a["offgrid_min"] is not None else "","offgrid_maximum":a["offgrid_max"] if a["offgrid_max"] is not None else "","daily_mean_sampling_pass":meanpass,"daily_extrema_sampling_pass":False if var=="windDir" else extempass,"readiness":status,"provenance_readiness":"SOURCE_VERIFIED_ONLY; ORIGINAL_LINEAGE_UNKNOWN_FOR_REMAINDER","limitations":"Coverage uses unique on-grid expected slots at monthly modal archive cadence; off-grid rows are separate. Time weights use each row's actual interval. Unknown lineage remains review-only."}
                item.update({"verified_source_on_grid_slots":a["source_on_grid"],"restored_on_grid_slots":a["restored_on_grid"],"verified_source_plus_restored_on_grid_slots":a["source_restored"],"verified_source_plus_restored_mean":source_restored_mean,"direction_noncalm_weight_seconds_current":a["dir_weight_current"],"direction_noncalm_weight_seconds_without_estimates":a["dir_weight_without_estimates"],"direction_noncalm_weight_seconds_source":a["dir_weight_source"],"direction_noncalm_weight_seconds_source_restored":a["dir_weight_source_restored"],"direction_resultant_current":math.hypot(a["all_sin"],a["all_cos"])/a["dir_weight_current"] if var=="windDir" and a["dir_weight_current"] else "","direction_resultant_source_only":math.hypot(a["source_sin"],a["source_cos"])/a["dir_weight_source"] if var=="windDir" and a["dir_weight_source"] else "","direction_resultant_source_plus_restored":math.hypot(a["source_restored_sin"],a["source_restored_cos"])/a["dir_weight_source_restored"] if var=="windDir" and a["dir_weight_source_restored"] else ""})
                resultant=item["direction_resultant_current"]
                item["direction_concentration_status"]=("NO_NONCALM_DIRECTION_SAMPLES" if resultant=="" else ("LOW_CONCENTRATION_MEAN_UNINTERPRETABLE" if float(resultant)<0.1 else "CONCENTRATED_DIRECTION")) if var=="windDir" else ""
                daily.append(item)

        while True:
            batch=q.fetchmany(5000)
            if not batch:break
            for raw in batch:
                ts=int(raw[0]);units=int(raw[1]);interval=int(raw[2] or 0);day_obj=local_day(ts);day=day_obj.isoformat()
                # This contract's output units are WeeWX METRIC. Refuse a mixed or
                # unexpected archive epoch until a conversion is explicitly
                # defined and independently validated.
                if units != 16:
                    raise RuntimeError(f"unsupported archive usUnits={units} at timestamp {ts}; expected METRIC (16)")
                if current_day is not None and day!=current_day:
                    flush_day(current_day,day_state);day_state={}
                current_day=day;last_local=day
                min_epoch=ts if min_epoch is None else min(min_epoch,ts);max_epoch=ts if max_epoch is None else max(max_epoch,ts)
                month=day_obj.strftime("%Y-%m");step=int(modes.get(month,5))*60;phase_s=int(phases.get(month,0))
                first,nexp,_,_,_=expected_grid(day_obj,step,phase_s)
                on_grid=ts>=first and (ts-first)%step==0
                slot_index=(ts-first)//step if on_grid else (ts-first+step//2)//step
                weight=max(0,interval)*60
                for i,var in enumerate(VARS):
                    value=raw[i+3]
                    if value is None:continue
                    first_observed.setdefault(var,ts)
                    a=day_state.setdefault(var,empty_day())
                    audit_payload=verified_source.get(ts)
                    if audit_payload and int(audit_payload.get("usUnits",-1)) != units:
                        audit_payload=None
                    if from_concordance:
                        category = raw[3+len(VARS)+i]
                    else:
                        category=classify(ts,var,value,{ts:audit_payload} if audit_payload else {},estimates,changes)
                    if category=="ESTIMATED" and (ts,var) not in estimates:category="UNCLASSIFIED"
                    if category=="RECOVERED_SOURCE":a["source"]+=1
                    elif category=="RESTORED":a["restored"]+=1
                    elif category=="CORRECTED":a["corrected"]+=1
                    elif category=="ESTIMATED":a["estimated"]+=1
                    else:a["unclassified"]+=1
                    add_value(a,value,weight,category,ts,slot_index,on_grid,dt.datetime.fromtimestamp(ts,TZ).hour)
                    speed_value=raw[3+VARS.index("windSpeed")]
                    direction_valid=var=="windDir" and on_grid and weight>0 and speed_value is not None and float(speed_value)>0
                    if direction_valid:
                        rad=math.radians(float(value));a["all_sin"]+=math.sin(rad)*weight;a["all_cos"]+=math.cos(rad)*weight
                        a["dir_weight_current"]+=weight
                        if category!="ESTIMATED":a["without_est_sin"]+=math.sin(rad)*weight;a["without_est_cos"]+=math.cos(rad)*weight;a["dir_weight_without_estimates"]+=weight
                        if category=="RECOVERED_SOURCE":a["source_sin"]+=math.sin(rad)*weight;a["source_cos"]+=math.cos(rad)*weight;a["dir_weight_source"]+=weight
                        if category in {"RECOVERED_SOURCE","RESTORED"}:a["source_restored_sin"]+=math.sin(rad)*weight;a["source_restored_cos"]+=math.cos(rad)*weight;a["dir_weight_source_restored"]+=weight
                    if var=="windDir" and on_grid and weight>0 and raw[3+VARS.index("windSpeed")] is not None and numeric_equal(raw[3+VARS.index("windSpeed")],0):
                        a["calm_wind_samples"]+=1
        q.close();flush_day(current_day,day_state)
        conn.rollback()
    finally:conn.close()

    # Emit a complete civil calendar through the current last observed local date.
    if min_epoch is None or max_epoch is None:raise RuntimeError("archive snapshot contains no rows")
    first_day=local_day(min_epoch);last_day=local_day(max_epoch)
    existing={(r["local_day"],r["variable"]):r for r in daily}
    for offset in range((last_day-first_day).days+1):
        day=(first_day+dt.timedelta(days=offset)).isoformat()
        for var in VARS:
            if (day,var) in existing:continue
            month=day[:7];step=int(modes.get(month,5))*60;ph=int(phases.get(month,0));d=dt.date.fromisoformat(day)
            first,nexp,dayexp,nightexp,_=expected_grid(d,step,ph)
            first_ts=first_observed.get(var)
            exp=nexp if first_ts is not None and day>=local_day(first_ts).isoformat() else 0
            if first_ts is not None and day==local_day(first_ts).isoformat():first,nexp,dayexp,nightexp,_=expected_grid(d,step,ph,first_ts);exp=nexp
            existing[(day,var)]={"local_day":day,"variable":var,"unit":UNITS[var],"expected_unique_slots":exp,"available_unique_on_grid_slots":0,"non_estimated_on_grid_slots":0,"missing_measured_slots":exp,"coverage_measured":"0.00000000" if exp else "","day_slots_expected":dayexp if exp else 0,"day_slots_measured":0,"day_coverage":"0.00000000" if exp else "","night_slots_expected":nightexp if exp else 0,"night_slots_measured":0,"night_coverage":"0.00000000" if exp else "","offgrid_nonnull_values":0,"duplicate_nearest_slot_values":0,"raw_nonnull_including_offgrid":0,"estimated_values":0,"restored_values":0,"recovered_source_values":0,"corrected_values":0,"unclassified_values":0,"original_verified_values":0,"calm_wind_samples_exact_zero_speed_with_direction":0 if var=="windDir" else "","verified_source_on_grid_slots":0,"restored_on_grid_slots":0,"verified_source_plus_restored_on_grid_slots":0,"direction_noncalm_weight_seconds_current":0,"direction_noncalm_weight_seconds_without_estimates":0,"direction_noncalm_weight_seconds_source":0,"direction_noncalm_weight_seconds_source_restored":0,"direction_concentration_status":"NO_NONCALM_DIRECTION_SAMPLES" if var=="windDir" else "","modal_interval_minutes":modes.get(month,""),"modal_cadence_share":f"{cadence_share.get(month,0):.8f}","max_observed_or_edge_gap_seconds":nexp*step,"mean_current_archive_on_grid":"","mean_excluding_known_estimates":"","mean_verified_source_only":"","mean_verified_source_plus_restored":"","verified_source_plus_restored_mean":"","direction_resultant_current":"","direction_resultant_source_only":"","direction_resultant_source_plus_restored":"","sum_weighted_current":0,"weight_seconds_current":0,"sum_weighted_without_estimates":0,"weight_seconds_without_estimates":0,"sum_weighted_verified_source":0,"weight_seconds_verified_source":0,"sum_weighted_source_restored":0,"weight_seconds_source_restored":0,"circular_sin_current":0,"circular_cos_current":0,"circular_sin_without_estimates":0,"circular_cos_without_estimates":0,"circular_sin_verified_source":0,"circular_cos_verified_source":0,"circular_sin_source_restored":0,"circular_cos_source_restored":0,"minimum_on_grid":"","maximum_on_grid":"","offgrid_minimum":"","offgrid_maximum":"","daily_mean_sampling_pass":False,"daily_extrema_sampling_pass":False,"readiness":"NO_ARCHIVE_ROW_SENSOR_EPOCH_VS_UNRESOLVED_GAP" if exp else "NOT_AVAILABLE_BEFORE_FIRST_OBSERVED_EPOCH","provenance_readiness":"SOURCE_VERIFIED_ONLY; ORIGINAL_LINEAGE_UNKNOWN_FOR_REMAINDER","limitations":"No archive row on this local civil date; cadence denominator uses monthly modal interval and DST-aware Europe/Prague slot grid."}
    daily=[existing[k] for k in sorted(existing)]
    for r in daily:
        if r["local_day"]==last_day.isoformat():r["readiness"]="PARTIAL_CURRENT_LOCAL_DAY"

    def group_summary(label, items, kind):
        first=items[0];expected=sum(int(x["expected_unique_slots"]) for x in items);available=sum(int(x["available_unique_on_grid_slots"]) for x in items)
        measured=sum(int(x["non_estimated_on_grid_slots"]) for x in items);est=sum(int(x["estimated_values"]) for x in items)
        offgrid=sum(int(x["offgrid_nonnull_values"]) for x in items);dups=sum(int(x["duplicate_nearest_slot_values"]) for x in items)
        source=sum(int(x["recovered_source_values"]) for x in items);restored=sum(int(x["restored_values"]) for x in items);corrected=sum(int(x["corrected_values"]) for x in items);unknown=sum(int(x["unclassified_values"]) for x in items)
        calm=sum(int(x.get("calm_wind_samples_exact_zero_speed_with_direction") or 0) for x in items)
        ratio=measured/expected if expected else None;mean_days=sum(bool(x["daily_mean_sampling_pass"]) for x in items);ext_days=sum(bool(x["daily_extrema_sampling_pass"]) for x in items)
        max_gap=max(int(x["max_observed_or_edge_gap_seconds"]) for x in items)
        day_expected=sum(int(x["day_slots_expected"]) for x in items);day_meas=sum(int(x["day_slots_measured"]) for x in items)
        night_expected=sum(int(x["night_slots_expected"]) for x in items);night_meas=sum(int(x["night_slots_measured"]) for x in items)
        current_sum=sum(float(x["sum_weighted_current"]) for x in items);current_weight=sum(float(x["weight_seconds_current"]) for x in items)
        without_sum=sum(float(x["sum_weighted_without_estimates"]) for x in items);without_weight=sum(float(x["weight_seconds_without_estimates"]) for x in items)
        source_sum=sum(float(x["sum_weighted_verified_source"]) for x in items);source_weight=sum(float(x["weight_seconds_verified_source"]) for x in items)
        sr_sum=sum(float(x["sum_weighted_source_restored"]) for x in items);sr_weight=sum(float(x["weight_seconds_source_restored"]) for x in items)
        if first["variable"]=="windDir":
            current_weight=sum(float(x["direction_noncalm_weight_seconds_current"]) for x in items)
            without_weight=sum(float(x["direction_noncalm_weight_seconds_without_estimates"]) for x in items)
            source_weight=sum(float(x["direction_noncalm_weight_seconds_source"]) for x in items)
            sr_weight=sum(float(x["direction_noncalm_weight_seconds_source_restored"]) for x in items)
            def circular(prefix, weight):
                s=sum(float(x[f"circular_sin_{prefix}"]) for x in items);c=sum(float(x[f"circular_cos_{prefix}"]) for x in items)
                return math.degrees(math.atan2(s,c))%360 if weight else "", math.hypot(s,c)/weight if weight else ""
            current_mean,current_resultant=circular("current",current_weight)
            without_mean,without_resultant=circular("without_estimates",without_weight)
            source_mean,source_resultant=circular("verified_source",source_weight)
            sr_mean,sr_resultant=circular("source_restored",sr_weight)
        else:
            current_mean=current_sum/current_weight if current_weight else "";without_mean=without_sum/without_weight if without_weight else ""
            source_mean=source_sum/source_weight if source_weight else "";sr_mean=sr_sum/sr_weight if sr_weight else ""
            current_resultant=without_resultant=source_resultant=sr_resultant=""
        modal=int(first["modal_interval_minutes"]) if first["modal_interval_minutes"] else ""
        cadence_ratio=float(first["modal_cadence_share"] or 0)
        mean_threshold=.95;ext_threshold=.99; required_mean_days=math.ceil(.90*len(items));required_ext_days=math.ceil(.95*len(items))
        sampling_ok=ratio is not None and ratio>=mean_threshold and mean_days>=required_mean_days and cadence_ratio>=.90 and max_gap<=21600
        extrema_ok=ratio is not None and ratio>=ext_threshold and ext_days>=required_ext_days and cadence_ratio>=.90 and max_gap<=1800 and not est and not unknown
        status="REVIEW_REQUIRED_ESTIMATED_VALUES_INCLUDED" if est else ("REVIEW_REQUIRED_PROVENANCE_UNKNOWN" if unknown else ("READY_WITH_LIMITATIONS" if sampling_ok else "NOT_REPRESENTATIVE_COVERAGE_OR_GAP"))
        extrema_status="NOT_APPLICABLE_CIRCULAR_VARIABLE" if first["variable"]=="windDir" else ("READY_WITH_LIMITATIONS" if extrema_ok else "NOT_READY_EXTREMA_COVERAGE_OR_GAP")
        direction_status=("NO_NONCALM_DIRECTION_SAMPLES" if current_resultant=="" else ("LOW_CONCENTRATION_MEAN_UNINTERPRETABLE" if float(current_resultant)<0.1 else "CONCENTRATED_DIRECTION")) if first["variable"]=="windDir" else ""
        return {"period":label,"variable":first["variable"],"unit":first["unit"],"expected_unique_slots":expected,"available_unique_on_grid_slots":available,"non_estimated_on_grid_slots":measured,"missing_measured_slots":max(0,expected-measured),"coverage_measured":f"{ratio:.8f}" if ratio is not None else "","day_slots_expected":day_expected,"day_slots_measured":day_meas,"day_coverage":f"{day_meas/day_expected:.8f}" if day_expected else "","night_slots_expected":night_expected,"night_slots_measured":night_meas,"night_coverage":f"{night_meas/night_expected:.8f}" if night_expected else "","offgrid_nonnull_values":offgrid,"duplicate_nearest_slot_values":dups,"estimated_values":est,"restored_values":restored,"recovered_source_values":source,"corrected_values":corrected,"unclassified_values":unknown,"original_verified_values":0,"calm_wind_samples_exact_zero_speed_with_direction":calm if first["variable"]=="windDir" else "","verified_source_on_grid_slots":sum(int(x["verified_source_on_grid_slots"]) for x in items),"restored_on_grid_slots":sum(int(x["restored_on_grid_slots"]) for x in items),"verified_source_plus_restored_on_grid_slots":sum(int(x["verified_source_plus_restored_on_grid_slots"]) for x in items),"mean_current_archive_time_weighted":current_mean,"mean_excluding_known_estimates_time_weighted":without_mean,"mean_verified_source_only_time_weighted":source_mean,"mean_verified_source_plus_restored_time_weighted":sr_mean,"direction_resultant_current":current_resultant,"direction_resultant_without_estimates":without_resultant,"direction_resultant_source_only":source_resultant,"direction_resultant_source_plus_restored":sr_resultant,"direction_concentration_status":direction_status,"days_passing_mean_rule":mean_days,"days_required_mean_rule":required_mean_days,"days_passing_extrema_rule":ext_days,"days_required_extrema_rule":required_ext_days,"max_observed_or_edge_gap_seconds":max_gap,"modal_interval_minutes":modal,"modal_cadence_share":f"{cadence_ratio:.8f}","readiness":status,"extrema_readiness":extrema_status,"method":"Expected unique civil slots use monthly modal interval/phase and Europe/Prague DST; period means combine exact per-row interval-weighted sums, with circular weights for nonzero wind; resultant length below 0.1 is marked uninterpretable.","limitations":"Provenance unknown values remain; estimate-contaminated groups are review-only; annual 2009/2026 and protected/diagnostic periods are limited."}

    month_map=defaultdict(list);year_map=defaultdict(list)
    for row in daily:
        month_map[(row["local_day"][:7],row["variable"])].append(row);year_map[(row["local_day"][:4],row["variable"])].append(row)
    monthly=[group_summary(p,items,"monthly") for (p,_),items in sorted(month_map.items())]
    annual=[group_summary(p,items,"annual") for (p,_),items in sorted(year_map.items())]
    monthly_by_year_var=defaultdict(list)
    for r in monthly:monthly_by_year_var[(r["period"][:4],r["variable"])].append(r)
    for r in annual:
        constituent=monthly_by_year_var[(r["period"],r["variable"])]
        shares=[float(x["modal_cadence_share"] or 0) for x in constituent]
        modes_in_year={str(x["modal_interval_minutes"]) for x in constituent if x["modal_interval_minutes"]!=""}
        r["modal_interval_minutes"]=next(iter(modes_in_year)) if len(modes_in_year)==1 else "VARIES"
        r["modal_cadence_share"]=f"{min(shares,default=0):.8f}"
        r["months_passing_mean_rule"]=sum(x["readiness"]=="READY_WITH_LIMITATIONS" for x in constituent)
        r["months_passing_extrema_rule"]=sum(x["extrema_readiness"]=="READY_WITH_LIMITATIONS" for x in constituent)
        if r["variable"]=="windDir":r["extrema_readiness"]="NOT_APPLICABLE_CIRCULAR_VARIABLE"
        elif r["extrema_readiness"]=="READY_WITH_LIMITATIONS" and r["months_passing_extrema_rule"]<11:r["extrema_readiness"]="NOT_READY_FEWER_THAN_11_MONTHS"
        if r["readiness"]=="READY_WITH_LIMITATIONS" and r["months_passing_mean_rule"]<11:r["readiness"]="NOT_READY_FEWER_THAN_11_MONTHS"
    for r in monthly:
        if r["period"] in {"2018-01","2018-02","2018-03"}:r["readiness"]="PROTECTED_Q1_2018_REVIEW_REQUIRED"
        if r["period"].startswith("2021-"):r["readiness"]="DIAGNOSTIC_2021_NO_PRODUCTION_DECISION"
        if r["period"]==last_day.strftime("%Y-%m"):r["readiness"]="PARTIAL_CURRENT_MONTH_NOT_CERTIFIABLE"
    for r in annual:
        if r["period"]=="2018":r["readiness"]="REVIEW_REQUIRED_Q1_2018_PROTECTED_SUBPERIOD"
        if r["period"]=="2021":r["readiness"]="DIAGNOSTIC_2021_NO_PRODUCTION_DECISION"
        if r["period"]=="2009":r["readiness"]="PARTIAL_FIRST_OBSERVED_YEAR_NOT_CERTIFIABLE"
        if r["period"]==str(last_day.year):r["readiness"]="PARTIAL_YEAR_NOT_CERTIFIABLE"
    provenance=[];missing=[];blockers=[];recommend=[]
    for r in monthly:
        provenance.append({k:r[k] for k in ("period","variable","recovered_source_values","restored_values","corrected_values","estimated_values","unclassified_values","original_verified_values","readiness")})
        if int(r["missing_measured_slots"]):
            missing.append({k:r[k] for k in ("period","variable","expected_unique_slots","non_estimated_on_grid_slots","missing_measured_slots","offgrid_nonnull_values","duplicate_nearest_slot_values","max_observed_or_edge_gap_seconds")})
            reason="Review exact source availability and gap distribution; do not insert estimates automatically."
            if r["period"].startswith("2018-0") and r["period"]<="2018-03":reason="Protected Q1 2018: preserve and continue the parallel review only."
            elif r["period"].startswith("2021-"):reason="Diagnostic-only 2021: no production decision."
            recommend.append({"period":r["period"],"variable":r["variable"],"missing_measured_slots":r["missing_measured_slots"],"recommended_next_action":reason})
        if r["readiness"] not in {"READY_WITH_LIMITATIONS"}:
            blockers.append({"period":r["period"],"variable":r["variable"],"readiness":r["readiness"],"estimated_values":r["estimated_values"],"unclassified_values":r["unclassified_values"],"missing_measured_slots":r["missing_measured_slots"],"publication_blocker":"Yes; current readiness is not sufficient for definitive climate publication."})
    script_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    snapshot_utc=conn.meta["snapshot_utc"] if from_concordance else dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
    snapshot={"schema":"loucka-authoritative-statistical-readiness-v1","snapshot_utc":snapshot_utc,"database_identity":snapshot_id,"timezone":"Europe/Prague","archive_min_timestamp":min_epoch,"archive_max_timestamp":max_epoch,"local_coverage_from":first_day.isoformat(),"local_coverage_through":last_day.isoformat(),"target_archive_rows_read":total_rows,"source_snapshot_sha256":conn.sha256 if from_concordance else None,"cadence_by_local_month":{m:{str(i):n for i,n in sorted(c.items())} for m,c in sorted(cadence.items())},"cadence_inferred_months_nearest_observed_month":cadence_inferred_months,"verified_source_timestamps":len(conn.verified_source_timestamps) if from_concordance else len(verified_source),"known_estimate_keys":conn.category_counts["ESTIMATED"] if from_concordance else len(estimates),"snapshot_provenance_categories":dict(conn.category_counts) if from_concordance else None,"script_sha256":script_hash,"methods":{"coverage":"non-estimated unique exact-grid slots divided by expected local-civil slots at monthly modal interval and phase; each variable starts at its own first non-NULL epoch; off-grid separate. Empty archive months inherit cadence/phase from nearest observed month, explicitly listed.","timezone":"Europe/Prague; local day lengths naturally include 23/25-hour DST","units":"Every target row must have usUnits=16 (WeeWX METRIC: Celsius, centimetres for rain, km/h for speed); the build fails closed on another code. Output units are degC, percent, km/h and hPa. No mixed-unit averaging or implicit conversion.","weights":"per-row interval minutes; monthly and annual weighted values combine exact daily weighted numerators and denominators","wind":"circular interval-weighted direction only when same-row windSpeed is non-NULL and strictly greater than zero; calm directions are counted separately and excluded from directional means and resultant concentration; resultant length below 0.1 is marked uninterpretable; minimum/maximum not applicable","calm_wind":"count exact on-grid zero windSpeed samples with a non-NULL windDir and positive recorded interval","rain":"excluded pending E4 counter semantics","provenance":"In concordance mode, RECOVERED_SOURCE/RESTORED/CORRECTED/ESTIMATED categories are accepted only as encoded by the immutable value-level concordance, whose build validates complete source batches and exact row-level evidence. SOURCE_MATCHED remains UNCLASSIFIED for strict readiness; ORIGINAL is never inferred."},"limitations":["Monthly modal cadence/phase is an archive-derived denominator, not an authoritative sensor deployment record.","Historical source lineage is unavailable for values not covered by current-source audit or an exact matching applied change event.","A high coverage ratio alone does not establish representativeness or publication readiness."]}
    outputs={"daily":"DAILY_STATISTICAL_READINESS_CURRENT.csv","monthly":"MONTHLY_STATISTICAL_READINESS_CURRENT.csv","annual":"ANNUAL_STATISTICAL_READINESS_CURRENT.csv","provenance":"STATISTICAL_PROVENANCE_CURRENT.csv","missing":"STATISTICAL_MISSING_DATA_CURRENT.csv","blockers":"STATISTICAL_PUBLICATION_BLOCKERS_CURRENT.csv","recommendations":"STATISTICAL_RECONSTRUCTION_RECOMMENDATIONS_CURRENT.csv"}
    output_dir=Path(os.environ.get("METEO_AUDIT_READINESS_OUTPUT_DIR",ROOT/"data"))
    output_dir.mkdir(parents=True,exist_ok=True)
    for key,name in outputs.items():write_csv(output_dir/name,{"daily":daily,"monthly":monthly,"annual":annual,"provenance":provenance,"missing":missing,"blockers":blockers,"recommendations":recommend}[key])
    api={"snapshot":snapshot,"daily":daily,"monthly":monthly,"annual":annual,"provenance":provenance,"missing_data":missing,"publication_blockers":blockers,"reconstruction_recommendations":recommend}
    output_path=output_dir/"STATISTICAL_READINESS_CURRENT.json"
    fd,temp_name=tempfile.mkstemp(prefix=output_path.name+".",suffix=".tmp",dir=output_path.parent);os.close(fd);temp_path=Path(temp_name)
    try:
        temp_path.write_text(json.dumps(api,ensure_ascii=False,separators=(",",":"),default=str)+"\n",encoding="utf-8")
        os.replace(temp_path,output_path)
    finally:temp_path.unlink(missing_ok=True)
    source_count=len(conn.verified_source_timestamps) if from_concordance else len(verified_source)
    print(json.dumps({"status":"PASS","daily_rows":len(daily),"monthly_rows":len(monthly),"annual_rows":len(annual),"archive_rows_read":snapshot["target_archive_rows_read"],"source_timestamp_count":source_count,"snapshot_utc":snapshot["snapshot_utc"],"local_coverage_from":first_day.isoformat(),"local_coverage_through":last_day.isoformat(),"script_sha256":script_hash},indent=2))


if __name__ == "__main__":main()
