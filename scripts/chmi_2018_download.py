#!/usr/bin/env python3
"""Download and normalize CHMI 10-minute T/H observations; no database access."""
import argparse
import calendar
import csv
import hashlib
import json
import math
import time
from urllib.error import HTTPError
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://opendata.chmi.cz/meteorology/climate/historical/data/10min"
STATIONS = ("0-203-0-11777", "0-203-0-11778")


def parse(raw, station, year, month):
    data = json.loads(raw)["data"]["data"]
    if data["header"].replace(" ", "") != "STATION,ELEMENT,DT,VAL,FLAG,QUALITY":
        raise ValueError("Unexpected CHMI header")
    rows, issues = {}, Counter()
    for s, element, stamp, value, flag, quality in data["values"]:
        if s != station:
            raise ValueError(f"Unexpected station: {s}")
        if element not in ("T", "H"):
            continue
        dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if (dt.utcoffset() != timezone.utc.utcoffset(dt)
                or dt.year != year or dt.month != month
                or dt.minute % 10 or dt.second or dt.microsecond):
            raise ValueError(f"Unexpected timestamp: {stamp}")
        key = (int(dt.timestamp()), element)
        if key in rows:
            raise ValueError(f"Duplicate {key}")
        valid = (isinstance(value, (int, float)) and not isinstance(value, bool)
                 and math.isfinite(value)
                 and ((-60 <= value <= 60) if element == "T" else (0 <= value <= 100)))
        if not valid:
            issues[f"{element}_invalid_or_missing"] += 1
        if flag not in ("", None) or quality != 0:
            issues[f"{element}_flag_or_quality_nonzero"] += 1
        # Preserve flags and original values; range checks are not official quality certification.
        rows[key] = (value, flag, quality, valid)
    for element in ("T", "H"):
        if not any(e == element for _, e in rows):
            issues[f"{element}_absent"] += 1
    return rows, issues


def read_file(path, url, station, year, month):
    if path.exists():
        raw = path.read_bytes()
        rows, issues = parse(raw, station, year, month)
        return raw, rows, issues
    for attempt in range(3):
        try:
            req = Request(url, headers={"User-Agent": "LouckaWeatherReferenceAudit/1.0"})
            with urlopen(req, timeout=120) as response:
                raw = response.read()
            rows, issues = parse(raw, station, year, month)
            tmp = path.with_suffix(".tmp")
            tmp.write_bytes(raw)
            tmp.replace(path)
            return raw, rows, issues
        except HTTPError as exc:
            if exc.code == 404 or attempt == 2:
                raise
            time.sleep(2 ** attempt)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("data/chmi-2018"))
    p.add_argument("--include-boundary", action="store_true",
                   help="try December 2017 for the local-year boundary; record unavailable files")
    args = p.parse_args()
    root = args.out
    rawdir = root / "raw"
    rawdir.mkdir(parents=True, exist_ok=True)
    periods = [(2018, m) for m in range(1, 13)]
    if args.include_boundary:
        periods.insert(0, (2017, 12))
    manifest, normalized = [], []
    for station in STATIONS:
        for year, month in periods:
            ym = f"{year}{month:02d}"
            name = f"10m-{station}-{ym}.json"
            url = f"{BASE}/{year}/{name}"
            print(f"Fetching {url}", flush=True)
            expected = calendar.monthrange(year, month)[1] * 144
            try:
                raw, rows, issues = read_file(rawdir / name, url, station, year, month)
            except HTTPError as exc:
                if (year, month) != (2017, 12) or exc.code != 404:
                    raise
                manifest.append(dict(station=station, month=ym, url=url, bytes=0,
                                     sha256=None, expected=expected, valid_T=0,
                                     valid_H=0, paired=0, status="unavailable_http_404",
                                     issues={"boundary_unavailable": 1}))
                print(f"WARNING: {station} {ym} unavailable (404); no extrapolation.", flush=True)
                continue
            timestamps = sorted({t for t, e in rows})
            n_t = sum(e == "T" and v[3] for (_, e), v in rows.items())
            n_h = sum(e == "H" and v[3] for (_, e), v in rows.items())
            paired = 0
            for t in timestamps:
                T = rows.get((t, "T"), (None, None, None, False))
                H = rows.get((t, "H"), (None, None, None, False))
                paired += int(T[3] and H[3])
                normalized.append((station, t, datetime.fromtimestamp(t, timezone.utc).isoformat(), *T, *H))
            manifest.append(dict(station=station, month=ym, url=url, bytes=len(raw),
                                 sha256=hashlib.sha256(raw).hexdigest(), expected=expected,
                                 valid_T=n_t, valid_H=n_h, paired=paired, status="downloaded", issues=dict(issues)))
            print(station, ym, paired, "/", expected, flush=True)
    csv_tmp = root / "reference_TH.csv.tmp"
    with csv_tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["station", "timestamp_utc", "iso_utc", "temperature_c", "T_flag",
                    "T_quality", "T_range_valid", "relative_humidity_pct", "H_flag",
                    "H_quality", "H_range_valid"])
        w.writerows(normalized)
    csv_tmp.replace(root / "reference_TH.csv")
    manifest_tmp = root / "manifest.json.tmp"
    manifest_tmp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest_tmp.replace(root / "manifest.json")
    downloaded = sum(row["status"] == "downloaded" for row in manifest)
    print(f"Completed: {downloaded} files; {len(manifest)-downloaded} unavailable optional files; no database writes.")


if __name__ == "__main__":
    main()
