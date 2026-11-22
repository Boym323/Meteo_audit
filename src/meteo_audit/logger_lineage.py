"""Forensic lineage evidence: website generator != data logger != import.

Only directly timestamped archival snapshots can bound a *website generator*
change. Database fingerprints can identify recording/storage changes, but
cannot prove that the logger was replaced. No DB connections or writes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


class LineageEvidenceError(ValueError):
    """Insufficient, mixed, or malformed source evidence."""


GENERATORS = frozenset(("Cumulus", "WeeWX"))
OBSERVATION_LEVELS = frozenset(("DIRECT_ARCHIVE", "USER_REPORTED_YEAR"))
ALLOWED_MARKER_TYPES = frozenset((
    "archive_last_before_gap",
    "archive_first_after_gap",
    "first_field_present",
    "first_subminute_timestamp",
    "first_nonfive_interval",
    "numeric_unit_ratio_break",
))


def _epoch(value: Any, label: str) -> int:
    if type(value) is not int or value < 0:
        raise LineageEvidenceError(label + " must be a nonnegative UTC integer")
    return value


def evaluate_logger_lineage(registry: Mapping[str, Any]) -> dict[str, Any]:
    """Make constrained conclusions; never infer logger switch from DB alone."""
    if registry.get("schema") != "loucka-cumulus-weewx-lineage-v1":
        raise LineageEvidenceError("unknown evidence registry schema")
    observations = registry.get("web_observations")
    markers = registry.get("archive_markers")
    if not isinstance(observations, list) or not isinstance(markers, list):
        raise LineageEvidenceError("web_observations and archive_markers must be lists")

    direct: dict[str, list[int]] = {x: [] for x in GENERATORS}
    reported: dict[str, list[int]] = {x: [] for x in GENERATORS}
    for row in observations:
        if not isinstance(row, dict):
            raise LineageEvidenceError("invalid observation")
        if set(row) - {"generator", "evidence_type", "capture_utc", "year", "source_ref",
                       "displayed_station", "displayed_units", "software_version"}:
            raise LineageEvidenceError("unexpected web observation keys or inferred logger")
        generator = row.get("generator")
        level = row.get("evidence_type")
        if generator not in GENERATORS or level not in OBSERVATION_LEVELS:
            raise LineageEvidenceError("unknown generator or evidence type")
        if not isinstance(row.get("source_ref"), str) or not row["source_ref"].strip():
            raise LineageEvidenceError("untraceable observation")
        if level == "DIRECT_ARCHIVE":
            ts = _epoch(row.get("capture_utc"), "capture_utc")
            actual_year = datetime.fromtimestamp(ts, timezone.utc).year
            if row.get("year") != actual_year:
                raise LineageEvidenceError("capture year does not match timestamp")
            direct[generator].append(ts)
        else:
            if "capture_utc" in row or type(row.get("year")) is not int:
                raise LineageEvidenceError("year-only report cannot impersonate exact capture")
            reported[generator].append(row["year"])

    for marker in markers:
        if not isinstance(marker, dict) or set(marker) - {
            "marker_type", "source", "time_utc", "source_ref", "notes"
        }:
            raise LineageEvidenceError("archive marker contains unsupported software claim")
        if marker.get("marker_type") not in ALLOWED_MARKER_TYPES:
            raise LineageEvidenceError("unknown pipeline marker")
        _epoch(marker.get("time_utc"), "marker.time_utc")
        if not isinstance(marker.get("source"), str) or not marker["source"].strip():
            raise LineageEvidenceError("pipeline source missing")
        if not isinstance(marker.get("source_ref"), str) or not marker["source_ref"].strip():
            raise LineageEvidenceError("pipeline evidence source missing")

    first_direct_weewx = min(direct["WeeWX"], default=None)
    last_direct_cumulus = max(direct["Cumulus"], default=None)
    if first_direct_weewx is None or last_direct_cumulus is None:
        website_result = "NO_EXACT_WEB_GENERATOR_SWITCH_BOUND"
    elif last_direct_cumulus < first_direct_weewx:
        website_result = "BOUNDED_WEB_GENERATOR_CHANGE_ONLY"
    else:
        website_result = "OVERLAPPING_GENERATORS_OR_ARCHIVE_CHRONOLOGY"

    return {
        "schema": "loucka-logger-lineage-assessment-v1",
        "last_direct_cumulus_utc": last_direct_cumulus,
        "first_direct_weewx_utc": first_direct_weewx,
        "reported_cumulus_years": sorted(set(reported["Cumulus"])),
        "reported_weewx_years": sorted(set(reported["WeeWX"])),
        "website_generator_assessment": website_result,
        "archive_pipeline_marker_count": len(markers),
        "logger_switched_at_utc": None,
        "hardware_switched_at_utc": None,
        "source_import_method": "UNVERIFIED",
        "disposition": "FORENSIC_EVIDENCE_ONLY_NO_HISTORIC_DATA_WRITE",
    }
