#!/usr/bin/env python3
"""Validate downloaded CHMI 10-minute station-pressure CSVs and SHA manifest."""
from __future__ import annotations
import argparse, csv, hashlib, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OK={"0","0.0"}

def validate(data_dir: Path):
    manifest=json.loads((data_dir/"manifest.json").read_text(encoding="utf-8"))
    results=[]
    for rec in manifest["records"]:
        path=data_dir/"raw"/rec["file"]; raw=path.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        if digest != rec["sha256"]: raise ValueError(f"SHA-256 mismatch: {rec['file']}")
        with path.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
        qs=Counter(); times=[]; vals=[]; invalid=[]
        for row in rows:
            if row["ELEMENT"]!="P" or row["STATION"] not in manifest["station_ids"]: raise ValueError("unexpected station/element")
            dt=datetime.fromisoformat(row["DT"].replace("Z","+00:00"))
            if dt.tzinfo is None or dt.utcoffset().total_seconds()!=0 or not row["DT"].endswith("Z"): raise ValueError("timestamp not explicit UTC")
            times.append(dt); qs[row["QUALITY"]]+=1
            if row["VALUE"]:
                v=float(row["VALUE"]); vals.append(v)
                if not 850<=v<=1100: invalid.append({"DT":row["DT"],"VALUE":v,"QUALITY":row["QUALITY"]})
        steps=Counter(int((b-a).total_seconds()) for a,b in zip(times,times[1:]))
        if any(x%600 for x in steps): raise ValueError(f"non-ten-minute cadence: {rec['file']}")
        results.append({"file":rec["file"],"sha256_verified":digest,"rows":len(rows),"quality_counts":dict(qs),"quality_0_valid":qs.get("0",0)+qs.get("0.0",0),"start_utc":times[0].isoformat(),"end_utc":times[-1].isoformat(),"cadence_seconds":sorted(steps),"non_null":len(vals),"range_hpa":[min(vals),max(vals)] if vals else None,"outside_broad_physical_range":invalid})
    return {"schema":"chmi-10min-pressure-validation-v1","source":manifest["source"],"stations":manifest["station_ids"],"unit":"hPa per CHMI meta2.csv (P, Tlak vzduchu)","temporal_support":"10-minute timestamped station pressure observations; quality != 0 excluded from model fitting; timestamps explicit UTC Z","manifest_sha256":hashlib.sha256((data_dir/"manifest.json").read_bytes()).hexdigest(),"files_verified":len(results),"rows":sum(x["rows"] for x in results),"quality_0_rows":sum(x["quality_0_valid"] for x in results),"quality_counts":dict(sum((Counter(x["quality_counts"]) for x in results),Counter())),"file_results":results}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("data_dir",type=Path);ap.add_argument("--out",type=Path,required=True);a=ap.parse_args()
    result=validate(a.data_dir);a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8");print(json.dumps({k:result[k] for k in ("files_verified","rows","quality_0_rows","quality_counts","manifest_sha256")}))
if __name__=="__main__":main()
