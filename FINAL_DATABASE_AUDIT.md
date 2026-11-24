# Finální audit databáze — 2026-11-24

## Rozsah a výsledek

Časový řez pro porovnání archivů je `dateTime <= 1795541700` (2026-11-24 15:15 UTC). Přímý read-only dotaz na MariaDB 11.8.6 potvrdil 1 697 715 řádků v `loucka_reconstruction.archive` v tomto řezu; celá tabulka nyní obsahuje 1 697 717 řádků, z toho 2 jsou za řezem. Uživatelský SQL audit uvádí 1 687 316 produkčních řádků a 0 produkčních timestampů chybějících v rekonstrukci.

Rozdíl představuje 10 399 vložení a 82 325 změn jednotlivých polí (92 724 operací na 80 237 společných timestampech). Počty změn podle polí: `outTemp` 47, `outHumidity` 20 422, `rain` 2 201, `rainRate` 59 595, `extraTemp1` 2, `extraTemp2` 14, `soilTemp1` 13, `soilTemp5` 10, `soilTemp6` 21. Ostatní sloupce jsou dle zadaného SQL auditu na společných timestampech shodné.

## Auditní události a typy operací

Každý návrh migrace musí být spojen s poslední událostí `reconstruction_changes` podle `(target_time, variable)`, jejího stavu, before/after hodnot, zdroje, zdrojového času a důvodu. Stavy `applied` a `reverted` se nesmějí zaměnit za produkční schválení. Typ operace se odvozuje z porovnání produkční a rekonstrukční hodnoty:

- `INSERT`: timestamp existuje pouze v rekonstrukčním archivu; přenáší se celý 80sloupcový řádek.
- `NULL_FILL`: produkční hodnota je NULL a rekonstrukční není NULL.
- `NULL_CLEAR`: produkční hodnota je neprázdná a rekonstrukční je NULL. Jde o invalidaci podezřelé hodnoty, vyžaduje výslovný souhlas.
- `VALUE_REPLACE`: obě hodnoty jsou neprázdné a liší se.

Přímý audit potvrdil 60 aplikovaných NULL_CLEAR událostí v dávkách `qc-extra-temp-outliers-20261123-v1` a `qc-soil-negative-outliers-20261123-v1`: 2 `extraTemp1`, 14 `extraTemp2`, 13 `soilTemp1`, 10 `soilTemp5`, 21 `soilTemp6`. Pro finální diff musí být u všech 60 ověřena shoda auditního `old_value` s produkční předchozí hodnotou a `new_value IS NULL` s rekonstrukcí; samotná událost není schválením produkčního zápisu.

## Úplnost auditu 80 sloupců

Stávající projekt obsahuje dílčí audity dostupnosti, jednotek/epoch, kontinuity a fyzikální kontroly. Úplná nová sada ročních coverage/min/max, distribucí extrémů, zamrznutých běhů, mezer, změn jednotek a kontrol odvozených polí pro všech 80 sloupců nebyla v této relaci přepočítána. Výsledky známých cílených screeningů jsou v `WIND_QUALITY_REPORT.md`; starší auditní podklady a jejich hranice jsou uvedeny v `README.md`, `ARCHIVE_*`, `STATISTICAL_READINESS_CURRENT_REPORT.md` a `sql/readonly/`.

Přímo ověřené počty v řezu: 1 513 řádků `rain>0 AND rainRate=0`, 4 `radiation>1400`, 729 `inTemp<0`, 4 `pm25_1=999.9`. Tyto případy jsou diagnostické kandidáty; bez doložené epochové sémantiky/zdroje se nepřepisují.

## Tlak

`pressure_reconstruction` a `pressure_reconstruction_stage_v1` mají 1 697 621 unikátních timestampů. Ponechat 150 942 archivních a 125 298 regionálních odhadů ve stavu neschváleno, zachovat Q1 2018 ochranu i původní `archive.pressure`. Tabulka odhadů se nesmí spojit do oficiálních měření ani statistik. Podrobnosti importu jsou v [záznamu importu tlaku](reports/2026-11-24-pressure-reconstruction-db-import.md).

## Závěr

Auditní diff lze připravit k review, ale produkční migrace je NO-GO do obnovení na schválené oddělené instanci, úplného operation-level diffu proti aktuálnímu produkčnímu snapshotu, testu dávkového přepočtu WeeWX a úspěšného testu rollbacku celé migrace. Produkce nebyla měněna.
