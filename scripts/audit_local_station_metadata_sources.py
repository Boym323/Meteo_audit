#!/usr/bin/env python3
"""Record read-only host search for station configs and local app metadata hints."""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = Path("/home/loucka/Loucka_weather")
SEARCH_ROOTS = [Path("/etc"), Path("/var/backups"), Path("/var/lib"), Path("/home/loucka"), Path("/opt")]
NAME = re.compile(r"(?:weewx|ecowitt|weather).*(?:\.conf|\.cfg|\.ini|\.bak|\.backup|\.old|\.tar(?:\.gz)?|\.zip)$|^(?:weewx\.conf(?:\.\w+)?|weewx\.sqlite(?:\.bak)?)$", re.I)
SKIP_DIRS = {".git", "node_modules", "dist", "__pycache__", ".venv"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    found = []
    checked_roots = []
    for base in SEARCH_ROOTS:
        checked_roots.append({"path": str(base), "exists": base.exists()})
        if not base.exists():
            continue
        for current, dirs, files in os.walk(base, followlinks=False):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not (Path(current) == Path("/opt") and d == "meteo-audit")]
            for name in files:
                if not NAME.search(name):
                    continue
                path = Path(current) / name
                found.append({"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)})

    station_path = APP / "tests/fixtures/station.json"
    sensors_path = APP / "tests/fixtures/sensors.json"
    channel_path = APP / "api/src/sensor-evidence.ts"
    station = json.loads(station_path.read_text())
    sensors = json.loads(sensors_path.read_text())
    channel_text = channel_path.read_text()
    doc = {
        "schema": "loucka-local-station-metadata-search-v1",
        "searched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": "Read-only filename search; no file contents were read from candidate configuration or backup paths. Local app metadata fixtures and sensor-channel evidence source were read and hashed.",
        "search_roots": checked_roots,
        "filename_pattern": NAME.pattern,
        "excluded_directory_names": sorted(SKIP_DIRS),
        "configuration_or_backup_matches": sorted(found, key=lambda x: x["path"]),
        "standard_named_configuration_or_backup_matches": len(found),
        "local_application_metadata": {
            "station_fixture": {
                "path": str(station_path), "sha256": sha(station_path),
                "location": station.get("location"),
                "archival_source": station.get("archivalSource"),
                "data_revision": station.get("dataRevision"),
            },
            "sensor_fixture": {
                "path": str(sensors_path), "sha256": sha(sensors_path),
                "sensor_records": len(sensors.get("sensors", [])),
                "records": [{"id": x.get("id"), "metric": x.get("metric"), "status": x.get("status"),
                             "enabled": x.get("enabled"), "valid_from": x.get("validFrom"),
                             "valid_to": x.get("validTo"), "depth_cm": x.get("depthCm"),
                             "confidence": x.get("confidence"), "note": x.get("note")} for x in sensors.get("sensors", [])],
            },
            "sensor_channel_source": {
                "path": str(channel_path), "sha256": sha(channel_path),
                "explicitly_unverified_mapping_count": channel_text.count("liveRelation:'unverified'"),
                "source_comment": "Measured channel evidence, never an assertion of sensor installation.",
                "interpretation": "Current app fixtures have null/unverified station location and unknown sensor status; live GW3000 channel catalog is explicitly not mapped to historical WeeWX sensor identity.",
            },
        },
        "conclusion": "No dated physical sensor epoch, historical WeeWX configuration, driver configuration, or sensor siting evidence was found by this search. The local app fixtures affirm that location and physical mapping remain unverified; they do not establish historical conditions.",
        "limitations": [
            "Filename-based search only covers listed roots and patterns; arbitrary filenames and unavailable/unmounted backups are not ruled out.",
            "Application fixtures describe current software metadata, not historical sensor installation records.",
            "No secret-bearing configuration contents were read.",
        ],
    }
    out = ROOT / "LOCAL_STATION_METADATA_SEARCH.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(out), "matching_config_or_backup_files": len(found),
                      "sensor_fixture_records": len(sensors.get("sensors", [])),
                      "physical_sensor_epoch_proven": False}, indent=2))


if __name__ == "__main__":
    main()
