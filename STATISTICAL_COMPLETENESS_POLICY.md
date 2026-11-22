# Statistical completeness and publication policy

Snapshot taken 2026-11-14. The reconstructed loucka_reconstruction.archive ends at local 2026-10-29 16:10 (UTC epoch 1793286600); there are no later target archive rows in this snapshot. Statistical outputs cover local 2009-03-29 through 2026-10-29. Dates before the first observed nonnull value of each variable are unavailable, not proven instrument downtime or data loss. The 2009 annual value is explicitly partial; 2026 is partial at the other edge.

## Variables, units, and scope

Daily/monthly/annual statistics cover eight primary variables: outdoor temperature outTemp (deg C), outdoor relative humidity outHumidity (%), wind speed and gust windSpeed and windGust (km/h), wind direction windDir (degrees from north), barometer, pressure, and altimeter (hPa/mbar). The archive uses usUnits=16; units follow the WeeWX METRIC system.

Wind direction uses a time-weighted circular mean and reports resultant length. Direction minimum and maximum are not applicable. windrun is excluded because historic interval accumulation and unit epochs are not reconciled. The 77-field monthly/annual matrix remains availability-only for the remaining auxiliary and derived fields. Their sensor deployment epochs are not independently verified, so they are not classified as missing or statistically ready; period statistics remain NOT_AVAILABLE_OR_SENSOR_EPOCH_UNRESOLVED until an epoch-specific assessment is made. Rain and rainRate are excluded under E4; no rainfall aggregation is inferred.

## Sampling thresholds

These are project screening rules, not an official climate certification. A five-minute operating slot is the comparison denominator only after the first observed nonnull value for each variable. Local civil days use Europe/Prague, so DST days have 276 or 300 slots. The inferred first-observation epoch is a screening assumption, not an authoritative sensor deployment record.

- Daily mean screen: at least 95% nominal slots; at least 90% coverage in both 06:00-18:00 and 18:00-06:00; longest within-day step at most 60 minutes.
- Daily extrema screen: at least 99% slots; at least 98% day and night coverage; longest within-day step at most 30 minutes. It does not apply to wind direction.
- Monthly mean: at least 95% slots, at least 90% daily mean-screen days, at least 90% modal-cadence share, and no within-day step over 6 hours.
- Monthly extrema: at least 99% slots, at least 95% daily extreme-screen days, and no within-day step over 30 minutes.
- Annual mean: at least 95% slots and at least 11 months meeting the monthly mean screen.
- Annual extrema: at least 99% coverage and at least 11 months meeting the stricter daily extreme screen. It does not apply to wind direction.

## Provenance, estimates, and statuses

An audit join identifies 30,537 unique estimated target keys among the five original core fields. Exact target-value matching was verified. Frozen daily aggregates cannot subtract these keys and recompute moments/extrema, so affected values are labeled CURRENT_ARCHIVE_RAW; ESTIMATES NOT REMOVED and receive REVIEW_REQUIRED_ESTIMATED_ROWS_PRESENT. Estimated values must be excluded from public climate statistics until raw rows are recomputed with those keys filtered.

Restored values are included and counted with flags: 300 among the five original core fields and one windDir restoration at local 2019-01-01, 22.5 degrees, matching the exact old_weewx source key/value and current target value. No applied CORRECTED operation was identified. Another 334 applied events among the five original core fields remain unclassified and are not treated as corrections. original_documented_values is zero throughout: absence of audit does not prove an untouched row is original. unclassified_origin_nonnull exposes this uncertainty.

READY_WITH_LIMITATIONS_ORIGIN_UNCLASSIFIED means only that the sampling screen passes; it does not authorize publication while source provenance is unknown. REVIEW_REQUIRED applies to estimate-contaminated or protected periods. REVIEW_REQUIRED_CIRCULAR_ORIGIN_UNCLASSIFIED marks circular direction values pending origin review; low resultant length is separately flagged. NOT_REPRESENTATIVE_COVERAGE_OR_GAP means sampling fails. NO_ARCHIVE_ROWS_SENSOR_EPOCH_VS_UNRESOLVED_GAP avoids claiming sensor absence when cause cannot be distinguished. Q1 2018 is protected, 2021 is diagnostic-only, and the right-censored 2026 month/year are non-certifiable.

## Web and atlas decision

The machine-readable API export can feed a provenance/coverage review interface. No computed values are approved for public daily/monthly/annual statistics or a climate atlas: estimates remain in raw aggregates where known, and original provenance is not reconciled. Passing sample groups are candidates for estimate-filtered recomputation and expert review, not ready-to-publish climate values. Temperature climate-day counts are not generated because daily extrema are not established after provenance filtering. E4 rainfall remains out of scope.

## Reproduction

Run python3 scripts/build_daily_statistical_readiness.py. It uses frozen daily exports data/daily_archive_core_2009.csv through data/daily_archive_core_2026.csv, pressure/altimeter daily exports, data/wind_direction_daily_circular.csv, audit summaries, and cadence histograms. No live DB query or write is needed for replay. data/STATISTICAL_READINESS_API.json is generated from the same rows as the CSVs.