#!/usr/bin/env python3
"""Extract a bounded date subset from cached CHMI daily temperature CSVs."""
import argparse
import csv
import hashlib
from datetime import date, datetime, timezone
from pathlib import Path

EXPECTED = {"STATION", "ELEMENT", "TIMEFUNC", "DT", "VALUE", "FLAG", "QUALITY"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--start-date", type=date.fromisoformat, required=True)
    parser.add_argument("--end-date", type=date.fromisoformat, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.start_date > args.end_date:
        parser.error("start-date must be <= end-date")

    output = []
    seen = set()
    files = sorted(args.raw_dir.glob("dly-*-TMA.csv")) + sorted(args.raw_dir.glob("dly-*-TMI.csv"))
    if not files:
        parser.error(f"No cached TMA/TMI CSV files in {args.raw_dir}")
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        parts = path.stem.split("-")
        station = "-".join(parts[1:-1])
        element = parts[-1]
        if element not in ("TMA", "TMI"):
            raise ValueError(f"Unexpected element in filename: {path.name}")
        with path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            if not EXPECTED.issubset(set(reader.fieldnames or [])):
                raise ValueError(f"Unexpected header in {path.name}: {reader.fieldnames}")
            for row in reader:
                if row["STATION"] != station or row["ELEMENT"] != element:
                    raise ValueError(f"File/data key mismatch in {path.name}")
                stamp = datetime.fromisoformat(row["DT"].replace("Z", "+00:00"))
                if stamp.utcoffset() != timezone.utc.utcoffset(stamp):
                    raise ValueError(f"Non-UTC timestamp in {path.name}: {row['DT']}")
                if not (args.start_date <= stamp.date() <= args.end_date):
                    continue
                key = (station, element, row["DT"])
                if key in seen:
                    raise ValueError(f"Duplicate station/element/time: {key}")
                seen.add(key)
                value = row["VALUE"].strip()
                output.append({
                    "station": station,
                    "element": element,
                    "timefunc": row["TIMEFUNC"],
                    "dt_utc": stamp.isoformat().replace("+00:00", "Z"),
                    "value": value,
                    "flag": row["FLAG"],
                    "quality": row["QUALITY"],
                    "source_file": path.name,
                    "source_sha256": digest,
                })
    output.sort(key=lambda x: (x["dt_utc"], x["station"], x["element"]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["station", "element", "timefunc", "dt_utc", "value", "flag", "quality", "source_file", "source_sha256"]
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)
    print(f"rows={len(output)} files={len(files)} output={args.output}")


if __name__ == "__main__":
    main()
