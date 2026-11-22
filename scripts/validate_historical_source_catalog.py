#!/usr/bin/env python3
"""Validate that the catalog is bound to the captured live inventory and graph."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"pocasi-loucka.eu", "pocasi-loucka.eu_old", "pocasi-loucka.eu_GW1000", "old_weewx", "weewx_WH1080", "loucka_reconstruction"}


def main() -> None:
    read = lambda p: json.loads((ROOT / p).read_text(encoding="utf-8"))
    snap = read("data/HISTORICAL_SOURCE_INVENTORY_LIVE.json")
    catalog = read("HISTORICAL_SOURCE_CATALOG.json")
    graph = read("HISTORICAL_SOURCE_DEPENDENCY_GRAPH.json")
    digest = hashlib.sha256((ROOT / "data/HISTORICAL_SOURCE_INVENTORY_LIVE.json").read_bytes()).hexdigest()
    assert catalog["inventory_snapshot_sha256"] == digest
    assert {x["database"] for x in catalog["sources"]} == EXPECTED
    assert {x["database"] for x in snap["archives"]} == EXPECTED
    by_name = {x["database"]: x for x in snap["archives"]}
    for source in catalog["sources"]:
        live = by_name[source["database"]]["archive"]
        assert source["row_count"] == live["row_count"]
        assert source["distinct_timestamps"] == live["distinct_timestamps"]
        assert source["duplicate_timestamp_count"] == 0
        assert source["usUnits_distribution"] == live["usUnits_distribution"]
        assert source["interval_minutes_distribution"] == live["interval_minutes_distribution"]
        assert source["schema_sha256"] == live["schema_sha256"]
    ids = [x["id"] for x in graph["nodes"]]
    assert len(ids) == len(set(ids))
    known = set(ids)
    assert all(e["from"] in known and e["to"] in known for e in graph["edges"])
    assert catalog["reconstruction_and_sync_evidence"]["applied_estimate_operation_count"] == 30537
    print(json.dumps({"status": "PASS", "source_archives": len(EXPECTED), "dependency_nodes": len(ids),
                      "dependency_edges": len(graph["edges"]), "inventory_sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
