#!/usr/bin/env python3
"""Read one timestamp/field from the local historical concordance SQLite."""
import argparse
import json
import sqlite3
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FIELDS={"outTemp","outHumidity","pressure","barometer","altimeter","windSpeed","windGust","windDir"}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("timestamp",type=int,help="Unix epoch seconds")
    parser.add_argument("variable",choices=sorted(FIELDS))
    parser.add_argument("--database",type=Path,default=ROOT/"data/historical_value_concordance.sqlite")
    args=parser.parse_args()
    uri=f"file:{args.database.resolve()}?mode=ro"
    with sqlite3.connect(uri,uri=True) as db:
        row=db.execute("SELECT local_year,local_month,target_usUnits,target_interval,comparison_zlib,audit_zlib FROM timestamp_evidence WHERE dateTime=?",(args.timestamp,)).fetchone()
    if row is None:raise SystemExit("timestamp is absent from the target snapshot")
    comparison=json.loads(zlib.decompress(row[4]))[args.variable]
    audit=json.loads(zlib.decompress(row[5]))
    print(json.dumps({"timestamp":args.timestamp,"local_year":row[0],"local_month":row[1],"target_usUnits":row[2],"target_interval_minutes":row[3],"comparison":comparison,"immutable_sync_audit":audit},ensure_ascii=False,indent=2))

if __name__=="__main__":main()
