# Finální test migrace — 2026-11-24

## Výsledek

**Testovací migrace nebyla spuštěna.** `final_migration_package/MIGRATION_TEST_MANIFEST_SAME_SERVER_v2.json` popisuje jiné databázové schéma (`loucka_migration_test`) na stejném serveru se `server_id=1`; není to izolovaná MariaDB instance. Tento host je sám LXC a nemá Proxmox `pct`/`pvesh`, `/etc/pve` ani `/dev/pve`; nelze z něj vytvořit ověřenou instanci.

Vytvořena je konzistentní záloha celé `loucka_reconstruction`; viz `FINAL_BACKUP_RECEIPT.json`. Záloha má SHA-256 `2ca58ceac5729d1411f8515509aa980b8a783e2d9d34fdd57b6b86cb5277c806`, 26 tabulek a gzip integrity test prošel. Skutečná obnova, porovnání obnovených řádků/schématu/obsahu a rollback celé migrace proto zůstávají neprovedené.

Aktuální operation-level diff je hotový: 92 724 operací z konzistentní read-only transakce. Nezávislý validator potvrdil všech 60 nových teplotních `NULL_CLEAR`; 1 497 starších audit/current-state neshod zůstává k review. Detail: `final_migration_package/FINAL_MIGRATION_OPERATIONS.jsonl.gz`; souhrn: `final_migration_package/FINAL_MIGRATION_DIFF_SUMMARY.json`.

## WeeWX denní statistiky

Neproveden přepočet ani kontrola denních tabulek. Chybí schválený obnovený klon a runtime/config WeeWX, který předchozí inventura uvádí jako nedostupný. Produkční denní statistiky nebyly změněny.

## Povinný test před případným produkčním rozhodnutím

Na schváleném izolovaném klonu musí být nejprve ověřena úplná shoda obnovy se zálohou. Pak aplikovat výslovně vybraný operation-level manifest v jedné koordinované migrační dávce, přepočítat pouze dotčené dny WeeWX, ověřit všechny dotčené řádky i denní tabulky. Rollback test musí v jediné transakci/řízené obnově vrátit celou dávku do předmigračního stavu a následně ověřit nulový obsahový rozdíl proti uloženému preimage. Samostatně ověřit opakované spuštění a ochrany Q1 2018, rok 2021, rain/rainRate a všech odhadů.

Tlak případně přenášet pouze jako samostatnou tabulku `pressure_reconstruction`, v odděleném transfer balíčku s hashem dumpu a počtů; přijímací validace nesmí vkládat řádky do `archive`, `archive_day_*` ani do statistik.
