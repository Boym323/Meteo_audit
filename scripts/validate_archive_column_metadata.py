#!/usr/bin/env python3
"""Reconcile the information_schema archive column metadata export."""
import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "reports/2026-11-13-archive-column-metadata.csv"
with path.open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream))
schemas = sorted({row["TABLE_SCHEMA"] for row in rows})
assert len(rows) == 515
assert len(schemas) == 6
by_schema = {schema: [row for row in rows if row["TABLE_SCHEMA"] == schema] for schema in schemas}
assert {schema: len(values) for schema, values in by_schema.items()} == {
    "loucka_reconstruction": 80,
    "old_weewx": 61,
    "pocasi-loucka.eu": 80,
    "pocasi-loucka.eu_GW1000": 66,
    "pocasi-loucka.eu_old": 114,
    "weewx_WH1080": 114,
}
column_maps = {schema: {row["COLUMN_NAME"]: row for row in values} for schema, values in by_schema.items()}
all_names = set().union(*(set(mapping) for mapping in column_maps.values()))
assert len(all_names) == 155
presence = Counter(sum(name in column_maps[schema] for schema in schemas) for name in all_names)
assert presence == Counter({1: 7, 2: 59, 3: 40, 4: 4, 5: 16, 6: 29})
signature_fields = ("COLUMN_TYPE", "IS_NULLABLE", "COLUMN_DEFAULT", "EXTRA", "COLUMN_KEY")
signature = lambda row: tuple(row[field] for field in signature_fields)
for name in all_names:
    present = [schema for schema in schemas if name in column_maps[schema]]
    if len(present) == 6:
        assert len({signature(column_maps[schema][name]) for schema in schemas}) == 1
only_one = {name for name in all_names if sum(name in column_maps[s] for s in schemas) == 1}
assert only_one == {"espHumidity", "raindrop", "Illuminance", "dustDensity", "espbarometer", "esppressure", "espaltimeter"}
assert all(name in column_maps["old_weewx"] for name in only_one)
for a, b, sizes, common, only_a, only_b in (
    ("loucka_reconstruction", "pocasi-loucka.eu", (80, 80), 80, 0, 0),
    ("pocasi-loucka.eu_GW1000", "pocasi-loucka.eu", (66, 80), 44, 22, 36),
    ("pocasi-loucka.eu_old", "weewx_WH1080", (114, 114), 114, 0, 0),
    ("old_weewx", "weewx_WH1080", (61, 114), 53, 8, 61),
):
    left, right = set(column_maps[a]), set(column_maps[b])
    shared = left & right
    assert (len(left), len(right), len(shared), len(left-right), len(right-left)) == (*sizes, common, only_a, only_b)
    assert all(signature(column_maps[a][n]) == signature(column_maps[b][n]) for n in shared)
print("PASS: 515 column records, six archive schemas, 155 names, and key schema comparisons reconcile")
