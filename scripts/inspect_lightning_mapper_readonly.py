"""Sanitized, read-only inspection of *local* WeeWX/Ecowitt lightning mapping.

Prints only allowlisted field identifiers and conservative warnings; never
outputs raw configuration lines, secrets, payloads, source files or values.
Does NOT infer correct mapping without original raw payload/driver evidence.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FIELDS = frozenset({
    "lightning_disturber_count", "lightning_noise_count",
    "lightning_strike_count", "lightning_distance", "lightning_energy",
    "lightning_time", "lightning_last_det_time", "lightning_num",
    "lightning", "lightningcount", "lightning_dist",
})
TARGETS = frozenset({"lightning_disturber_count", "lightning_noise_count"})
TIMESTAMP_LIKE = frozenset({"lightning_time", "lightning_last_det_time"})
ASSIGN = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
SAFE = re.compile(r"^[A-Za-z][A-Za-z0-9_.]{0,99}$")


def inspect_configuration(contents: str) -> dict[str, object]:
    """Inspect simple allowlisted field mappings; ignore all other values."""
    candidates: list[dict[str, object]] = []
    for line_number, raw_line in enumerate(contents.splitlines(), 1):
        cleaned = raw_line.split("#", 1)[0].split(";", 1)[0].strip()
        match = ASSIGN.fullmatch(cleaned)
        if not match:
            continue
        left, value = match.groups()
        if left not in FIELDS:
            continue
        # Do not print secret/config value even if it is attached to a
        # lightning field by mistake. Only report known enumerated field names.
        right = value if SAFE.fullmatch(value) and value in FIELDS else None
        warning = (
            "POSSIBLE_TIMESTAMP_IN_DISTURBER"
            if left == "lightning_disturber_count" and right in TIMESTAMP_LIKE
            else "POSSIBLE_STRIKE_ALIAS_IN_NOISE"
            if left == "lightning_noise_count" and right in {"lightning_strike_count", "lightning_num", "lightningcount"}
            else "UNVERIFIED_FIELD_SEMANTICS"
        )
        candidates.append({
            "line": line_number,
            "target": left,
            "mapped_allowlisted_key": right,
            "status": warning,
        })
    return {
        "schema": "loucka-lightning-mapper-local-inspection-v1",
        "mapping_candidates": candidates,
        "driver_and_raw_payload_verified": False,
        "historical_db_update_authorized": False,
    }


def inspect_driver_presence(contents: str) -> dict[str, int]:
    """Only count allowed token occurrences, never emit source content."""
    return {
        field: len(re.findall(r"(?<![A-Za-z0-9_])" + re.escape(field) + r"(?![A-Za-z0-9_])", contents))
        for field in sorted(FIELDS)
        if re.search(r"(?<![A-Za-z0-9_])" + re.escape(field) + r"(?![A-Za-z0-9_])", contents)
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only, sanitized local WeeWX lightning mapper review")
    parser.add_argument("--weewx-conf", type=Path, required=True)
    parser.add_argument("--driver-source", type=Path)
    args = parser.parse_args()
    # This command reads local files. No network, SQL, process restart, or log dump.
    config = args.weewx_conf.read_text(encoding="utf-8", errors="replace")
    if len(config) > 2_000_000:
        parser.error("configuration larger than the safe limit")
    result = inspect_configuration(config)
    if args.driver_source:
        driver = args.driver_source.read_text(encoding="utf-8", errors="replace")
        if len(driver) > 2_000_000:
            parser.error("driver larger than the safe limit")
        result["driver_allowlisted_token_counts"] = inspect_driver_presence(driver)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
