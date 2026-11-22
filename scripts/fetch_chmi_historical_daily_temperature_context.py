#!/usr/bin/env python3
"""Fetch immutable CHMI daily mean temperature CSVs for regional context."""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://opendata.chmi.cz/meteorology/climate/historical_csv/data/daily/temperature"
OUT = ROOT / "data/chmi-historical-daily-temperature/raw"
MANIFEST = ROOT / "data/chmi-historical-daily-temperature/manifest.json"
STATIONS = {"0-203-0-11777": "Vizovice", "0-203-0-11778": "Kladná-Žilín"}

def fetch(station: str, name: str, expected_sha256: str | None) -> dict:
    filename = f"dly-{station}-T.csv"
    url = f"{BASE}/{filename}"
    path = OUT / filename
    if path.exists():
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if expected_sha256 and actual != expected_sha256:
            raise RuntimeError(f"Refusing to use changed immutable evidence: {path}")
        retrieved = None
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "LouckaWeatherReferenceAudit/1.0"})
        with urllib.request.urlopen(req, timeout=120) as response:
            if response.status != 200:
                raise RuntimeError(f"Unexpected HTTP {response.status}: {url}")
            raw = response.read()
        text = raw.decode("utf-8-sig")
        header = text.splitlines()[0].strip().rstrip(",")
        if header != "STATION,ELEMENT,TIMEFUNC,DT,VALUE,FLAG,QUALITY":
            raise ValueError(f"Unexpected CSV header in {url}: {header}")
        if not any(line.startswith(f"{station},T,AVG,") for line in text.splitlines()[1:]):
            raise ValueError(f"No daily mean temperature rows for {station}")
        OUT.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as f:
                f.write(raw)
        except FileExistsError:
            if path.read_bytes() != raw:
                raise RuntimeError(f"Refusing to overwrite changed evidence: {path}")
        retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {"station_id": station, "station_name": name,
            "url": url, "path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "retrieved_at_utc": retrieved, "status": "cached_immutable"}

def main() -> None:
    prior = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    prior_by_station = {x["station_id"]: x for x in prior.get("files", [])}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(lambda item: fetch(item[0],item[1],prior_by_station.get(item[0],{}).get("sha256")), STATIONS.items()))
    for row in rows:
        old = prior_by_station.get(row["station_id"], {})
        if old.get("sha256") == row["sha256"]:
            row["retrieved_at_utc"] = old.get("retrieved_at_utc")
    doc = {"schema": "loucka-chmi-historical-daily-temperature-context-v1",
           "provider": "Český hydrometeorologický ústav",
           "dataset": "historical daily mean air temperature (T, AVG)",
           "source_base_url": BASE,
           "method": "Official station CSV files are immutable local evidence. Daily means are regional context and are not treated as direct substitutes for civil-month archive means; daily observation window semantics remain a limitation.",
           "files": sorted(rows, key=lambda x: x["station_id"])}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({"files": len(rows), "bytes": sum(x["bytes"] for x in rows),
                      "sha256": {x["station_id"]: x["sha256"] for x in rows}}, indent=2))

if __name__ == "__main__":
    main()
