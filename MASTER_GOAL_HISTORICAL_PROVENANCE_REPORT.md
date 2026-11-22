# Master goal II: historical provenance and publication readiness

## Outcome

The requested read-only provenance and publication-readiness work is complete with explicit blockers. No historical archive writes, source database changes, API changes, public web changes, or publication were made.

## Evidence and decisions

- Source inventory and dependency limits: `HISTORICAL_SOURCE_CATALOG.md`, `.json`, and `HISTORICAL_SOURCE_DEPENDENCY_GRAPH.json`. Related archives are not presumed independent.
- Current field-level evidence: 1,695,104 timestamp rows, eight priority variables, five compatible archive copies, immutable sync audit and applied reconstruction evidence in `data/historical_value_concordance.sqlite`. Snapshot: 2026-11-15 16:03:04 UTC; see its manifest and `HISTORICAL_VALUE_CONCORDANCE_REPORT.md`. Of 12,695,375 non-NULL prioritized field values, 7,793,278 are SOURCE_MATCHED, 38,703 RECOVERED_SOURCE, 301 RESTORED, 30,537 ESTIMATED, 4,832,556 CONFLICTING_SOURCE, and 418,497 UNCLASSIFIED. ORIGINAL_VERIFIED and identified INVALIDATED values are both zero. An additional 446,960 NULL target fields have at least one source value and remain UNRESOLVED candidates.
- The source catalog evidence does not establish independent sensor lineage for copy matches. No absent audit row is treated as proof of original measurement. The SQLite registry preserves the original values, unit codes and normalized comparisons; only exact decimal conversion of METRICWX wind speeds to METRIC is used.
- Statistical variants A–E and the monthly/annual readiness matrix are documented in `STATISTICAL_VARIANTS_REPORT.md` and `STATISTICAL_PUBLICATION_READINESS_REPORT.md`. Of 3,927 explicit decisions, zero are ready for publication and zero are ready with disclosed limitations. The matrix records sampling/gap representativeness separately from provenance.
- E4 remains blocked for rain and rainRate in every epoch. Do not use them for accumulated statistics or rates. See `E4_RAIN_SEMANTICS_CURRENT_REPORT.md`. Q1 2018 remains protected and 2021 diagnostic-only.
- Registry reconciliation: 324 unique operations consist of 317 exact v1.2 applied operations, five 2018 non-rain operations already applied under later equivalent events, and two E4-blocked rain operations. There are zero newly recommended safe non-rain operations. No new approval package is proposed.
- Phase A operations are documented in `PHASE_A_OPERATIONS_CHECKPOINT_2026-11-15.md`: stale health state fix, monthly read-only full reconciliation timer, isolated MariaDB integration/regression checks, and successful live sync state. No change to the approved INSERT-only sync scope.
- Atlas contract is local at `data/METEOROLOGICAL_ATLAS_DATA_CONTRACT_V1.json`; no production endpoint was created.

## Remaining evidence needed

Independent sensor lineage/instrument logs are needed before promoting archive-copy matches to original measurements. Driver/configuration and raw counter/reset evidence are needed to resolve E4. Sampling representativeness, provenance, and estimate review prevent a publication recommendation today. These are explicit blockers, not inferred resolutions.
