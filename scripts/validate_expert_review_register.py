#!/usr/bin/env python3
"""Check that every ER heading is explicitly categorized in the review register."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADING = re.compile(r"^## (ER-[^—]+) — (.+)$")
source = (ROOT / "EXPERT_REVIEW_REQUIRED.md").read_text(encoding="utf-8")
expected = {}
for line in source.splitlines():
    match = HEADING.match(line)
    if match:
        issue_id = match.group(1).strip()
        if "supplement" not in issue_id.lower():
            expected[issue_id] = match.group(2).strip()
with (ROOT / "reports/2026-11-13-expert-review-register.csv").open(newline="", encoding="utf-8") as stream:
    records = list(csv.DictReader(stream))
by_id = {row["issue_id"]: row for row in records}
assert len(records) == len(expected) == 44, (len(records), len(expected))
assert set(by_id) == set(expected)
for issue_id, title in expected.items():
    row = by_id[issue_id]
    assert row["title"] == title
    assert row["quality_status"] == "REVIEW_REQUIRED"
    assert row["register_scope"] == "issue_group_only_not_row_level_quality_classification"
for tag in ("LONG_OUTAGE", "FREEZE", "INVERSION", "MODEL_UNCERTAINTY", "SOURCE_CONFLICT"):
    assert any(tag in row["review_tags"].split(";") for row in records), tag
assert by_id["ER-02"]["protected_2021"] == "false"
assert by_id["ER-24"]["protected_2021"] == "true"
# Publication blockers must identify an actual period/field and the publication effect;
# generic "specified issue group" placeholders are not sufficient evidence mapping.
for issue_id in ("ER-05", "ER-20", "ER-21", "ER-29", "ER-30"):
    row = by_id[issue_id]
    assert row["impact_class"] == "BLOCKS_FINAL_PUBLICATION"
    assert "specified issue group" not in row["affected_scope"].lower()
    assert len(row["affected_scope"]) >= 100
    assert len(row["evidence_required"]) >= 100
    assert any(token in row["affected_scope"] for token in ("2024", "2026", "2009", "2022"))
    assert any(token in row["affected_proposals"].lower() for token in ("withhold", "hold", "no correction", "no current", "no meteorological"))
assert by_id["ER-23"]["q1_2018_interim"] == "true"
assert "ZERO_SERIES" in by_id["ER-33"]["review_tags"].split(";")
assert by_id["ER-33"]["impact_class"] == "BLOCKS_SPECIFIC_CORRECTIONS"
assert by_id["ER-34"]["impact_class"] == "BLOCKS_SPECIFIC_CORRECTIONS"
assert by_id["ER-35"]["impact_class"] == "BLOCKS_SPECIFIC_CORRECTIONS"
assert "SENSOR_EPOCH" in by_id["ER-35"]["review_tags"].split(";")
assert "FILTER_SELECTION" in by_id["ER-34"]["review_tags"].split(";")
assert "Independent local RH truth" in by_id["ER-34"]["evidence_required"]
assert "Sensitivity holdout is complete" in by_id["ER-34"]["evidence_required"]
assert by_id["ER-35"]["impact_class"] == "BLOCKS_SPECIFIC_CORRECTIONS"
assert "2009" in by_id["ER-35"]["affected_scope"]
assert by_id["ER-39"]["impact_class"] == "BLOCKS_SPECIFIC_CORRECTIONS"
assert "1458239400" in by_id["ER-39"]["affected_scope"] and "1546297200" in by_id["ER-39"]["affected_scope"]
assert "1484989500" in by_id["ER-39"]["affected_scope"] and "1512155700" in by_id["ER-39"]["affected_scope"]
assert "1478177400" in by_id["ER-39"]["affected_scope"] and "1480693800" in by_id["ER-39"]["affected_scope"]
assert "157?" not in by_id["ER-39"]["affected_scope"]
assert "94 RH restoration/review targets" in by_id["ER-39"]["affected_proposals"]
assert by_id["ER-40"]["impact_class"] == "BLOCKS_SPECIFIC_CORRECTIONS"
assert "1364095500" in by_id["ER-40"]["affected_scope"] and "1382118900" in by_id["ER-40"]["affected_scope"]
assert "frost/inversion" in by_id["ER-40"]["evidence_required"]
assert by_id["ER-41"]["impact_class"] == "BLOCKS_SPECIFIC_CORRECTIONS"
assert "outHumidity" in by_id["ER-41"]["affected_scope"] and "13" in by_id["ER-41"]["affected_scope"]
assert "raw packets" in by_id["ER-41"]["evidence_required"]
assert by_id["ER-42"]["impact_class"] == "BLOCKS_SPECIFIC_CORRECTIONS"
assert "12 specific" in by_id["ER-42"]["affected_scope"] and "19/24 endpoints" in by_id["ER-42"]["affected_scope"] and "endpoint" in by_id["ER-42"]["evidence_required"]

schema = json.loads((ROOT / "config/quality-provenance-record.schema.json").read_text(encoding="utf-8"))
assert schema["type"] == "object" and schema["additionalProperties"] is False
required = set(schema["required"])
assert {"variable", "timestamp_utc_epoch", "unit", "origin_class", "review_status", "source",
        "method", "validation", "uncertainty", "expected_target_state", "reason"} <= required
assert set(schema["properties"]["origin_class"]["enum"]) == {
    "ORIGINAL", "RESTORED", "CORRECTED", "ESTIMATED", "MISSING", "NOT_AVAILABLE"
}
assert set(schema["properties"]["review_status"]["enum"]) == {
    "CLEAR", "SUSPECT", "REVIEW_REQUIRED"
}
report = (ROOT / "reports/QUALITY_CLASSIFICATION_AUDIT.md").read_text(encoding="utf-8")
for label in ("ORIGINAL", "RESTORED", "CORRECTED", "ESTIMATED", "MISSING", "NOT_AVAILABLE",
              "NOT_CLASSIFIED", "SUSPECT", "REVIEW_REQUIRED", "INVERSION", "FREEZE"):
    assert label in report, label

print("PASS: 43 issue groups plus one masked-extrema follow-up are categorized; quality/provenance schema is structurally consistent")

assert by_id['ER-43']['impact_class']=='BLOCKS_SPECIFIC_CORRECTIONS'
assert all(t in by_id['ER-43']['affected_scope'] for t in ('1561406100','1561408200','1564776000'))
assert '2019-05-30' in by_id['ER-43']['affected_proposals']
