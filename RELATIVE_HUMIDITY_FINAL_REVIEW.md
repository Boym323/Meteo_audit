# U4 — Relative humidity completion review

Updated UTC: 2026-11-14T18:10:03.070795+00:00. The table reflects current live counts by UTC year.

| UTC year | Rows | NULL outHumidity | Applied RESTORED RH ops in 322 |
|---:|---:|---:|---:|
| 2016 | 87902 | 12810 | 0 |
| 2017 | 76831 | 24334 | 0 |
| 2018 | 97704 | 44306 | 1 |
| 2019 | 104751 | 15099 | 0 |
| 2022 | 104207 | 41792 | 0 |

## Decisions and protected period

Applied RH recoveries in the 322-event phase are limited to evidence-backed pilot fields in 2013, 2014 and the 2018-12-31 Q4 timestamp; they do not resolve the broad 2016–2019 or 2022 NULL cohorts. Regional models are not promoted to local measured values. Existing source-first and LuhaMet/CHMI validation reviews show seasonal/epoch limitations and unresolved copy conflicts; no new statistical RH estimate meets the stricter U8 permission (which excludes estimates). New estimates require owner approval and the exact pre-existing model validation / payload evidence.

Q1 2018 remains protected. Live audit history shows 5,973 RH, 10,118 temperature, and 303 rainRate applied field events in Q1 2018, with the latest event IDs respectively through 135125, 133602 and 20115. Those events predate the 322-operation phase; the new phase wrote none into Q1. This is a reconciliation requirement, not permission to edit the period.

Do not convert long RH NULL runs to synthetic five-minute observations merely to improve completeness. When independent local training coverage is insufficient, preserve NULL; period-level statistics stay `REVIEW_REQUIRED`. U4 status: `COMPLETED_WITH_LIMITATIONS`; new RH estimates/operations in this goal: 0.
