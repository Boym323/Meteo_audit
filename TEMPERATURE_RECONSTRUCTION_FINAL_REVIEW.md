# U3 — Outdoor temperature completion review

Updated UTC: 2026-11-14T18:10:03.070795+00:00. Annual figures use UTC epoch bounds.

| UTC year | Rows | NULL outTemp | Applied RESTORED outTemp operations | Applied ESTIMATED outTemp operations |
|---:|---:|---:|---:|---:|
| 2013 | 95488 | 5658 | 4 | 0 |
| 2020 | 103047 | 4727 | 31 | 21 |
| 2022 | 104207 | 2828 | 65 | 0 |
| 2025 | 102946 | 1312 | 0 | 0 |

## Disposition

All previously prepared exact source-first temperature groups in the approved application package have already been applied (the 322-operation range is independently confirmed applied in the live audit ledger). The 21-value v2.1 short-gap model estimate group is also applied and remains classified ESTIMATED; it is not a recovered local observation. Earlier regional transfer / longer-gap candidate work is reused from the audit package; no failed model is rerun and no long outage is filled by analogy.

The remaining outTemp NULL counts in these priority years are not all recoverable: existing source reviews found unresolved lineage, suspected stuck/zero episodes, occupied/off-grid projections, source conflicts, or no source row. Specific no-promotion decisions are in `SOURCE_ONLY_RESTORATION_ELIGIBILITY.md`, `reports/2026-11-14-2015-source-only-field-eligibility.md`, `reports/2026-11-14-2016-2017-source-only-field-eligibility.md`, `reports/2026-11-14-source-only-2012-nearest-slot-review.md`, and source-only 2019–2020 gap reports. No new temperature candidate passed all U8 requirements in this review.

Annual readiness remains `REVIEW_REQUIRED` for climatological means, extremes, and trends. Raw graphs can show real gaps with restored/estimated flags; the 21 estimates must be visibly distinct. U3 status: `COMPLETED_WITH_LIMITATIONS`; new operations in this goal: 0.
