# Historical field provenance categories

This policy applies to one `(dateTime, variable)` pair. Timestamp presence by itself is never evidence that every field shares the same origin. Exact `Decimal` equality is required after only the unit conversion stated in the source concordance metadata.

## Categories and minimum evidence

| Category | Required evidence | Does not imply |
|---|---|---|
| `ORIGINAL_VERIFIED` | Contemporaneous primary sensor or logger record, identifiable instrument/driver/unit epoch, and no invalidation or subsequent replacement; preserved link to the exact field value | No value currently meets this standard merely because it is in the target or agrees with copies |
| `SOURCE_MATCHED` | At least one compatible archive has the exact timestamp and exact field value after approved unit normalization | Original sensor identity, independence, or correctness; archive copies may share lineage |
| `RECOVERED_SOURCE` | Complete verified INSERT-only sync batch; complete audit row and matching hashes; approved source/target identities; matching units and exact field value in current target and immutable `row_json` | Independent historic validation outside the sync source |
| `RESTORED` | Applied reconstruction event whose current value exactly equals its recorded `new_value`, with restoration reason and operation evidence | That the source was independent or the original sensor was valid |
| `CORRECTED` | Applied correction event whose current value exactly equals its recorded `new_value`, with method and evidence preserved | Acceptance of unrelated fields at that timestamp |
| `ESTIMATED` | Applied estimate-registry entry whose target value exactly equals the current value | A measured observation |
| `CONFLICTING_SOURCE` | Compatible observations at the same timestamp disagree after explicit normalization, including disagreement between target and otherwise concordant copies | Which observation is correct |
| `INVALIDATED` | Explicit row/field invalidation record tied to a documented sensor, driver, or ingestion failure and affected time window | Invalidation inferred from a NULL or a lone copy disagreement |
| `UNRESOLVED` | Target field is NULL while one or more source copies contain a value, or a required evidence chain is incomplete | Permission to restore the value |
| `UNCLASSIFIED` | No sufficient, consistent field-level evidence | Original measurement |

## Precedence

For a non-NULL current target value, exact applied estimate evidence is checked first, then the latest exact applied reconstruction event, then validated immutable sync evidence, then archive-copy concordance, then source conflict. If none applies, retain `UNCLASSIFIED`. A NULL target with a source candidate is `UNRESOLVED`; it is not `SOURCE_MATCHED` because there is no current value to compare. A later audit or change record supersedes an older event only when the current value exactly matches its postimage. No broad tolerance is used.

## Known evidence limits

The live source catalog documents shared historical bases and unknown merge paths among several archive copies. Therefore source matches are recorded as comparison evidence but do not establish independence. No complete row-level historical invalidation registry was found in the inspected evidence; the comparison output records this limitation and does not label values `INVALIDATED` based on inference. Original lineage remains unverified unless new primary-source evidence is added.
