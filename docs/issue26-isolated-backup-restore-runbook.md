> **ARCHIVNÍ / NEPOVINNÁ ALTERNATIVA (rozhodnutí vlastníka 23. 11. 2026)**
>
> Nová MariaDB instance se **nebude zřizovat**. Tento nástroj z PR #72
> zůstává jako již implementovaný a synteticky otestovaný příklad obnovy,
> **není povinnou podmínkou issue #26 a nemá se spouštět**.
> Schválenou provozní cestou je stávající Proxmox Backup Server:
> viz [PBS backup/recovery policy](issue26-pbs-backup-recovery-policy.md).
> Bez reálného obnovení není dovoleno tvrdit DATABASE_RESTORE_VERIFIED.

# Issue #26 — izolovaný backup/restore drill

Tento postup **neopravuje meteorologické hodnoty**. Doplňuje dosavadní
approval/rollback simulátor a syntetické integrační testy MariaDB o
ověřitelnou obnovu celé pracovní databáze na samostatné instanci.

## Bezpečnostní předpoklady

- Zdroj: pouze databáze loucka_reconstruction, všechny základní tabulky InnoDB.
  Zdrojový uživatel pouze pro čtení a konzistentní mariadb-dump.
- Cíl: **nová samostatná MariaDB instance** bez uživatelské databáze;
  odlišné hostname a server_id od zdroje. Druhá databáze v tomtéž
  MariaDB serveru ani jiná IP/DNS stejného serveru nestačí.
- Účet cíle je určen pouze pro obnovu a musí mít práva pro kompletní
  import databáze včetně schema, triggerů a views.
- Synchronizaci pracovní databáze během zálohování dočasně stabilizovat
  provozním postupem; skript ji sám nezastavuje.
- Přístupové CNF jsou dva oddělené absolutní privátní soubory s právy 0600,
  vlastněné běžícím uživatelem. Necommitovat přístupové údaje.
- Netýká se denních extrémů: archive_day_* později přepočítá WeeWX po
  dokončení rekonstrukce, nikdy v tomto bezpečnostním testu.

## Postup

1. Read-only gate, bez jakýchkoliv zápisů do DB:

    python3 scripts/isolated_restore_drill.py \
      --source-cnf /root/restore-source.cnf \
      --destination-cnf /root/restore-target.cnf

Očekáváme DRY_RUN_NO_WRITES. Zkontroluje identity skutečných SQL serverů,
prázdný cíl, dostupnost zdrojových tabulek, součty a základní invarianty.

2. Fyzická obnova **pouze** do čisté izolované instance:

    python3 scripts/isolated_restore_drill.py \
      --source-cnf /root/restore-source.cnf \
      --destination-cnf /root/restore-target.cnf \
      --receipt-dir /var/lib/meteo-audit/isolated-restore-YYYYMMDD \
      --execute \
      --confirm RESTORE-ONLY-TO-SEPARATE-EMPTY-MARIADB

Adresář nesmí předem existovat. Skript ho vytvoří s právy 0700.
Pořídí per-table COUNT a CHECKSUM TABLE EXTENDED, konzistentní dump,
zopakovaným výpočtem ověří neměnnost zdroje, znovu zkontroluje izolaci cíle,
teprve potom provede import a porovná všechny základní tabulky.

Invarianta července 2021 musí zůstat 42,567 mm (zaokrouhlení) a musí být
přítomných 60 aplikovaných null-corrections ze dvou QC dávek 23.11.2026.
Výsledkem je privátní restore-receipt.json a archivní SQL dump. Oba obsahují
citlivá technická data, **nevkládat je do veřejného GitHubu**.

Pokud import nebo kontrola selže, izolovanou testovací instanci odstranit,
nevykonávat žádné automatické opravy a opakovat pouze na nové čisté instanci.
PASS_ISOLATED_RESTORE_DRILL_ONLY neautorizuje cutover ani schválení oprav.

## Co zbývá před uzavřením #26

- [x] Python manifesty, hashovaný preflight, simulované NULL-safe CAS a rollback (PR #60).
- [x] Skutečné syntetické MariaDB transakční testy v Loucka_weather PR #170.
- [x] Operator-ready fail-closed obnovovací skript, unit testy a CI test na dvou
      samostatných **syntetických** MariaDB instancích.
- [ ] Ověřit **skutečný úplný restore** aktuálních 1,7M+ archivních záznamů
      na samostatné MariaDB a uložit autentický receipt.
- [ ] Real-world DB batch apply/rollback runner s nezávislým schválením
      konkrétního batch ID + SHA256, before-image, journalem a rollbackem.
- [ ] Ověření celé Fáze A a aktuálních historických override případů
      na obnovené kopii; žádné automatické uvolnění karanténních operací.

Proto issue #26 zůstává otevřené, dokud operátor tyto důkazy nepředloží.
