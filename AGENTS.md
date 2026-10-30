# AGENTS.md — Počasí Loučka / audit historických dat

## Úloha
Prováděj reprodukovatelný audit a návrhy rekonstrukcí meteorologických dat stanice Počasí Loučka za období přibližně 2009–2026. Komunikuj česky. Nejdříve zmapuj existující stav; neopakuj již provedené práce bez důvodu.

## Bezpečnost a změny dat
- Ve výchozím stavu **pouze čti**. Neupravuj, nemaž, nepřepisuj ani netrunkuj tabulky v žádné databázi.
- Před změnou dat vždy připrav: konkrétní SQL návrh, počet dotčených řádků, zálohu, důkazní podklady, možnost rollbacku a ověřovací dotazy. Vyžádej si výslovné schválení změny.
- Neprováděj automaticky ani opravy odvozených veličin (`rainRate`, denní akumulace) bez znalosti jejich přesné sémantiky v daném období.
- Chybějící měření **není totéž co nula**. Nulu dosazuj jen při doložené bezesrážkové situaci a po schválení pravidla rekonstrukce.
- Každé podezření a návrh opravy eviduj s časem UTC, názvem veličiny, původní hodnotou, navrženou hodnotou, zdrojem a stupněm jistoty.
- Hesla, tokeny a connection stringy neuváděj do Markdownu, logů ani Gitu. Konfiguraci ukládej do `.env` s oprávněním 600. Nikdy `.env` necommituj.
- Pracuj pod neprivilegovaným systémovým účtem; přístup do DB minimalizuj.
- Pro analytické CLI používej existující `DB_USER=loucka_audit` a `DB_PASSWORD` z místního `.env`. Účet má v rekonstrukční DB i zápisová práva; tato skutečnost nezakládá souhlas se zápisem. Zachovej jediný SELECT/SHOW v `START TRANSACTION READ ONLY`, neměň granty a nevyžaduj nový účet, pokud to uživatel sám nepožádá.
- Pro archivní agregace používej WeeWX konec intervalu a hranice `(start, end]`; denní občanské součty výslovně odlišuj od meteorologického srážkoměrného dne.

## Známý kontext
- Databázový server: MariaDB, dle dřívější dokumentace verze 11.8.x (ověř aktuální stav).
- Produkční historická databáze: `pocasi-loucka.eu`, hlavní tabulka `archive`.
- Pracovní rekonstrukční databáze: `loucka_reconstruction`, také obsahuje `archive`, auditní a referenční tabulky.
- Další existující databáze: `old_weewx`, `pocasi-loucka.eu_GW1000`, `pocasi-loucka.eu_old`, `weewx_WH1080`.
- `archive.dateTime` je Unix timestamp v sekundách (UTC), místní zobrazení `Europe/Prague` se změnami CET/CEST.
- Typické intervaly archivace určuje `archive.interval` (minuty); zjisti je z dat, nepředpokládej jednotný interval.
- Primární zdroje dat: Ecowitt GW3000 / WeeWX; historicky také další generace stanic, které je potřeba časově rozlišovat.
- Srovnávací stanice: LuhaMet a Weather Underground ILOUKA4; posuzuj vzdálenost, kvalitu a dostupné období.

## Pořadí práce
1. Zjisti dostupné DB, tabulky, definice sloupců, indexy, časová pokrytí a počet řádků. Vše pouze read-only.
2. Zmapuj již provedené zásahy a srovnávací data v `loucka_reconstruction`, zejména červenec 2021 (déšť) a duben 2022 (vlhkost).
3. Zpracuj celkové časové pokrytí a nepravidelnosti intervalů měření.
4. Audituj veličiny po skupinách a současně po časových úsecích: srážky, teploty, vlhkost, tlak, vítr, sluneční záření/UV, PM2.5, blesky, půdní senzory.
5. U každé anomálie porovnej fyzikální konzistenci, sousední časové body, období a nezávislé stanice; případně oficiální zdroje ČHMÚ.
6. Vytvoř návrhy oprav a zprávy s důkazy; zásahy do databáze pouze po schválení.

## Výstupy
Průběžně vytvářej `reports/`, `sql/readonly/` a `proposals/`. Každý report uvádí přesné časové rozmezí, dotazy, počty, metodu, nejistoty a rozdíly proti předchozímu běhu. Nedohaduj připojovací údaje ani jednotky — vždy ověř definice a konfiguraci WeeWX.

## Synchronizace s GitHubem
- Hlavní vzdálený repozitář je `https://github.com/Boym323/Meteo_audit`, lokální remote `origin`, větev `main`.
- Po dokončení každého auditního úkolu aktualizuj příslušný report a souhrnné Markdown soubory; přidej související CSV/JSON data a reprodukovatelné SQL/kód.
- Před commitem zkontroluj staged soubory a diff. `.env`, hesla, tokeny, connection stringy a jiné tajné údaje se nikdy necommitují ani neposílají.
- Po kontrole vytvoř commit na pracovní větvi, pushni ji na `origin` a otevři pull request do `main`; PR automaticky neslučuj, pokud to zadání výslovně nepožaduje. Do commitu zahrň pouze soubory související s úkolem; neukládej Python cache ani nesouvisející balíčky.
- Exporty z databáze musí uvádět původ, časové rozmezí, časovou zónu, jednotky, filtry a počet řádků. Zachovávej rozdíl mezi měřenými zdrojovými daty, odvozenými souhrny a návrhy rekonstrukcí.
- Pokud se commit nebo push nepodaří, ponech změny lokálně, uveď důvod a nevypisuj přihlašovací údaje.
