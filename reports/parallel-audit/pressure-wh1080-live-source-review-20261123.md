# C004 — přímý read-only přezkum WH1080 tlaků (2016–2018)

**Datum:** 23. 11. 2026 · **Zdroj:** přímé SQL SELECT přes existující Weather_MCP konektor k `lo-infra-db-mariadb01`.
**Rozsah:** `loucka_reconstruction.archive` vs `weewx_WH1080.archive`, `old_weewx.archive` a historická databázová kopie `pocasi-loucka.eu_GW1000.archive` (historický obsah kopie **není fyzicky GW1000 měření** před jeho instalací).
**Bez SQL změn:** žádné GRANT, SQL účty, CREATE, INSERT, UPDATE, DELETE ani APPLY/ROLLBACK. Produkční archiv a WeeWX v jiném LXC nedotčeny.
**Status:** SOURCE_ROW_INSPECTED / REPLACEMENT_NOT_VALIDATED / NO_GO_APPLY.

## Proč tento audit nevyžadoval nové granty

LXC `loucka_web_ro@192.168.0.131` nemá SELECT nad zdrojovými archivními schématy. To nebrání **tomuto samostatnému** auditu: připojený Weather_MCP konektor k MariaDB dovoluje read-only SELECT i nad těmito zdrojovými schématy; neumožňuje však spouštět `GRANT` nebo přidávat oprávnění LXC účtu. Tedy **bez změny práv** lze ověřovat konkrétní hodnoty přímo touto cestou, ale skript PR #89 stále nemůže číst tyto tabulky s LXC `loucka_web_ro`.

## Souhrn skutečně ověřených SQL zdrojových řádků

| UTC rok | target pressure NULL | Přímý WH1080 pressure | WH identický s old_weewx | Překryv WH s GW-copy | WH vs GW-copy rozdíl ≤0,5 hPa | WH vs GW-copy rozdíl >2 hPa |
|---|---:|---:|---:|---:|---:|---:|
| 2016 | 15 727 | 3 764 | 3 764 | 3 132 | 2 385 | 80 |
| 2017 | 28 287 | 25 189 | 25 189 | 11 660 | 4 511 | 370 |
| 2018 | 46 542 | 46 121 | 46 121 | 6 582 | 2 347 | 24 |
| **Celkem** | **90 556** | **75 074** | **75 074** | **21 374** | **9 243** | **474** |

**Kritické pravidlo:** WH1080 a old_weewx jsou na těchto 75 074 timestampích přesně stejná kopie; jejich shoda neposkytuje nezávislé fyzikální ověření. Také GW1000-named kopie obsahuje historické přenesené záznamy, nikoli nezávislé měření pozdější brány před instalací.

Ve společných řádcích, kde je pracovní tlak **vyplněný**, se `WH1080.pressure − reconstruction.pressure` v letech 2016/17/18 liší v průměru o **−0,724 / −0,538 / −0,601 hPa** (SD 0,452 / 0,496 / 0,493 hPa). To indikuje velmi podobnou datovou linii, nikoli ověřenou správnost.

Z chybějících tlaků s WH hodnotou má lokální `barometer − WH1080.pressure` rozumný rozsah 35–70 hPa u 3 764 / 25 185 / 36 041 řádků, ale tato vnitřní konzistence neprokazuje nezávislou kalibraci. V části 2018 chybí také `barometer`, takže vnitřní kontrola není možná.

## První konkrétní source-level předobrazy (NIKOLIV schválený manifest)

Pro všechny níže uvedené časové body je `loucka_reconstruction.archive.pressure IS NULL`, `usUnits=16`; WH1080 se přesně rovná old_weewx. Uvedené hodnoty jsou **jen kandidátní zdroj**, nikoli povolená náhrada.

| UTC timestamp | WH1080 / old_weewx (hPa) | GW historická kopie (hPa) | `barometer` prac. archivu (hPa) | Poznámka |
|---|---:|---:|---:|---|
| 2016-01-04 09:30 | 938,9000 | 939,3158 | 992,1872 | Zdrojový rozdíl 0,416 hPa |
| 2016-01-04 09:35 | 938,8000 | 939,2158 | 992,0815 | Navazující interval |
| 2016-09-18 02:55 | 947,9167 | 947,4196 | 999,5521 | `outTemp` NULL |
| 2016-09-18 03:00 | 947,8500 | 947,3780 | 999,5082 | `outTemp` NULL |
| 2017-01-01 16:30 | 952,8500 | 952,7660 | 1005,8180 | Zdrojový rozdíl 0,084 hPa |
| 2017-01-01 16:35 | 952,8167 | 952,7860 | 1005,8243 | Navazující interval |
| 2017-01-01 16:40 | 952,8167 | 952,7693 | 1005,8067 | Navazující interval |
| 2017-01-01 16:50 | 952,7833 | 952,7584 | 1005,9066 | Navazující interval |
| 2018-01-13 17:10 | 955,8000 | 955,3098 | 1008,2386 | Zdrojový rozdíl 0,490 hPa |
| 2018-01-13 17:15 | 955,8500 | 955,3715 | 1008,3045 | Navazující interval |
| 2018-01-13 17:20 | 955,8167 | 955,3381 | 1008,2694 | Navazující interval |
| 2018-01-13 17:30 | 955,7500 | 955,2532 | 1008,1793 | Navazující interval |

## Vztah k opravdu nezávislé ČHMÚ validaci PR #89

[PR #89](../pressure-chmi-numeric-2009-2026.md) vyčíslil na hodinových datech ČHMÚ Holešov pro rok 2018 medián rozdílu *výškově přepočtený pracovní pressure − ČHMÚ P* **−22,84 hPa** (MAD 1,57 hPa). WH tlak se v tomtéž roce na společných nenulových pracovních záznamech liší od pracovního průměrně asi o −0,60 hPa, a tak jeho prosté převzetí **může zachovat stejný velký problém kalibrace**. Zde uvedená čísla nejsou přímým párováním WH s jednotlivými hodinami ČHMÚ; proto **nelze tvrdit**, že těchto 12 konkrétních řádků má oproti ČHMÚ odchylku −23 hPa.

Srovnání ČHMÚ z PR #89 má surová CSV lokálně na LXC, nikoliv v GitHub repozitáři; zdejší samostatný read-only databázový konektor má WH řádky, ale v tomto prostředí nemá místní ČHMÚ cache. Bez přesného hodinového párování WH a ČHMÚ nelze schválit konkrétní numerické náhrady.

**Závěr:** máme hodnoty, ne však ještě prokazatelně správné hodnoty. `NO_GO_APPLY`, žádný sériový `COALESCE` ani pevná offset korekce +22 hPa.

## Následující bezpečný krok

1. Přes tento read-only konektor lze dále exportovat agregáty, reprezentativní řádky a předobrazy bez nového `GRANT`. Nezakládat SQL účty.
2. Vhodné je spojit WH source rows a ČHMÚ hodinové P/P_hm v **jednom izolovaném výpočtu** s dokumentovaným vstupem z PR #89 (a konzistentními UTC timestampy), ideálně před spuštěním agregovat hodinové WH průměry z 5min intervalů. Zohlednit rozdílnou podporu hodinových SYNOP a 5min archivu.
3. Ověřit případnou změnu offsetu po jednotlivých senzorových epochách a rozdíly `pressure` vs `barometer`; měřený zdroj a případný modelovaný přepočet musíme rozlišit.
4. Teprve poté sestavit jednotlivé `target_time, expected_old=NULL, proposed_new, source_database, source_time, unit_epoch, confidence` pro kandidáty s vysokou důvěrou. Pouhé příklady výše **nejsou** takovým schváleným manifestem.
5. Jakýkoli UPDATE/INSERT až po samostatném schválení přesného batch ID, SHA-256, jednotlivých old/new a podepsaného receipt vlastníkem. Produkční DB a denní tabulky mimo rozsah.

Všechny hodnoty tohoto reportu jsou z čtecích SQL spojení na přesných UTC timestampích. Ověřování bylo provedeno bez databázových změn.
