# Unified archive quality and provenance model

## Value-level classes

- `ORIGINAL_VERIFIED`: primary/source evidence demonstrates the local measured value and its unit/time mapping. Do not assign from absence of a change event.
- `RESTORED` / `RECOVERED_SOURCE`: specific historical source value recovered with source archive/time/value, transform, rationale and confidence.
- `CORRECTED`: a documented correction to an existing value with before/after values and evidence.
- `ESTIMATED`: method-produced value with model/version, training/reference, holdout validation and uncertainty.
- `REVIEW_REQUIRED`: source, unit, time, quality or conflict unresolved.
- `MISSING`: actual measured timestamp/value gap established against a validated epoch cadence. Keep distinct from NULL field in an existing row.
- `SENSOR_NOT_AVAILABLE`: field was not measured in that sensor epoch.
- `PROVENANCE_UNKNOWN`: value origin/transform cannot be proved. This is the conservative status for unlogged current values absent stronger evidence.
- `INVALID`: reproducibly invalid value, with evidence and reason; never inferred from a simple threshold alone.

Value classes do not determine statistical suitability. Period-level use must separately carry `READY`, `READY_WITH_LIMITATIONS`, `REVIEW_REQUIRED`, `NOT_AVAILABLE`, `BLOCKED`, or `PROTECTED` per statistic.

## Required provenance

For source recovery retain target UTC, source archive, source timestamp, source value/unit, target value/unit, transform, source independence/lineage basis, evidence reference, audit event and confidence. For estimates retain model/code version, inputs, reference, holdout metrics by season/condition, uncertainty and allowed uses. Preserve all original values and events.

The current table lacks a per-field origin column. `reconstruction_changes` documents applied/reverted operations but not complete archive lineage. `ARCHIVE_PROVENANCE_BASELINE.json` explicitly avoids asserting original provenance for values without events. Future API must expose the metadata without mutating the archive schema in this goal.
