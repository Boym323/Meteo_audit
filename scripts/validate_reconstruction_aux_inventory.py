#!/usr/bin/env python3
"""Reconcile exact reconstruction auxiliary row counts and state aggregates."""
import csv
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with (root / "reports/2026-11-13-reconstruction-aux-exact-counts.csv").open(newline="", encoding="utf-8") as f:
    counts = list(csv.DictReader(f))
with (root / "reports/2026-11-13-reconstruction-aux-state-summary.csv").open(newline="", encoding="utf-8") as f:
    states = list(csv.DictReader(f))
assert len(counts) == 17 and len({r["table_name"] for r in counts}) == 17
assert {r["snapshot_utc"] for r in counts + states} == {"2026-11-13T03:58Z"}
c = {r["table_name"]: int(r["exact_rows"]) for r in counts}
assert c["reconstruction_batches"] == 24
assert c["reconstruction_candidates"] == 365
assert c["reconstruction_changes"] == 112772
assert c["reference_observations"] == 1652638
assert c["reconstruction_humidity_202204"] == 3734
s = {(r["entity"], r["bucket"]): int(r["exact_rows"]) for r in states}
assert s[("batch", "pending")] + s[("batch", "cancelled")] == c["reconstruction_batches"]
assert s[("batch_candidates", "pending")] + s[("batch_candidates", "cancelled")] == c["reconstruction_candidates"]
assert s[("changes", "applied")] + s[("changes", "reverted")] == c["reconstruction_changes"]
assert s[("reference_observations", "luhamet_sehradice")] + s[("reference_observations", "wu_ilouka4")] == c["reference_observations"]
assert s[("humidity_202204", "estimate_ready")] + s[("humidity_202204", "invalidate_frozen")] + s[("humidity_202204", "missing_unresolved")] == c["reconstruction_humidity_202204"]
print("PASS: 17 exact table counts and state/station subtotals reconcile")
