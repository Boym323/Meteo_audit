#!/usr/bin/env python3
"""Build a compact CSV view from frozen read-only 2017 RH evidence."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / "data/rh_p2_2017_regional_conflict_review.json").read_text())
fields = [
    "dateTime", "source_rh", "luhamet_rh", "rh_difference_pp", "source_temp",
    "target_temp", "prev_rh", "next_rh", "prev_temp", "next_temp",
    "source_rain", "wh_rain", "source_rainRate", "wh_rainRate",
    "source_wind", "wh_wind", "all_events", "rh_events",
    "euold_row", "eu_row", "gw_row", "old_row", "wh_row",
]
out = ROOT / "data/rh_p2_2017_regional_conflict_review.csv"
with out.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows({k: row[k] for k in fields} for row in source["rows"])
print(f"wrote {len(source['rows'])} rows to {out.relative_to(ROOT)}")
