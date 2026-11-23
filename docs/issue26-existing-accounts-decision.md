# Issue #26 — závazné rozhodnutí: žádné další SQL účty

Datum: 23. listopadu 2026. Poslední výslovné rozhodnutí vlastníka.

## Co se nesmí

- **Nevytvářet žádné nové MariaDB/MySQL uživatelské účty** pro audit,
  rekonstrukci, read-only kontrolu ani SQL writer.
- Nevytvářet `meteo_issue26_writer` ani další servisní účty.
- Nepoužívat v provozu předchozí `scripts/issue26_db_provision.py
  --execute`, protože starší varianta zakládá nový SQL účet.
  Instalační procedury a dokumenty PR #77/#78, které to
  doporučovaly, jsou tímto rozhodnutím **překonané**.
- Neměnit hesla, host pravidla ani granty existujících účtů
  jen kvůli vytvoření nového účtu; případné potřebné oprávnění
  řešit až po zjištění reálného stavu existujícího účtu.
- Žádná nová samostatná MariaDB instance, bez prověřování PBS
  nebo záloh (starší závazná rozhodnutí vlastníka).

## Co máme

- Stávající MariaDB `lo-infra-db-mariadb01` (`server_id=1`),
  pracovní schéma `loucka_reconstruction`.
- Přístup Navicat pro DDL používá podle uživatelem dodaného
  `CURRENT_USER()` účet `root@%` s administrátorskými
  oprávněními. To **nedokazuje** granty jiného účtu.
- Read-only Weather_MCP hlásí `CURRENT_USER()=loucka_audit@%`.
  Účet existuje a umožňuje čtení pracovních dat. Rozsah
  jeho SQL oprávnění pro INSERT do auditních tabulek a UPDATE
  pracovní `archive` zatím nebyl nezávisle ověřen.
- **Auditní DDL je již uživatelem nainstalováno prostřednictvím
  Navicatu**. Stav ověřen i přes Weather_MCP:
  `loucka_reconstruction.issue26_batch_events` a
  `loucka_reconstruction.issue26_field_events`
  existují jako InnoDB tabulky a obě mají **0 řádků**.
  To potvrzuje existenci/počty, **nikoli zatím plnou shodu
  FK, indexů, sloupců ani práva účtu `loucka_audit`**.

## Následující provozní postup

1. **Nevytvářet další účet ani auditní tabulky** a neopakovat
   instalaci DDL. Obě tabulky již existují.
2. V Navicatu podle potřeby zkontrolovat oprávnění
   `SHOW GRANTS FOR 'loucka_audit'@'%';` — pouze čtení
   metadat, nezakládá ani nemění účet. Administrativní
   aktuální účet `root@%` není totéž co `loucka_audit@%`.
3. Ověřit úplný typový a indexový/FK soulad obou auditních
   tabulek s `sql/issue26_transactional_audit_schema.sql`
   před povolením generického SQL writeru.
4. Dál používat reálný read-only export a schválení
   jednotlivých dávek. **Nevydávat žádné nové UPDATE**
   meteorologických hodnot bez výslovně schváleného
   manifestu, předobrazu a podpisu.
5. Neměnit `pocasi-loucka.eu.archive` ani denní tabulky
   `archive_day_*`; denní extrémy později přepočítá WeeWX.

Toto rozhodnutí má přednost před dřívějším návrhem omezeného
nového účtu z PR #77 a PR #78.
