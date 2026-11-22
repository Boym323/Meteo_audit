#!/usr/bin/env python3
"""Cache CHMI 10-minute references for all priority candidate months.

Only candidate months with an official file are cached. Existing canonical files
are immutable: a different response for a cached path is reported and never
overwritten. HTTP 404 is recorded as unavailable evidence.
"""
from __future__ import annotations
import concurrent.futures, hashlib, json, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/chmi-priority-temperature/raw"
MANIFEST = ROOT / "data/chmi-priority-temperature/manifest.json"
STATIONS = {"0-203-0-11777": "Vizovice", "0-203-0-11778": "Kladná-Žilín"}
BASE = "https://opendata.chmi.cz/meteorology/climate/historical/data/10min"

def fetch(item):
    period, station, name = item
    year, month = period.split("-")
    filename = f"10m-{station}-{year}{month}.json"
    url = f"{BASE}/{year}/{filename}"
    path = OUT / filename
    if path.exists():
        data = path.read_bytes()
    else:
        req = urllib.request.Request(url, headers={"User-Agent":"LouckaWeatherReferenceAudit/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                if response.status != 200: raise RuntimeError(f"HTTP {response.status}")
                data = response.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"period":period,"station_id":station,"station_name":name,"url":url,"status":"unavailable_http_404"}
            raise
        raw = json.loads(data)
        vals = raw["data"]["data"]["values"]
        header = raw["data"]["data"]["header"].replace(" ", "")
        if header not in ("STATION,ELEMENT,DT,VAL,FLAG,QUALITY", "STATION,ELEMENT,DT,VALUE,FLAG,QUALITY"):
            raise ValueError(f"Unexpected header in {url}: {header}")
        if not vals or any(row[0] != station for row in vals) or not any(row[1] in ("T","TA") for row in vals):
            raise ValueError(f"Empty, station-mismatched, or temperature-free response: {url}")
        OUT.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents concurrent or later runs from replacing evidence.
        try:
            with path.open("xb") as f: f.write(data)
        except FileExistsError:
            prior = path.read_bytes()
            if prior != data: raise RuntimeError(f"Refusing to overwrite changed CHMI evidence: {path}")
        data = path.read_bytes()
    raw = json.loads(data); vals = raw["data"]["data"]["values"]
    if any(row[0] != station for row in vals): raise ValueError(f"Cached station mismatch: {path}")
    trows = [row for row in vals if row[1] in ("T","TA")]
    if not trows: raise ValueError(f"No temperature rows: {path}")
    return {"period":period,"station_id":station,"station_name":name,"url":url,
            "path":path.relative_to(ROOT).as_posix(),"status":"cached","provider":"ČHMÚ",
            "element":"T","cadence":"10-minute UTC timestamps","row_count":len(vals),
            "temperature_rows":len(trows),"quality_counts":{q:sum(str(r[5])==q for r in trows) for q in sorted({str(r[5]) for r in trows})},
            "bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),
            "retrieved_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds")}

def main():
    candidates=json.loads((ROOT/"MONTHLY_PUBLICATION_CANDIDATES.json").read_text())["candidates"]
    # Shared CHMI files contain T, H and wind elements; cover every period of
    # those priority candidates so later validators use the same immutable input.
    target_variables={"outTemp","outHumidity","windSpeed","windGust","windDir"}
    periods=sorted({x["period"] for x in candidates if x["variable"] in target_variables})
    old=json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    old_by_path={x.get("path"):x for x in old.get("files",[]) if x.get("path")}
    tasks=[(p,s,n) for p in periods for s,n in STATIONS.items()]
    OUT.mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        entries=list(pool.map(fetch,tasks))
    for entry in entries:
        old_entry=old_by_path.get(entry.get("path"),{})
        if entry.get("status")=="cached" and entry.get("sha256")==old_entry.get("sha256"):
            entry["retrieved_at_utc"]=old_entry.get("retrieved_at_utc",entry["retrieved_at_utc"])
    manifest={"schema":"loucka-chmi-priority-temperature-cache-v1","provider":"Český hydrometeorologický ústav",
      "dataset":"10-minute station meteorological observations","source_base_url":BASE,"candidate_periods":periods,
      "stations":STATIONS,"files":sorted(entries,key=lambda x:(x["period"],x["station_id"])),
      "method":"Fetch official historical monthly files for all priority temperature, humidity, and wind candidate months; 404 is retained as unavailable; cached bytes are immutable."}
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"candidate_periods":len(periods),"files_cached":sum(x["status"]=="cached" for x in entries),
      "unavailable":sum(x["status"]!="cached" for x in entries),"bytes":sum(x.get("bytes",0) for x in entries)},indent=2))

if __name__=="__main__": main()
