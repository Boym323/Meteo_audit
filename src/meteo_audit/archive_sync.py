"""INSERT-only GW3000 archive synchronizer planning primitives.

The planner is deliberately independent of a driver.  It never fills NULLs,
converts units, or treats an incomplete source read as an empty success.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import isfinite
from numbers import Real
from typing import Any, Iterable, Mapping

PROTECTED_LOWER_BOUND = 1_793_286_600  # 2026-10-29T15:10:00Z, strict
EXPECTED_US_UNITS = 16
EXPECTED_INTERVAL_MINUTES = 5
ARCHIVE_FIELDS = frozenset("""dateTime usUnits interval altimeter appTemp barometer batteryStatus1 batteryStatus2 bgt cloudbase dewpoint ET extraHumid1 extraHumid2 extraTemp1 extraTemp2 heatindex humidex inDewpoint inHumidity inTemp lightning_Batt lightning_distance lightning_disturber_count lightning_energy lightning_noise_count lightning_strike_count luminosity maxSolarRad outHumidity outTemp pb pm25_1 pm25_Batt1 pressure radiation rain rainDur rainRate soilad1 soilMoist1 soilMoistBatt1 soilTemp1 soilTemp2 soilTemp3 soilTemp4 soilTemp5 soilTemp6 sunshine_time sunshineDur UV vpd wbgt wh26_rssi wh31_ch1_rssi wh31_ch1_sig wh31_ch2_sig wh40_rssi wh41_ch1_rssi wh51_ch1_rssi wh51_ch1_sig wh57_rssi windchill windDir windGust windGustDir windrun windSpeed ws80_batt ws80_rssi ws80_sig outEquiTemp GTS GTSdate dayET ET24 yearGDD seasonGDD outHumAbs outThetaE""".split())
VALUE_FIELDS = ARCHIVE_FIELDS - {"dateTime", "usUnits", "interval"}


class SyncError(ValueError):
    """Invalid, incomplete, or conflicting synchronization input."""


@dataclass(frozen=True)
class SyncAction:
    kind: str
    timestamp: int
    values: Mapping[str, Any]
    us_units: int
    interval_minutes: int


@dataclass(frozen=True)
class SyncConflict:
    timestamp: int
    variable: str
    reason: str
    source_value: Any = None
    target_value: Any = None


@dataclass(frozen=True)
class SyncPlan:
    window_start: int
    window_end_exclusive: int
    captured_source_max: int | None
    previous_watermark: int
    proposed_watermark: int
    actions: tuple[SyncAction, ...]
    conflicts: tuple[SyncConflict, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"window_start": self.window_start, "window_end_exclusive": self.window_end_exclusive,
                "captured_source_max": self.captured_source_max, "previous_watermark": self.previous_watermark,
                "proposed_watermark": self.proposed_watermark,
                "actions": [asdict(x) for x in self.actions], "conflicts": [asdict(x) for x in self.conflicts]}


def _validate_row(row: Mapping[str, Any], *, side: str) -> None:
    missing = ARCHIVE_FIELDS - set(row)
    extra = set(row) - ARCHIVE_FIELDS
    if missing or extra:
        raise SyncError(f"{side} row schema mismatch; missing={sorted(missing)}, extra={sorted(extra)}")
    for name in ("dateTime", "usUnits", "interval"):
        value = row[name]
        if type(value) is not int:
            raise SyncError(f"{side} {name} must be an integer")
    for name in VALUE_FIELDS:
        value = row[name]
        if value is not None and (isinstance(value, bool) or not isinstance(value, Real) or not isfinite(float(value))):
            raise SyncError(f"{side} {name} must be NULL or a finite numeric value")


def validate_action(action: SyncAction, *, lower_exclusive: int = PROTECTED_LOWER_BOUND,
                    upper_exclusive: int | None = None) -> None:
    """Validate untrusted serialized actions immediately before writing."""
    if action.kind != "INSERT_ROW":
        raise SyncError("only INSERT_ROW actions are supported")
    _validate_row(action.values, side="action")
    if type(action.timestamp) is not int or action.timestamp <= lower_exclusive:
        raise SyncError("action timestamp violates strict lower protection boundary")
    if upper_exclusive is not None and action.timestamp >= upper_exclusive:
        raise SyncError("action timestamp is outside the authorized exclusive upper bound")
    if action.values["dateTime"] != action.timestamp:
        raise SyncError("action timestamp differs from values.dateTime")
    if action.us_units != EXPECTED_US_UNITS or action.values["usUnits"] != EXPECTED_US_UNITS:
        raise SyncError("action units differ from authorized units")
    if action.interval_minutes != EXPECTED_INTERVAL_MINUTES or action.values["interval"] != EXPECTED_INTERVAL_MINUTES:
        raise SyncError("action interval differs from authorized interval")


def map_archive_row(source: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return the complete approved 80-column mapping, NULLs included."""
    _validate_row(source, side="source")
    return {name: source[name] for name in sorted(ARCHIVE_FIELDS, key=lambda x: (x != "dateTime", x))}


def build_sync_plan(
    source_rows: Iterable[Mapping[str, Any]] | None,
    target_rows: Iterable[Mapping[str, Any]],
    *, watermark: int, window_end: int, lookback_seconds: int = 86_400,
    source_complete: bool = True, source_schema: Iterable[str] | None = None,
    target_schema: Iterable[str] | None = None,
    protected_timestamps: set[int] | None = None,
    protected_fields: set[tuple[int, str]] | None = None,
) -> SyncPlan:
    """Plan complete row inserts only, for ``window_start <= ts < window_end``.

    ``window_end`` is exclusive; snapshot callers must use captured max + 1 so
    the row at the captured maximum is included.  The cursor advances only if
    every source record is complete and conflict-free.
    """
    if source_rows is None or not source_complete:
        raise SyncError("source read was unavailable or incomplete; watermark cannot advance")
    if type(watermark) is not int or watermark < 0 or type(window_end) is not int or window_end <= watermark:
        raise SyncError("watermark and exclusive window_end must be valid and window_end must exceed watermark")
    if type(lookback_seconds) is not int or lookback_seconds < 0:
        raise SyncError("lookback_seconds must be a non-negative integer")
    if source_schema is not None and set(source_schema) != ARCHIVE_FIELDS:
        raise SyncError("source schema differs from the approved 80-column mapping")
    if target_schema is not None and set(target_schema) != ARCHIVE_FIELDS:
        raise SyncError("target schema differs from the approved 80-column mapping")
    # Re-scan the complete post-fence range on each run. A simple recent
    # lookback can permanently miss a late arrival older than that window.
    window_start = PROTECTED_LOWER_BOUND + 1
    targets: dict[int, Mapping[str, Any]] = {}
    for row in target_rows:
        _validate_row(row, side="target")
        if row["dateTime"] in targets:
            raise SyncError(f"duplicate target timestamp {row['dateTime']}")
        targets[row["dateTime"]] = row

    src: dict[int, Mapping[str, Any]] = {}
    conflicts: list[SyncConflict] = []
    source_max: int | None = None
    for raw in source_rows:
        _validate_row(raw, side="source")
        ts = raw["dateTime"]
        if ts < window_start or ts >= window_end:
            continue
        source_max = ts if source_max is None else max(source_max, ts)
        prior = src.get(ts)
        if prior is not None and dict(prior) != dict(raw):
            conflicts.append(SyncConflict(ts, "*", "conflicting duplicate source rows"))
        else:
            src[ts] = map_archive_row(raw)

    actions: list[SyncAction] = []
    protected = protected_timestamps or set()
    protected_fields = protected_fields or set()
    for ts, row in sorted(src.items()):
        if ts <= PROTECTED_LOWER_BOUND:
            conflicts.append(SyncConflict(ts, "dateTime", "timestamp is at or before the strict protection boundary"))
            continue
        if row["usUnits"] != EXPECTED_US_UNITS:
            conflicts.append(SyncConflict(ts, "usUnits", "source units differ from approved epoch", row["usUnits"], EXPECTED_US_UNITS)); continue
        if row["interval"] != EXPECTED_INTERVAL_MINUTES:
            conflicts.append(SyncConflict(ts, "interval", "source interval differs from approved 5-minute epoch", row["interval"], EXPECTED_INTERVAL_MINUTES)); continue
        if not any(row[name] is not None for name in VALUE_FIELDS):
            conflicts.append(SyncConflict(ts, "*", "all meteorological fields are NULL; row cannot establish completeness or advance cursor")); continue
        if ts in protected:
            conflicts.append(SyncConflict(ts, "*", "timestamp is protected by reconstruction history")); continue
        target = targets.get(ts)
        if target is None:
            blocked = sorted(name for stamp, name in protected_fields if stamp == ts)
            if blocked:
                conflicts.append(SyncConflict(ts, "*", "new row contains protected fields; INSERT is blocked", blocked, None))
                continue
            actions.append(SyncAction("INSERT_ROW", ts, row, EXPECTED_US_UNITS, EXPECTED_INTERVAL_MINUTES))
            continue
        # Existing timestamps are immutable in this mode.  Compare every field
        # so mismatches are visible; matching rows are harmless idempotent replay.
        differences = [name for name in ARCHIVE_FIELDS if target[name] != row[name]]
        if differences:
            for name in differences:
                conflicts.append(SyncConflict(ts, name, "existing target row differs; INSERT-only mode leaves it unchanged", row[name], target[name]))

    proposed = max(watermark, source_max if source_max is not None else watermark)
    if conflicts:
        proposed = watermark
    return SyncPlan(window_start, window_end, source_max, watermark, proposed, tuple(actions), tuple(conflicts))


def apply_plan_to_memory(plan: SyncPlan, target_rows: Iterable[Mapping[str, Any]], *, fail_after: int | None = None) -> list[dict[str, Any]]:
    """Atomic in-memory simulation only; not evidence of database integration."""
    if plan.conflicts:
        raise SyncError("plan contains conflicts; no actions applied")
    original = [dict(row) for row in target_rows]
    copy = [dict(row) for row in original]
    index = {row["dateTime"]: row for row in copy}
    for i, action in enumerate(plan.actions):
        if fail_after is not None and i >= fail_after:
            raise RuntimeError("simulated transaction failure")
        if action.kind != "INSERT_ROW":
            raise SyncError(f"unsupported action kind {action.kind}")
        if action.timestamp in index:
            raise SyncError("insert target appeared after planning")
        new_row = dict(action.values)
        if new_row["dateTime"] != action.timestamp:
            raise SyncError("mapped timestamp changed after planning")
        copy.append(new_row); index[action.timestamp] = new_row
    return sorted(copy, key=lambda row: row["dateTime"])


def committed_watermark(plan: SyncPlan, *, transaction_succeeded: bool) -> int:
    if not transaction_succeeded or plan.conflicts:
        return plan.previous_watermark
    return plan.proposed_watermark
