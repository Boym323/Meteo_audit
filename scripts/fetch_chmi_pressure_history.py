#!/usr/bin/env python3
"""Fetch official ČHMÚ pressure reference files and record immutable SHA-256s.

Raw data are intentionally ignored by git; only the manifest is publishable.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/chmi-pressure-2009-2026"
BASE = "https://opendata.chmi.cz/meteorology/climate"
STATIONS = ("0-20000-0-11774", "0-20000-0-11782")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs.extend(v for k, v in attrs if k == "href")


def get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Meteo_audit pressure reference audit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read(), dict(response.headers)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    items = []

    def save(url: str, rel: str, kind: str, station: str | None = None, element: str | None = None):
        path = OUT / "raw" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            payload, headers = get(url)
        except urllib.error.HTTPError as exc:
            items.append({"path": rel, "url": url, "kind": kind, "station_id": station, "element": element,
                          "availability": "http_error", "http_status": exc.code, "retrieved_at_utc": retrieved})
            return False
        except Exception as exc:
            items.append({"path": rel, "url": url, "kind": kind, "station_id": station, "element": element,
                          "availability": "fetch_error", "error_type": type(exc).__name__, "retrieved_at_utc": retrieved})
            return False
        if path.exists() and sha(path.read_bytes()) != sha(payload):
            raise SystemExit(f"Refusing to overwrite changed immutable cache: {path}")
        if not path.exists():
            path.write_bytes(payload)
        items.append({"path": rel, "url": url, "kind": kind, "station_id": station, "element": element,
                      "availability": "available", "http_status": 200, "bytes": len(payload), "sha256": sha(payload),
                      "content_type": headers.get("Content-Type"), "last_modified": headers.get("Last-Modified"),
                      "etag": headers.get("ETag"), "retrieved_at_utc": retrieved})
        return True

    # Official station history files.
    for sid in STATIONS:
        station_no = sid.rsplit("-", 1)[-1]
        url = f"{BASE}/historical_csv/data/daily/air_pressure/dly-{sid}-P.csv"
        save(url, f"daily-{station_no}-P.csv", "daily_csv", sid, "P")

    historical = f"{BASE}/historical_csv/data/1hour/synop"
    monthly_present = set()
    for year in range(2018, 2026):
        index_url = f"{historical}/{year}/"
        try:
            html, _ = get(index_url)
            parser = Links(); parser.feed(html.decode("utf-8", "replace"))
            names = set(parser.hrefs)
        except Exception as exc:
            raise SystemExit(f"Could not enumerate official CHMI directory {index_url}: {type(exc).__name__}")
        for sid in STATIONS:
            for element in ("P", "P_hm"):
                for month in range(1, 13):
                    name = f"1h-{sid}-{element}-{year}{month:02d}.csv"
                    if name not in names:
                        items.append({"path": f"hourly/{year}/{name}", "url": f"{index_url}{name}", "kind": "hourly_csv",
                                      "station_id": sid, "element": element, "period": f"{year}-{month:02d}",
                                      "availability": "not_listed", "retrieved_at_utc": retrieved})
                        continue
                    ok = save(f"{index_url}{name}", f"hourly/{year}/{name}", "hourly_csv", sid, element)
                    if ok:
                        items[-1]["period"] = f"{year}-{month:02d}"
                        monthly_present.add(f"{year}-{month:02d}")

    recent = f"{BASE}/recent/data/1hour"
    for month in range(1, 13):
        mm = f"{month:02d}"
        try:
            html, _ = get(f"{recent}/{mm}/")
            parser = Links(); parser.feed(html.decode("utf-8", "replace"))
            names = set(parser.hrefs)
        except Exception as exc:
            items.append({"period": f"2026-{mm}", "availability": "directory_error", "error_type": type(exc).__name__, "retrieved_at_utc": retrieved})
            continue
        for sid in STATIONS:
            name = f"1h-{sid}-2026{mm}.json"
            if name not in names:
                items.append({"path": f"recent/{mm}/{name}", "url": f"{recent}/{mm}/{name}", "kind": "recent_json",
                              "station_id": sid, "period": f"2026-{mm}", "availability": "not_listed", "retrieved_at_utc": retrieved})
                continue
            ok = save(f"{recent}/{mm}/{name}", f"recent/{mm}/{name}", "recent_json", sid)
            if ok:
                items[-1]["period"] = f"2026-{mm}"

    # The current month is published as one JSON per station and UTC day in
    # the recent root directory (the month subdirectory is a different batch).
    try:
        html, _ = get(f"{recent}/")
        parser = Links(); parser.feed(html.decode("utf-8", "replace"))
        names = set(parser.hrefs)
    except Exception as exc:
        names = set()
        items.append({"period": "2026-current", "availability": "directory_error", "error_type": type(exc).__name__, "retrieved_at_utc": retrieved})
    for sid in STATIONS:
        day_names = sorted(n for n in names if re.fullmatch(rf"1h-{re.escape(sid)}-2026\d{{4}}\.json", n))
        for name in day_names:
            day = name.rsplit("-", 1)[-1][:8]
            ok = save(f"{recent}/{name}", f"recent/daily/{name}", "recent_daily_json", sid)
            if ok:
                items[-1]["period"] = f"{day[:4]}-{day[4:6]}"
                items[-1]["date"] = f"{day[:4]}-{day[4:6]}-{day[6:8]}"

    docs = []
    doc_dir = OUT / "docs"
    for filename, source_url in (
        ("metadata.json", f"{BASE}/historical/metadata/meta1.json"),
        ("meta2.csv", f"{BASE}/historical_csv/metadata/meta2.csv"),
        ("meta3.csv", f"{BASE}/historical_csv/metadata/meta3.csv"),
        ("meta4.csv", f"{BASE}/historical_csv/metadata/meta4.csv"),
        ("description.pdf", f"{BASE}/Klimatologicka_data_popis.pdf"),
    ):
        path = doc_dir / filename
        payload, _ = get(source_url)
        if path.exists() and sha(path.read_bytes()) != sha(payload):
            raise SystemExit(f"Refusing to overwrite changed official documentation cache: {path}")
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(payload)
        docs.append({"path": str(path.relative_to(OUT)), "url": source_url, "sha256": sha(path.read_bytes()), "bytes": path.stat().st_size})
    manifest = {"schema": "loucka-chmi-pressure-reference-manifest-v1", "provider": "Český hydrometeorologický ústav",
                "base_urls": [f"{BASE}/historical_csv/data/daily/air_pressure/", f"{historical}/", f"{recent}/"],
                "retrieved_at_utc": retrieved, "historical_hourly_years": "2018–2025", "recent_year": 2026,
                "documentation_sources": docs, "items": items}
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"items": len(items), "available": sum(x.get("availability") == "available" for x in items),
                      "not_listed": sum(x.get("availability") == "not_listed" for x in items),
                      "error": sum(x.get("availability") in ("http_error", "fetch_error", "directory_error") for x in items),
                      "historical_months": len(monthly_present), "manifest": str(OUT / "manifest.json")}, indent=2))


if __name__ == "__main__":
    main()
