# Current GW3000 E4 validation report

## Frozen archive evidence

Source archive payload window: 2026-10-29T15:15:00Z to 2026-11-14T19:00:00Z (4651 rows). Payload SHA-256: `1b4e953fa85f16f25582db9b177d9dab5d0d9fc30d4e364057760b9cfc7a9aad`.

Archive `rain`: non-null 4651, nonzero 177, stored sum 2.750000 (not interpreted as a period total). `rainRate`: non-null 4651, nonzero 259, range 0–0.5600000000000137. Cadence metadata: [5] minutes; archive `usUnits`: [16].

The frozen export has 102 decreases or positive-to-zero sequences in `rain`. These are not classified as resets: without contemporaneous raw inputs and the deployed driver contract, they could reflect interval values, event behavior, reset, or mapping.

## Current device read-only evidence

A sanitized current HTTP GET capture at 2026-11-16T01:07:48.909Z–2026-11-16T01:07:49.466Z reports `Version: GW3000A_V1.2.5`; rain unit setting code `0` and live strings in millimetres. Gateway rain priority is `1` (the response labels value 1 `Traditional rain gauge`); `rainGain` is `1.00`. Sensor inventory includes wh85 / Wind & Rain (active flag 1), wh90 / Temp & Humidity & Solar & Wind & Rain (active flag 1), wh69 / Temp & Humidity & Solar & Wind & Rain (active flag 1), wh40 / Rain (active flag 1), wn20 / Rain Mini (active flag 1), wn64 / Temp & Humidity & Wind & Rainstatus (active flag 1). Raw rain-field excerpt: event `0x0D`=0.0 mm, rate `0x0E`=0.0 mm/Hr, day `0x10`=0.0 mm, week `0x11`=0.0 mm, month `0x12`=25.2 mm, year `0x13`=519.8 mm, total `0x14`=519.8 mm. The official protocol names these IDs Rain Event, Rain Rate, Rain Day/Week/Month/Year/Totals; this documents gateway fields but not their WeeWX archive mapping. Capture file SHA-256: `d3a74538b9d86f2a1157ae030fccae6b27954f1cffbbc51de444c865a76d5412`.

The capture retains hashes for each unmodified HTTP response and exact rain-field excerpts, while omitting network and sensor radio IDs. It is a current dry sample, not an immutable historical raw-device export. The Ecowitt protocol maps `0x0D` to event rain and `0x0E` to rate and names day/week/month/year/total fields [`official HTTP API protocol`](https://oss.ecowitt.net/uploads/20260109/HTTP%20API%20interface%20Protocol%20%28Generic%29-%28V1.0.5-2025-10-08%29%20.pdf). The manufacturer’s Web UI manual explains the traditional/piezo priority selection and WH40’s role as a reference for piezo rain calibration [`official Web UI manual`](https://oss.ecowitt.net/uploads/20250408/WS%20View%20Plus%20%26%20Web%20UI%20Manual%20%28Generic%29.pdf).

## Decision and open evidence

E4 remains blocked for the current GW3000 epoch. The actual gateway firmware, unit setting, selected rain priority, gain, current dry event/rate, and active rain-capable sensor catalog are now recorded. Sensor resolution/deployment, exact sensor-to-archive mapping, deployed WeeWX driver/version/configuration, historical raw wet/reset payloads, rate derivation window, reset/rollover meaning, archive timestamp mapping, and independent gauge evidence remain unresolved. No rainfall total or rate is cleared; no historical values or gateway settings were changed.

Detailed machine-readable evidence: `CURRENT_GW3000_E4_VALIDATION.json`; immutable local capture: `data/gw3000-current-readonly/capture-20261116T010749Z.json`.
