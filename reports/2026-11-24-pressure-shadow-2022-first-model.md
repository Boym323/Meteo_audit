# Pressure shadow series: first 2022 reconstruction model

2026-11-24. Read-only SQL analysis; no meteorological writes, no approval manifest changes. Model is deliberately separate from archive and its output is ESTIMATED / UNAPPROVED.

## Coverage

The current target has 198175 NULL pressure slots, 179436 with barometer, 167630 with both barometer and outTemp, 11806 with barometer but without outTemp, 18739 without barometer. No NULL pressure slot has altimeter. In 2022 there are 46305 NULL and 42484 with barometer plus outTemp.

## Actual local holdout

Fit on 92641 valid rows from 2020 ONLY. Invert the local barometer with dry-air transport to 425 m, using outTemp as column-temperature proxy; fit OLS to pressure minus physical estimate on 2020 only. Select temperature correction on 2021 and freeze it before assessing 2022. Formula:

p_est = barometer * exp(-9.80665 * 425 / (287.05 * (outTemp + 273.15))) + 0.4167213203943744 - 0.01941207276210084 * (outTemp - 9.429312079930027).

| Period | n | Physical MAE | Constant MAE | Temperature correction MAE |
|---|---:|---:|---:|---:|
| 2021 validation | 100606 | 0.5714 | 0.4536 | 0.4449 |
| 2022 before Aug 20 | 20321 | 0.7066 | 0.6110 | 0.5637 |

All error units hPa, compared to existing local pressure, not independent truth. A deterministic inverse of a derived field may show high agreement without being calibrated.

Restrict to 2020 training domain: outTemp [-7.25,31.3] °C, barometer [981.88875,1043.1] hPa. Within this domain:
- 2021 n=98619, MAE 0.4472, p95 abs 1.068.
- 2022 Jan–Jul n=14502, MAE 0.5393, p95 abs 1.235.
- 41437 missing rows with valid in-domain inputs in Jan–Jul 2022 (8247/7819/6880/1442/8286/7754/1009). They are potential estimates, NOT approved candidates. July has fewer than 100 missing exact-hour slots even before quality/domain filtering, so the predeclared gate may reject it.

## Next independent test

The frozen model is in models/pressure-shadow-2022-v1.json. The new runner compares predictions at actual missing-target exact UTC hours to **both** CHMI station P references, with identical common hours and physical height transport. It checks the original reference cache hashes through the PR #95 loader. Gate fixed before seeing results: at least 100 common hours/month, at least 80% coverage of eligible missing exact hours, MAE <=2 hPa, absolute median bias <=1.5 hPa and P95 absolute <=4 hPa at both stations. This is a preliminary regional screening gate, not proof of five-minute measurement accuracy.

For passing months only, write separate local CSV with original NULL, prediction, provenance, frozen model hash, reference hash, local and regional empirical p95 diagnostics (not individual uncertainty bounds), status ESTIMATED and UNAPPROVED. Never send this CSV to APPLY. Report all failed months, preserve all originals and keep approved count at zero. Not tested across Aug 2022 sensor change or 2016–2018 bias.

On existing LXC, use clean worktree containing this PR, with the original reference cache:
```sh
/opt/meteo-audit-issue26/.venv/bin/python scripts/build_pressure_shadow_2022.py \
 --cnf /root/meteo-loucka-ro.cnf \
 --chmi-cache /opt/meteo-pressure-chmi/data/chmi-pressure-2009-2026 \
 --out-dir /tmp/loucka-pressure-shadow-2022-v1
```
Choose a new output directory if it already exists. External test NOT_RUN in this chat (reference files are on LXC). Synthetic unit tests added, no claim of their execution until CI or local results are available.

No SQL writes/DDL, new grants/users, production or WeeWX changes. Q1 2018 untouched. Independent regional estimates should remain separate, even if gate passes. Further validation: gap-length and weather-regime stratification, comparison with known local points and independent reanalysis, five-minute temporal support, explicit approval.
