# Humidity candidate series screening

Frozen concordance SHA-256: `1e34859d05bb0ec20d3810c4fbb376d231a6ee0bfca0c4c636dcfb2d1114e4ba`. Series diagnostic SHA-256: `8a43b737f20d446cda103285a779a3e654efa426ac3baa20066cafddcffaa306`.

The archive-series scan covers 45 of 45 priority monthly outHumidity candidates. 31 candidates contain at least one value at or above 99%; across those candidates there are 23,612 such rows.

## Longest runs at or above 99%

Run continuity uses adjacent archived rows and breaks when the timestamp gap exceeds 1.5 times the larger adjacent interval. A run may contain both 99% and 100% values.

| Period | Rows ≥99% | Longest run | Value at longest exact run | Candidate rows |
|---|---:|---:|---:|---:|
| 2011-01 | 3,624 | 79.67 h | 99.0 (78.42 h exact) | 8,927 |
| 2020-12 | 2,380 | 79.25 h | 100.0 (64.83 h exact) | 8,903 |
| 2010-12 | 1,222 | 47.50 h | 99.0 (46.92 h exact) | 8,906 |
| 2026-02 | 1,968 | 22.25 h | 99.0 (22.25 h exact) | 8,044 |
| 2010-09 | 1,395 | 21.58 h | 99.0 (11.50 h exact) | 8,566 |
| 2010-11 | 1,692 | 19.00 h | 99.0 (17.50 h exact) | 8,619 |
| 2024-12 | 833 | 18.75 h | 99.0 (18.75 h exact) | 8,923 |
| 2011-02 | 844 | 17.42 h | 99.0 (16.67 h exact) | 8,038 |
| 2026-01 | 1,269 | 15.67 h | 99.0 (15.67 h exact) | 8,925 |
| 2024-02 | 824 | 15.58 h | 99.0 (15.58 h exact) | 8,329 |
| 2010-01 | 166 | 13.83 h | 99.0 (13.83 h exact) | 8,901 |
| 2024-03 | 517 | 13.17 h | 99.0 (13.17 h exact) | 8,870 |
| 2025-10 | 976 | 12.00 h | 99.0 (12.00 h exact) | 8,882 |
| 2025-09 | 985 | 11.58 h | 99.0 (11.58 h exact) | 8,611 |
| 2025-07 | 608 | 11.50 h | 99.0 (11.50 h exact) | 8,888 |

January 2026 remains sensor-review-required: the detailed pilot review identifies two 99% plateaus, the longest lasting 15 h 40 min. That differs from the aggregate period scan's definition of any consecutive ≥99% run, so the values are not directly interchangeable.

These runs are flags for targeted context review. High humidity and long repeated values can arise from weather, quantization, saturation, condensation, or sensor behavior; the archive series alone cannot distinguish these explanations. The station's humidity sensor model, upper measurement limit, siting, ventilation, and dated configuration remain undocumented. No correction is applied and no candidate receives positive readiness from this screen.

Source: `MONTHLY_CANDIDATE_SERIES_DIAGNOSTICS.json`; target values from the frozen value concordance. The scan does not treat archive-copy matches as independent sensor validation.

## Regional comparison extension: 45 humidity months screened

Exact UTC 10-minute CHMI data were compared for 25 of 45 priority humidity candidate months, with 50 station-month results. References include Vizovice (0-203-0-11777) and Kladná-Žilín (0-203-0-11778) where available. The comparator is regional evidence only. CHMI quality code 0 is required; no interpolation is used. The candidate value is the existing monthly Loučka mean.

Candidates without compatible same-month 10-minute humidity references: 20 (2009-05, 2009-09, 2009-11, 2010-01, 2010-04, 2010-05, 2010-09, 2010-11, 2010-12, 2011-01, 2011-02, 2013-09, 2013-11, 2014-02, 2014-08, 2014-10, 2014-11, 2014-12, 2015-01, 2015-02). Plateau runs are separately screened across all 45 candidate months.

| Period | CHMI station | Matched pairs | Reference coverage | Loučka paired RH | CHMI paired RH | CHMI−Loučka bias | MAE | RMSE | Correlation |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2020-12 | 0-203-0-11777 | 4446 | 99.708% | 92.31% | 82.66% | -9.65 pp | 10.29 pp | 11.58 pp | 0.774 |
| 2020-12 | 0-203-0-11778 | 4446 | 99.708% | 92.31% | 85.45% | -6.86 pp | 7.58 pp | 9.09 pp | 0.813 |
| 2023-01 | 0-203-0-11777 | 4458 | 99.866% | 84.91% | 86.66% | 1.75 pp | 4.79 pp | 6.07 pp | 0.797 |
| 2023-01 | 0-203-0-11778 | 4458 | 99.866% | 84.91% | 86.13% | 1.22 pp | 3.58 pp | 4.75 pp | 0.837 |
| 2023-02 | 0-203-0-11777 | 4025 | 99.826% | 78.18% | 80.65% | 2.47 pp | 5.82 pp | 6.94 pp | 0.877 |
| 2023-02 | 0-203-0-11778 | 4025 | 99.826% | 78.18% | 78.48% | 0.30 pp | 4.85 pp | 6.32 pp | 0.867 |
| 2023-03 | 0-203-0-11777 | 4438 | 99.551% | 68.57% | 68.88% | 0.31 pp | 6.15 pp | 7.64 pp | 0.915 |
| 2023-03 | 0-203-0-11778 | 4437 | 99.551% | 68.58% | 68.63% | 0.05 pp | 5.43 pp | 6.87 pp | 0.921 |
| 2023-04 | 0-203-0-11777 | 4299 | 99.514% | 70.81% | 74.14% | 3.33 pp | 6.07 pp | 7.59 pp | 0.945 |
| 2023-04 | 0-203-0-11778 | 4299 | 99.514% | 70.81% | 71.34% | 0.53 pp | 4.23 pp | 5.59 pp | 0.954 |
| 2023-06 | 0-203-0-11777 | 4289 | 99.605% | 65.03% | 71.04% | 6.01 pp | 7.20 pp | 9.13 pp | 0.949 |
| 2023-06 | 0-203-0-11778 | 4292 | 99.605% | 65.03% | 69.99% | 4.96 pp | 6.17 pp | 8.00 pp | 0.951 |
| 2023-07 | 0-203-0-11777 | 4424 | 99.104% | 63.61% | 67.62% | 4.01 pp | 6.67 pp | 8.55 pp | 0.951 |
| 2023-07 | 0-203-0-11778 | 4424 | 99.104% | 63.61% | 68.65% | 5.04 pp | 6.52 pp | 8.19 pp | 0.954 |
| 2023-08 | 0-203-0-11777 | 4440 | 99.462% | 73.88% | 78.65% | 4.77 pp | 6.34 pp | 8.07 pp | 0.936 |
| 2023-08 | 0-203-0-11778 | 4440 | 99.462% | 73.88% | 79.09% | 5.21 pp | 6.66 pp | 8.70 pp | 0.919 |
| 2023-09 | 0-203-0-11777 | 4313 | 99.838% | 71.07% | 78.00% | 6.93 pp | 7.96 pp | 9.44 pp | 0.946 |
| 2023-09 | 0-203-0-11778 | 4313 | 99.838% | 71.07% | 78.36% | 7.29 pp | 7.77 pp | 9.46 pp | 0.941 |
| 2023-10 | 0-203-0-11777 | 4452 | 99.597% | 78.35% | 79.52% | 1.16 pp | 5.24 pp | 6.27 pp | 0.930 |
| 2023-10 | 0-203-0-11778 | 4452 | 99.597% | 78.35% | 80.69% | 2.33 pp | 5.14 pp | 6.50 pp | 0.919 |
| 2023-12 | 0-203-0-11777 | 4451 | 99.821% | 89.21% | 86.81% | -2.40 pp | 4.60 pp | 6.15 pp | 0.863 |
| 2023-12 | 0-203-0-11778 | 4451 | 99.821% | 89.21% | 87.34% | -1.87 pp | 3.59 pp | 4.82 pp | 0.859 |
| 2024-02 | 0-203-0-11777 | 4159 | 99.712% | 87.85% | 81.40% | -6.45 pp | 7.72 pp | 9.18 pp | 0.861 |
| 2024-02 | 0-203-0-11778 | 4158 | 99.712% | 87.84% | 81.56% | -6.29 pp | 7.28 pp | 8.75 pp | 0.867 |
| 2024-03 | 0-203-0-11777 | 4434 | 99.462% | 77.81% | 71.47% | -6.34 pp | 7.42 pp | 8.71 pp | 0.943 |
| 2024-03 | 0-203-0-11778 | 4434 | 99.462% | 77.81% | 70.50% | -7.31 pp | 7.81 pp | 8.86 pp | 0.955 |
| 2024-04 | 0-203-0-11777 | 4305 | 99.653% | 75.00% | 70.75% | -4.25 pp | 6.20 pp | 7.70 pp | 0.948 |
| 2024-04 | 0-203-0-11778 | 4305 | 99.653% | 75.00% | 71.19% | -3.81 pp | 6.28 pp | 7.77 pp | 0.935 |
| 2024-05 | 0-203-0-11777 | 4442 | 99.507% | 70.72% | 70.22% | -0.50 pp | 5.92 pp | 7.89 pp | 0.934 |
| 2024-05 | 0-203-0-11778 | 4442 | 99.507% | 70.72% | 70.84% | 0.12 pp | 5.25 pp | 7.13 pp | 0.944 |
| 2024-06 | 0-203-0-11777 | 4314 | 99.861% | 75.54% | 75.04% | -0.49 pp | 4.88 pp | 6.55 pp | 0.941 |
| 2024-06 | 0-203-0-11778 | 4314 | 99.861% | 75.54% | 75.59% | 0.06 pp | 4.77 pp | 6.23 pp | 0.943 |
| 2024-08 | 0-203-0-11777 | 4448 | 99.642% | 71.82% | 72.52% | 0.70 pp | 5.64 pp | 6.99 pp | 0.951 |
| 2024-08 | 0-203-0-11778 | 4448 | 99.642% | 71.82% | 73.25% | 1.42 pp | 6.08 pp | 7.41 pp | 0.939 |
| 2024-10 | 0-203-0-11777 | 4427 | 99.282% | 83.30% | 78.20% | -5.10 pp | 6.38 pp | 7.81 pp | 0.952 |
| 2024-10 | 0-203-0-11778 | 4425 | 99.282% | 83.31% | 81.75% | -1.57 pp | 4.92 pp | 6.25 pp | 0.912 |
| 2024-12 | 0-203-0-11777 | 4462 | 99.955% | 91.22% | 84.29% | -6.93 pp | 7.19 pp | 8.52 pp | 0.855 |
| 2024-12 | 0-203-0-11778 | 4462 | 99.955% | 91.22% | 86.04% | -5.18 pp | 6.01 pp | 7.43 pp | 0.805 |
| 2025-06 | 0-203-0-11777 | 4295 | 99.745% | 71.79% | 68.70% | -3.09 pp | 7.33 pp | 8.64 pp | 0.936 |
| 2025-06 | 0-203-0-11778 | 4309 | 99.745% | 71.73% | 69.07% | -2.66 pp | 7.15 pp | 8.54 pp | 0.941 |
| 2025-07 | 0-203-0-11777 | 4445 | 99.574% | 77.16% | 74.59% | -2.57 pp | 6.13 pp | 7.64 pp | 0.949 |
| 2025-07 | 0-203-0-11778 | 4445 | 99.574% | 77.16% | 74.82% | -2.34 pp | 6.10 pp | 7.62 pp | 0.948 |
| 2025-09 | 0-203-0-11777 | 4295 | 99.675% | 83.88% | 80.83% | -3.04 pp | 5.89 pp | 7.39 pp | 0.927 |
| 2025-09 | 0-203-0-11778 | 4295 | 99.675% | 83.88% | 82.37% | -1.50 pp | 4.92 pp | 6.42 pp | 0.933 |
| 2025-10 | 0-203-0-11777 | 4442 | 99.374% | 86.58% | 81.68% | -4.90 pp | 7.18 pp | 9.10 pp | 0.876 |
| 2025-10 | 0-203-0-11778 | 4442 | 99.374% | 86.58% | 82.70% | -3.87 pp | 6.34 pp | 8.25 pp | 0.892 |
| 2026-01 | 0-203-0-11777 | 4458 | 99.978% | 87.21% | 78.81% | -8.40 pp | 8.76 pp | 10.43 pp | 0.904 |
| 2026-01 | 0-203-0-11778 | 4458 | 99.978% | 87.21% | 81.21% | -6.00 pp | 6.77 pp | 8.51 pp | 0.888 |
| 2026-02 | 0-203-0-11777 | 4021 | 99.727% | 91.77% | 84.44% | -7.33 pp | 8.04 pp | 9.59 pp | 0.843 |
| 2026-02 | 0-203-0-11778 | 4021 | 99.727% | 91.77% | 85.39% | -6.38 pp | 6.83 pp | 8.31 pp | 0.882 |

## Individual archive-series outcome for every priority candidate

Each candidate below has a separate archive-series screen. “≥99% rows” and the longest continuous run are flags, not fault diagnoses. Subdaily bias ranges summarize exact-UTC comparisons; daily values are aggregate regional context only. CHMI daily aggregation window and weighting are not documented as equivalent to the Loučka civil-month archive mean.

| Period | Loučka mean RH | Rows ≥99% | Longest ≥99% run | Longest exact-value run | 10m CHMI station-months | 10m bias range | Daily context (station: mean; Δ pp) |
|---|---:|---:|---:|---:|---:|---:|---|
| 2009-05 | 64.73% | 0 (0.0%) | 0.00 h | 92.0 for 2.58 h | 0 | no reference | Vizovice: 69.5% (+4.8 pp); Kladna-Zilin: 69.8% (+5.1 pp) |
| 2009-09 | 73.87% | 0 (0.0%) | 0.00 h | 89.0 for 4.17 h | 0 | no reference | Vizovice: 78.5% (+4.6 pp); Kladna-Zilin: 76.3% (+2.4 pp) |
| 2009-11 | 89.51% | 185 (2.1%) | 7.08 h | 99.0 for 7.08 h | 0 | no reference | Vizovice: 85.7% (-3.8 pp); Kladna-Zilin: 83.7% (-5.8 pp) |
| 2010-01 | 87.68% | 166 (1.9%) | 13.83 h | 99.0 for 13.83 h | 0 | no reference | Vizovice: 85.0% (-2.7 pp) |
| 2010-04 | 74.99% | 292 (3.4%) | 9.67 h | 99.0 for 9.67 h | 0 | no reference | Vizovice: 72.8% (-2.2 pp) |
| 2010-05 | 84.54% | 44 (0.5%) | 3.67 h | 95.0 for 5.92 h | 0 | no reference | Vizovice: 85.6% (+1.1 pp) |
| 2010-09 | 85.48% | 1,395 (16.3%) | 21.58 h | 99.0 for 11.50 h | 0 | no reference | Vizovice: 83.8% (-1.7 pp) |
| 2010-11 | 89.68% | 1,692 (19.6%) | 19.00 h | 99.0 for 17.50 h | 0 | no reference | Vizovice: 80.6% (-9.1 pp) |
| 2010-12 | 92.28% | 1,222 (13.7%) | 47.50 h | 99.0 for 46.92 h | 0 | no reference | Vizovice: 85.2% (-7.1 pp) |
| 2011-01 | 93.98% | 3,624 (40.6%) | 79.67 h | 99.0 for 78.42 h | 0 | no reference | Vizovice: 86.8% (-7.1 pp) |
| 2011-02 | 84.98% | 844 (10.5%) | 17.42 h | 99.0 for 16.67 h | 0 | no reference | Vizovice: 75.7% (-9.3 pp); Kladna-Zilin: 73.6% (-11.3 pp) |
| 2013-09 | 81.42% | 797 (9.2%) | 7.58 h | 100.0 for 5.33 h | 0 | no reference | Vizovice: 83.0% (+1.5 pp); Kladna-Zilin: 84.9% (+3.5 pp) |
| 2013-11 | 89.00% | 53 (0.6%) | 2.00 h | 93.0 for 10.50 h | 0 | no reference | Vizovice: 84.4% (-4.6 pp); Kladna-Zilin: 87.3% (-1.7 pp) |
| 2014-02 | 82.78% | 0 (0.0%) | 0.00 h | 95.0 for 8.67 h | 0 | no reference | Vizovice: 74.9% (-7.9 pp); Kladna-Zilin: 79.6% (-3.1 pp) |
| 2014-08 | 81.73% | 384 (4.3%) | 3.67 h | 99.0 for 3.67 h | 0 | no reference | Vizovice: 81.4% (-0.3 pp); Kladna-Zilin: 84.1% (+2.3 pp) |
| 2014-10 | 89.66% | 184 (2.1%) | 1.67 h | 97.0 for 6.75 h | 0 | no reference | Vizovice: 85.4% (-4.3 pp); Kladna-Zilin: 88.1% (-1.6 pp) |
| 2014-11 | 89.00% | 274 (3.2%) | 7.50 h | 99.0 for 7.50 h | 0 | no reference | Vizovice: 78.7% (-10.3 pp); Kladna-Zilin: 82.5% (-6.5 pp) |
| 2014-12 | 89.53% | 354 (4.0%) | 5.92 h | 98.0 for 7.75 h | 0 | no reference | Vizovice: 78.9% (-10.6 pp); Kladna-Zilin: 82.4% (-7.2 pp) |
| 2015-01 | 90.88% | 190 (2.1%) | 3.08 h | 98.0 for 9.50 h | 0 | no reference | Vizovice: 81.9% (-9.0 pp); Kladna-Zilin: 85.5% (-5.4 pp) |
| 2015-02 | 73.42% | 123 (1.5%) | 5.58 h | 90.0 for 6.92 h | 0 | no reference | Vizovice: 77.2% (+3.8 pp); Kladna-Zilin: 81.9% (+8.4 pp) |
| 2020-12 | 92.30% | 2,380 (26.7%) | 79.25 h | 100.0 for 64.83 h | 2 | -9.65 to -6.86 pp | Vizovice: 82.5% (-9.8 pp); Kladna-Zilin: 85.2% (-7.1 pp) |
| 2023-01 | 84.91% | 0 (0.0%) | 0.00 h | 93.0 for 8.58 h | 2 | 1.22 to 1.75 pp | Vizovice: 85.2% (+0.3 pp); Kladna-Zilin: 84.9% (-0.0 pp) |
| 2023-02 | 78.18% | 0 (0.0%) | 0.00 h | 92.0 for 4.08 h | 2 | 0.30 to 2.47 pp | Vizovice: 79.9% (+1.8 pp); Kladna-Zilin: 77.6% (-0.6 pp) |
| 2023-03 | 68.57% | 0 (0.0%) | 0.00 h | 94.0 for 3.33 h | 2 | 0.05 to 0.31 pp | Vizovice: 68.2% (-0.4 pp); Kladna-Zilin: 68.6% (+0.0 pp) |
| 2023-04 | 70.82% | 0 (0.0%) | 0.00 h | 93.0 for 6.92 h | 2 | 0.53 to 3.33 pp | Vizovice: 73.0% (+2.2 pp); Kladna-Zilin: 71.0% (+0.2 pp) |
| 2023-06 | 65.07% | 0 (0.0%) | 0.00 h | 94.0 for 3.42 h | 2 | 4.96 to 6.01 pp | Vizovice: 67.8% (+2.7 pp); Kladna-Zilin: 67.7% (+2.7 pp) |
| 2023-07 | 63.61% | 0 (0.0%) | 0.00 h | 93.0 for 2.17 h | 2 | 4.01 to 5.04 pp | Vizovice: 66.1% (+2.5 pp); Kladna-Zilin: 67.0% (+3.4 pp) |
| 2023-08 | 73.86% | 0 (0.0%) | 0.00 h | 95.0 for 7.00 h | 2 | 4.77 to 5.21 pp | Vizovice: 77.9% (+4.0 pp); Kladna-Zilin: 77.6% (+3.7 pp) |
| 2023-09 | 71.07% | 0 (0.0%) | 0.00 h | 92.0 for 2.92 h | 2 | 6.93 to 7.29 pp | Vizovice: 78.7% (+7.7 pp); Kladna-Zilin: 78.0% (+6.9 pp) |
| 2023-10 | 78.35% | 0 (0.0%) | 0.00 h | 95.0 for 7.92 h | 2 | 1.16 to 2.33 pp | Vizovice: 79.0% (+0.6 pp); Kladna-Zilin: 79.1% (+0.7 pp) |
| 2023-12 | 89.22% | 0 (0.0%) | 0.00 h | 98.0 for 15.25 h | 2 | -2.40 to -1.87 pp | Vizovice: 86.0% (-3.2 pp); Kladna-Zilin: 85.9% (-3.3 pp) |
| 2024-02 | 87.85% | 824 (9.9%) | 15.58 h | 99.0 for 15.58 h | 2 | -6.45 to -6.29 pp | Vizovice: 80.6% (-7.2 pp); Kladna-Zilin: 81.0% (-6.9 pp) |
| 2024-03 | 77.80% | 517 (5.8%) | 13.17 h | 99.0 for 13.17 h | 2 | -7.31 to -6.34 pp | Vizovice: 71.2% (-6.6 pp); Kladna-Zilin: 70.3% (-7.5 pp) |
| 2024-04 | 74.99% | 465 (5.4%) | 11.42 h | 99.0 for 11.42 h | 2 | -4.25 to -3.81 pp | Vizovice: 70.4% (-4.6 pp); Kladna-Zilin: 70.7% (-4.3 pp) |
| 2024-05 | 70.72% | 0 (0.0%) | 0.00 h | 97.0 for 5.08 h | 2 | -0.50 to 0.12 pp | Vizovice: 67.2% (-3.6 pp); Kladna-Zilin: 68.7% (-2.0 pp) |
| 2024-06 | 75.54% | 155 (1.8%) | 8.58 h | 99.0 for 8.58 h | 2 | -0.49 to 0.06 pp | Vizovice: 74.0% (-1.6 pp); Kladna-Zilin: 73.9% (-1.7 pp) |
| 2024-08 | 71.83% | 99 (1.1%) | 5.17 h | 91.0 for 5.25 h | 2 | 0.70 to 1.42 pp | Vizovice: 71.8% (-0.0 pp); Kladna-Zilin: 72.0% (+0.2 pp) |
| 2024-10 | 83.33% | 491 (5.5%) | 10.75 h | 99.0 for 10.75 h | 2 | -5.10 to -1.57 pp | Vizovice: 78.3% (-5.1 pp); Kladna-Zilin: 80.5% (-2.8 pp) |
| 2024-12 | 91.22% | 833 (9.3%) | 18.75 h | 99.0 for 18.75 h | 2 | -6.93 to -5.18 pp | Vizovice: 82.8% (-8.4 pp); Kladna-Zilin: 84.4% (-6.8 pp) |
| 2025-06 | 71.74% | 219 (2.5%) | 7.75 h | 99.0 for 7.75 h | 2 | -3.09 to -2.66 pp | Vizovice: 65.1% (-6.6 pp); Kladna-Zilin: 66.2% (-5.5 pp) |
| 2025-07 | 77.16% | 608 (6.8%) | 11.50 h | 99.0 for 11.50 h | 2 | -2.57 to -2.34 pp | Vizovice: 72.9% (-4.3 pp); Kladna-Zilin: 73.8% (-3.3 pp) |
| 2025-09 | 83.91% | 985 (11.4%) | 11.58 h | 99.0 for 11.58 h | 2 | -3.04 to -1.50 pp | Vizovice: 80.7% (-3.2 pp); Kladna-Zilin: 82.1% (-1.8 pp) |
| 2025-10 | 86.58% | 976 (11.0%) | 12.00 h | 99.0 for 12.00 h | 2 | -4.90 to -3.87 pp | Vizovice: 80.5% (-6.1 pp); Kladna-Zilin: 81.5% (-5.0 pp) |
| 2026-01 | 87.22% | 1,269 (14.2%) | 15.67 h | 99.0 for 15.67 h | 2 | -8.40 to -6.00 pp | no quality-0 data |
| 2026-02 | 91.77% | 1,968 (24.5%) | 22.25 h | 99.0 for 22.25 h | 2 | -7.33 to -6.38 pp | no quality-0 data |

- 2026-01: 13 local ≥99% runs of at least 10 minutes; longest was 15.67 hours. That episode's mean RH at matched CHMI stations ranged from 95.5% to 97.5%.

- 2026-02: 19 local ≥99% runs of at least 10 minutes; longest was 22.25 hours. That episode's mean RH at matched CHMI stations ranged from 96.5% to 96.7%.

Across periods, results support only regional consistency and plateau context. Daily comparisons are not matched external validation and do not set the candidate evidence external-validation flag. They do not establish physical sensor accuracy, distinguish sensor saturation from quantization or condensation, or authorize a correction. Sensor model, siting, configuration, and epoch-specific driver semantics remain unresolved. The January pilot remains sensor-review-required; no month is cleared solely by regional comparison.

Subdaily reference validation JSON SHA-256: `32644f309c2a2382585ed4d06e9e17e7b23dc95a74e10269233f814a0e1d7599`. Daily context JSON SHA-256: `0dd251270c58d63355ddbca7099efc9a9e525913be4843fa6a5c86a7d620106f`. Snapshot SHA-256: `1e34859d05bb0ec20d3810c4fbb376d231a6ee0bfca0c4c636dcfb2d1114e4ba`.
