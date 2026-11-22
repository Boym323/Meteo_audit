"""Shared evidence classifier for monthly and annual statistics.

Readiness is an expert evidence outcome; it never grants publication authority.
"""
from __future__ import annotations


def classify_evidence(e: dict) -> tuple[str, str]:
    """Classify a normalized evidence record using conservative ordered gates."""
    # Accept the two historical caller contracts while they migrate. Explicit
    # normalized keys take precedence, including explicit False values.
    def get(primary: str, legacy: str | None = None, default=None):
        return e[primary] if primary in e else e.get(legacy, default) if legacy else default
    if e.get("protected"): return "PROTECTED", "Period is protected."
    if e.get("diagnostic"): return "DIAGNOSTIC_ONLY", "Period is diagnostic-only."
    if e.get("e4"): return "BLOCKED_E4", "Rain semantics are unresolved."
    if not get("integrity_ok", "integrity"): return "REVIEW_REQUIRED_PROVENANCE", "Snapshot integrity is not established."
    if e.get("estimates", 0): return "REVIEW_REQUIRED_ESTIMATES", "Statistic includes estimates."
    if not e.get("representative"): return "NOT_REPRESENTATIVE_COVERAGE", "Sampling or gap screen failed."
    if get("sensor_error", "known_sensor_fault"): return "REVIEW_REQUIRED_SENSOR_VALIDATION", "Known sensor fault requires review."
    if get("unresolved_conflicts", "unmatched_conflicts", 0): return "REVIEW_REQUIRED_CONFLICTS", "Value conflicts remain unresolved."
    if not get("physical_validation", "physical_interpretation"): return "REVIEW_REQUIRED_SENSOR_VALIDATION", "Physical interpretation or sensor validation is incomplete."
    if not get("provenance_sufficient", "value_provenance"): return "REVIEW_REQUIRED_PROVENANCE", "Value-level provenance is insufficient."
    if e.get("external_validation") and e.get("independent_sensor_lineage"):
        return "READY_FOR_PUBLICATION", "Required evidence, including independent validation, passes."
    if e.get("documented_archive_continuity") and e.get("explicit_limitations"):
        return "READY_WITH_DISCLOSED_LIMITATIONS", "Archive continuity supports a limited station statistic with disclosed lineage limits."
    return "REVIEW_REQUIRED_PROVENANCE", "Evidence does not meet a recommendation level."
