#!/usr/bin/env python3
"""Deterministic validation for the targeted three-row, read-only source review."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
d = json.loads((ROOT / "data/long_gap_three_singleton_source_rows.json").read_text())
rows = d["rows"]
assert [r["gap_id"] for r in rows] == [1, 4, 5]
assert len({r["timestamp"] for r in rows}) == 3
assert d["summary"] == {"rows": 3, "off_grid_rows": 3, "legacy_copy_agreement_rows": 3, "change_events": 0, "restored_proposals": 0, "estimated_proposals": 0}
for r in rows:
    assert r["timestamp"] % 300 == r["epoch_grid_remainder_seconds"] != 0
    assert r["legacy_copy_agreement"] is True
    assert r["reconstruction_change_events"] == 0
    assert r["source_metadata"]["old_weewx"] == {"usUnits": 17, "interval": 5}
    assert r["source_metadata"]["weewx_WH1080"] == {"usUnits": 17, "interval": 5}
    assert r["archive_row_presence"]["old_weewx"] and r["archive_row_presence"]["weewx_WH1080"]
    assert not r["archive_row_presence"]["loucka_reconstruction"]
    assert r["disposition"].startswith("REVIEW_REQUIRED_OFF_GRID_")
assert d["safety"] == {"database_writes": 0, "staging": False, "application": False, "publication": False}
print("PASS: 3 exact keys; all off-grid, copies concordant, no changes, no proposals")
