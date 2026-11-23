# Statistical publication policy v3

## Separate evidence dimensions

Each candidate statistic is assessed independently for (1) frozen snapshot integrity, (2) value-level provenance, (3) variable meaning and units, (4) temporal coverage, (5) representativeness, (6) estimates, (7) known sensor faults, (8) unresolved value conflicts, (9) external technical validation, and (10) permitted use. A pass in one dimension cannot compensate for a failure in another.

`SOURCE_MATCHED` retains its exact-concordance meaning: the target agrees with every available compatible source value. “Matches at least one archive” is reported separately and does not upgrade the category. `CONFLICTING_SOURCE` remains unchanged even when the target matches the current primary archive. Conflict subtype flags distinguish primary match, legacy-only match, no compatible match, and disagreement among available copies. The copy relationship graph must be considered; copies are not independent measurements.

Missing target values are classified separately as NULL with a source value or NULL without a source value. They are never included in nonempty `UNCLASSIFIED` provenance counts.

## Outcomes

- `READY_FOR_PUBLICATION`: all required evidence passes, including resolved physical interpretation, strong provenance, representativeness, and suitable independent validation where needed.
- `READY_WITH_DISCLOSED_LIMITATIONS`: a private-station archive statistic has a reproducible value chain, documented archive continuity, sound physical interpretation and representativeness, no disqualifying estimates/conflicts/faults, and explicit disclosure of incomplete independent sensor history.
- `REVIEW_REQUIRED_PROVENANCE`: source identity or value lineage is inadequate.
- `REVIEW_REQUIRED_ESTIMATES`: applied estimates affect the statistic.
- `NOT_REPRESENTATIVE_COVERAGE`: the period fails declared temporal sampling checks.
- `REVIEW_REQUIRED_SENSOR_VALIDATION`: instrumentation, epoch, physical meaning, or sensor behavior remains unresolved.
- `REVIEW_REQUIRED_CONFLICTS`: material value conflicts remain unreviewed.
- `PROTECTED`: reserved review period.
- `DIAGNOSTIC_ONLY`: diagnostic period, never a publication candidate.
- `BLOCKED_E4`: rain or rain-rate method is unresolved.
- `READY_FOR_PUBLICATION` and `READY_WITH_DISCLOSED_LIMITATIONS` are evidence-derived outcomes, not default states. The implemented classifier is `classify_decision()` in `scripts/build_publication_pilot_v2.py`.

## Sampling and statistics

Monthly means use the local civil period and canonical expected slots, time-weighted by archive-end interval duration. The existing mean screen (coverage at least 95%, at least 80% of days passing the daily coverage rule, no gap over six hours, modal cadence share at least 90%) is an initial screen only. Monthly extrema require the stricter existing daily coverage and gap screen and a variable-specific extremum review. Wind direction uses circular statistics, excludes calm intervals and requires adequate resultant concentration. Wind speeds/gusts require units and gust-window interpretation to be checked.

Annual means require at least 11 passing months, at least 95% annual coverage, maximum gap no greater than six hours, and modal cadence share at least 90%. These thresholds are not waived by high annual coverage. Month-by-month and day-of-year composition must also be reviewed where the selected variant differs materially from the full archive. Partial years, 2018 protected data, and 2021 diagnostic data remain excluded as specified.

## Physical interpretation

Units are read from normalized evidence and source metadata. `barometer`, `pressure`, and `altimeter` are separate fields. WeeWX defines pressure as station pressure, barometer as sea-level pressure corrected using altitude and local temperature, and altimeter as station pressure corrected for altitude. Hardware/driver determines which is measured or derived; the historical site-specific configuration is still required. Wind direction means are circular. A regional reference supports plausibility only after location, elevation, exposure, cadence, timestamp, unit, and element are checked; it cannot establish that a value is the original Loučka observation. See [WeeWX meteorological definitions](https://www.weewx.com/docs/latest/usersguide/troubleshooting/meteo/).

## Pilot disposition

The January 2026 `outTemp` mean meets `READY_WITH_DISCLOSED_LIMITATIONS` for a future private-station statistic: the snapshot is verified, all values exactly match available archive copies, B and E give the same mean, coverage is 99.966%, and a CHMI Vizovice regional time-series check supports physical plausibility. Disclose that January is part of a shared historical archive baseline and independent sensor serial/configuration history is unavailable; it does not prove a GW3000 live measurement.

January `outHumidity` remains `REVIEW_REQUIRED_SENSOR_VALIDATION` because repeated long 99% plateaus and regional divergence leave saturation/sticking unresolved. January `barometer` remains in sensor/semantics review because the pressure transformations cannot be reproduced without driver configuration and site elevation. Archive mirrors are dependent lineage evidence. No public release is authorized. Rain remains blocked under E4.

## V3 additions: evidence registry and interval geometry

Each of the 248 selected monthly mean candidates has an individually keyed evidence record in `MONTHLY_VALIDATION_EVIDENCE.json`. The record includes snapshot-derived provenance counts, coverage, available exact-UTC regional reference results, evidence references, and explicit missing-evidence limitations. A regional comparison may set `external_validation=true`; it never sets `physical_validation=true` or establishes independent sensor lineage. Missing records are rejected by the matrix registry contract.

Monthly representativeness also consumes `INTERVAL_COVERAGE_REVIEW.json`. Where interval overlap prevents a safe unique-time coverage calculation, the sample-count screen does not pass. Diagnostic interval-adjusted means are stored separately and do not replace canonical variant outputs. Annual results still use the existing slot-based annual screen; the interval review is not yet applied to annual representativeness.

The readiness classifier produces an expert evidence outcome only. `publication_authorized` is a separate field and is false for every V3 decision row. Publication requires an independent authorization outside this statistical evidence pipeline.

## V3 implementation limits

This policy version does not assert completion of individual expert validation for all 248 candidates. Detailed physical validation is currently limited to the January 2026 pilot; CHMI temperature comparisons cover available cache months only and are regional plausibility checks. Humidity and pressure sensor epochs remain unresolved, wind candidates have not received the requested variable-specific expert review, historical conflict epochs remain open, and current GW3000 E4 validation is not completed. These limitations keep affected records in review or blocked states.

## Operational decision (2026-11-23): daily extrema belong to WeeWX

The Meteo_audit reconstruction scope **does not manually repair, derive, reconcile or certify daily extrema** (`min`, `max`, `mintime`, `maxtime`) in `archive_day_*`. We correct or quality-flag individual observations in the `archive` source and retain their provenances; this is NOT permission to ignore sensor faults in raw values or to publish contaminated summary rows.

Once the final archive has been separately approved, backed up, and restored to the intended WeeWX binding, **WeeWX regenerates daily summary/extrema tables from that final archive** using its documented `weectl database rebuild-daily` operation (scoped to the affected dates/fields as appropriate). The rebuild is a **separate authorized later operational step**, not an automatic side effect of updating `archive`, and it must not be triggered by audit jobs, PR merges or read-only checks. Until then, the API keeps `HISTORICAL_QC_HOLD` for affected old `archive_day_*` aggregates.

Acceptance after WeeWX rebuild is limited to technical checks (completed process, source/binding selection, touched date ranges, consistency with final archive, and preserved unmodified production before cutover), **not manual per-day extreme correction**. Official utility documentation: https://www.weewx.com/docs/latest/utilities/weectl-database/
