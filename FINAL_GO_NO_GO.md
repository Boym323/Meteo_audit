# Finální rozhodnutí

## GO

- Read-only SQL audity a kontrola stavu DB.
- Konzistentní komprimovaná záloha `loucka_reconstruction` do root-only úložiště mimo webroot.
- Review dosavadních auditních podkladů a tlakové rekonstrukce jako oddělených neschválených odhadů.

## NO-GO

- Obnova zálohy: skutečně izolovaná instance není dostupná/provisionovaná z tohoto hostu. `loucka_migration_test` je jen schema na serveru se `server_id=1`.
- Testovací migrace, přepočet WeeWX a celý rollback: závisí na obnoveném klonu a jeho WeeWX konfiguraci.
- Produkční zápis: vyžaduje samostatné schválení, jak požaduje zadání.
- Tlakové odhady do `archive.pressure` nebo oficiálních statistik: zakázáno rozhodnutím pro tlak.

Aktuální operation-level diff byl vytvořen při řezu `1795541700` (2026-11-24 17:35 UTC) v konzistentní read-only transakci. `final_migration_package/MIGRATION_DIFF.csv` z 2026-11-17 zůstává archivním artefaktem. Aktuální diff je `final_migration_package/FINAL_MIGRATION_OPERATIONS.jsonl.gz`; hash a validace jsou v `FINAL_MIGRATION_MANIFEST.json`. Produkce zůstala nezměněna.
