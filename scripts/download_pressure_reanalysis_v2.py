#!/usr/bin/env python3
"""Download hourly Open-Meteo ERA5 pressure context with response-level provenance.

ERA5-Land pressure is deliberately not downloaded through this API: tested
requests return null pressure fields for that model. Use the authenticated CDS
product only when its terms and an authorized API token are available.
"""
from __future__ import annotations
import argparse, hashlib, json, time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

URL = "https://archive-api.open-meteo.com/v1/archive"
POINTS = {
    "loucka_era5_nearest": {"latitude": 49.165277777777774, "longitude": 17.8775,
                              "meaning": "Loucka nominal ERA5 nearest cell; sensitivity point at 49.25N 18.00E"},
    "loucka_era5_adjacent": {"latitude": 49.165277777777774, "longitude": 17.75,
                               "meaning": "Loucka adjacent ERA5 longitude sensitivity; 49.25N 17.75E"},
    "holesov_era5": {"latitude": 49.3206, "longitude": 17.5700,
                       "meaning": "CHMI WSI 0-20000-0-11774 station location"},
    "mosnov_era5": {"latitude": 49.6918, "longitude": 18.1126,
                      "meaning": "CHMI WSI 0-20000-0-11782 station location"},
}


def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "Meteo_audit/pressure-reanalysis-audit (research)"})
    for attempt in range(5):
        try:
            with urlopen(req, timeout=90) as response:
                body = response.read()
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                return body
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--start-year", type=int, default=2009)
    ap.add_argument("--end-date", default="2026-11-24")
    args = ap.parse_args()
    end = date.fromisoformat(args.end_date)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": "loucka-pressure-era5-api-manifest-v1", "provider": "Open-Meteo Historical Weather API",
                "source_url": URL, "requested_model": "era5", "hourly_variables": ["pressure_msl", "surface_pressure", "temperature_2m"],
                "requested_units": {"pressure": "hPa", "temperature": "°C"}, "elevation_parameter": "nan (disable statistical elevation correction)",
                "timezone": "GMT", "hourly_temporal_support": "hourly model values; not 5-minute observations",
                "points": {}, "responses": []}
    for key, point in POINTS.items():
        manifest["points"][key] = point
        for year in range(args.start_year, end.year + 1):
            start_date = date(year, 1, 1)
            stop_date = min(date(year, 12, 31), end) if year == end.year else date(year, 12, 31)
            params = {"latitude": f"{point['latitude']:.9f}", "longitude": f"{point['longitude']:.9f}",
                      "start_date": start_date.isoformat(), "end_date": stop_date.isoformat(),
                      "hourly": "pressure_msl,surface_pressure,temperature_2m", "models": "era5",
                      "timezone": "GMT", "timeformat": "iso8601", "elevation": "nan"}
            url = URL + "?" + urlencode(params)
            body = fetch(url)
            payload = json.loads(body)
            for field in ("pressure_msl", "surface_pressure", "temperature_2m"):
                if field not in payload.get("hourly", {}):
                    raise RuntimeError(f"Missing {field} in {key}/{year}")
            if payload.get("hourly_units", {}).get("pressure_msl") != "hPa" or payload.get("hourly_units", {}).get("surface_pressure") != "hPa":
                raise RuntimeError(f"Unexpected pressure units at {key}/{year}")
            if payload.get("timezone") != "GMT" or payload.get("utc_offset_seconds") != 0:
                raise RuntimeError(f"Unexpected timezone at {key}/{year}")
            name = f"{key}-{year}.json"
            (args.out_dir / name).write_bytes(body)
            vals = payload["hourly"]["surface_pressure"]
            record = {"file": name, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body),
                      "request_url": url, "requested_start": start_date.isoformat(), "requested_end": stop_date.isoformat(),
                      "returned_latitude": payload["latitude"], "returned_longitude": payload["longitude"],
                      "returned_grid_elevation_m": payload["elevation"], "hours_returned": len(payload["hourly"]["time"]),
                      "surface_pressure_non_null": sum(v is not None for v in vals),
                      "pressure_msl_non_null": sum(v is not None for v in payload["hourly"]["pressure_msl"]),
                      "temperature_2m_non_null": sum(v is not None for v in payload["hourly"]["temperature_2m"])}
            manifest["responses"].append(record)
            print(json.dumps({"point": key, "year": year, "bytes": len(body),
                              "grid": [record["returned_latitude"], record["returned_longitude"]],
                              "hours": record["hours_returned"], "surface_p_non_null": record["surface_pressure_non_null"]}))
    manifest["responses"].sort(key=lambda x: x["file"])
    raw_manifest = json.dumps(manifest, indent=2, ensure_ascii=False).encode() + b"\n"
    (args.out_dir / "manifest.json").write_bytes(raw_manifest)
    print(json.dumps({"status": "DONE", "responses": len(manifest["responses"]), "manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(), "directory": str(args.out_dir)}))


if __name__ == "__main__":
    main()
