#!/usr/bin/env python3
"""Fetch official CHMI 10-minute files for currently uncovered 2026 candidates."""
import csv, hashlib, json, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://opendata.chmi.cz/meteorology/climate/recent/data/10min"
PERIODS = ("2026-01", "2026-02")
STATIONS = {"0-203-0-11777": "Vizovice", "0-203-0-11778": "Kladná-Žilín"}
OUT = ROOT / "data/chmi-2026-recent/raw"

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    old_manifest_path = ROOT / "data/chmi-2026-recent/manifest.json"
    old_manifest = json.loads(old_manifest_path.read_text()) if old_manifest_path.exists() else {}
    old_by_path = {x["path"]: x for x in old_manifest.get("files", [])}
    entries = []
    for period in PERIODS:
        year, month = period.split("-")
        for station, name in STATIONS.items():
            filename = f"10m-{station}-{year}{month}.json"
            url = f"{BASE}/{month}/{filename}"
            path = OUT / filename
            if not path.exists():
                request = urllib.request.Request(url, headers={"User-Agent": "LouckaWeatherReferenceAudit/1.0"})
                with urllib.request.urlopen(request, timeout=120) as response:
                    if response.status != 200:
                        raise RuntimeError(f"Unexpected HTTP status {response.status} for {url}")
                    data = response.read()
                path.write_bytes(data)
            data = path.read_bytes()
            raw = json.loads(data)
            values = raw["data"]["data"]["values"]
            header = raw["data"]["data"]["header"].replace(" ", "")
            if header not in ("STATION,ELEMENT,DT,VAL,FLAG,QUALITY", "STATION,ELEMENT,DT,VALUE,FLAG,QUALITY"):
                raise ValueError(f"Unexpected CHMI header {header!r} in {filename}")
            if not values or any(row[0] != station for row in values):
                raise ValueError(f"Empty or station-mismatched CHMI file: {filename}")
            elements = sorted({row[1] for row in values})
            if "T" not in elements:
                raise ValueError(f"Temperature element missing in {filename}")
            relpath = path.relative_to(ROOT).as_posix()
            previous = old_by_path.get(relpath, {})
            retrieved = previous.get("retrieved_at_utc") if previous.get("sha256") == hashlib.sha256(data).hexdigest() else None
            entries.append({
                "path": relpath, "url": url, "provider": "ČHMÚ",
                "station_id": station, "station_name": name, "period": period,
                "element": "T", "cadence": "10-minute UTC timestamps", "header": header,
                "row_count": len(values), "temperature_rows": sum(row[1] in ("T", "TA") for row in values),
                "quality_counts": {str(q): sum(str(row[5]) == str(q) for row in values if row[1] in ("T", "TA")) for q in sorted({str(row[5]) for row in values if row[1] in ("T", "TA")})},
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "retrieved_at_utc": retrieved or datetime.now(timezone.utc).isoformat(timespec="seconds")
            })
    manifest = {
        "schema": "loucka-chmi-temperature-reference-cache-v1", "provider": "Český hydrometeorologický ústav",
        "dataset": "10-minute station air temperature", "periods": list(PERIODS), "source_base_url": BASE,
        "source_snapshot_note": "CHMI recent monthly files for January and February 2026; cached unchanged for UTC boundary matching.",
        "files": entries, "reused_without_modification": True
    }
    (ROOT / "data/chmi-2026-recent/manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(entries), "temperature_rows": [x["temperature_rows"] for x in entries],
                      "sha256": [x["sha256"] for x in entries]}, indent=2))

if __name__ == "__main__":
    main()
