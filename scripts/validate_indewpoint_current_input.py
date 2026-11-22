"""Validate the compact inDewpoint formula-consistency aggregate."""
from csv import DictReader
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "reports/2026-11-13-indewpoint-current-input-consistency.csv"
row = next(DictReader(p.open(newline="", encoding="utf-8")))
expected = {"compared": 433955, "within_0_1c": 433955, "greater_0_1c": 0, "greater_1c": 0, "greater_2c": 0}
for key, value in expected.items():
    assert int(row[key]) == value, key
assert int(row["within_0_1c"]) + int(row["greater_0_1c"]) == int(row["compared"])
assert int(row["greater_2c"]) <= int(row["greater_1c"]) <= int(row["greater_0_1c"])
assert float(row["max_abs_delta_c"]) < 0.1
print("inDewpoint current-input consistency checks: OK")
