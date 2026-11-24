# Loučka pressure reconstruction — final read-only review

**Run date:** 2026-11-24 · **Scope:** 2009-03-29 through 2026-11-23 UTC · **Disposition:** no numeric replacement is approved by the evidence currently available.

This report consolidates the existing pressure audits through PR #94 and adds a final decision record. No meteorological values, database rows, daily aggregates, live WeeWX services, credentials, or grants were changed. The approval manifest is intentionally empty. It is a read-only proposal artifact, not an APPLY input.

## Decision summary

| Output class | Count supported by current evidence | Decision |
|---|---:|---|
| `MEASURED` | Existing non-NULL target values remain the measured archive | Preserve original value and source history; this review does not reclassify them as universally calibrated |
| `CALIBRATED` | 0 replacement values | No candidate passes independent, epoch-specific block holdouts for both pressure semantics |
| `ESTIMATED` | 0 | No gap-filling estimate is included; model outputs must not be presented as measurement |
| `UNRESOLVED` | 198,175 NULL `pressure` target slots in the 2026-11-23 read-only snapshot; 62,185 lack any direct value in the compared archive copies | Leave NULL and preserve as unresolved |

The counts above refer to the snapshot reported by the read-only PR #89 analysis, not a new row-by-row source reconciliation in this worktree. The archive is live and counts may move slightly. In the 2016–2018 pressure-loss cohort, 90,556 target slots were NULL; WH1080 provides 75,074 direct values, all exactly duplicated by `old_weewx`. This is one lineage, not two independent observations. The remaining 15,482 slots do not have a WH1080 value in that cohort.

For 2022, the cited inventory reports 46,305 NULL `pressure` slots; 45,069 lack a direct numeric value in the five compared archive copies. The other 1,236 values are source leads only, not validated candidates.

## Field semantics and station pressure

The working interpretation is `pressure` = station pressure, `barometer` = sea-level reduced pressure, and `altimeter` = standard-atmosphere altimeter setting. These names are not proof of the historical driver/calculation chain. The diagnostic height transport used in the November 23 numeric study assumes a Loučka elevation of 425 m and uses contemporaneous `outTemp`:

`P_station_at_reference_height = P_Loucka × exp(g × (425 m − reference_height) / (Rd × (T_out + 273.15 K)))`.

This is a physical hydrostatic comparison, not a calibration or replacement algorithm. It avoids imposing a fixed 50 hPa or +23 hPa correction. `pressure` after transport is compared with ČHMÚ station `P`; `barometer` is compared with `P_hm`. The temperature is only a proxy for mean column temperature, so the residual includes method and spatial uncertainty.

## Epoch disposition

| Epoch | Evidence available | Disposition |
|---|---|---|
| 2009–2011 | Daily ČHMÚ `P` context only; old sensor lineage and missing historical pressure derivations | `MEASURED` values retained; missing values `UNRESOLVED`; no hourly accuracy claim |
| 2012–2013-08-07 | Daily ČHMÚ context only; source transitions not fully configured | `UNRESOLVED` for proposed restoration |
| 2013-08-08–2015 | Daily ČHMÚ context only; available copy values do not establish calibrated lineage | `UNRESOLVED` for proposed restoration |
| 2016–2017 | 2016–2018 WH/old copy cohort; daily ČHMÚ only for external reference | No direct candidate is accepted without exact timestamp/block validation |
| 2018 | Hourly ČHMÚ P/P_hm exists; PR #91 pilot evaluated 8,055 full-hour WH matches | Reject restoration from WH in this pilot: adjusted WH pressure − CHMI P median about −23 hPa at both Holešov and Mošnov; no candidate promoted |
| 2019-01–2019-04 | Hourly ČHMÚ available; historic source relationship changes near April/May | Split at the observed change; no value restoration approved |
| 2019-05–2021 | Hourly CHMI comparisons support changing epochs; no dated local configuration proves cause | Keep missing slots unresolved; no uniform correction |
| 2022 | 46,305 NULL target pressure slots in cited snapshot; 45,069 have no direct copy value | Direct-source recovery unavailable for most slots; no interpolation/estimation accepted |
| 2023–2024 | Hourly references and source-copy differences; archive relationships remain field/configuration dependent | Preserve measured values; no missing-value calibration approved |
| 2024–2025 | Multiple reported changes in `barometer-pressure` for GW1000-named historical copy; 2025 hourly P is not published in the cited cache | Do not infer calibration from copy name or constant offset |
| 2026 | Hourly comparison through 2026-11-22 in cited study; current archive is incomplete at the end | Regional plausibility only; no unobserved interval is estimated |

Epoch boundaries dated 2013-08-08 and 2019-04-26 remain segmentation markers, not proof of a pressure sensor/calibration change on those exact days. The independent hourly evidence identifies a strong relationship break across April/May 2019. Earlier intervals have daily-only pressure references and must not be reported as hourly validated.

## Validation evidence and limits

The available numerical analysis reports 495,270 exact-UTC row/station/element/field comparisons. These are hourly SYNOP timestamps paired with WeeWX archive timestamps; equal timestamps do not prove equal temporal support. Quality codes other than 0 were excluded. The two CHMI stations provide independent regional checks.

The 2026-11-24 physical station-pressure run used 49,542 local exact-hour pressure values and 122,315 quality-zero CHMI station-hour references across 2018–2024. Coverage below is the share of valid CHMI reference hours matched by a non-NULL local station pressure. Bootstrap intervals resample whole UTC months (2,000 replicates), so they reflect between-month uncertainty and not the full sensor/elevation uncertainty.

Selected Holešov station-pressure results (transported from 425 m to station height and compared with CHMI `P`) are:

| Year | Pairs / reference coverage | MAE (hPa) | Median bias (hPa) | MAD (hPa) | P95 absolute error (hPa) | 95% month-block CI for MAE |
|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 4,242 / 48.7% | 22.83 | −22.84 | 1.57 | 25.62 | 21.72–23.80 |
| 2019 | 7,049 / 80.7% | 5.70 | −0.88 | 2.00 | 26.07 | 2.37–10.73 |
| 2020 | 7,698 / 88.0% | 2.28 | −2.02 | 1.69 | 4.86 | 1.54–3.00 |
| 2021 | 8,322 / 95.8% | 2.39 | −1.87 | 1.65 | 5.70 | 1.51–3.33 |
| 2022 | 4,829 / 55.2% | 1.05 | −0.26 | 0.75 | 3.16 | 0.77–1.47 |
| 2023 | 8,650 / 98.8% | 2.92 | +1.91 | 2.13 | 7.22 | 1.79–4.24 |
| 2024 | 8,592 / 97.9% | 2.94 | +2.84 | 1.16 | 5.53 | 2.37–3.49 |

Mošnov results are in the machine-readable output. Its transported-pressure MAE is 22.28, 5.46, 1.79, 1.97, 1.25, 3.40 and 3.51 hPa in 2018–2024, respectively. Both stations show the same large 2018 bias and changing later residuals. This is validation of a physical comparison method, not evidence that every station-pressure value is calibrated or that a 5-minute source value is safe to restore.

The new read-only runner is [`scripts/validate_pressure_station_field.py`](../scripts/validate_pressure_station_field.py); exact results and source hashes are in [`reports/pressure-station-field-validation-2026-11-24.json`](pressure-station-field-validation-2026-11-24.json). Its unit tests check the hypsometric direction/round trip, bad inputs and block bootstrap behavior.

### Hourly `barometer` model holdout

The frozen monthly model was separately evaluated on actual unseen hourly pairs in a single read-only transaction: 154,935 quality-zero CHMI station/reference values, 75,092 local `barometer` hours, and 20 train-station × test-station × epoch combinations. The references have SHA-256 manifest `3c935d0a134a6cd351fe1915cb0a720cf47bed4dc8fc18c0e7d88ece4b72409e`. H1 holdout has three months; H5 has five months.

| Epoch / direction | Raw hourly MAE | Frozen-model hourly MAE | Median residual | MAD | P95 absolute error | Gate |
|---|---:|---:|---:|---:|---:|---|
| H1 H→H | 27.133 | 0.709 | +0.328 | 0.498 | 1.928 | pass diagnostic |
| H1 H→M | 26.556 | 1.362 | +0.928 | 0.999 | 3.185 | pass diagnostic |
| H1 M→H | 27.133 | 1.411 | +1.300 | 0.530 | 2.897 | pass diagnostic |
| H1 M→M | 26.556 | 2.042 | +1.908 | 0.981 | 4.163 | fail |
| H2 (four directions) | 1.893–2.056 | 1.893–2.765 | −0.573 to +2.032 | 1.494–1.699 | 4.583–6.695 | all fail |
| H3 (four directions) | 2.410–2.896 | 2.107–2.695 | +1.505 to +2.297 | 1.353–1.420 | 4.913–5.787 | all fail |
| H5 (four directions) | 4.161–4.562 | 1.285–1.516 | −0.789 to +0.120 | 1.016–1.189 | 3.211–3.733 | pass diagnostic |
| H6 (four directions) | 0.660–1.000 | 0.635–1.030 | −0.264 to +0.340 | 0.589–0.893 | 1.403–2.311 | insufficient months (2) |

The diagnostic gate requires at least 3 test months and 200 hours, MAE ≤2 hPa, P95 ≤4 hPa, and at least 20% improvement over raw. H1 passes three of four directions, H5 passes all four, and no other epoch passes. These are actual hourly metrics for `barometer` against sea-level-reduced `P_hm`, with all frozen coefficients and station selection unchanged. They do not validate individual five-minute values, do not validate `pressure`, and do not authorize APPLY.

For 2025, the cited cache lacks hourly CHMI `P`; for 2026 its recent slice also lacks hourly `P`. `barometer` vs `P_hm` results exist but concern a different field and cannot validate `pressure` replacements by themselves. The reported 2018 WH pilot includes hourly MAE only in the cited group aggregates? The published pilot table provides median/MAD and quantiles, not candidate-specific hourly or five-minute error; therefore this review does not claim an MAE for WH restoration or a five-minute validation score.

For 2009–2017, daily `P` is used only as monthly context with its `TIMEFUNC` retained. No interpolation from daily values to hourly targets is treated as observation. The monthly model uses chronological train/validation/holdout splits and the hourly evaluation uses frozen coefficients only. The pressure runner above is a non-fitted physical transport diagnostic. No model is trained on future data. Candidate calibration for `pressure` still fails closed because exact source-level WH1080-to-hourly-CHMI pair data cannot be accessed through the existing LXC read-only SQL account, and no five-minute holdout has been completed.

## Read-only approval manifest and rollback

Machine-readable manifest: [`pressure-approval-manifest-2026-11-24.json`](pressure-approval-manifest-2026-11-24.json). Its candidate list has zero entries. Detached SHA-256 for the exact JSON file is recorded in the adjacent `.sha256` file; the canonical candidate-array SHA-256 is `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.

No batch ID for a data write is issued. If a future, separately approved process ever uses this evidence, it must create a new immutable manifest with exact target timestamp, variable, old/new values, source timestamp/database, method, unit, uncertainty, status, per-batch SHA-256, and an independent before-image. Rollback would restore only the recorded old value after verifying the current value still equals the approved new value; it must be a separate explicitly approved operation. This report itself does not authorize that step.

## Reproduction sources

- `reports/parallel-audit/pressure-2009-2026-chmi-readonly-20261123.md` — official reference coverage, methods, and completeness summary.
- `reports/parallel-audit/pressure-chmi-numeric-2009-2026.md` in the pressure analysis worktree / PR #89 — hourly and daily aggregate results.
- `reports/parallel-audit/pressure-wh1080-live-source-review-20261123.md` in the WH pilot worktree / PR #90 — exact source lineage counts and disposition.
- `reports/parallel-audit/pressure-wh1080-chmi-pilot-2018/README.md` in PR #91 — exact-hour WH diagnostic and dual-station results.
- `PRESSURE_SEMANTICS_VALIDATION_REPORT.md` — limited field-semantic validation for Jan–Feb 2026.

All committed data and read-only reports are versioned; original ČHMÚ CSV stay outside Git and are SHA-256 checked by the runners. The 2018 WH1080 source audit records 75,074 exact source values but its row-level source table is not available to the existing `loucka_web_ro` account, so this task did not create a candidate value from that series.

**Final disposition:** zero candidates for restoration; 198,175 target NULL pressure slots remain unresolved in the cited snapshot. Hourly `barometer` calibration is diagnostically supported only for H5, not for direct pressure restoration. No meteorological data write is proposed.
