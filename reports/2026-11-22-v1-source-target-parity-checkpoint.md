# Rekonstrukce v1: kontrola shody řádků a omezení publikace

**Datum živé read-only kontroly:** 2026-11-22. Zdroj `pocasi-loucka.eu.archive`, cíl `loucka_reconstruction.archive`. SQL: [`sql/readonly/reconstruction_v1_source_target_parity.sql`](../sql/readonly/reconstruction_v1_source_target_parity.sql).

## Ověřené při jednom SELECTu

| Ukazatel | Výsledek |
|---|---:|
| Produkční řádky | 1 686 765 |
| Rekonstrukční řádky | 1 697 164 |
| Zdrojový timestamp chybějící v cíli | **0** |
| Cílové timestampy navíc | **10 399** |
| Cílové timestampy navíc bez vazby v `reconstruction_changes` | **0** |
| Rovnost `source + target-only − missing = target` | **PASS** |
| Poslední timestamp obou tabulek v tomto běhu | `1795376400` |

Počet target-only odpovídá 10 399 historickým INSERT operacím dřívějšího diffu; toto číselné srovnání samo **nedokazuje, že každá operace je legitimní nebo schválená pro produkční publikaci**. Existence change eventu dokládá auditní stopu, ne kvalitu zdrojového měření.

## Rozložení cílových řádků navíc podle původního UTC data

| UTC rok | Řádky navíc | Nenulové (NOT NULL) outTemp | Nenulové outHumidity |
|---|---:|---:|---:|
| 2013 a dříve | 3 | 3 | 3 |
| 2018 | **10 081** | 10 081 | 293 |
| 2019 | 1 | 1 | 0 |
| 2020 | 52 | 52 | 0 |
| 2021 | 7 | 0 | 0 |
| 2022 | 65 | 65 | 0 |
| 2023 | 190 | 190 | 0 |
| **Celkem** | **10 399** | **10 392** | **296** |

V žádném target-only řádku nebyl vyplněný `rainRate`. **Poznámka:** tyto počty vyjadřují přítomnost hodnot, ne nezávislé meteorologické ověření; skupina 2018 zůstává pod výslovným Q1 2018 omezením.

## Rozhodnutí pro web a data

- **GO pro vývoj webu nad původním archivem jako `original_unverified`:** už dnes bezpečně běží read-only API, denní záznamy označuje jako předběžné. Není třeba blokovat vývoj vzhledu a interakcí do dokončení historické forenziky.
- **GO pro zveřejnění časového pokrytí rekonstruovaných řádků pouze v jasně označeném interním preview**, nikoliv pro automaticky certifikované rekordy.
- **NO-GO pro přepsání produkční DB nebo zveřejnění datasetu jako `approved`:** ochrana Q1 2018, karanténa 92 366 operací, dobové jednotky/odvozeniny, rebuilding a verifikace denních souhrnů a skutečně testovaný DB rollback zůstávají nedokončené.
- **Žádný nový souborový/snapshot backup nebyl v tomto běhu vytvořen.** Read-only SQL a ledger úplnost nejsou náhradou fyzické konzistentní zálohy a restore testu.

## Opakování

Spouštěj blok A a B samostatně přes read-only Weather MCP. A je časově konzistentní jednotlivý SELECT; B je další MVCC snapshot a během živého přírůstku archivu se počty mohou měnit. Proto nesčítat čerstvé nezávislé dotazy bez kontroly timestampů; vyhodnocovat stejné hranice. Testovat kvalitu na úrovni veličiny a roku, nikoli pouze podle existence timestampu.

## Další akceptační brány před dataset=approved

1. Reprodukovatelný, konzistentní snapshot DB + ověřená fyzická obnova zálohy na oddělenou MariaDB.
2. Per-field QC provenance a historické jednotkové epochy, zejména Cumulus → WeeWX a 2013 numerický zlom větru; neověřené položky musí zůstat UNCLASSIFIED.
3. Samostatný schvalovací manifest a skutečně integračně otestovaný rollback, chráněný Q1 2018 a diagnostický rok 2021.
4. Znovusestavení a kontrola denních statistik, srážkových rekordů a odvozených veličin bez falešných hodnot.
5. Výslovné schválení konkrétního migračního manifestu/hashe před prod cutover.
