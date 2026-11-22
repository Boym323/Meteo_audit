#!/usr/bin/env python3
"""Validate the exact-count snapshot for production archive_day metric tables."""
import csv
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "reports/2026-11-13-production-archive-day-exact-inventory.csv"
with path.open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 78, f"expected 78 metric tables, got {len(rows)}"
assert len({r["table_name"] for r in rows}) == 78, "duplicate table names"
assert all(r["table_name"].startswith("archive_day_") for r in rows)
assert all(r["table_name"] != "archive_day__metadata" for r in rows)
assert {int(r["exact_rows"]) for r in rows} == {6104}
assert {int(r["first_epoch"]) for r in rows} == {1238281200}
assert {int(r["last_epoch"]) for r in rows} == {1794524400}
assert {r["first_utc"] for r in rows} == {"2009-03-28T23:00:00Z"}
assert {r["last_utc"] for r in rows} == {"2026-11-12T23:00:00Z"}
print("PASS: 78 unique metric tables; exact rows and key ranges reconcile")
