# Loučka migration recovery

## Aktuální diff — 2026-11-24

- `FINAL_MIGRATION_OPERATIONS.jsonl.gz`: kompletní operation-level diff z jedné `REPEATABLE READ`, `WITH CONSISTENT SNAPSHOT`, `READ ONLY` transakce při `dateTime <= 1795541700` (2026-11-24 17:35 UTC).
- `FINAL_MIGRATION_DIFF_SUMMARY.json`: počty, transakční identita, zdrojové/auditní stavy a očekávané baseline hodnoty.
- `../FINAL_MIGRATION_MANIFEST.json`: SHA-256, test policy, jednotky a neschválení všech operací pro produkci.
- `scripts/capture_final_migration_diff.py`: read-only builder navazující na tento migrační balíček; použije soukromý MariaDB option file.
- `scripts/validate_final_migration_diff.py`: nezávislá validace hashů, počtů, klíčů, payloadů, jednotek a všech 60 nových teplotních NULL_CLEAR operací.

Poslední běh obsahuje 92 724 operací: 10 399 INSERT, 12 671 NULL_FILL, 68 759 VALUE_REPLACE a 895 NULL_CLEAR (z toho přesně 60 nových teplotních clearů a 835 starších rain/humidity invalidací). Všech 82 325 field operations má auditní event; 1 497 latest-event/current-state rozdílů je explicitně zachováno k review. Žádná operace není schválena pro produkci.

Spuštění z rootu repozitáře:

~~~bash
.venv/bin/python final_migration_package/scripts/capture_final_migration_diff.py
.venv/bin/python final_migration_package/scripts/validate_final_migration_diff.py
~~~

## Historický diff

`MIGRATION_DIFF.csv`, `MIGRATION_DIFF_VALIDATION.json` a JSONL zdrojové stránky jsou neměnným snapshotem z 2026-11-17 s watermarkem `1794907800`. Nejsou aktuálním diffem.

## Testovací instance a produkční hranice

`loucka_migration_test` v `MIGRATION_TEST_MANIFEST_SAME_SERVER_v2.json` je pouze další schema na MariaDB serveru se `server_id=1`, nikoli oddělená instance. Současný klient LXC nemá Proxmox provisioning přístup. Fail-closed preflight a přesný postup jsou v `ISOLATED_TEST_PROVISIONING_2026-11-24.md`; stav obnovy/testu je v `../FINAL_MIGRATION_TEST_REPORT.md`.

Produkce nebyla změněna. Auditní `applied` událost není produkční schválení. Tlakové odhady zůstávají v samostatné tabulce a nesmí vstoupit do `archive` ani oficiálních statistik.
