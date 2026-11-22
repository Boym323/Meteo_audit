# Pressure semantics validation review

Frozen target concordance: `1e34859d05bb0ec20d3810c4fbb376d231a6ee0bfca0c4c636dcfb2d1114e4ba`. Pressure reference manifest SHA-256: `5ecb9ebb639d6dfd00610526dc62408b9260157170349d9b8397168795f2a762`.

## Scope and disposition

The evidence covers all 68 priority monthly `barometer` candidates as concurrent field-offset diagnostics, plus exact-UTC-hour regional CHMI pressure context for January and February 2026. This evidence does not identify which Loučka field is raw, station pressure, sea-level pressure or a driver/WeeWX derivation. Keep pressure candidates in review; no field substitution or recalculation is authorized.

## Candidate-wide field relationships

`barometer − pressure` and `altimeter − barometer` distributions are available for 68 of 68 monthly barometer candidates in `PRESSURE_CANDIDATE_SEMANTICS_REVIEW.md`. January 2026 reproduces medians of +52.620 hPa and −2.399 hPa across 8,888 paired archive rows. The relationship changes seasonally: the 68 candidates show a range of monthly medians rather than one constant offset.

## Official CHMI regional context

CHMI Holešov hourly SYNOP `P_hm` is sea-level-reduced pressure. Comparisons below use exact UTC hourly timestamps, quality code 0, and no interpolation. CHMI metadata gives Holešov elevation 222.25 m; verified Loučka sensor coordinates and elevation are still absent. Hourly timestamp equality does not establish equal time functions for CHMI and WeeWX samples.

| Period | Expected hours | Valid CHMI hours | Matched hours | Coverage | Local barometer mean | CHMI P_hm mean | CHMI−barometer bias | MAE | RMSE | Correlation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-01 | 744 | 736 | 735 | 99.864% | 1016.03 hPa | 1012.93 hPa | -3.09 hPa | 3.09 hPa | 3.28 hPa | 0.996 |
| 2026-02 | 672 | 672 | 671 | 99.851% | 1009.95 hPa | 1010.67 hPa | 0.72 hPa | 1.36 hPa | 1.66 hPa | 0.992 |

### Other stored fields at the same timestamps

| Period | Local `pressure` mean | CHMI−pressure bias | Local `altimeter` mean | CHMI−altimeter bias | Median barometer−pressure | Median altimeter−barometer |
|---|---:|---:|---:|---:|---:|---:|
| 2026-01 | 963.43 hPa | 49.51 hPa | 1013.56 hPa | -0.61 hPa | 52.63 hPa | -2.40 hPa |
| 2026-02 | 958.31 hPa | 52.36 hPa | 1008.22 hPa | 2.45 hPa | 51.70 hPa | -1.57 hPa |

These observations support only a limited regional consistency check: local `barometer` is within a few hPa of CHMI P_hm in these months, while local `pressure` is roughly 50–52 hPa lower. That pattern is consistent with distinct station-level and reduced pressure quantities, but it does not prove that is what the Loučka fields mean. The offset is not used to infer Loučka elevation, and no pressure value is corrected. The 2026 results do not resolve the other 66 barometer candidates or historical sensor epochs.

## Remaining evidence required

To decide the fields’ physical meaning, obtain the dated Loučka station elevation and coordinates, model/identity of the pressure sensor, gateway and firmware, WeeWX driver/version, complete configuration snapshots and the specific reduction formula/parameters. Row-wise reproduction should start from a verified raw station-pressure input and temperature. CHMI Holešov is regional context, not a substitute for those deployment records.

Reference source manifest: `data/chmi-2026-synop-pressure/manifest.json`. Validation JSON SHA-256: `ddbfe69a5dc4877407073a8647a616a068ed2f2a748e3e2a578d20bc9df4130f`.
