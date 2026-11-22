# Statistical readiness methodology (current implementation)

`scripts/build_authoritative_statistical_readiness.py` reads `loucka_reconstruction.archive`, reconstruction changes, sync audit/verification, and applied estimates in one read-only consistent transaction. It writes only local artifacts. Snapshot manifest: `data/STATISTICAL_READINESS_SNAPSHOT_2026-11-15T154445Z.json`.

## Coverage and units

- For each field, infer the modal positive archive interval (1–120 minutes) and epoch phase by local month. Build unique expected slots on `Europe/Prague` civil dates; DST days naturally contain 23 or 25 hours. The denominator starts at that field's first non-NULL epoch.
- Six entirely empty archive months (2011-09 through 2012-02) use cadence and phase from the nearest observed month; they are listed in snapshot metadata and remain unresolved archive gaps.
- Coverage is non-estimated exact-grid slots divided by expected unique slots. Off-grid values, nearest-slot duplicate candidates, raw counts, missing slots, daytime/nighttime coverage, and longest gaps stay separate. Ratios are not capped.
- The builder reads `usUnits` on every target row and fails closed unless every row is 16 (WeeWX METRIC). Report units are degC, percent, km/h, degrees from north, and hPa as applicable. It does not average mixed unit systems or silently convert historical values. The live source inventory separately records the actual historical `usUnits` distribution for all archive databases. WeeWX code 17 is METRICWX; in source comparisons its wind speeds require explicit m/s-to-km/h normalization. Rain uses different units across 16/17 and is excluded pending E4.
- Time means use each row's recorded interval in seconds. Period means combine daily stored numerators and denominators, not rounded means. Wind direction uses interval-weighted circular components only when same-row `windSpeed` is non-NULL and greater than zero. Calm direction samples are counted separately and excluded; resultant length below 0.1 is marked `LOW_CONCENTRATION_MEAN_UNINTERPRETABLE`.

## Provenance

- `RECOVERED_SOURCE` requires a verification row for the batch, complete matching batch row count, matching aggregate source payload hash, valid per-row `source_row_sha256`, the approved source/target schema identities, matching `usUnits`, and exact numeric equality between the current field and that field in immutable audit `row_json`. Timestamp membership alone is not evidence.
- An exact matching applied reconstruction event takes precedence over sync evidence. Applied estimates take the `ESTIMATED` category. Existing restorations/corrections are identified only when the current field exactly matches the latest applied operation. Remaining values are `UNCLASSIFIED`. `ORIGINAL_VERIFIED` remains zero; original lineage is not inferred.
- Monthly rollup at snapshot: 38,655 recovered-source field values; 301 restored; 0 corrected; 30,485 estimated; 12,625,886 unclassified; 0 originally verified. Provenance totals are field values, not timestamps.

## Screening and publication

Monthly mean screens require at least 95% measured coverage, 90% of days meeting day/night coverage, modal cadence share at least 90%, and no gap over six hours. Extrema screens require 99%, 95% of days, cadence share at least 90%, and no gap over 30 minutes. Annual screens need at least 11 passing constituent months. These screens measure sampling only; they do not establish trustworthy source lineage or authorize publication. The current snapshot has no mean or extrema period passing publication screening. Q1 2018 remains protected; 2021 remains diagnostic-only. Rain and rainRate remain excluded pending E4 counter semantics.

## Verification and files

The output validator reports `PASS`: 51,528 daily, 1,704 monthly, and 144 annual rows; zero coverage ratios above 100%; zero weighted-period mean discrepancies; zero protected/diagnostic flag discrepancies; and zero wind-direction extrema rows. The time-stamped manifest contains SHA-256 hashes for each output and both builder/finalizer scripts.
