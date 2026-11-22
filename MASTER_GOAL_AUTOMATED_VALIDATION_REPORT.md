# Automated statistical validation status

Generated from source snapshot `1e34859d05bb0ec20d3810c4fbb376d231a6ee0bfca0c4c636dcfb2d1114e4ba`. This is a status report for the implemented local pipeline, not a declaration that MASTER GOAL IV is complete.

## Current result

- Full deterministic replay: `PASS` (exit code 0, 58 artifacts), run against the current E1 humidity plateau-weather extension, including the humidity candidate review/report, daily pressure reference context, decision matrices and atlas contract.
- Priority monthly mean candidates: 248; joined candidate result records: 248. All have explicit evidence records and reference linkage where available; period-specific expert interpretation remains incomplete across the 248-candidate set.
- Candidate-specific outcome count (monthly means only): 248 processed; 0 strict positive, 1 limited positive, 245 awaiting physical/sensor validation, 0 awaiting conflict resolution, and 0 in other review states. None are labeled rejected; these are review outcomes. Evidence statuses: `{"B_VARIANT_STATISTIC_UNAVAILABLE_SAME_VARIANT_SPEED_MISSING": 1, "DAILY_REGIONAL_CONTEXT_ONLY_PHYSICAL_VALIDATION_MISSING": 109, "PILOT_EVIDENCE_AVAILABLE": 2, "REGIONAL_REFERENCE_COMPARISON_AVAILABLE_PHYSICAL_VALIDATION_MISSING": 136}`. See the year × variable breakdown in `MASTER_GOAL_AUTOMATED_VALIDATION_CANDIDATE_OUTCOMES.json`.
- Frozen target-series diagnostics cover 248 period-variable candidates, including ranges, exact-value runs, humidity saturation and calm-wind descriptors. These are screening measures, not sensor-fault findings.
- Full readiness decision matrix: 3927 rows, including monthly and annual means/extrema and explicit E4 rows.
- Current ongoing GW3000 sync status snapshot: HEALTHY; systemd timer active/enabled, last service result success, source/target maximum 1794792900/1794792900, lag 0 s; older read-only reconciliation PASS.
- Latest read-only GW3000 LAN poll at 2026-11-16T21:47:18.674921Z: local snapshot present (`GW3000_LAN_HTTP`), with the poll timer active/enabled and the most recent oneshot service successful at 22:47:18 CET (exit 0). This confirms polling, not rain sensor validity or historical archive mapping.
- Readiness counts: {"BLOCKED_E4": 462, "DIAGNOSTIC_ONLY": 195, "NOT_REPRESENTATIVE_COVERAGE": 2305, "PROTECTED": 60, "READY_WITH_DISCLOSED_LIMITATIONS": 2, "REVIEW_REQUIRED_CONFLICTS": 475, "REVIEW_REQUIRED_ESTIMATES": 76, "REVIEW_REQUIRED_SENSOR_VALIDATION": 352}.
- Post-pipeline verification on the same snapshot: 48 orchestration stages passed; 82 relevant tests passed; 3465 monthly/annual mean/extrema rows matched exact interval sidecars; 462 E4 rows are confined to rain/rainRate; Q1 2018 and 2021 protection checks passed; archive sync timer active/enabled, latest service success (exit 0), health HEALTHY with 0 s lag, 0 missing rows and 0 conflicts.
- Snapshot-derived value provenance: 1,695,104 rows × 8 fields = 13,560,832 slots; 12,695,375 nonempty values and 865,457 NULL values. All five declared partition/rollup invariants pass, and recomputed counts match the prior artifact for the same SHA-256 snapshot. The orchestrator rebuilds these counts and V2 pilot/candidate outputs after validating source manifests.
- Daily readiness and monthly/annual statistical variants use the same concordance snapshot: 8,520 monthly and 720 annual field-variant rows; alignment `MATCH`, with 1695104 readiness rows and 1695104 concordance rows through epoch 1794758400.
- Fully ready: 0; limited recommendations: 2; publication authorization: false.
- CHMI temperature comparisons: 62 unique station-month results across 31 candidate months; availability partitions the 54 candidates into 31 with subdaily reference, 2 daily-context-only, and 21 without a cached same-month reference. Results use exact UTC pairs, quality-code 0 and no interpolation; they are regional plausibility evidence. The immutable cache contains 46 available periods across the union of temperature, humidity and wind candidates. Candidate-specific expert dispositions now cover 54 outTemp months, including exact station-to-station UTC comparisons where both sources exist; no numeric correction or publication was authorized.
- CHMI daily mean context was added for 23 months without a same-month subdaily reference (46 station-month rows). It remains regional context because daily-window semantics and weighting are not mapped to the Loučka civil-month archive mean; no decision changed. The candidate-specific daily summaries are joined to 23 outTemp result records with `external_validation=false`.
- Station/sensor registry retains 7 archive availability cohorts separately from two operator-reported station configuration periods (Watson W-8681 start and GW1000 replacement) and two public location/elevation reports that differ by 11 m. These reports improve site-history context but do not establish exact sensor siting, sensor-specific epochs, WeeWX mapping, or SQL archive lineage; the point-in-time GW3000A V1.2.5 observation remains separate.
- Local station metadata search: 0 standard-named WeeWX/config/backup matches across the recorded host roots; the app station fixture reports location verified=False, and 1 sensor fixture records remain unknown/unconfirmed. Filename search limitations are recorded in `LOCAL_STATION_METADATA_SEARCH.json`.
- Interval diagnostics: 248 candidate period-variable rows have clipped interval-union coverage; maximum is 100.0%, with 998 overlaps and 2934 UTC gap spans. The sidecar computes 8,520 monthly and 720 annual interval-weighted variants across the snapshot, including off-grid intervals. Exact-variant clipped interval coverage and gap gates now constrain all monthly and annual mean/extrema readiness decisions alongside slot screens; candidate diagnostic means cover 248 candidates; their largest absolute difference is 5.362090.
- Humidity plateau context across all 45 selected periods: 444 sustained ≥99% episodes in 31 periods; no ≥99% episodes in all 10 selected 2023 periods. For 2026-01, 13 episodes occurred with local outTemp averaging -0.16 °C and wind averaging 5.80 km/h. During exact-UTC CHMI pairs inside those local episodes, Vizovice was ≥99% in 10/629 pairs and Luhačovice in 0/629; reference RH was ≥95% in 413/629 and 479/629, respectively. These are event associations, not sensor diagnosis; rainfall/dew point and dated sensor epochs remain unavailable.
- Humidity analysis screens all 45 candidates and 444 local ≥99% plateau runs; candidate-specific evidence dispositions cover all 45 months (25 with exact-UTC regional comparisons, 20 with daily context only). Official CHMI daily H,AVG provides quality-0 regional context for all 20 months without subdaily comparisons; daily aggregation semantics are not matched to Loučka monthly means and do not count as external or physical validation. Sensor saturation, microclimate and sensor behavior remain unresolved. Pressure analysis covers all 68 candidates; 66 have CHMI Holešov daily P,AVG regional context and two 2026 months have exact-hour P_hm comparisons. Daily P is not equated to Loučka pressure, barometer or altimeter, and does not count as matched external or physical validation; sensor elevation, deployed field semantics and configuration remain unresolved. Wind comparisons cover all 81 candidates (162 station-month results): speeds use km/h→m/s normalization and direction uses circular metrics; temporal support, gust windows, exposure and physical epoch remain unresolved.
- Three unmatched temperature cases have individual dispositions: two 2015 records are floating-point epsilon disagreements (no meteorological correction indicated), while the 2022-12-24 23:15 UTC value remains an unresolved 0.525 C archive-copy conflict. For that single-slot alternative, the illustrative unweighted monthly mean sensitivity is 0.00005886310124453414039125779710 C; this does not establish which reading is true. No source or target value was changed. The historical conflict review preserves 168 evidence-availability cohorts and adds directional/distributional comparisons for 240 field/year/named-archive groups; the wind 3.6-factor screen is diagnostic only, and causal transformation support remains unproven. Current GW3000 E4 review combines 4,651 frozen archive rows with one immutable sanitized live read-only capture; gateway firmware, unit settings, traditional-rain priority, active rain-sensor catalog, and a dry raw rain-field excerpt are evidenced, while historical wet/reset payloads and WeeWX mapping remain unresolved, so E4 remains blocked.
- V3 policy and decision exports cover all matrix rows; they do not grant publication authorization. A local versioned atlas contract and filterable preview cover all 248 candidate evidence records; every publication authorization remains false.

## Candidate evidence and readiness classifications

Among 248 monthly mean candidates: `VALIDATED_BY_EXACT_REFERENCE` 138; `REGIONAL_CONTEXT_ONLY` 109; `SENSOR_VALIDATION_REQUIRED` 245 awaiting sensor metadata or physical validation; `READY_WITH_DISCLOSED_LIMITATIONS` 1; `READY_FOR_PUBLICATION` 0; `NOT_VALIDATED` 1. These are evidence/readiness dimensions: exact regional comparisons do not prove Loučka sensor correctness, and regional context alone never clears a sensor-validation blocker. `BLOCKED_E4` applies to 462 E4 rows in the full readiness matrix, outside the monthly mean candidate set.

## Interval-aware annual temperature review

- 2010 outTemp: interval-aware B mean 8.811586 °C (slot-based 8.811676), E mean 8.786687 °C (slot-based 8.786777); B/E time coverage 98.64%/98.93%, worst monthly gap 26700 s.
- 2024 outTemp: interval-aware B mean 11.284354 °C (slot-based 11.284302), E mean 11.284560 °C (slot-based 11.284508); B/E time coverage 98.97%/98.97%, worst monthly gap 57300 s.

Means differ from slot-based values because civil-month boundaries clip actual archive intervals. The review is diagnostic; representativeness, sensor epochs, and provenance still govern decisions.

## Counts by variable

| Variable | Readiness counts |
|---|---|
| altimeter | `{"DIAGNOSTIC_ONLY": 26, "NOT_REPRESENTATIVE_COVERAGE": 344, "PROTECTED": 8, "REVIEW_REQUIRED_CONFLICTS": 84}` |
| barometer | `{"DIAGNOSTIC_ONLY": 26, "NOT_REPRESENTATIVE_COVERAGE": 284, "PROTECTED": 8, "REVIEW_REQUIRED_CONFLICTS": 39, "REVIEW_REQUIRED_SENSOR_VALIDATION": 105}` |
| outHumidity | `{"DIAGNOSTIC_ONLY": 26, "NOT_REPRESENTATIVE_COVERAGE": 277, "PROTECTED": 8, "REVIEW_REQUIRED_CONFLICTS": 30, "REVIEW_REQUIRED_ESTIMATES": 60, "REVIEW_REQUIRED_SENSOR_VALIDATION": 61}` |
| outTemp | `{"DIAGNOSTIC_ONLY": 26, "NOT_REPRESENTATIVE_COVERAGE": 290, "PROTECTED": 8, "READY_WITH_DISCLOSED_LIMITATIONS": 2, "REVIEW_REQUIRED_CONFLICTS": 47, "REVIEW_REQUIRED_ESTIMATES": 16, "REVIEW_REQUIRED_SENSOR_VALIDATION": 73}` |
| pressure | `{"DIAGNOSTIC_ONLY": 26, "NOT_REPRESENTATIVE_COVERAGE": 344, "PROTECTED": 8, "REVIEW_REQUIRED_CONFLICTS": 84}` |
| rain | `{"BLOCKED_E4": 231}` |
| rainRate | `{"BLOCKED_E4": 231}` |
| windDir | `{"DIAGNOSTIC_ONLY": 13, "NOT_REPRESENTATIVE_COVERAGE": 173, "PROTECTED": 4, "REVIEW_REQUIRED_CONFLICTS": 6, "REVIEW_REQUIRED_SENSOR_VALIDATION": 35}` |
| windGust | `{"DIAGNOSTIC_ONLY": 26, "NOT_REPRESENTATIVE_COVERAGE": 297, "PROTECTED": 8, "REVIEW_REQUIRED_CONFLICTS": 92, "REVIEW_REQUIRED_SENSOR_VALIDATION": 39}` |
| windSpeed | `{"DIAGNOSTIC_ONLY": 26, "NOT_REPRESENTATIVE_COVERAGE": 296, "PROTECTED": 8, "REVIEW_REQUIRED_CONFLICTS": 93, "REVIEW_REQUIRED_SENSOR_VALIDATION": 39}` |

## Counts by year

| Year | Readiness counts |
|---|---|
| 2009 | `{"BLOCKED_E4": 22, "NOT_REPRESENTATIVE_COVERAGE": 136, "REVIEW_REQUIRED_CONFLICTS": 16, "REVIEW_REQUIRED_SENSOR_VALIDATION": 13}` |
| 2010 | `{"BLOCKED_E4": 26, "NOT_REPRESENTATIVE_COVERAGE": 140, "REVIEW_REQUIRED_CONFLICTS": 32, "REVIEW_REQUIRED_SENSOR_VALIDATION": 23}` |
| 2011 | `{"BLOCKED_E4": 26, "NOT_REPRESENTATIVE_COVERAGE": 169, "REVIEW_REQUIRED_CONFLICTS": 17, "REVIEW_REQUIRED_SENSOR_VALIDATION": 9}` |
| 2012 | `{"BLOCKED_E4": 26, "NOT_REPRESENTATIVE_COVERAGE": 181, "REVIEW_REQUIRED_CONFLICTS": 10, "REVIEW_REQUIRED_SENSOR_VALIDATION": 4}` |
| 2013 | `{"BLOCKED_E4": 26, "NOT_REPRESENTATIVE_COVERAGE": 171, "REVIEW_REQUIRED_CONFLICTS": 12, "REVIEW_REQUIRED_SENSOR_VALIDATION": 12}` |
| 2014 | `{"BLOCKED_E4": 26, "NOT_REPRESENTATIVE_COVERAGE": 137, "REVIEW_REQUIRED_CONFLICTS": 32, "REVIEW_REQUIRED_SENSOR_VALIDATION": 26}` |
| 2015 | `{"BLOCKED_E4": 26, "NOT_REPRESENTATIVE_COVERAGE": 142, "REVIEW_REQUIRED_CONFLICTS": 19, "REVIEW_REQUIRED_ESTIMATES": 20, "REVIEW_REQUIRED_SENSOR_VALIDATION": 14}` |
| 2016 | `{"BLOCKED_E4": 26, "NOT_REPRESENTATIVE_COVERAGE": 177, "REVIEW_REQUIRED_CONFLICTS": 4, "REVIEW_REQUIRED_ESTIMATES": 10, "REVIEW_REQUIRED_SENSOR_VALIDATION": 4}` |
| 2017 | `{"BLOCKED_E4": 26, "NOT_REPRESENTATIVE_COVERAGE": 187, "REVIEW_REQUIRED_ESTIMATES": 8}` |
| 2018 | `{"BLOCKED_E4": 26, "NOT_REPRESENTATIVE_COVERAGE": 59, "PROTECTED": 60, "REVIEW_REQUIRED_CONFLICTS": 37, "REVIEW_REQUIRED_SENSOR_VALIDATION": 39}` |
| 2019 | `{"BLOCKED_E4": 26, "NOT_REPRESENTATIVE_COVERAGE": 83, "REVIEW_REQUIRED_CONFLICTS": 94, "REVIEW_REQUIRED_ESTIMATES": 10, "REVIEW_REQUIRED_SENSOR_VALIDATION": 8}` |
| 2020 | `{"BLOCKED_E4": 26, "NOT_REPRESENTATIVE_COVERAGE": 159, "REVIEW_REQUIRED_CONFLICTS": 20, "REVIEW_REQUIRED_ESTIMATES": 12, "REVIEW_REQUIRED_SENSOR_VALIDATION": 4}` |
| 2021 | `{"BLOCKED_E4": 26, "DIAGNOSTIC_ONLY": 195}` |
| 2022 | `{"BLOCKED_E4": 26, "NOT_REPRESENTATIVE_COVERAGE": 126, "REVIEW_REQUIRED_CONFLICTS": 39, "REVIEW_REQUIRED_ESTIMATES": 12, "REVIEW_REQUIRED_SENSOR_VALIDATION": 18}` |
| 2023 | `{"BLOCKED_E4": 26, "NOT_REPRESENTATIVE_COVERAGE": 100, "REVIEW_REQUIRED_CONFLICTS": 34, "REVIEW_REQUIRED_SENSOR_VALIDATION": 61}` |
| 2024 | `{"BLOCKED_E4": 26, "NOT_REPRESENTATIVE_COVERAGE": 111, "REVIEW_REQUIRED_CONFLICTS": 16, "REVIEW_REQUIRED_ESTIMATES": 4, "REVIEW_REQUIRED_SENSOR_VALIDATION": 64}` |
| 2025 | `{"BLOCKED_E4": 26, "NOT_REPRESENTATIVE_COVERAGE": 144, "REVIEW_REQUIRED_CONFLICTS": 10, "REVIEW_REQUIRED_SENSOR_VALIDATION": 41}` |
| 2026 | `{"BLOCKED_E4": 24, "NOT_REPRESENTATIVE_COVERAGE": 83, "READY_WITH_DISCLOSED_LIMITATIONS": 2, "REVIEW_REQUIRED_CONFLICTS": 83, "REVIEW_REQUIRED_SENSOR_VALIDATION": 12}` |

## Outstanding work

The implementation does not yet meet the requested completion conditions. Missing or incomplete work includes: period-specific physical validation and external comparisons for all applicable candidates; humidity and pressure epoch resolution beyond January 2026; wind expert validation; historical conflict epoch explanation; systematic current GW3000 E4 validation; and complete source-to-output evidence for all requested invariants. The orchestration rebuilds snapshot-derived provenance counts, canonical daily readiness, monthly/annual variants and V2 pilot/candidate evidence before downstream period validations. Several expert evidence phases remain incomplete.

No historical database writes, source archive modifications, production API changes, deployments, or publication were performed by this pipeline run.
