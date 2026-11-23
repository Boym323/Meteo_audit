# C001 — duben 2022: rosný bod po rekonstrukci relativní vlhkosti

**Datum:** 23. 11. 2026. **Režim:** pouze SELECT na stávající
loucka_reconstruction (lo-infra-db-mariadb01). Žádný nový SQL účet,
žádné meteorologické UPDATE, žádná nová MariaDB instance.

**Klasifikace:** DIAGNOSIS_CONFIRMED / REPLACEMENT_UNRESOLVED /
NOT_APPROVED.

## Pomocná tabulka rekonstrukce dubna 2022

Loucka_reconstruction.reconstruction_humidity_202204 obsahuje
3 734 unikátních timestampů. Rozložení:
- estimate_ready / frozen: **2 194**;
- estimate_ready / missing: **1 299**;
- missing_unresolved / missing: **156**;
- invalidate_frozen / frozen: **85**.

U všech 3 734 záznamů platí
archive.outHumidity <=> proposed_humidity_pct
a archive.outTemp <=> local_temperature_c (NULL-safe).
3 578/3 734 má applied historii outHumidity;
156 missing_unresolved nikoli.

## Co je skutečně prokázáno

U skupiny 2 194 estimate_ready/frozen:

- **2 194/2 194** uložených rosných bodů odpovídá
  diagnostickému Magnusovu výpočtu z **původní RH**
  (original_humidity_pct) s tolerancí ±0,1 °C.
- Pouze **79/2 194** odpovídá ±0,1 °C diagnostickému
  výpočtu ze **současné RH** (archive.outHumidity).
- **1 077/2 194** se od diagnostického výpočtu
  ze současné RH liší o **více než 2 °C**.
- Maximum absolutní odchylky ≈ **13,507 °C**.

Příklad: target_time 1649183700, T=6,2 °C, původní RH=89 %,
současná RH=91,13 %, uložený dewpoint≈4,5229 °C. Ten
odpovídá původní RH, nikoli aktuálně upravené RH.

Další důležitá odlišnost:
- U 85 invalidate_frozen/frozen je aktuální RH **NULL**,
  ale dewpoint stále vyplněný, odpovídající původní RH.
  Případná změna na NULL vyžaduje vlastní rozhodnutí.
- U 1 299 estimate_ready/missing je RH nově vyplněná,
  ale dewpoint **NULL**. To je odlišná situace od
  2 194 zmrazených intervalů a nelze ji plošně zaměnit
  za automatický numerický přepočet.
- U 156 missing_unresolved zůstává RH i dewpoint NULL.

## Reprodukovatelná diagnostika (jen čtení)

Pro danou teplotu T (°C), vlhkost RH (%) se používá
diagnostická **Magnusova aproximace**:
alpha = LN(RH/100) + 17.625*T/(243.04+T)
DP = 243.04*alpha/(17.625-alpha)

U každého ze záznamů estimate_ready/frozen se testuje
uložený dewpoint proti DP s původní i současnou RH.
Pro 1 077 intervalů rozdíl current-RH DP přesahuje 2 °C.
U NULL a RH<=0 musí být diagnostika nevyčíslitelná.

Příklad čtecího výpisu:

    SELECT h.target_time,h.original_humidity_pct,
           h.proposed_humidity_pct,
           a.outHumidity,a.outTemp,a.dewpoint,
           h.defect_type,h.decision,h.method_version
    FROM loucka_reconstruction.reconstruction_humidity_202204 h
    JOIN loucka_reconstruction.archive a
      ON a.dateTime=h.target_time
    WHERE h.decision='estimate_ready'
      AND h.defect_type='frozen'
    ORDER BY h.target_time LIMIT 5;

## Meteorologické hranice závěru

Magnusovy konstanty zde jsou 17,625 a 243,04 °C;
**není doloženo, že jsou přesně dobovými konstantami WeeWX**.
Výsledek silně podporuje zastaralou odvozeninu dewpoint
po změně RH, ale **nedokazuje správnou náhradní hodnotu**.
Je nutné zjistit dobovou implementaci WeeWX a předpis
pro jednotky, teplotu, RH, zaokrouhlování a NULL.

Před jakoukoliv návrhovou dávkou prověřit i heatindex
a appTemp (ne všechna pole mají stejnou sémantiku), připojit
source evidence, unit epoch, diagnózu a náhradní confidence.
Aplikovat výhradně jednotlivě schválené batch ID + SHA256
s read-only before-image a transakčním CAS/rollbackem.
**Tento report není důvodem k SQL UPDATE**, zvlášť ne
k masovému přepočítání všech 3 734 hodnot.

Starší report C001=1 077 rozdílů >2 °C je aktuálně
potvrzený, nikoli automaticky odstraněný.
Denní extrémy se přepočítají později WeeWX.
