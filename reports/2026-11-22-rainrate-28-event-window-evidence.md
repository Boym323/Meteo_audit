# RainRate 2023–2024: 28 špiček — per-event pokrytí ±60 minut

**Stav:** 2026-11-22; read-only Weather MCP / MariaDB `SELECT`, bez změny databází.
**Vazba:** issue #16, C002. **Výsledek:** potvrzená provenience a časové pokrytí, nikoliv schválená fyzikální náhrada.

## Reprodukovatelnost

- Dotaz: [`sql/readonly/rainrate_28_candidate_window_grid.sql`](../sql/readonly/rainrate_28_candidate_window_grid.sql).
- Zdroje: `pocasi-loucka.eu_GW1000.archive`, `pocasi-loucka.eu.archive`, `loucka_reconstruction.archive` a `loucka_reconstruction.reconstruction_changes`.
- UTC `dateTime` = konec archivního intervalu; kandidát je GW1000 `rainRate > 5` a produkční `rainRate = 0` mezi 2023-01-01 00:00 UTC a 2025-01-01 00:00 UTC.
- Pro každý kandidát se individuálně ověřuje **25 očekávaných pětiminutových timestampů** od −60 do +60 minut včetně. Okna se překrývají; jejich počty **nelze sčítat** jako počet různých intervalů.
- `usUnits=16` ve všech 28 aktuálních kandidátních řádcích: `rainRate` v cm/h, `rain` v cm/archivní interval. Poměr `rain*12` není fyzikálně ověřenou náhradou uloženého `rainRate`.

## Ověřené výsledky (živý snapshot 2026-11-22)

| Veličina | Výsledek |
|---|---:|
| Kandidáti 2023 / 2024 | **13 / 15** |
| Kandidáti celkem | **28** |
| Existující řádky ve zdroji, produkci i rekonstrukci na event timestampu | **28/28** |
| Shodné nenulové `rainRate` GW1000 a rekonstrukce | **28/28** |
| Nulové produkční `rainRate` na event timestampu | **28/28** |
| `rainRate` s právě jednou událostí v `reconstruction_changes` (`state=applied`) | **28/28** |
| Úplné okolní okno 25/25 v každém ze tří archivů | **26/28 událostí** |
| Neúplná okolní okna | **2/28 událostí**, 23/25 v každém ze tří archivů |

### Konkrétní dvě neúplná okna

| UTC event epoch | GW1000 / produkce / rekonstrukce | Chybějící offsety vůči eventu |
|---:|---|---|
| `1687367100` | `23/25`, `23/25`, `23/25` | **+10 a +20 minut** |
| `1687367400` | `23/25`, `23/25`, `23/25` | **+5 a +15 minut** |

Obě okna se překrývají; jde o **stejné dvě chybějící UTC časové značky** `1687367700` a `1687368300`. Přítomnost 23 archivních bodů tedy není důkazem kompletního ±60min okna. SQL se ptá na přesné gridové timestampy; případné off-grid měření je nutné vyšetřit zvlášť.

## Co ještě chybí pro akceptaci issue #16

1. Dobová konfigurace WeeWX/RainRater a přesná sémantika `rainRate` versus krátkodobá intenzita i intervalový úhrn.
2. Externí nezávislý intervalový důkaz (radar ČHMÚ, WU/ILOUKA4 s ověřenou časovou osou) a per-event meteorologická klasifikace.
3. Bezpečný samostatný návrh až pro skutečně ověřené hodnoty; **momentálně žádný nový UPDATE ani INSERT není schválen**.

### Omezení

Shoda GW1000 a rekonstrukce dokládá původ obnoveného údaje, **nikoli** nezávislou senzorovou verifikaci. Auditní události dokazují existenci aplikované obnovy, nikoli správnost její fyzikální interpretace. Původní produkční archiv a staré zdroje zůstaly beze změny.
