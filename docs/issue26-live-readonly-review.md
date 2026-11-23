# Issue #26: read-only review on existing MariaDB

## Scope

Owner decision remains in force: do NOT provision another persistent MariaDB
instance and do NOT check or require backups or Proxmox Backup Server as part of
this work. This choice does not prove disaster-recovery capability.

The only allowed live activity in this phase is SELECT-based inspection of
loucka_reconstruction. No archive corrections, no production cutover, no DDL.

## Live inventory, 2026-11-23

- DB server hostname: lo-infra-db-mariadb01, server_id 1, MariaDB 11.8.6.
- Working archive and legacy reconstruction_changes are InnoDB.
- 113154 change events: 95312 applied, 17842 reverted.
- July 2021 rain: 42.567 mm after rounding. The separate original rain
  reference table contains 8921 rows.
- The two new issue26 audit tables have NOT been created in live MariaDB.
- These counts do not by themselves establish complete Phase A provenance.

## New safe review workflow

The Python module src/meteo_audit/issue26_readonly_export.py and its
command-line wrapper scripts/issue26_db_readonly_review.py inspect only
the precise entries in an operator-reviewed CandidateBatch manifest.

- A dedicated connection starts REPEATABLE READ WITH CONSISTENT SNAPSHOT,
  READ ONLY and always ends the transaction with ROLLBACK.
- The operator must name the expected SQL hostname and server_id.
- Database identity and InnoDB table presence are checked. The tool works
  with both issue26 audit tables absent, but refuses partial installation.
- Before-image values are fetched from the live archive, compared with
  manifest old values (NULL and zero are distinct), and checked against
  the legacy change history and optional issue26 change history.
- The July 2021 rain invariant remains enforced.
- No automatic approval, no source-verification claim and no APPLY switch.

MariaDB transaction syntax reference:
https://mariadb.com/docs/server/reference/sql-statements/transactions/start-transaction

## Operator command, read-only only

First prepare a CandidateBatch JSON with exact schema
loucka-field-correction-review-v1, target
loucka_reconstruction.archive, and explicit per-field evidence.

Use a private MariaDB client CNF (operator-owned, mode 0600) with a
SELECT-only account limited to the working reconstruction schema.

    PYTHONPATH=src python3 scripts/issue26_db_readonly_review.py \
      --manifest /private/issue26-batch.json \
      --client-file /root/meteo-readonly.cnf \
      --expect-host lo-infra-db-mariadb01 \
      --expect-server-id 1 \
      --output-dir /var/lib/meteo-audit/reviews/batch-unique-YYYYMMDD

The output path must be absolute and must NOT already exist.
Successful output is a mode-0700 directory containing three mode-0600
files: before-image.json, review-evidence.json and review-complete.json.
All three are evidence for human review only; they cannot authorize a
database write. Review raw sensor provenance and unit epochs separately.

After that review (not automatically), an operator may generate the
precise challenge through the existing offline script:

    PYTHONPATH=src python3 scripts/issue26_approval_review.py challenge \
      --manifest /private/issue26-batch.json \
      --before-image /var/lib/meteo-audit/reviews/batch-unique-YYYYMMDD/before-image.json

The full batch/manifest and the before-image hashes must be explicitly
approved by the owner before any future SQL mutation. A file alone is
not evidence of human identity, source validity, or SQL authorization.

## Database preparation (not yet authorized)

The existing DB does not contain issue26_batch_events or
issue26_field_events. The two-table DDL proposal from PR #75 has
not been executed on the user's MariaDB.

Before a real writer can run, the table definitions and a least-privilege
SQL role restricted to loucka_reconstruction must be separately reviewed.
The writer should be allowed SELECT/INSERT for append-only audit tables,
not UPDATE or DELETE; archive UPDATE must be narrowly scoped. A successful
GitHub PR or CI is not an instruction to deploy DDL or apply any batch.

## Remaining acceptance work

- Demonstrate a real read-only export of a specifically vetted candidate
  with independent raw evidence, unit epoch and field identity.
- Explicitly review the audit DDL and restricted SQL credentials and only
  then consider deployment on the existing server.
- Build an operator-controlled entrypoint for signed APPLY and ROLLBACK,
  with per-batch separate consent and fresh transactional CAS.
- Verify remaining Phase A and historical supersession invariants.
- Do not update archive_day_*; after the final archived data is approved,
  WeeWX performs the daily-statistics rebuild.
