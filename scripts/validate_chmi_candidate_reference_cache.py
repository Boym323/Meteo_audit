#!/usr/bin/env python3
"""Fail closed if frozen 2026 CHMI reference inputs are missing or altered."""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/chmi-2026-recent/manifest.json"

def main():
    doc = json.loads(MANIFEST.read_text())
    if doc.get("schema") != "loucka-chmi-temperature-reference-cache-v1":
        raise SystemExit("Unexpected CHMI candidate reference cache schema")
    if len(doc.get("files", [])) != 4:
        raise SystemExit("Expected four CHMI station-month source files for Jan/Feb 2026")
    checked = []
    for item in doc["files"]:
        path = ROOT / item["path"]
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != item["sha256"] or len(raw) != item["bytes"]:
            raise SystemExit(f"Reference file hash/size mismatch: {item['path']}")
        period = item["period"]
        if period not in {"2026-01", "2026-02"} or item["station_id"] not in {"0-203-0-11777", "0-203-0-11778"}:
            raise SystemExit(f"Unexpected station or period in reference manifest: {item}")
        if item["temperature_rows"] <= 0:
            raise SystemExit(f"No temperature rows recorded: {item['path']}")
        checked.append({"path": item["path"], "sha256": digest, "temperature_rows": item["temperature_rows"]})
    print(json.dumps({"files_verified": len(checked), "records": checked,
                      "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest()}, indent=2))

if __name__ == "__main__": main()
