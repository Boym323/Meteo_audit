"""Aggregate-only QC for lightning cross-archive evidence.

The checks detect suspicious mapping patterns; they do not establish field
semantics or authorize correction of stored observations.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

SUMMARY_FIELDS = (
    "source",
    "target_n",
    "matched_rows",
    "disturber_nonnull",
    "disturber_exact_matches",
    "noise_nonnull",
    "noise_equals_strike",
)
EXAMPLE_FIELDS = (
    "dateTime",
    "lightning_disturber_count",
    "lightning_strike_count",
    "lightning_noise_count",
)


class LightningEvidenceError(ValueError):
    """Malformed or internally inconsistent lightning evidence."""


def _count(row: Mapping[str, object], key: str) -> int:
    raw = row.get(key)
    if isinstance(raw, bool):
        raise LightningEvidenceError(f"{key} must be a non-negative integer")
    try:
        value = int(raw)  # CSV values are strings; JSON callers may pass ints.
    except (TypeError, ValueError) as exc:
        raise LightningEvidenceError(f"{key} must be a non-negative integer") from exc
    if str(raw).strip() not in (str(value), f"+{value}") or value < 0:
        raise LightningEvidenceError(f"{key} must be a non-negative integer")
    return value


def inspect_lightning_evidence(
    summaries: Sequence[Mapping[str, object]],
    examples: Sequence[Mapping[str, object]],
    *,
    target_source: str,
) -> dict[str, int | str]:
    """Validate bounded summary/sample rows and return aggregate-only findings.

    Source labels and individual timestamps/values are deliberately omitted
    from the result so it is safe to include in CI logs.
    """
    if not target_source:
        raise LightningEvidenceError("target_source is required")
    if not summaries:
        raise LightningEvidenceError("at least one summary row is required")

    by_source: dict[str, Mapping[str, object]] = {}
    for row in summaries:
        missing = set(SUMMARY_FIELDS) - set(row)
        if missing:
            raise LightningEvidenceError("summary row is missing required fields")
        source = str(row["source"])
        if not source or source in by_source:
            raise LightningEvidenceError("summary source labels must be non-empty and unique")
        by_source[source] = row

    if target_source not in by_source:
        raise LightningEvidenceError("target_source is absent from summaries")

    for row in summaries:
        values = {key: _count(row, key) for key in SUMMARY_FIELDS[1:]}
        if values["matched_rows"] > values["target_n"]:
            raise LightningEvidenceError("matched_rows cannot exceed target_n")
        if values["disturber_nonnull"] > values["matched_rows"]:
            raise LightningEvidenceError("disturber_nonnull cannot exceed matched_rows")
        if values["disturber_exact_matches"] > values["disturber_nonnull"]:
            raise LightningEvidenceError("disturber_exact_matches exceeds non-null observations")
        if values["noise_nonnull"] > values["matched_rows"]:
            raise LightningEvidenceError("noise_nonnull cannot exceed matched_rows")
        if values["noise_equals_strike"] > values["noise_nonnull"]:
            raise LightningEvidenceError("noise_equals_strike exceeds non-null observations")

    timestamp_like = noise_alias = samples_with_disturber = 0
    for row in examples:
        if set(EXAMPLE_FIELDS) - set(row):
            raise LightningEvidenceError("sample row is missing required fields")
        timestamp = _count(row, "dateTime")
        disturber = _optional_count(row, "lightning_disturber_count")
        strike = _optional_count(row, "lightning_strike_count")
        noise = _optional_count(row, "lightning_noise_count")
        if disturber is not None:
            samples_with_disturber += 1
            timestamp_like += disturber > timestamp
        if noise is not None and strike is not None:
            noise_alias += noise == strike

    target = by_source[target_source]
    return {
        "schema": "lightning-qc-summary-v1",
        "source_count": len(by_source),
        "target_rows": _count(target, "target_n"),
        "sample_rows": len(examples),
        "samples_with_disturber": samples_with_disturber,
        "disturber_exceeds_epoch_count": timestamp_like,
        "noise_equals_strike_count": noise_alias,
        "interpretation": "diagnostic_only_mapping_semantics_unverified",
    }


def _optional_count(row: Mapping[str, object], key: str) -> int | None:
    raw = row.get(key)
    if raw is None or (isinstance(raw, str) and raw.strip().upper() in ("", "NULL", "\\N")):
        return None
    return _count(row, key)
