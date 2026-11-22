#!/usr/bin/env python3
"""Verify local finalization hashes/counts without exposing operation values or using a DB."""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, help="Write sanitized summary JSON; stdout by default")
    args = parser.parse_args()
    root = args.root.resolve()
    checkpoint_path = root / "MASTER_FINALIZATION_CHECKPOINT_20261117.json"
    manifest_path = root / "FINAL_MIGRATION_MANIFEST_20261117.jsonl"
    diff_path = root / "final_migration_package" / "MIGRATION_DIFF.csv"
    summary_path = root / "FINAL_MIGRATION_DECISION_SUMMARY_20261117.json"
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    expected_summary = json.loads(summary_path.read_text(encoding="utf-8"))

    status_counts: collections.Counter[str] = collections.Counter()
    reason_counts: collections.Counter[str] = collections.Counter()
    with manifest_path.open(encoding="utf-8") as stream:
        metadata = json.loads(next(stream))
        for line in stream:
            record = json.loads(line)
            if record.get("record_type") != "operation":
                raise ValueError("unexpected non-operation record after manifest metadata")
            status_counts[record["final_status"]] += 1
            reason_counts[record["decision_reason_code"]] += 1

    manifest_hash = sha256(manifest_path)
    diff_hash = sha256(diff_path)
    expected_count = int(metadata["expected_operation_count"])
    observed_count = sum(status_counts.values())
    checkpoint_manifest = checkpoint["manifest"]
    checkpoint_diff = checkpoint["source_diff"]
    expected_statuses = {k: int(v) for k, v in expected_summary["statuses"].items()}
    expected_reasons = {k: int(v) for k, v in expected_summary["by_reason_code"].items()}
    observed_statuses = dict(sorted(status_counts.items()))
    observed_reasons = dict(sorted(reason_counts.items()))
    checks = {
        "manifest_hash_matches_checkpoint": manifest_hash == checkpoint_manifest["sha256"],
        "manifest_hash_matches_decision_summary": manifest_hash == expected_summary["manifest_sha256"],
        "diff_hash_matches_checkpoint": diff_hash == checkpoint_diff["sha256"],
        "diff_hash_matches_decision_summary": diff_hash == expected_summary["diff_sha256"],
        "operation_count_matches_metadata": observed_count == expected_count == int(checkpoint_manifest["operation_count"]),
        "status_counts_match_checkpoint": observed_statuses == {k: int(v) for k, v in checkpoint_manifest["statuses"].items()},
        "status_counts_match_decision_summary": observed_statuses == expected_statuses,
        "reason_counts_match_checkpoint": observed_reasons == {k: int(v) for k, v in checkpoint_manifest["status_reason_counts"].items()},
        "reason_counts_match_decision_summary": observed_reasons == expected_reasons,
        "status_sum_verified": observed_count == sum(observed_statuses.values()),
    }
    result = {
        "schema": "loucka-finalization-integrity-verification-v1",
        "verification": "PASS" if all(checks.values()) else "FAIL",
        "source_artifacts": {
            "checkpoint": checkpoint_path.name,
            "manifest": manifest_path.name,
            "migration_diff": "final_migration_package/MIGRATION_DIFF.csv",
            "decision_summary": summary_path.name,
        },
        "sha256": {"manifest": manifest_hash, "migration_diff": diff_hash,
                   "checkpoint": sha256(checkpoint_path), "decision_summary": sha256(summary_path)},
        "operation_count": observed_count,
        "status_counts": observed_statuses,
        "reason_counts": observed_reasons,
        "checks": checks,
        "database_access_performed": False,
        "operation_level_values_emitted": False,
    }
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
