#!/usr/bin/env python3
"""Validate the CHMI local-mean-solar-time window comparison artifacts."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
base = ROOT / "reports/2026-11-13-chmi-sra-lmt-offset"
with (base.with_suffix(".summary.csv")).open(encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 14
get = {(r["station"], r["candidate"]): r for r in rows}
for station, pairs, matches, wet, wet_matches in (
    ("0-203-0-11777", 328, 328, 154, 154),
    ("0-203-0-11778", 334, 333, 106, 106),
):
    r = get[(station, "assigned_day_07_lmt_nearest_10m")]
    assert int(r["qc_pairs"]) == pairs
    assert int(r["matches_within_0_05mm"]) == matches
    assert int(r["wet_qc_rows"]) == wet
    assert int(r["wet_matches_within_0_05mm"]) == wet_matches
    assert abs(float(r["mae_mm"])) < 0.00031
    assert get[(station, "assigned_day_07_lmt_nearest_10m")]["matches_within_0_05mm"] >= \
           get[(station, "dt_plus_24h")]["matches_within_0_05mm"]
manifest = json.loads(base.with_suffix(".manifest.json").read_text(encoding="utf-8"))
assert len(manifest["source_files"]) == 28
assert len(manifest["outputs"]) == 2
assert all(len(x["sha256"]) == 64 for x in manifest["source_files"] + manifest["outputs"] + [manifest["script"]])
for item in manifest["source_files"] + manifest["outputs"] + [manifest["script"]]:
    path = Path(item["path"])
    raw = path.read_bytes()
    assert len(raw) == item["bytes"]
    assert hashlib.sha256(raw).hexdigest() == item["sha256"]
with base.with_suffix(".csv").open(encoding="utf-8", newline="") as f:
    detail = list(csv.DictReader(f))
assert len(detail) == 730
assert sum(r["daily_qc_valid"] == "True" and
           r["assigned_day_07_lmt_nearest_10m_complete_qc_window"] == "True" and
           r["assigned_day_07_lmt_nearest_10m_exact_to_0_1mm"] == "True" and
           float(r["assigned_day_07_lmt_nearest_10m_daily_mm"] or 0) > 0 for r in detail
           if r["station"] == "0-203-0-11777") == 154
assert sum(r["daily_qc_valid"] == "True" and
           r["assigned_day_07_lmt_nearest_10m_complete_qc_window"] == "True" and
           r["assigned_day_07_lmt_nearest_10m_exact_to_0_1mm"] == "True" and
           float(r["assigned_day_07_lmt_nearest_10m_daily_mm"] or 0) > 0 for r in detail
           if r["station"] == "0-203-0-11778") == 106
print("PASS: both-station LMT endpoint, wet-day validation, 730 detail rows, and source/output hashes")
