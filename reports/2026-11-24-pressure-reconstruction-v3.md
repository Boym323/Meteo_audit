# Pressure reconstruction V3 — five-minute masked validation and unified shadow series

**Run:** 2026-11-24 · **status:** diagnostic, all new values `ESTIMATED / UNAPPROVED` · no data writes or APPLY.

## Read-only archive snapshot and station metadata

The export ran on `zl-dev-frontendPocasi` with the existing `/root/meteo-loucka-ro.cnf`, the established Python virtual environment and the existing `loucka_web_ro` account. The transaction began `START TRANSACTION READ ONLY`; server identity was checked before reading. The query exported every archive timestamp from 2009-01-01 through 2026-11-24 UTC (no whole-hour filter), with `usUnits`, interval, pressure, barometer and temperature. It returned **1,697,621 rows**, SHA-256 `e6b09eaef88f10d7334988928a84334c7b729bed941774565896f7dbaba86e42`. The 2020–2025 control subset has **557,367** records with pressure, barometer and temperature and the requested unit/range checks. Export CSV and V3 values remain outside Git under `/opt/meteo-audit-artifacts/pressure-reanalysis-v3/`.

ČHMÚ `meta1.csv` resolves Mošnov’s metadata conflict by epoch: **250.4 m through 2016-05-23 23:59 UTC; 252.8 m from 2016-05-24 00:00 UTC**, when the listed coordinates also change. The validation era uses 252.8 m. Transport sensitivity for 2.4 m is about **0.284 hPa** under the test temperature. We did not select a height to pass a gate.

## Control selection, splits and interpolation

Five-minute controls require `usUnits=16`, pressure 900–1050 hPa, barometer 930–1080 hPa and temperature −40..45 °C. This is broad source QC, not independent proof of local sensor calibration. Comparison methods require available, SHA-verified references; ERA5 can assimilate station observations. The resulting station-transfer holdout errors below are therefore shown directly and are not treated as truth for accepting candidates.

The frozen V1 barometer/temperature relation was residual-calibrated on **2020–2021**. Model choice was made only on **2022** (minimum 1,000 targets per model). The final chronological holdout is **2023–2025**. Synthetic contiguous masks were drawn only from that holdout, at lengths **5 min, 30 min, 1 h, 6 h, 1 d, 3 d, 14 d and 28 d**, with UTC season and stable/fast-change strata. Fast change is an absolute local pressure difference over the surrounding 10 minutes greater than 0.8 hPa. Uncertainty intervals use a deterministic UTC-month block bootstrap where at least three months are available; group empirical P95 is reported for every gap group.

A separate temporal-only test masks the same local five-minute targets for 10-minute and hourly interpolation. It requires a complete hour, 12 valid five-minute pressure records in range and adjacent five-minute changes ≤2 hPa. Results are **N=149,154** across 2023–2025; the exact same target timestamps are used for both estimates:

| Year | N | 10-minute linear MAE / P95 | Hourly linear MAE / P95 |
|---:|---:|---:|---:|
| 2023 | 50,736 | 0.0555 / 0.1395 hPa | 0.0910 / 0.2377 hPa |
| 2024 | 50,292 | 0.0547 / 0.1372 hPa | 0.0880 / 0.2308 hPa |
| 2025 | 48,126 | 0.0531 / 0.1331 hPa | 0.0846 / 0.2207 hPa |

These figures measure temporal interpolation of known local pressure observations only. They do not validate long-gap reconstruction or the transfer of raw ČHMÚ station pressure to Loučka.

## Model selection, matched holdout and gap results

On 2022 selection controls, the local V1 family had **MAE 0.431, median bias −0.044, P95 1.132 hPa (N=57,902)**. ERA5-hourly had 1.834 / −1.635 / 4.406 (N=57,902), transferred/interpolated ČHMÚ 10min had 1.854 / −1.426 / 4.210 (N=57,775), and the all-source blend had 1.286 / −1.100 / 2.874 (N=57,775). Local V1 was selected without seeing holdout.

On the **same 305,434 holdout timestamps** available to every model (99.744% of 306,218 local control targets), metrics were:

| Model | N / target coverage | MAE | Median bias | P95 absolute error |
|---|---:|---:|---:|---:|
| Local barometer V1 + frozen residual calibration | 305,434 / 99.744% | 0.456 | −0.021 | 1.231 |
| ČHMÚ 10min transferred/interpolated | 305,434 / 99.744% | 4.787 | −4.835 | 7.608 |
| ERA5 hourly interpolated | 305,434 / 99.744% | 4.764 | −4.811 | 7.497 |
| 1/3 blend: local + ČHMÚ + ERA5 | 305,434 / 99.744% | 3.219 | −3.214 | 5.252 |

The full, per-model denominators, exact paired metrics, year scores, and all gap-length × year × season × change-regime groups with bootstrap uncertainty are in [blocked-backtest-2020-2025.json](data/pressure-reanalysis-v3/blocked-backtest-2020-2025.json). V3 selected the local model. The ČHMÚ/ERA5 transfer and mixed candidates failed to improve the independent time holdout and are not used to create numeric V3 candidates.

Annual frozen-local-model masked comparisons against existing local archive pressure show MAE 0.388–0.508 hPa and P95 0.966–1.215 hPa in 2009–2017; 0.450/1.112 in 2018; 0.410/1.031 in 2019; 0.415–0.495/1.066–1.249 in 2020–2025. These are in-sample-in-epoch masked field-consistency checks for a derived local field, **not independent accuracy guarantees**. Annual ERA5 and ČHMÚ transfer scores are also present in the JSON; large epoch-dependent biases (for example 2016–2017 ERA5 and 2018 ČHMÚ/ERA5) are why those sources were not used as uncorrected point estimates.

For 2009–2017 the ERA5 hourly series is scored as a competing coarse reference. The existing daily ČHMÚ P context is used only at UTC calendar-month summary support: 68 months were screened, 66 have quality-zero daily AVG coverage. The prior context marks it `DAILY_STATION_PRESSURE_CONTEXT_ONLY`; no daily value is matched to an individual five-minute slot. It therefore supplies broad epoch/season context, not minute-level validation. The source audit records daily reference SHA-256 `1cc64eddb7b91bc8698536a99d548f00c551079b3c375f8da8eb8a147ea805cb` and explicitly prohibits treating it as individual-time validation.

## Unified V3 and comparison with V1/V2

V3 is a separate, complete row-aligned shadow series for the **1,697,621** snapshot timestamps through 2026-11-24 (partial year):

| Classification | Rows |
|---|---:|
| Existing source pressure (`MEASURED`) | 1,499,446 |
| V3 local-model estimate (`ESTIMATED / UNAPPROVED`) | 165,173 |
| `UNRESOLVED` | 20,467 |
| Protected Q1 2018 NULLs | 12,535 |

Thus V3 supplies candidates for 89.0% of NULL pressure timestamps outside protected Q1 2018. No Q1 2018 candidate exists. Candidate estimates have a gap-duration empirical uncertainty P95 and remain unapproved. Every row is preserved in the unified gzip; separate NULL-only candidate CSV carries model and source provenance. Full data artifacts and SHA-256 are in the local manifest [final-v3-artifact-manifest.json](data/pressure-reanalysis-v3/final-v3-artifact-manifest.json); the 1.7M-row values are not published to Git.

| Version | Candidate rows | Coverage scope | Validation note |
|---|---:|---|---|
| V1 | 15,166 | 2022 pilot | Local barometer model; old artifacts retained unchanged |
| V2 | 16,985 | 2022 hourly shadow | ERA5 plus filtered V1; hourly-only; old artifacts retained unchanged |
| V3 | 165,173 | 2009–2026 partial | Local V1 family after temporal holdout; 89.0% of unprotected NULL rows |

V3 expands candidate coverage substantially while keeping the original V1/V2 files unchanged (original artifact hashes are recorded in the build environment). The accuracy figures compare model families on actual measured local pressure controls and do not establish independent sensor calibration. The status of every proposed value is still `UNAPPROVED`.

## Reproducible artifacts and checks

- [Read-only exporter](../scripts/export_pressure_reconstruction_v3_readonly.py), archive export provenance and SHA in `data/pressure-reanalysis-v3/`.
- [Blocked artificial-gap backtest](../scripts/backtest_pressure_reconstruction_v3.py) and [V3 row-series builder](../scripts/build_pressure_reconstruction_v3.py); no SQL writes.
- [Temporal interpolation check](../scripts/validate_pressure_temporal_interpolation_v3.py) and [SVG plot](data/pressure-reanalysis-v3/pressure-v3-validation.svg).
- Nine targeted V2/V3 regression tests pass; Python compilation and `git diff --check` pass. CI is run on this PR.
- New source references and candidate values remain outside Git; only aggregate metrics, manifests and hashes are published.

No SQL writes, APPLY, production/WeeWX changes or permission changes were performed. Q1 2018, V1 and V2 are preserved.

## Review follow-up: corrected ERA5 physics, QC and physical reference series

The newest PR #99 review found a sign error in ERA5 hypsometric transport and found that the earlier backtest described, but did not enforce, its QC screen. Both are corrected in the source. The shared transport now uses `p_target = p_source × exp(g × (z_source − z_target) / (Rd × T))`; descending from the ERA5 grid at 480 m to Loučka at 425 m raises 950 hPa at 10 °C to about 956.3 hPa. Tests cover equal heights, ascent, descent, round trip and the actual ERA5 predictor. The backtest now uses one fail-closed control predicate before fitting, selection, holdout, and annual comparisons: `usUnits=16`, five-minute interval and UTC cadence, input ranges, frozen V1 training domain, and exclusion of the SHA-identified suspected isolated-spike timestamps. Model, archive and QC hashes are bound into the result. The corrected V3 shadow builder verifies those hashes, applies the same input domain, and leaves gaps longer than the empirically tested 28-day maximum without a reported empirical uncertainty.

The complete corrected backtest was rerun on the read-only snapshot. After QC, frozen-model selection on 2022 still selects local V1 (MAE 0.429 hPa, P95 1.137, n=56,588). On the 2023–2025 holdout, models have **300,450 identical timestamps** out of 301,216 eligible targets. Local V1 is 0.456 / 1.234 hPa MAE/P95; corrected ERA5 is 4.741 / 7.509 and transferred ČHMÚ is 4.832 / 7.627. These local-target metrics concern the historically stored field and do not validate its absolute physical level. The gap experiment now contains 926,181 point scores in 510 model × length × year × season × regime groups. The model, comparison and gap metrics remain diagnostic and unapproved.

The separate physical series is built directly from quality-zero 10-minute ČHMÚ station pressure: interpolate each station only over gaps ≤20 minutes, transport each pressure from its epoch-valid station height to 425 m, then average the two station estimates. The hypsometric column temperature uses local `outTemp` when it passes the −40..45 °C screen, otherwise interpolated ERA5 2 m temperature; estimates are withheld if neither is valid. The corrected ERA5 series and local archive pressure changes are retained as separate diagnostics; local changes are compared to CHMI changes so level drift does not become a calibration offset. The two station directions are reported as **paired interstation disagreement**, separated by year and the 2019-04-26T14:45Z source boundary. The directions share the same timestamps and are not independent validations. Their P95 is a disagreement screen, not a calibrated prediction interval or a coverage guarantee. The physical layer records exact 10-minute references separately from linear support (up to 20 minutes), plus local-temperature versus ERA5-temperature fallback counts. This validates consistency of nearby station transfer only; it does not prove absolute calibration of the Loučka sensor. All physical values remain `ESTIMATED / UNAPPROVED`.

| Period / source epoch | Physically validated regional-reference estimates | Archive-reproducing only | Unresolved | Interpretation |
|---|---:|---:|---:|---|
| 2009–2015 | 1,833 | 11,456 | 8,387 | Separate hourly ERA5 diagnostic passes daily context screen; hourly accuracy is not validated. |
| 2016–2017 | 3,669 | 35,684 | 4,661 | Separate hourly ERA5 diagnostic passes daily context screen; hourly accuracy is not validated. |
| 2018 (Q1 protected) | 34,007 | 0 | 0 | Bidirectional station holdout passes; Q1 remains protected and contains no candidates. |
| 2019 through 2019-04-25 | 19,389 | 7 | 0 | Separate pre-source-change station consistency screen passes. |
| 2019 from 2019-04-26 14:45Z | 653 | 0 | 0 | Separate post-source-change station consistency screen passes. |
| 2020–2022 | 59,462 | 106 | 1 | Epoch-specific regional reference support. |
| 2023–2025 | 6,285 | 1 | 1 | Epoch-specific regional reference support. |
| 2026 partial | 0 | 37 | 1 | No completed epoch holdout. |

The earlier **77,556-row legacy V3 catalogue for 2016–2018 is superseded**. It produced 43,549 archive-reproducing-only values in 2016–2017, based on the old candidate catalogue. The final decision classes use corrected QC plus separate physical support: 35,684 corrected archive-only rows, 3,669 hourly ERA5 regional estimates with daily-context support, and 4,661 unresolved in 2016–2017; 34,007 CHMI regional estimates in 2018. Corrected candidate rows can overlap the ERA5 category as specified above. Q1 2018 remains protected. Historical archive replicas are not promoted as physical pressure.

The external level comparison documents the historical drift. Local stored pressure minus the transported two-station CHMI mean has median **−22.14 hPa in 2018**, **−24.43 hPa before 2019-04-26**, and **+0.23 hPa after that date**. Local short-term changes remain much closer to CHMI. Corrected ERA5 is also compared to the two-station mean, but ERA5 may assimilate CHMI and is not treated as an independent station holdout.

| Source epoch | Local stored level vs transported CHMI mean (n; MAE / median bias / P95 hPa) | Local 10-minute change vs CHMI change (MAE hPa) | Corrected ERA5 vs CHMI mean (MAE hPa) | CHMI station cross-holdout |
|---|---:|---:|---:|---|
| 2018 | 25,601; 22.04 / −22.14 / 24.81 | 0.117 | 0.652 | H→M and M→H: each n=48,806; MAE 0.691, P95 1.778; pass |
| 2019 through 2019-04-25 | 6,946; 24.51 / −24.43 / 26.44 | 0.118 | 0.663 | Separate pre-change gate passes |
| 2019-04-26 onward | 35,349; 1.65 / +0.23 / 3.56 | 0.105 | 0.758 | Separate post-change gate passes |

ERA5, calibrated to the stored 2020–2021 local field for the comparison backtest, still has median errors of **+10.95 hPa in 2016** and **+15.74 hPa in 2017** against that field. Those are drift diagnostics, not ERA5 physical accuracy scores. The 2016–2017 point-level physical decision remains unresolved because the available CHMI context is daily, not timestamp-matched 10-minute pressure.

The separate complete row-aligned physical series and corrected archive-reproduction shadow remain outside Git at `/opt/meteo-audit-artifacts/pressure-reanalysis-v3/corrected-physical-v1/`. Aggregate decision and validation tables, hashes, and corrected backtest are in [corrected-physical-v1 artifacts](data/pressure-reanalysis-v3/corrected-physical-v1/). The original V1, V2 and first V3 outputs are unchanged. The corrected shadow build has 150,942 estimates (all unapproved); it is explicitly a historical-field reproduction product and is not the physical series.


## Final review reconciliation: three independent layers and epoch decisions

The final release is aligned to the **corrected QC V3 catalogue (150,942 candidates)**. The older 165,173-row catalogue is kept only as superseded provenance; its values never determine corrected archive-only counts. In 2016–2017 the corrected candidate catalog contains **38,924 rows** (13,636 + 25,288), rather than the superseded 43,549. Of these, **35,684** are classified archive-only, **3,240** also have an ERA5 regional estimate, and **429** of the 3,669 ERA5 estimates are not corrected-catalog candidates. The final decision classes are mutually exclusive and sum to the target NULLs; the catalogue overlap is provenance and is not additive. The final row-aligned three-layer shadow contains 1,697,621 timestamps; its SHA-256 is `d606dcbee01491f1e393635f8a560bf96d89b2ae0de4260be18a78d2a4bbe5da`. Q1 2018 has **12,535 protected NULLs and zero proposed values**.

The three output columns are kept separate: (1) original archived pressure, unchanged; (2) corrected-QC reconstruction of the historical archive field; and (3) regional physical reference estimates. The first layer is not thereby certified as calibrated; the second reproduces the historical local field and is unapproved; the third uses the exact hourly ERA5 physical transfer in 2009–2017, with no fitted offset, and the transferred CHMI 10-minute station references from 2018 onward. No silent fill/coalescing occurs. Every new value remains `ESTIMATED / UNAPPROVED`.

| Epoch | Regional physical estimates | Corrected archive-only | Unresolved | Separate-layer recommendation |
|---|---:|---:|---:|---|
| 2009–2015 | 1,833 | 11,456 | 8,387 | **GO**, hourly ERA5 regional diagnostic only; daily context passes, but hourly accuracy is not validated. |
| 2016–2017 | 3,669 | 35,684 | 4,661 | **GO**, hourly ERA5 regional diagnostic only. Context-screen metrics below; do not interpret as point-level hourly accuracy. |
| 2018 (Q1 protected) | 34,007 | 0 | 0 | **GO**, CHMI regional diagnostic; Q1’s 12,535 NULLs remain protected and blank. |
| 2019 before 2019-04-26 14:45Z | 19,389 | 7 | 0 | **GO**, CHMI diagnostic, evaluated as its own source epoch. |
| 2019 from 2019-04-26 14:45Z | 653 | 0 | 0 | **GO**, CHMI diagnostic, evaluated as its own source epoch. |
| 2020–2022 | 59,462 | 106 | 1 | **GO**, CHMI regional diagnostic. |
| 2023–2025 | 6,285 | 1 | 1 | **GO**, CHMI regional diagnostic. |
| 2026 partial | 0 | 37 | 1 | **NO-GO**, no completed CHMI 10-minute validation epoch. |

CHMI reference consistency screen by epoch (paired station disagreement, hPa):

| Epoch | Paired timestamps n | MAE | Signed mean bias H−M | P95 absolute disagreement | Screen |
|---|---:|---:|---:|---:|---|
| 2018 | 48,806 | 0.691 | +0.405 | 1.778 | Pass |
| 2019 before 14:45Z | 16,632 | 0.949 | +0.797 | 2.087 | Pass |
| 2019 from 14:45Z | 35,533 | 0.689 | +0.534 | 1.723 | Pass |
| 2020 | 49,112 | 0.810 | +0.649 | 1.958 | Pass |
| 2021 | 51,112 | 0.791 | +0.633 | 1.874 | Pass |
| 2022 | 50,549 | 0.784 | +0.540 | 2.002 | Pass |
| 2023 | 52,053 | 0.787 | +0.561 | 2.005 | Pass |
| 2024 | 51,989 | 0.746 | +0.487 | 1.980 | Pass |
| 2025 | 50,710 | 0.766 | +0.620 | 1.844 | Pass |

**Database replacement is NO-GO for every epoch.** The regional GO above permits review/use only as a separate unapproved research layer; no epoch has independent local absolute calibration, and nothing is approved for APPLY. Older candidate provenance can overlap other categories and is not additive.

For 2009–2017 the physical ERA5 layer has **78,888 exact hourly values**, zero duplicate timestamps, and 3,287 complete UTC-date matches against quality-zero CHMI daily `P / AVG`. Every year has 100% daily coverage and passes the unchanged context screen. Annual daily comparison MAE / median bias / P95 absolute error (hPa), with n=365/366 days: 2009 **0.527 / +0.184 / 1.332**; 2010 **0.548 / +0.218 / 1.379**; 2011 **0.477 / +0.044 / 1.172**; 2012 **0.493 / −0.046 / 1.234**; 2013 **0.518 / −0.091 / 1.317**; 2014 **0.503 / −0.161 / 1.265**; 2015 **0.536 / −0.166 / 1.203**; 2016 **0.558 / −0.027 / 1.352**; 2017 **0.562 / +0.133 / 1.440**. This compares same-date daily means, with daily CHMI transferred using mean ERA5 temperature; it cannot validate hourly extremes or point-level hour accuracy. ERA5 may assimilate CHMI. The hourly file SHA-256 is `efb1af3e4b39d129b2d40259b4c2171ca510767c1186f4049a4ee8935ee4540a`.

The local-increment hybrid was tested on the withheld 2018 Q4 controls (n=7,752). Relative to ordinary CHMI interpolation, increment MAE worsened from **0.0634 to 0.0886 hPa** (+39.6%); P95 worsened from 0.1636 to 0.2299 hPa. Its absolute level still differed from the local archive by MAE 23.76 hPa. It is **NO-GO** and is not part of the three released layers.

Continuity checks preserve source support and do not smooth detected jumps. In the separate regional layer, 2018 maximum adjacent 5-minute step was 1.814 hPa (zero >2); 2019 maximum was 1.194 hPa (zero >2). In 2021 eight adjacent steps exceeded 3 hPa (maximum 5.265); in 2017 ERA5 had one >3 hPa step (maximum 3.245). Across the entire hypothetical coalescing diagnostic there are 2,351 adjacent steps >3 hPa and maximum 28.124 hPa; no such coalesced series is emitted. This is a boundary/continuity warning, not a pointwise error score. Daily and monthly layer means, spread, range, and counts are included in the external catalog audit; the daily/monthly summary CSVs and million-row series remain in `/opt/meteo-audit-artifacts/pressure-reanalysis-v3/final-layers-v1/final-three-layers/`.

Uncertainty semantics are intentionally limited: interstation P95 is paired station disagreement; ERA5-vs-CHMI P95 is a daily-support validation statistic; neither is a row-wise calibrated 95% interval. Archive reconstruction has its empirical backtest P95 only within tested strata. Exact versus linearly interpolated station support, temperature fallback, and the corrected QC catalogue are preserved in the final manifests.

Final aggregate manifests: [three-layer release](data/pressure-reanalysis-v3/final-layers-v1/pressure-three-layer-manifest-v1.json), [physical reference and support](data/pressure-reanalysis-v3/final-layers-v1/manifest-physical-v1.json), [ERA5 daily validation](data/pressure-reanalysis-v3/final-layers-v1/era5-daily-check-2009-2017.json), and [hybrid holdout](data/pressure-reanalysis-v3/final-layers-v1/hybrid-holdout-2018-Q4.json). Original data, V1/V2 and earlier V3 artifacts are preserved. No SQL write, APPLY, production/WeeWX change, or permission change was performed.
