#!/usr/bin/env python3
"""Run an offline correction-package simulation from JSON snapshot artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from meteo_audit.simulation import ArchiveRow, Correction, SimulationConflict, order_batches, simulate_batch


def read_package(path: Path):
    package = json.loads(path.read_text(encoding="utf-8"))
    if package.get("schema_version") != "1.0":
        raise ValueError("package schema_version must be '1.0'")
    columns = package["schema_columns"]
    if len(set(columns)) != len(columns) or not columns:
        raise SimulationConflict("schema_columns must be non-empty and unique")
    rows = {}
    for item in package["archive_rows"]:
        timestamp = int(item["timestamp"])
        if timestamp in rows:
            raise SimulationConflict(f"duplicate snapshot timestamp: {timestamp}")
        rows[timestamp] = ArchiveRow(
            int(item["us_units"]), int(item["interval_minutes"]), item["fields"]
        )
    sources = {}
    for item in package["source_observations"]:
        key = (item["database"], int(item["timestamp"]), item["variable"])
        if key in sources:
            raise SimulationConflict(f"duplicate source observation: {key}")
        sources[key] = item["value"]
    batches = package["batches"]
    ids = order_batches(batches)
    batch_by_id = {item["batch_id"]: item for item in batches}
    if len(batch_by_id) != len(batches):
        raise SimulationConflict("duplicate batch_id in package")
    return package, columns, rows, sources, ids, batch_by_id


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="local JSON package and snapshot; never connects to DB")
    parser.add_argument("--output", type=Path, required=True, help="local JSON simulation result")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a new path so prior results are preserved")
    package, columns, rows, sources, order, batch_by_id = read_package(args.package)
    ledger: dict[str, str] = {}
    results = []
    for batch_id in order:
        spec = batch_by_id[batch_id]
        corrections = [Correction(**item) for item in spec["corrections"]]
        result, ledger = simulate_batch(
            rows, corrections, sources, columns, batch_id=batch_id,
            prior_batches=ledger, fail_after=spec.get("inject_failure_after"),
        )
        rows = dict(result.output_rows)
        results.append({
            "batch_id": result.batch_id,
            "status": result.status,
            "payload_sha256": result.payload_sha256,
            "applied_operations": result.applied_operations,
            "before_stats": result.before_stats,
            "after_stats": result.after_stats,
        })
    output = {
        "simulation_scope": "LOCAL_ONLY_NOT_DATABASE_DRY_RUN",
        "input_package": str(args.package),
        "batch_order": order,
        "batch_results": results,
        "final_rows": {
            str(timestamp): {
                "us_units": row.us_units,
                "interval_minutes": row.interval_minutes,
                "fields": dict(row.fields),
            }
            for timestamp, row in sorted(rows.items())
        },
        "simulated_batch_ledger": ledger,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=args.output.parent,
                                     delete=False) as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        temp_path = Path(stream.name)
    temp_path.replace(args.output)
    print(f"local simulation complete: {args.output} ({len(results)} batches)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
