#!/usr/bin/env python3
"""Attach read-only reconstruction change history to the exact-source inventory."""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
decisions_path = ROOT / "data/EXACT_SOURCE_COHORT_DECISIONS.json"
history_path = ROOT / "data/EXACT_SOURCE_RECONSTRUCTION_HISTORY.json"
pending_path = ROOT / "data/EXACT_SOURCE_PENDING_COHORT_INTERSECTIONS.json"
csv_path = ROOT / "data/REMAINING_EXACT_SOURCE_CANDIDATES.csv"

doc = json.loads(decisions_path.read_text(encoding="utf-8"))
events = json.loads(history_path.read_text(encoding="utf-8"))
pending = json.loads(pending_path.read_text(encoding="utf-8"))["records"]
by_key = defaultdict(list)
pending_by_key = defaultdict(list)
for event in events:
    by_key[(int(event["target_time"]), event["variable"])].append(event)
for event in pending:
    pending_by_key[(int(event["dateTime"]), event["variable"])].append(event)

cohorts = Counter()
for row in doc["records"]:
    history = by_key.get((int(row["dateTime"]), row["variable"]), [])
    staged = pending_by_key.get((int(row["dateTime"]), row["variable"]), [])
    row["history"] = history
    row["pending_review_candidates"] = staged
    if history:
        row["cohort"] = "HISTORICALLY_REMOVED_INVALID_DATA"
        row["decision_status"] = "REJECT_RESTORATION_PRESERVE_INTENTIONAL_NULL"
        row["reason"] = "Current exact-source candidate overlaps an applied invalidation. Original source readings were judged invalid/unreliable; source archive copies do not reverse that decision."
    else:
        legacy_values = [row["source_values"].get(k) for k in ("old_weewx", "weewx_WH1080")]
        legacy_values = [x for x in legacy_values if x is not None]
        primary_value = row["source_values"].get("old")
        if row["variable"] == "outTemp" and row["timestamp_utc"].startswith("2020-04-23T"):
            row["cohort"] = "SOURCE_CONFLICT_SUSPECTED_STALE_PLATEAU"
            row["decision_status"] = "REJECT_CURRENT_SOURCE_VALUE_PENDING_SENSOR_EPOCH_REVIEW"
            row["reason"] = "pocasi-loucka.eu_old repeats outTemp=4.25 across the 2020-04-23 episode while old_weewx and weewx_WH1080 contain changing exact-time values at 102 of 103 keys; the two legacy copies are not independent, but their disagreement means the flat source value is unsafe."
        elif primary_value is not None and any(x != primary_value for x in legacy_values):
            row["cohort"] = "SOURCE_CONFLICT"
            row["decision_status"] = "HOLD_FOR_SOURCE_CONFLICT_REVIEW"
            row["reason"] = "A legacy exact-time archive disagrees with pocasi-loucka.eu_old. The legacy archives may be copies rather than independent evidence; no value is selected."
        elif row["cohort"] == "SOURCE_ZERO_REVIEW":
            row["decision_status"] = "HOLD_SOURCE_ZERO_SENSOR_VALIDATION"
            row["reason"] = "Exact source value is zero. Plausibility and sensor status are unresolved; no zero restoration is proposed."
        else:
            row["cohort"] = "PROBABLE_SOURCE_VALUE_REQUIRES_VALIDATION"
            row["decision_status"] = "HOLD_PROVENANCE_AND_REMOVAL_REASON"
            row["reason"] = "The exact source value is available in pocasi-loucka.eu_old, but other primary archives have no value. Matching old_weewx/weewx_WH1080 copies, when present, are not independent; the removal reason and raw provenance are not established."
    cohorts[row["cohort"]] += 1
doc["cohort_counts"] = dict(cohorts)
doc["history_event_rows"] = len(events)
doc["history_matched_keys"] = len(by_key)
doc["pending_review_intersections"] = len(pending)
decisions_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

with csv_path.open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
for row in rows:
    events_for_key = by_key.get((int(row["dateTime"]), row["variable"]), [])
    staged_for_key = pending_by_key.get((int(row["dateTime"]), row["variable"]), [])
    if events_for_key:
        row["cohort"] = "HISTORICALLY_REMOVED_INVALID_DATA"
        row["decision_reason"] = "Applied invalidation history exists; do not restore unreliable value. See EXACT_SOURCE_RECONSTRUCTION_HISTORY.json."
    elif row["variable"] == "outTemp" and row["timestamp_utc"].startswith("2020-04-23T"):
        row["cohort"] = "SOURCE_CONFLICT_SUSPECTED_STALE_PLATEAU"
        row["decision_reason"] = "pocasi-loucka.eu_old repeats 4.25 across the 2020-04-23 episode; changing legacy exact-time values conflict at 102/103 keys."
    elif row["old_value"] and any(row[k] and row[k] != row["old_value"] for k in ("old_weewx_value", "wh1080_value")):
        row["cohort"] = "SOURCE_CONFLICT"
        row["decision_reason"] = "At least one legacy exact-time archive disagrees with pocasi-loucka.eu_old; hold without choosing a value."
    elif row["cohort"] == "SOURCE_ZERO_REVIEW":
        row["decision_reason"] = "Source zero; sensor validation required; do not restore automatically."
    else:
        row["cohort"] = "PROBABLE_SOURCE_VALUE_REQUIRES_VALIDATION"
        row["decision_reason"] = "pocasi-loucka.eu_old exact-time value only among primary sources; removal reason and provenance unresolved."
    row["history_row_count"] = str(len(events_for_key))
    row["history_batch_keys"] = "|".join(sorted({str(x["batch_key"]) for x in events_for_key}))
    row["history_states"] = "|".join(sorted({str(x["state"]) for x in events_for_key}))
    row["pending_review_batch_keys"] = "|".join(sorted({str(x["batch_id"]) for x in staged_for_key}))
    row["pending_review_reason"] = " | ".join(str(x["reason"]) for x in staged_for_key)
fields = list(rows[0])
with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader(); writer.writerows(rows)
print(json.dumps({"candidate_rows": len(rows), "history_event_rows": len(events),
                  "history_matched_keys": len(by_key), "cohort_counts": dict(cohorts)}, indent=2))
