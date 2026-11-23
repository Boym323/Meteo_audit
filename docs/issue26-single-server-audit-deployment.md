# Issue #26 — nasazení dvou auditních tabulek a SQL identity na současné MariaDB

## Závazné rozhodnutí

Použijeme **pouze** existující `lo-infra-db-mariadb01`, server_id=1,
MariaDB 11.8.6, pracovní databázi `loucka_reconstruction`.
Žádná nová MariaDB, žádné kontrolování záloh/PBS, žádné přepnutí do
produkčního `pocasi-loucka.eu`. Denní agregace `archive_day_*`
se neřeší; později je přepočítá WeeWX.

## Co lze provést autonomně již nyní

1. Live read-only ověřením potvrdit host/database, InnoDB, počet
   sloupců (archiv=80, legacy historie=13) a srážky červenec 2021
   zaokrouhleně 42,567 mm.
2. Ve workflow GitHub Actions na dočasné syntetické MariaDB
   skutečně vytvořit auditní tabulky a omezeného SQL uživatele
   a ověřit odmítnutí nedovolených příkazů.
3. Dodat provozní skript s výchozím read-only preflightem,
   kontrolou identity serveru a DDL driftu.

**Co nelze provést přes dostupný Weather_MCP konektor:**
živé `CREATE TABLE`, `CREATE USER`, `GRANT` nebo nastavení
SQL práv; konektor poskytuje pouze read-only `execute_sql`.
Tento dokument ani merge GitHub PR proto nesmí tvrdit, že jsou
tabulky či SQL účet na skutečném serveru vytvořené.

## Návrh cílových objektů

Dva nové InnoDB objekty v **existujícím schématu**:

- `loucka_reconstruction.issue26_batch_events`: 1 APPLY / 1 ROLLBACK
  na dávku s payload SHA256, before-image SHA256, schvalovatelem
  a odkazem na konkrétní podepsané schválení.
- `loucka_reconstruction.issue26_field_events`: jednotlivé
  nevratně auditované změny s old/new, source_ref a metodikou;
  unikátní klíč (batch, event, target_time, variable), cizí klíč
  na batch tabulku, InnoDB.

Instalační soubor: `sql/issue26_transactional_audit_schema.sql`.
Nástroj `issue26_audit_ddl_guard.py` kontroluje přesné sloupce,
typy, indexy, primární klíče, FK a nepřítomnost triggerů na
journalu. SQL zapisovač nyní fail-closed odmítne i částečné či
pozměněné DDL.

## SQL identita a práva

Jméno účtu: `meteo_issue26_writer`; přístup **jen** ze
stroje `192.168.0.131`, kde již existuje LXC s Codexem.
SQL server používá `192.168.1.52:3306`.

Účet má dostat pouze:

- `SELECT` na `loucka_reconstruction.archive`;
- `SELECT` na `loucka_reconstruction.reconstruction_changes`;
- `SELECT, INSERT` na dvě nové auditní tabulky;
- sloupcové `UPDATE (value_fields)` na pracovní `archive`,
  **nikoli** na `dateTime`, `usUnits`, `interval`.

Účet nedostane obecné oprávnění `UPDATE` celé databáze,
`DELETE`, `DROP`, `ALTER`, `CREATE`, `GRANT OPTION`
ani jakékoli oprávnění k `pocasi-loucka.eu`.
Heslo se při instalaci kryptograficky vygeneruje a uloží mimo Git
do privátního `writer.cnf` (0600), bez výpisu do terminálu.
Přihlášení musí zůstat oddělené od root Linux SSH účtu.

Ověření SQL uživatele `loucka_audit@%` provedl read-only
konektor jen částečně: `CURRENT_USER()` potvrzen, příkaz
`SHOW GRANTS` konektor odmítá. Z toho **nelze odvodit**
reálnou úplnou sadu jeho oprávnění.

## Operátorské příkazy po nahrání repozitáře na databázový host

Skript `scripts/issue26_db_provision.py` nejprve validuje
read-only host, DB, 80 sloupců, známou srážkovou invariantu
a auditní DDL. Nevyužívá žádný další SQL server.

Za běhu jako Linux root na DB hostu s privátním souborem
`/root/meteo-admin.cnf`, který umožňuje DDL/GRANT do
pracovního schématu, nejprve výchozí režim **bez zápisu**:

```bash
PYTHONPATH=src python3 scripts/issue26_db_provision.py \
  --admin-client-file /root/meteo-admin.cnf
```

Očekávaná návratová hodnota:
`DRY_RUN_NOT_INSTALLED_NO_DB_WRITES` a SHA-256 přesného DDL.
Je-li něco špatně, nezapisovat a prohlédnout chybu.

Při samostatném provozním souhlasu s vytvořením obou auditních
tabulek a omezeného účtu, na **témže stávajícím serveru**:

```bash
PYTHONPATH=src python3 scripts/issue26_db_provision.py \
  --admin-client-file /root/meteo-admin.cnf \
  --execute \
  --confirm INSTALL-ISSUE26-AUDIT-AND-RESTRICTED-USER-ONLY
```

Tento příkaz se **neprovádí** automaticky přes PR nebo CI.
Je to jednorázové DDL+GRANT a MariaDB tyto operace
nelze vracet prostým SQL ROLLBACK. Při částečné chybě
skript selže a nedovolí automatické znovuspuštění:
nejprve manuálně ověřit skutečný stav.

Privátní `/root/meteo-issue26-private/writer.cnf`
je třeba případně chráněným přenosem dostat na LXC
`192.168.0.131` pro budoucí schvalovací workflow.

## Co neautorizuje ani provedená instalace

- Ani vytvoření tabulek, ani nový SQL účet nesmějí
  samy o sobě aplikovat žádnou meteorologickou hodnotu.
- Pro každý APPLY je potřeba live read-only review,
  doložený raw source, epochy jednotek, exact manifest,
  explicitní podpis batch+SHA a čerstvý SQL CAS.
- Pro ROLLBACK je nutný oddělený nový souhlas
  a shoda s aktuální po-opravnou hodnotou.
- Žádná změna produkční DB, žádné automatické uvolnění
  historických QUARANTINE ani ruční zásah do denních extrémů.

**Provozní stav:** tento dokument popisuje připravený a v CI
testovaný postup; samotné živé DDL nasazení není provedeno,
dokud nemáme oprávněné administrativní spojení.
