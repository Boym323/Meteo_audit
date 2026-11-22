# Rekonstrukce v1: původ 10 399 doplněných timestampů

**Datum čtení:** 22. 11. 2026; živá MariaDB, read-only SELECT, bez operací nad původními nebo pracovními hodnotami. Rozšíření [kontroly úplnosti source/target](2026-11-22-v1-source-target-parity-checkpoint.md).

## Zjištěné typy původního INSERT

| Kategorie podle history reason (diagnostická) | Počet timestampů |
|---|---:|
| `insert: ESTIMATED` | **10 101** |
| `insert: RESTORED` | **290** |
| `insert: RECOVERED_SOURCE` | **1** |
| Dočasný bootstrap `insert: Insert missing archive grid` | **7** |
| **Celkem** | **10 399** |

Všech **7** bootstrap timestampů má navazující `update: Spatial estimate:` u srážek. Z 10 101 původně odhadnutých řádků má navíc **292** následný odhad RH; žádný z 290 původně RESTORED řádků nemá takový `outHumidity` update. **303** z cílových timestampů navíc má více než jednu událost v `reconstruction_changes`. Bez historie není žádný. Klasifikace počátečních INSERT událostí je jednoznačná pro všech 10 399 podle uvedených předpon, ale založená na historickém volném textu.

Pouhý součet označení tedy **nesmí** být vykládán jako 10 399 nezávisle naměřených řádků. Včetně 7 dočasných bootstrapů později nahrazených prostorovým odhadem obsahuje nejméně **10 108** těchto řádků nějakou odhadnutou veličinu. Ostatních **291** má prvotní označení RESTORED/RECOVERED_SOURCE, nikoli automaticky nezávisle ověřenou hodnotu všech 80 sloupců.

## Publikační rozhodnutí

- **NE**: povýšit 10 399 doplňků na `MEASURED` pouze podle existence řádku nebo času. Ani RESTORED neznamená automatickou fyzickou nezávislou validaci; kopie starých archivů mohou mít společný původ.
- **NE**: použít `ESTIMATED` nebo bootstrap jako kandidáta pro definitivní historický extrém, denní rekord nebo řadu s neoznačenou interpolací.
- **ANO**: v interním read-only historickém preview zobrazit kvalitu po **(timestamp,variable)**, explicitní intervalovou mezeru a nejistotu, se zdroji/změnami; nikdy nepřevést neověřené `NULL` na 0.
- **ANO**: nad původním datasetem nadále rozvíjet web, který rekordy správně označuje jako `preliminary` a `unverified_original`.

## Co je nutné před certifikací

1. Převést volnotextové `reason` na verzovaný **per-field** provenance registry s odkazem na source/payload a číslo schválení (issue #25). Při více událostech vyhodnotit konečnou hodnotu každé veličiny, ne pouze první INSERT.
2. Zrevidovat fyzický/výpočtový původ 10 108 odhadových timestampů, primárně chráněné Q1 2018 a sedm prostorově dosazovaných srážek 2021.
3. Rebuild denních souhrnů z množiny schválených veličin a ověřit výstupy před produkční migrací, s plným rollbackem (#26).

Reprodukce: [`sql/readonly/reconstruction_v1_target_only_origin.sql`](../sql/readonly/reconstruction_v1_target_only_origin.sql). Pozor: historické texty `reason` nejsou kanonickým kódem; výsledek je screening, ne publish-ready hodnotový manifest.
