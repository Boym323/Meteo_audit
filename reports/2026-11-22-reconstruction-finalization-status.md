# Rekonstrukce historických dat Počasí Loučka — ověřený stav k 22. 11. 2026

**Rozsah:** synchronizace kódu, dokumentace a bezpečných souhrnů projektu `Meteo_audit`. Tento report ověřuje lokální soubory v `/opt/meteo-audit`; neprovádí nový databázový audit ani nepotvrzuje produkční publikaci meteorologických hodnot.

## Finální rozhodnutí z 17. 11. 2026 — ověřeno proti lokálním artefaktům

| Metrika | Ověřený výsledek |
| --- | ---: |
| Operace v rozhodovacím manifestu | 92 664 |
| `QUARANTINE` | 92 366 |
| `ALREADY_APPLIED` | 298 |
| Další `APPLY` / `KEEP` | 0 / 0 |
| Zásahy tohoto finálního běhu do produkčního archivu | 0 |

Ověřovací skript prošel všemi porovnáními SHA-256, počtů operací, stavů a důvodů mezi JSONL manifestem, checkpointem, souhrnným rozhodnutím a CSV diffem. Podrobnosti bez hodnotových řádků jsou v [ověřovacím souhrnu](data/2026-11-22-finalization-integrity-verification.json); reprodukovatelný skript je `scripts/verify_finalization_integrity.py`.

- SHA-256 rozhodovacího manifestu: `a6ed14c902b9bec4e746c00aeb71aed225b9672363592cf5add3d57a3a242ef6`.
- SHA-256 migračního CSV diffu: `8adda4e543ea7a0128d919689efe2f18475e1330488cd9e4dfb98b21c5eb5780`.
- `ALREADY_APPLIED` označuje 298 dříve ověřených operací v pracovní/testovací rekonstrukci (291 řádků a 7 doplnění polí). Neznamená to 298 zápisů do produkce.
- `QUARANTINE` není počet chybných měření. Zahrnuje neodsouhlasené odhady, chráněná období, konflikty a nerozřešenou sémantiku srážek.
- Obsah manifestu a CSV diffu obsahuje časové značky, zdrojové databáze a navrhované/historické hodnoty. Tyto hodnotové soubory nejsou zveřejněny; jejich velikost a SHA jsou evidovány v lokálním inventáři balíčků.

## Brány kvality a otevřené blokace

- **Q1 2018 zůstává chráněné.** Checkpoint eviduje 10 080 chybějících řádků a 10 080 odpovídajících rekonstrukčních návrhů; 10 372 návrhů/odvozených událostí nejsou potvrzením místního měření. Přístup `SELECT` k referenčnímu schématu LuhaMet/ČHMÚ byl odepřen, proto související kandidáti zůstávají v karanténě.
- **Rok 2021 je diagnostický**, nikoli automaticky publikační nebo opravný. Automatická publikační matice má 195 řádků `DIAGNOSTIC_ONLY`.
- **GW3000 E4 zůstává blokované:** 462 řádků v matici, z toho 231 `rain` a 231 `rainRate`. Suchý současný odečet neprokazuje historické významy mokrých/reset událostí; žádný srážkový úhrn ani rychlost není touto kontrolou uvolněna.
- Automatická validační matice má 3 927 řádků; `READY_FOR_PUBLICATION` je 0 a `READY_WITH_DISCLOSED_LIMITATIONS` jsou 2. Publikace historických rekordů není povolena.
- WeeWX denní souhrny nebyly přepočteny. Produkční cutover ani deploy neproběhl.

Čísla výše pocházejí z lokálního checkpointu a validačních artefaktů vytvořených 15.–17. 11. 2026. Při synchronizaci nebylo připojení k databázi použito; integrita zde znamená kontrolu souborů a jejich hashů, nikoli nový read-only SQL běh.

## Lokální velké balíčky

V `/opt/meteo-audit` je 114 ZIP balíčků (celkem 3 403 538 773 bajtů) a databáze SQLite `data/historical_value_concordance.sqlite` (1 663 004 672 bajtů). Databáze obsahuje souhrnné tabulky `field_rollup`, `snapshot_meta` a hodnotové důkazy `timestamp_evidence`; archivní konkordance je uložena komprimovaně. ZIP inventář, ukázky obsahu, velikosti a SHA-256 jsou v [lokálním inventáři](data/2026-11-22-local-package-integrity.json). Tyto balíčky ani databáze nejsou v GitHubu.

## GitHub synchronizace

PR #28, #29, #30, #34, #35, #36 a #38 jsou sloučeny do `main`. Jejich již začleněný obsah nebyl znovu kopírován. Commit `b0b5750` není dostupný jako objekt v této checkout ani řešitelný přes GitHub API; nebyl rekonstruován z popisu. Větve PR #32 a #33 zůstávají oddělenou výzkumnou prací.

Po dokončení nynějšího synchronizačního PR doplňte odkaz a výsledek CI do tohoto oddílu. Dokud PR není sloučen a vzdálený `main` znovu porovnán, synchronizace není označena za dokončenou.

### Synchronizační sada v této větvi

V lokálním LXC prošlo 193 testů. Publikovatelná větev obsahuje samostatně běžitelný výběr 168 testů a syntax check. Dalších 60 testovacích případů v prvním pokusu vyžadovalo neveřejné hodnotové snapshoty a lokální preview soubory; jejich testovací moduly proto nejsou v PR, aby CI nevyžadovalo vynechaná data. Kompletní zdrojové výsledky a snapshotově vázané testy zůstávají v `/opt/meteo-audit`. Větev neobsahuje `.env`, databázové exporty, SQLite ani ZIP balíčky.

## Bezpečnostní hranice

Žádný zápis do databáze `pocasi-loucka.eu`, změna produkčního archivu, WeeWX rebuild, zásah do živé synchronizace GW3000 ani nasazení na web nebyly provedeny. Publikační a produkční migrační rozhodnutí zůstává samostatně blokováno.
