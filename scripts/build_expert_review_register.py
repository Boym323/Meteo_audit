#!/usr/bin/env python3
"""Build an explicit review register from the expert-review issue ledger."""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "EXPERT_REVIEW_REQUIRED.md"
OUTPUT = ROOT / "reports/2026-11-13-expert-review-register.csv"
HEADING = re.compile(r"^## (ER-[^—]+) — (.+)$")

# Tags are triage dimensions, not conclusions about the underlying value.
TAGS = {
    "ER-01": "LONG_OUTAGE;MISSINGNESS;TIME_EPOCH",
    "ER-02": "LONG_OUTAGE;FREEZE;INVERSION;MODEL_UNCERTAINTY",
    "ER-03": "SOURCE_CONFLICT;PRESSURE_SEMANTICS;TEMPERATURE_STRATIFICATION",
    "ER-04": "SOURCE_CONFLICT;RAIN_COUNTER_SEMANTICS;UNIT_EPOCH",
    "ER-05": "SUSPECT_EPISODE;SENSOR_VALIDITY;MODEL_UNCERTAINTY",
    "ER-06": "SOURCE_AVAILABILITY_CONFLICT;SENSOR_MAPPING",
    "ER-07": "MODEL_UNCERTAINTY;REFERENCE_TRANSFER",
    "ER-08": "DERIVED_DEPENDENCY;RH_RECONSTRUCTION;FORMULA_LINEAGE",
    "ER-09": "DERIVED_DEPENDENCY;RH_RECONSTRUCTION;FORMULA_LINEAGE",
    "ER-10": "REFERENCE_TIME_MAPPING;SOURCE_SEMANTICS",
    "ER-11": "SOURCE_CONFLICT;RH;LINEAGE",
    "ER-12": "SUSPECT_VALUE;SOURCE_CONFLICT;FREEZE_CONTEXT",
    "ER-13": "SENSOR_PLATEAU;RH;SENSOR_VALIDITY",
    "ER-14": "SENSOR_PLATEAU;FREEZE;TEMPERATURE;RH",
    "ER-15": "LONG_OUTAGE;FREEZE;SOURCE_ONLY;TEMPERATURE",
    "ER-16": "SOURCE_CONFLICT;RAIN_COUNTER_SEMANTICS",
    "ER-17": "SOURCE_CONFLICT;WIND;UNIT_EPOCH",
    "ER-18": "SUSPECT_VALUE;RADIATION;UV;SOURCE_CONCORDANCE",
    "ER-19": "SOURCE_CONFLICT;MISSINGNESS;WIND_DIRECTION",
    "ER-20": "SENSOR_IDENTITY;UNIT_EPOCH;SOURCE_CONFLICT",
    "ER-21": "TELEMETRY_SEMANTICS;SENSOR_IDENTITY",
    "ER-22": "DERIVED_DEPENDENCY;TEMPERATURE_RECONSTRUCTION;FORMULA_LINEAGE",
    "ER-23": "ACTIVE_INTERIM;HISTORY_PROVENANCE;SCOPE_CONFLICT",
    "ER-24": "PROTECTED_YEAR;SOURCE_CONFLICT;HISTORY_PROVENANCE;RAIN",
    "ER-25": "SOURCE_TIME_PROVENANCE;HISTORY_PROVENANCE",
    "ER-26": "MODEL_UNCERTAINTY;RH;LONG_GAP;FREEZE;INVERSION",
    "ER-27": "REFERENCE_TIME_MAPPING;RAIN;SOURCE_SEMANTICS",
    "ER-28": "MODEL_UNCERTAINTY;SOURCE_CONFLICT;ZERO_REFERENCE;TEMPERATURE",
    "ER-07 follow-up": "MODEL_UNCERTAINTY;LONG_OUTAGE;EXTREMA_ATTENUATION",
    "ER-29": "SUMMARY_CONFLICT;SOURCE_CONFLICT;TEMPERATURE;RECORDS",
    "ER-30": "SUMMARY_CONFLICT;SOURCE_CONFLICT;RH;WIND;RAIN",
    "ER-31": "LONG_OUTAGE;RH;WINTER;FOG;INVERSION;MODEL_UNCERTAINTY",
    "ER-32": "SOURCE_CONFLICT;MISSINGNESS;TEMPERATURE;UNIT_EPOCH;TIME_EPOCH;MODEL_UNCERTAINTY",
    "ER-33": "SOURCE_CONFLICT;ZERO_SERIES;TEMPERATURE;MISSINGNESS;SENSOR_EPOCH;MODEL_UNCERTAINTY",
    "ER-34": "MODEL_UNCERTAINTY;RH;TEMPERATURE;HISTORY_PROVENANCE;FILTER_SELECTION",
    "ER-35": "SOURCE_CONFLICT;SENSOR_EPOCH;TIME_EPOCH;RAIN",
    "ER-36": "HISTORICAL_REMOVAL;SOURCE_CONFLICT;SENSOR_EPOCH;UNIT_EPOCH;WIND;ZERO_SERIES",
    "ER-37": "LONG_OUTAGE;SOURCE_CONFLICT;SENSOR_EPOCH;TEMPERATURE;RH;HISTORICAL_REMOVAL",
    "ER-38": "FREEZE;INVERSION;RH_SENSOR_EPOCH;SOURCE_LINEAGE",
    "ER-39": "SOURCE_CONFLICT;SENSOR_EPOCH;HISTORY_PROVENANCE;HUMIDITY",
    "ER-40": "SOURCE_CONFLICT;FREEZE;INVERSION;RH;SENSOR_EPOCH;HISTORY_PROVENANCE",
    "ER-41": "SOURCE_CONFLICT;RH;SENSOR_EPOCH;HISTORY_PROVENANCE;HUMIDITY",
    "ER-42": "SOURCE_CONFLICT;TEMPERATURE;SOURCE_LINEAGE;HISTORY_PROVENANCE",
    "ER-43": "SOURCE_CONFLICT;OUTTEMP;RH;HISTORICAL_REMOVAL;SHORT_GAP;SOURCE_LINEAGE",
}

text = SOURCE.read_text(encoding="utf-8")
records = []
for line in text.splitlines():
    match = HEADING.match(line)
    if not match:
        continue
    issue_id, title = (part.strip() for part in match.groups())
    if "supplement" in issue_id.lower():
        continue
    if issue_id not in TAGS:
        raise SystemExit(f"No review tags configured for {issue_id}")
    tags = TAGS[issue_id].split(";")
    records.append({
        "issue_id": issue_id,
        "title": title,
        "quality_status": "REVIEW_REQUIRED",
        "review_tags": TAGS[issue_id],
        "protected_2021": str("PROTECTED_YEAR" in tags or "2021" in title).lower(),
        "q1_2018_interim": str("ACTIVE_INTERIM" in tags or "2018" in title and "Q1" in title).lower(),
        "register_scope": "issue_group_only_not_row_level_quality_classification",
        "evidence_source": f"EXPERT_REVIEW_REQUIRED.md#{issue_id.lower().replace(' ', '-')}",
    })

fields = (
    "issue_id", "title", "quality_status", "review_tags", "protected_2021",
    "q1_2018_interim", "register_scope", "evidence_source",
)
with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(records)
print(f"wrote {len(records)} review issue groups to {OUTPUT.relative_to(ROOT)}")
