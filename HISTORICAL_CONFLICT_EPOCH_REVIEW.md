# Historical conflict epoch and directional archive review

Snapshot `1e34859d05bb0ec20d3810c4fbb376d231a6ee0bfca0c4c636dcfb2d1114e4ba`; source value-concordance SHA-256 `1e34859d05bb0ec20d3810c4fbb376d231a6ee0bfca0c4c636dcfb2d1114e4ba`.

The canonical value-level totals are preserved: 4,832,556 source conflicts, including 4,373,735 materially different legacy values and 458,821 rounding-only values. The value-level transformation-supported count remains 0; unmatched target/source cases remain 3.

## Pairwise direction and distribution

For each local calendar year, field, and named non-primary archive, the companion JSON compares source values only when the target exactly equals `pocasi-loucka.eu` and the named archive differs. Delta is normalized comparison archive minus primary archive. These are pairwise diagnostic counts, can count a timestamp once per source archive, and are not additions to the canonical conflict count. Exact direction, extrema and moments use all eligible pairs; p10/median/p90 use the deterministic SHA256 bottom-512 sample per group.

| Field | Pairwise differing values | Legacy above primary | Legacy below primary | Exact 3.6-factor screen |
|---|---:|---:|---:|---:|
| `altimeter` | 3,463,062 | 1,303,390 | 2,159,672 | 0 |
| `barometer` | 227,216 | 57,817 | 169,399 | 0 |
| `outHumidity` | 127,986 | 38,034 | 89,952 | 0 |
| `outTemp` | 382,764 | 310,867 | 71,897 | 6 |
| `pressure` | 3,457,601 | 1,345,205 | 2,112,396 | 0 |
| `windDir` | 63,629 | 31,766 | 31,863 | 0 |
| `windGust` | 1,124,286 | 786,933 | 337,353 | 628,204 |
| `windSpeed` | 1,138,310 | 819,815 | 318,495 | 622,064 |

The exact 3.6 screen is `legacy = 3.6 × primary` within relative/absolute 1e-9 after the existing unit normalization. It identifies a candidate scaling signature, not proven cause or a correction rule. In wind, the signature also appears in 2009–2013. This is consistent with the existing wind review finding that early `usUnits=16/17` copies can contain identical raw speed/gust values: applying the stored unit codes yields a 3.6 normalized difference, while the raw archive pair itself does not identify which copy is already converted. The new pairwise result therefore extends the named archive comparison, not the proven transformation window. These cohorts remain open without dated configuration/driver evidence. Archive aliases share lineage, so apparent replication across copies is not independent confirmation.

The source availability cohorts are not physical sensor epochs. This review adds no hardware replacement or driver change dates because local dated evidence has not established them. The canonical provenance categories, exact comparisons, historical values, and publication decisions are unchanged; no target values or archives were modified.

## Reproduction

Run `python3 scripts/build_historical_conflict_epoch_review.py`. It reads `data/historical_value_concordance.sqlite` via SQLite `mode=ro`, streams timestamp records, and writes the JSON evidence plus this report.
