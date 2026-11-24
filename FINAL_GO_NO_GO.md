# Finální rozhodnutí

## GO

- Read-only SQL audity a kontrola stavu DB.
- Konzistentní komprimovaná záloha `loucka_reconstruction` do root-only úložiště mimo webroot.
- Review dosavadních auditních podkladů a tlakové rekonstrukce jako oddělených neschválených odhadů.

## NO-GO

- Obnova zálohy: schválená izolovaná instance není dostupná/provisionovaná z tohoto hostu.
- Testovací migrace, přepočet WeeWX a celý rollback: závisí na obnoveném klonu a jeho WeeWX konfiguraci.
- Produkční zápis: vyžaduje samostatné schválení, jak požaduje zadání.
- Tlakové odhady do `archive.pressure` nebo oficiálních statistik: zakázáno rozhodnutím pro tlak.

Současný `final_migration_package/MIGRATION_DIFF.csv` je snapshot z 2026-11-17 a není aktuální. Manifest pro tento běh záměrně nevydává jeho hash jako nový diff. Před testem je nutné vytvořit nový konzistentní operation-level export nad oběma archivy při stejném řezu `1795541700`, doplnit before/after hodnoty a poslední auditní událost pro každou operaci, zdroj a stav schválení. Produkce zůstala nezměněna.
