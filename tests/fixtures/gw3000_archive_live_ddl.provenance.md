# Provenance metadata: gw3000_archive_live_ddl.sql

- Source: actual `SHOW CREATE TABLE archive` result from an independent read-only Weather MCP `execute_sql` call.
- Query database: `information_schema`; qualified object: `loucka_reconstruction.archive`.
- Independently repeated against `pocasi-loucka.eu.archive`; the full `Create Table` strings were exactly identical.
- Captured: 2026-11-15 UTC.
- This is live production DDL evidence, not a synthetic schema fixture. It is immutable evidence for this release candidate; regenerate and review explicitly if live DDL changes.
