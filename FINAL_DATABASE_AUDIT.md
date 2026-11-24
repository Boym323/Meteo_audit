# Finální audit databáze — 2026-11-24

## Rozsah a výsledek

Časový řez pro porovnání archivů je `dateTime <= 1795541700`, tedy 2026-11-24 17:35 UTC. Přímý konzistentní read-only snapshot na MariaDB 11.8.6 potvrdil 1 697 715 řádků v `loucka_reconstruction.archive` a 1 687 316 řádků v produkčním `archive`; v řezu je 0 produkčních timestampů chybějících v rekonstrukci.

Zdrojový účet má `SELECT` na produkčním schematu a dostupném `weewx_WH1080.archive`. Na `loucka_reconstruction` má účet také širší oprávnění, proto všechny exportní dotazy výslovně běžely v `START TRANSACTION ... READ ONLY`; během diffu nebyl proveden databázový zápis.

Rozdíl představuje 10 399 vložení a 82 325 změn jednotlivých polí (92 724 operací na 80 237 společných timestampech). Počty změn podle polí: `outTemp` 47, `outHumidity` 20 422, `rain` 2 201, `rainRate` 59 595, `extraTemp1` 2, `extraTemp2` 14, `soilTemp1` 13, `soilTemp5` 10, `soilTemp6` 21. Zbytek z 80 sloupců je na společných timestampech shodný. Detail je v `final_migration_package/FINAL_MIGRATION_OPERATIONS.jsonl.gz`; transakční snímek a hash v `FINAL_MIGRATION_MANIFEST.json`.

## Auditní události a typy operací

Každý návrh migrace musí být spojen s poslední událostí `reconstruction_changes` podle `(target_time, variable)`, jejího stavu, before/after hodnot, zdroje, zdrojového času a důvodu. Stavy `applied` a `reverted` se nesmějí zaměnit za produkční schválení. Typ operace se odvozuje z porovnání produkční a rekonstrukční hodnoty:

- `INSERT`: timestamp existuje pouze v rekonstrukčním archivu; přenáší se celý 80sloupcový řádek.
- `NULL_FILL`: produkční hodnota je NULL a rekonstrukční není NULL.
- `NULL_CLEAR`: produkční hodnota je neprázdná a rekonstrukční je NULL. Jde o invalidaci podezřelé hodnoty, vyžaduje výslovný souhlas.
- `VALUE_REPLACE`: obě hodnoty jsou neprázdné a liší se.

V úplném diffu je 895 `NULL_CLEAR`: 835 starších invalidací a 60 nových teplotních odstranění v dávkách `qc-extra-temp-outliers-20261123-v1` a `qc-soil-negative-outliers-20261123-v1`. Poslední aplikovaný event, jeho `old_value` proti produkční hodnotě a NULL after-value proti rekonstrukci se přesně shodují u všech 60: 2 `extraTemp1`, 14 `extraTemp2`, 13 `soilTemp1`, 10 `soilTemp5`, 21 `soilTemp6`. Starších 835 invalidací je odděleno.

Všech 82 325 změn polí má auditní event i zdrojový claim; všechny operace jsou `NOT_APPROVED` pro produkci. U 1 497 změn nejnovější auditní událost neodpovídá aktuálnímu stavu rekonstrukce; jsou zachovány jako `REVIEW_REQUIRED`. Všech 10 399 INSERT řádků je propojeno s událostmi pro timestamp (nikoliv s jedním řádkovým eventem); související eventy, zdroje a stav schválení jsou v detailním JSONL.

Každý diff řádek nese `usUnits`. Kód `16` (WeeWX METRIC) znamená rychlost větru v km/h a srážky v cm (`rainRate` v cm/h). `usUnits=17` je METRICWX; historické wind archivy však mají epochy, kde raw hodnoty neodpovídají jednoduchému převodu. Kódy jsou metadata, nikoli důvod k automatické konverzi.

## Úplnost auditu 80 sloupců

Stávající projekt obsahuje dílčí audity dostupnosti, jednotek/epoch, kontinuity a fyzikální kontroly. Úplná nová sada ročních coverage/min/max, distribucí extrémů, zamrznutých běhů, mezer, změn jednotek a kontrol odvozených polí pro všech 80 sloupců nebyla v této relaci přepočítána. Výsledky známých cílených screeningů jsou v `WIND_QUALITY_REPORT.md`; starší auditní podklady a jejich hranice jsou uvedeny v `README.md`, `ARCHIVE_*`, `STATISTICAL_READINESS_CURRENT_REPORT.md` a `sql/readonly/`.

Přímo ověřené počty v řezu: 1 513 řádků `rain>0 AND rainRate=0`, 4 `radiation>1400`, 729 `inTemp<0`, 4 `pm25_1=999.9`. Tyto případy jsou diagnostické kandidáty; bez doložené epochové sémantiky/zdroje se nepřepisují.

## Tlak

`pressure_reconstruction` a `pressure_reconstruction_stage_v1` mají 1 697 621 unikátních timestampů. Ponechat 150 942 archivních a 125 298 regionálních odhadů ve stavu neschváleno, zachovat Q1 2018 ochranu i původní `archive.pressure`. Tabulka odhadů se nesmí spojit do oficiálních měření ani statistik. Podrobnosti importu jsou v [záznamu importu tlaku](reports/2026-11-24-pressure-reconstruction-db-import.md).

## Závěr

Diff je připraven k review a ověřen proti původním počtům. Produkční migrace je NO-GO do obnovení na skutečně oddělené MariaDB instanci, testu přepočtu WeeWX a rollbacku celé migrace. Schéma `loucka_migration_test` na stejném serveru (`server_id=1`) není izolovaná instance. Produkce nebyla měněna.
