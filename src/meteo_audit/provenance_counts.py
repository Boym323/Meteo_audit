"""Snapshot-bound value provenance counts from concordance rollups."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


PROVENANCE_FIELDS = (
    "source_matched",
    "conflicting_source",
    "recovered_source",
    "estimated",
    "restored",
    "corrected",
    "original_verified",
    "unclassified",
)
OUTPUT_NAMES = {
    "source_matched": "SOURCE_MATCHED",
    "conflicting_source": "CONFLICTING_SOURCE",
    "recovered_source": "RECOVERED_SOURCE",
    "estimated": "ESTIMATED",
    "restored": "RESTORED",
    "corrected": "CORRECTED",
    "original_verified": "ORIGINAL_VERIFIED",
    "unclassified": "UNCLASSIFIED",
}


def build_provenance_counts(database: Path, prior_output: Path | None = None) -> dict:
    """Derive all field/value provenance totals from a read-only SQLite snapshot.

    ``field_rollup`` is the snapshot builder's controlled per-period/per-field
    aggregate. Its category partition is checked before totals are emitted.
    The target row count is independently read from ``timestamp_evidence``.
    """
    database = Path(database).resolve()
    uri = f"file:{database.as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        metadata = dict(connection.execute("SELECT key, value FROM snapshot_meta"))
        target = json.loads(metadata["target"])
        fields = json.loads(metadata["fields"])
        actual_rows = int(connection.execute("SELECT COUNT(*) FROM timestamp_evidence").fetchone()[0])
        if actual_rows != int(target["rows"]):
            raise ValueError(f"Snapshot row count mismatch: metadata={target['rows']} actual={actual_rows}")
        found_fields = {row[0] for row in connection.execute("SELECT DISTINCT variable FROM field_rollup")}
        if found_fields != set(fields):
            raise ValueError(f"Rollup field set mismatch: metadata={sorted(fields)} rollup={sorted(found_fields)}")
        columns = ",".join(f"SUM({name})" for name in PROVENANCE_FIELDS)
        rows = connection.execute(
            f"SELECT variable, SUM(target_nonnull), {columns}, "
            "SUM(target_null_with_source_value), SUM(unresolved) FROM field_rollup "
            "WHERE length(period)=7 GROUP BY variable"
        ).fetchall()
        year_rows = connection.execute(
            f"SELECT variable, SUM(target_nonnull), {columns}, "
            "SUM(target_null_with_source_value), SUM(unresolved) FROM field_rollup "
            "WHERE length(period)=4 GROUP BY variable"
        ).fetchall()
    finally:
        connection.close()

    by_variable = {}
    totals = {name: 0 for name in OUTPUT_NAMES.values()}
    null_with_source = 0
    nonempty_total = 0
    for row in rows:
        variable = row[0]
        nonempty = int(row[1] or 0)
        raw_categories = {OUTPUT_NAMES[field]: int(value or 0) for field, value in zip(PROVENANCE_FIELDS, row[2:10])}
        variable_null_with_source = int(row[10] or 0)
        variable_unresolved = int(row[11] or 0)
        if variable_null_with_source < 0:
            raise ValueError(f"Negative NULL_WITH_SOURCE_VALUE count for {variable}")
        variable_null_total = actual_rows - nonempty
        variable_null_without_source = variable_null_total - variable_null_with_source
        if variable_unresolved != variable_null_with_source:
            raise ValueError(f"NULL_WITH_SOURCE_VALUE rollup mismatch for {variable}")
        categories = dict(raw_categories)
        # In the source rollup, target-NULL/no-source fields use the
        # UNCLASSIFIED category. Remove those NULLs to obtain nonempty-only
        # provenance; NULL-with-source fields are separately UNRESOLVED.
        categories["UNCLASSIFIED"] -= variable_null_without_source
        if categories["UNCLASSIFIED"] < 0 or sum(categories.values()) != nonempty:
            raise ValueError(f"Nonempty provenance partition failed for {variable}")
        by_variable[variable] = {
            "nonempty_total": nonempty,
            "nonempty_value_provenance": categories,
            "null_with_source_value": variable_null_with_source,
            "null_without_source_value": variable_null_without_source,
        }
        nonempty_total += nonempty
        null_with_source += variable_null_with_source
        for name, value in categories.items():
            totals[name] += value

    monthly_rollups = {row[0]: tuple(int(value or 0) for value in row[1:]) for row in rows}
    annual_rollups = {row[0]: tuple(int(value or 0) for value in row[1:]) for row in year_rows}
    if monthly_rollups.keys() != annual_rollups.keys():
        raise ValueError("Monthly and annual rollup variable sets differ")
    for variable, monthly in monthly_rollups.items():
        if monthly != annual_rollups[variable]:
            raise ValueError(f"Annual and monthly rollups disagree for {variable}")

    field_total = actual_rows * len(fields)
    null_total = field_total - nonempty_total
    null_without_source = null_total - null_with_source
    if min(null_total, null_with_source, null_without_source) < 0:
        raise ValueError("NULL count partition failed: derived negative count")
    if nonempty_total + null_total != field_total:
        raise ValueError("nonempty + missing != field slot total")
    if null_with_source + null_without_source != null_total:
        raise ValueError("NULL_WITH_SOURCE_VALUE + NULL_WITHOUT_SOURCE_VALUE != NULL_TOTAL")

    output = {
        "snapshot_rows": actual_rows,
        "field_count": len(fields),
        "field_value_total": field_total,
        "nonempty_total": nonempty_total,
        "nonempty_value_provenance": totals,
        "nonempty_percentages": {key: 100 * value / nonempty_total if nonempty_total else 0 for key, value in totals.items()},
        "all_field_slot_percentages": {key: 100 * value / field_total if field_total else 0 for key, value in totals.items()},
        "missing_values": {
            "NULL_WITH_SOURCE_VALUE": null_with_source,
            "NULL_WITHOUT_SOURCE_VALUE": null_without_source,
            "NULL_TOTAL": null_total,
        },
        "missing_percentages_of_all_field_slots": {
            "NULL_WITH_SOURCE_VALUE": 100 * null_with_source / field_total if field_total else 0,
            "NULL_WITHOUT_SOURCE_VALUE": 100 * null_without_source / field_total if field_total else 0,
            "NULL_TOTAL": 100 * null_total / field_total if field_total else 0,
        },
        "by_variable": by_variable,
        "source_snapshot_sha256": hashlib.sha256(database.read_bytes()).hexdigest(),
        "source_snapshot_metadata": {
            "schema": metadata.get("schema"),
            "snapshot_utc": metadata.get("snapshot_utc"),
            "database_identity": json.loads(metadata.get("database_identity", "{}")),
            "target": target,
            "fields": fields,
            "provenance_method": metadata.get("provenance_method"),
        },
        "invariants": {
            "snapshot_rows_times_field_count_equals_field_value_total": actual_rows * len(fields) == field_total,
            "nonempty_plus_missing_equals_field_total": nonempty_total + null_total == field_total,
            "provenance_categories_sum_to_nonempty": sum(totals.values()) == nonempty_total,
            "null_with_source_plus_null_without_source_equals_null_total": null_with_source + null_without_source == null_total,
            "annual_rollups_match_monthly_rollups": True,
        },
        "note": "Counts are derived from this snapshot's validated field_rollup aggregate. Missing target NULL status is orthogonal to nonempty-value provenance; no nulls are added to UNCLASSIFIED.",
    }
    if prior_output and Path(prior_output).exists():
        previous = json.loads(Path(prior_output).read_text(encoding="utf-8"))
        if previous.get("source_snapshot_sha256") == output["source_snapshot_sha256"]:
            previous_totals = previous.get("nonempty_value_provenance", {})
            previous_nulls = previous.get("missing_values", {})
            output["known_snapshot_comparison"] = {
                "matches_existing_counts": (
                    previous.get("field_value_total") == field_total
                    and previous.get("nonempty_total") == nonempty_total
                    and previous_totals == totals
                    and previous_nulls == output["missing_values"]
                ),
                "prior_artifact": str(Path(prior_output)),
            }
    if output.get("known_snapshot_comparison", {}).get("matches_existing_counts") is False:
        raise ValueError("Recomputed values differ from prior counts for the same snapshot hash")
    return output
