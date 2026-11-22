# U6 — Units, time continuity and physical quality review

Updated UTC: 2026-11-14T18:21:14.946099+00:00. Status: `COMPLETED_WITH_LIMITATIONS`.

The current database is metric code 16; the archive has mainly 5-minute interval metadata, but live historical profiles include interval=6 cohorts in 2014–2019 and sparse 10/30/40/55/75 minute values. These are preserved as evidence, not normalized. MariaDB session timezone is SYSTEM/CET, so audit-year queries use explicit UTC epoch boundaries. Current interval-aware edge scan found 24,488 candidate discontinuity edges; these are not a lost-observation total. 2013 remains a known example of observed 10-minute cadence with declared 5-minute interval.

Prior field-specific unit, wind transformation, physical plausibility and temporal continuity reviews were reused. The 322 newly applied field operations from the previous phase were independently checked against exact payloads, source provenance, postimages and audit state; they are prior work and not new changes in this goal. No universal physical bounds, automatic timestamp shifts, deduplication, or mass repair is asserted. There is no whole-archive, all-field physical certification; non-logged values remain unverified for provenance and plausibility.

Evidence: `HISTORICAL_WIND_TRANSFORMATION_REPORT.md`, `reports/B5_TEMPORAL_CONTINUITY_FINAL.md`, `RECONSTRUCTION_EXECUTION_FINAL_REPORT.md`, `POST_RECONSTRUCTION_INVENTORY.json`.
