# Bezpečné dokončování `loucka_reconstruction`: živý triage čekajících návrhů
**Ověřeno:** 22. listopadu 2026, MariaDB přes read-only Weather MCP.  
**Reprodukce:** [`sql/readonly/reconstruction_pending_candidate_disposition_20261122.sql`](../sql/readonly/reconstruction_pending_candidate_disposition_20261122.sql) — čtyři samostatné `SELECT` příkazy; všechny A–D skutečně spuštěny a porovnány s aktuálním stavem.

## 1. Úplnost řádků ≠ úplnost měření

Při prvním konzistentním snapshotu: `pocasi-loucka.eu.archive` **1 686 769** řádků; `loucka_reconstruction.archive` **1 697 167**; **1** nejnovější produkční timestamp teprve čeká na 5min sync; **10 399** extra historických timestampů s auditní stopou. Průběžný synchronizér je v provozu. Žádný chybějící starý produkční timestamp z těchto počtů nevyplývá.

Souhrn z dřívějšího read-only screeningu: 10 101 extra historických INSERTů `ESTIMATED`, 290 `RESTORED`, 1 `RECOVERED_SOURCE`, 7 bootstrap řádků následně změněných na prostorový odhad srážek. Bez per-field provenance a meteorologické validace se v1 nemůže publikovat jako fyzicky certifikovaná. **Počty nejsou součtem nezávislých nových senzorových měření.**

## 2. Čekající kandidáti v existujících auditních staging tabulkách

Read-only `reconstruction_status`: **20 pending batches, 272 pending kandidátů**; 4 zrušené dávky a 93 zrušených kandidátů zůstávají v historii a nesmějí být znovu aplikovány.

Ze 272 pending kandidátů:

| Dispozice | Počet | Důsledek |
|---|---:|---|
| Bez číselné `proposed_value` | **264** | Jsou to varovné/revizní položky, nikoli 264 schválených hodnot k doplnění |
| Návrh číselné hodnoty již přítomné a auditně aplikované | **7** | `ALREADY_APPLIED_NO_REPEAT`, žádný nový zápis |
| Návrh chybějícího 5min timestampu s konfliktem okolních zdrojů | **1** | `HOLD_MISSING_TARGET_NO_INDEPENDENT_PROOF` |

Sedm číselných již aplikovaných položek: 3 `rainRate` historické špičky (2013, 2023, 2023) a 4 dříve obnovené nulové intervalové srážky (2020×2, 2026×2). Ve všech sedmi existuje právě odpovídající `state=applied` audit a současná hodnota odpovídá návrhu. **Netvrdit, že 7 položek stále čeká na apply.**

Jediný čekající INSERT je `batch_id=loucka-test-gap-20220915-1455`, UTC epoch `1663246500`, `rain=0.335279992` cm ve staré DB `pocasi-loucka.eu_old`. Tento timestamp chybí v produkci, pracovní rekonstrukci **i** historickém GW1000. Při kontrolním okně ±20 minut má stará DB 9 záznamů a ostatní archivy 8; srážkový úhrn ve starém zdroji se během významné srážkové epizody liší od GW1000. Nemáme nezávisle doložené časové přiřazení / původ starého srážkového měření a není bezpečné vložit ho jako fyzické pozorování.

## 3. Proč nelze mechanicky kopírovat NULL ze staré produkční kopie

Exact-timestamp, `usUnits` a `interval` shodný s `pocasi-loucka.eu_old` nalezl **3 057** pozic s `outTemp` NULL v rekonstrukci a nenulovým (NOT NULL) údajem ve staré kopii. To **není** 3 057 schválených obnov.

V roce 2020 jde o **103** takových pozic: historická kopie má pouze **dvě různé** hodnoty (0 a 4,25 °C), zatímco `weewx_WH1080` má teplotu ve 102 z nich, s **96 různými** hodnotami, a s historickou kopií se neshoduje ani jednou. `weewx_WH1080` se ve všech 102 případech shoduje s `old_weewx`, ale tyto dvě databáze mohou být kopie stejné originální řady. Nejsou dvěma nezávislými měřeními.

Rovněž 2013 vykazuje **1 946** pozic chybějícího `outTemp` s hodnotou v kopii starého archivu, ale zásadně v souvislých výpadcích/anomálních úsecích. Přímý plošný NULL fill, lineární interpolace nebo neověřený převod jednotek je zablokován. Pro všech 3 057 bodů chybí datum/verze původního loggeru a per-field nezávislá fyzická verifikace; shoda importních kopií sama nepostačuje.

## 4. Stav operací

- Do `loucka_reconstruction.archive` **nebyl touto forenzní kontrolou proveden žádný INSERT, UPDATE ani DELETE**; nebyla vytvořena nová dávka ani rušen existující audit.
- Produkční zdroj, běžící WeeWX a kontinuální GW3000 synchronizace zůstávají nedotčené.
- **92 366 QUARANTINE** operací v dřívějším finálním manifestu zůstává odděleně neschválených. Nesmí se zaměnit s 272 původními pending QA příznaky ve stagingu.
- Pro další automatický apply momentálně **0** nových kandidátů s doloženým source time, jednotkovou epochou, nekolizním cílem, nezávislou věcnou kontrolou, explicitní approval a ověřeným restore/rollback.
- Read-only připojení mělo krátký výpadek `UNAVAILABLE`, ale obnovilo se; následně se podařilo **ověřit i všech 80 sloupců** společných původních a rekonstruovaných timestampů. Reprodukce níže.

## 5. Kompletní NULL-safe kontrola všech 80 sloupců

Při obnoveném připojení jsem přímo spustil **tři read-only SELECTy** přes všechny společné timestampy: 79 měřených/metadatových sloupců `<=>` + klíčový `dateTime` pro přesné párování. Ve všech třech dotazech bylo **1 686 768** společných řádků. Ze 79 porovnaných sloupců se přesně **75** vůbec neliší; další sloupec `dateTime` je identita joinu, tj. **76 z 80 sloupců nezměněno**.

| Rozdílné pole | Počet překryvných řádků s rozdílem |
|---|---:|
| `outTemp` | 47 |
| `outHumidity` | 20 422 |
| `rain` | 2 201 |
| `rainRate` | 59 595 |
| **Součet hodnotových změn** | **82 265** |

K tomu je **10 399** historicky přidaných řádků: **92 664** operací proti současnému původnímu archivu, což číselně přesně odpovídá poslednímu dříve zafixovanému diffu. Tyto výsledky neznamenají, že 92 664 operací bylo schváleno pro produkci: manifest stále eviduje **92 366 QUARANTINE** + **298 ALREADY_APPLIED** jako samostatné rozhodovací stavy. Samotný číselný diff není fyzikální validace a nemá význam náhrady originálních hodnot.

Přesný reprodukovatelný checkpoint: [`sql/readonly/reconstruction_v1_all_80_columns_parity.sql`](../sql/readonly/reconstruction_v1_all_80_columns_parity.sql), s pevným horním UTC timestampem `1795377300`, aby nově přicházející GW3000 nezkreslovala porovnání. Počty odpovídají živému MariaDB SELECTu; publikovaný SQL se má samostatně znovu spustit při budoucí revizi.

## 6. Akceptační kritéria bez fiktivních hodnot


1. Každý archivní sloupec klasifikovat **po veličině a čase** jako MEASURED / RESTORED / ESTIMATED / SENSOR_ERROR / UNVERIFIED / MISSING s auditní stopou, ne přes celý řádek.
2. Teplotní 2020 konflikt a 2022 dešťovou mezeru označit `HOLD_SOURCE_CONFLICT` a vyloučit z certifikovaných extrémů; `NULL` zachovat tam, kde chybí nezávislý důkaz.
3. Připravit konzistentní `mariadb-dump --single-transaction` nebo fyzický snapshot, jeho SHA-256 a samostatný restore test; bez toho žádná hromadná změna.
4. Aktuální zdroj/cíl sync a 80-sloupcové nulově-kolizní invarianty obnovit po dostupnosti DB konektoru.
5. Bezpečný webový vývoj může používat původní údaje `original_unverified`, ale žádný `approved` cutover, přepis produkce nebo nové certifikované rekordy.

**Výsledná dispozice:** archiv je časově průběžně sladěný s produkcí, ale není fyzicky uzavřený; další neupravené historické hodnoty nelze bezpečně doplnit bez nové evidence.
