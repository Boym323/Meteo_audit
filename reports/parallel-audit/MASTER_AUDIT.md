# MASTER_AUDIT — Počasí Loučka, syntéza paralelních auditů 01–09

**Stav:** 2026-10-30 · **Větev:** `audit/master-synthesis-20261030` · **Cíl:** nezávislá syntéza bez zásahu do meteorologických dat.  
**Metoda:** čtení všech devíti reportů na jejich vlastních větvích, čtení metodiky repozitáře a cílené read-only kontroly přes Weather MCP v MariaDB. **Nic v archive ani jiných DB tabulkách nebylo tímto během upraveno.**  
**Rozsah:** historická měření cca 2009–2026, šest schémat. **Není** nezávisle dokončena fyzikální validace každého z ~1,68 mil. intervalů. Reporty jsou navíc pořízeny za chodu živé produkce, proto se její `COUNT(*)` v různých bězích mírně liší.

## 1. Vstupní reporty a jejich skutečný stav

Všech 9 souborů **existuje na samostatných auditních větvích**, nikoli v `main` k okamžiku syntézy. Odkazy jsou připnuté ke konkrétním commitům, aby bylo možné výstup reprodukovat a zabránit tiché změně důkazu.

| ID | Oblast | Zdrojový report | Rozsah dokončení |
|---|---|---|---|
| 01 | Srážky 2009–2013 | [01-historic-rain.md](https://github.com/Boym323/Meteo_audit/blob/37315a33c55e20acf946efd527244bb43c6ad561/reports/parallel-audit/01-historic-rain.md) | Historické jednotky a převody; fyzikální kalibrace neuzavřena |
| 02 | Srážky 2014–2026 | [02-rain-2014-2026.md](https://github.com/Boym323/Meteo_audit/blob/fa7d5f6fc97c9ee35a7c8be42f75678b37b8bbce/reports/parallel-audit/02-rain-2014-2026.md) | Měsíční screening, vybrané události; ne každý jednotlivý déšť |
| 03 | Intenzity `rainRate` | [03-rainrate.md](https://github.com/Boym323/Meteo_audit/blob/246beb08fbce0b790798ef685396115d3f04c4b5/reports/parallel-audit/03-rainrate.md) | Všechny roky a zdroje; sémantika driveru otevřená |
| 04 | WH1080 a mezery | [04-history-recovery.md](https://github.com/Boym323/Meteo_audit/blob/a6f1c5daa9b3328048c43e7c6f367bf93ea5e818/reports/parallel-audit/04-history-recovery.md) | 49 796 kandidátů posouzeno souhrnně; jednotlivě neodsouhlaseno |
| 05 | Teplota/vlhkost | [05-temperature-humidity.md](https://github.com/Boym323/Meteo_audit/blob/da2d2ef833fc89239d9af00b0c1e4da44c66f92d/reports/parallel-audit/05-temperature-humidity.md), [měsíční CSV](https://github.com/Boym323/Meteo_audit/blob/da2d2ef833fc89239d9af00b0c1e4da44c66f92d/reports/parallel-audit/05-temperature-humidity-monthly.csv) | Roční/měsíční QC, diagnostika odvozenin; nutná přesná meteorologická validace |
| 06 | Tlak | [06-pressure.md](https://github.com/Boym323/Meteo_audit/blob/69ccb729b3f26aecaacc21b712fd266b5130564d/reports/parallel-audit/06-pressure.md) | Důkladná diagnostika, kalibrace a reference neuzavřeny |
| 07 | Vítr | [07-wind.md](https://github.com/Boym323/Meteo_audit/blob/64f1c0bdc8abb03b53dc82f3eb053e0ec4449451/reports/parallel-audit/07-wind.md) | Jednotkové režimy a extrémy, náhrady neuzavřeny |
| 08 | Čas/provenience | [08-time-provenance.md](https://github.com/Boym323/Meteo_audit/blob/6a4dbaa5affdc660d3948c29ff7374957cbca52f/reports/parallel-audit/08-time-provenance.md) | Inventář 214 měsíců; řádky nejsou validovaný uptime |
| 09 | Další senzory | [09-additional-sensors.md](https://github.com/Boym323/Meteo_audit/blob/76fd1b90fe86dcf05b867406305748c149cc4b19/reports/parallel-audit/09-additional-sensors.md) | Screening UV, radiace, PM, blesků a půdy; servisní konfigurace chybí |

**Žádný z devíti vstupních reportů nechybí.** Jejich dílčí metodické limity jsou výše uvedeny; nelze je zaměnit za kompletní certifikaci měření.

## 2. Jednotný slovník a časový kontrakt

- `dateTime`: Unix epoch **UTC**, konec WeeWX archivního intervalu; měření reprezentuje `(dateTime - interval*60, dateTime]`. Občanský měsíc/datum používat s IANA `Europe/Prague` a předpočtenými epochovými hranicemi. Filtr: `dateTime > :start_epoch AND dateTime <= :end_epoch`, nikoli `[start,end)`.
- `interval`: **skutečná délka** v minutách, nikoli garantovaných 5. Počet řádků není totéž co dostupnost senzoru a nemusí odpovídat unikátním pětiminutovkám (nepravidelné/posunuté intervaly; i >100 % při hrubém čítači).
- `usUnits=16` METRIC: déšť `rain` cm, `rainRate` cm/h, vítr standardně km/h, teploty °C, tlaky hPa.
- `usUnits=17` METRICWX: standardně déšť mm, intenzita mm/h, vítr m/s; **historická číselná sémantika není vždy konformní!** Starší větrná data až do přechodu v dubnu 2013 jsou navzdory deklaraci numericky v km/h, nikoli m/s. U starých `old_weewx.rain` a `weewx_WH1080.rain` jde ve starších epochách o **stav/akumulaci čítače** s resety, nikoli 5min úhrn.
- `rain` hlavního archivu: intervalový úhrn jen po ověření epochy a zdroje. `rainRate`: uložená měřená/driverem odvozená intenzita; **není** totožná s intervalovým průměrem. Výpočet `rain_mm*60/interval_min` je výslovně **jiná analytická veličina**, ne automatická oprava `rainRate`.
- `pressure`: tlak na stanovišti; `barometer`: redukovaný tlak na hladinu moře; `altimeter`: výškoměrné nastavení. Vše hPa, výpočtové parametry/kalibrace vyžadují konfiguraci. Srovnávat stejné druhy tlaků.
- `outTemp`: °C, `outHumidity`: %, `dewpoint`: °C; odvozeniny se po opravě RH mohou stát zastaralými. `radiation`: měřené W/m² **pouze v prokazatelně instalované éře**; `maxSolarRad` je modelová veličina. `pm25_1` a `soilMoist1` vyžadují vlastní QC; `lightning_*` mapování je v roce 2026 podezřelé.
- `NULL` = neuvedeno/nezměřeno, číselná `0` = uložená nula (může být skutečná nebo chybná); chybějící timestamp = žádný archivní záznam. Vždy rozlišit od `NOT_INSTALLED`, `FROZEN`, `SUSPECTED` a `ESTIMATED`.
- Produkce, GW1000, stará kopie a WH1080 se často odvozují ze **stejné fyzické stanice**. Shoda těchto kopií **není nezávislé potvrzení**. Reference ČHMÚ denní SRA vyžadují správné mapování `DT`/`TIMEFUNC` a měřicího dne; samotné shodné datum nepotvrzuje pětiminutový impuls.

## 3. Deduplikace nálezů — jedna příčina, více reportů

| Klíč incidentu | Jednotný nález | Reporty | Stav |
|---|---|---|---|
| A-2009-2011-UTC-RESET | 328 oprav půlnočního resetu + historická diagnostika raw čítače | 01, 02, 03, 08 | **APPLIED** v pracovní DB; nepřidávat nový kandidát na stejné časy |
| A-2010-06 | 30 opravených chybných impulsů (161,76 mm) včetně binárních/časových resetů | 01, 02, 03 | **APPLIED**; konkrétní náhradní nuly mohou mít nižší fyzikální jistotu než identifikace artefaktu |
| A-2011-03-28 a A-2025-02-27 | Dva izolované falešné impulzy 30,72 + 30,5 mm | 01, 02, 03 | **APPLIED**; v roce 2025 i `rainRate`; produkci nechat nedotčenou |
| 2013-UNITS | Přechod raw `rain`, `rainRate`, numerické větrné jednotky v dubnu 2013 | 01, 03, 07, 08 | **Potvrzené režimy**, nikoli doklad vhodného násobku pro opravu |
| 2020-09 & 2022-08 | Výpadek a nový hardware/režim, déšť 0,2794/0,1 mm, změny větru a dalších senzorů | 02, 07, 08, 09 | Datové body potvrzené; přesné modely/config ke kontrole |
| 2021-07 | Rekonstrukce `rain` podle 10min ČHMÚ (~42,567 mm) a odvozené `rainRate` | 02, 03, 08 | **V archivu aplikováno**; fyzikální lokalita/odvozená intenzita stále nejistá |
| 2022-04-RH | Rekonstrukce venkovní RH a následná nekonzistence `dewpoint` | 05, 08 | **RH již změněna**, derivační QC otevřené |
| WH1080-MISSING | Kandidáti 49 796; 47 737 pressure-only, 1 301 frozen, 758 review | 04, 06, 08 | **Staged only**, nikdy automaticky celý řádek |
| 2026-03-SOURCE-DIVERGENCE | Od 8. 3. 2026 samostatná větev dat GW1000 vs rekonstrukce | 02, 06, 07, 09 | **Potvrzený mezizdrojový rozdíl**, příčina otevřená |
| GW2026-MAY-RAIN | 131,2 mm a 142,8 mm v GW1000 dne 12./16. 5. | 02, 03, 09 | Zdrojový artefakt; pracovní kopie má 0,5/0,1 mm; **nic nepřenášet zpět** |
| SENSORS-QC | Solar/UV, PM, lightning, soil: placebo nuly před montáží, výpadky a extrémy | 05, 07, 09 | QC a metadata, ne hromadné přepisování |

## 4. Rozpory a jejich nezávislé ověření

**R1 — fáze A v původním reportu versus aktuální DB.** `reports/2026-10-30-diagnostic-phase-a.md` a `proposals/phase-a-review-20261030.md` jsou historické read-only snímky, v nichž jsou návrhy `pending`. Aktuální live `reconstruction_changes` však má `applied`: 328 řádků v `rain-2009-2011-utc-midnight-reset-v1` (175,14 mm), 30 v `rain-phaseA-june2010-corrected-20261030-v1` (161,76 mm), 2 `rain` a 1 `rainRate` v `rain-phaseA-apply-20261030-v1` (61,22 mm). **Celkem 360 změněných timestampů `rain` a 398,12 mm**, jedna navazující intenzita. Zálohy mají počty 328/30/2 a opravený červen 2010 je nulový ve všech 30 cílových řádcích. Staré `pending` reporty **nesmí spustit opětovné apply**; oba uvedené návrhové batche Fáze A jsou už `cancelled`.

**R2 — „potvrzená chyba“ ≠ „potvrzená náhrada“.** Diagnóza 2010/2011 binárního čítače je silná, ale regionální denní ČHMÚ neposkytuje přesnou lokální pětiminutovou náhradu. Aplikované nuly uchovat jako **reconstructed/corrected-with-uncertainty**, nikoli bezvýhradně změřený déšť 0 mm. Bez samostatné validace neprovádět automatický rollback ani další opravu.

**R3 — vítr se nesmí normalizovat jen podle `usUnits=17`.** Report 04 obecně uvádí konverzi WH1080 ×3,6, report 07 dokazuje režim před dubnem 2013 již numericky km/h. Live porovnání `wh1080_missing_5min_candidates_20261030` s původním WH1080: v roce 2011 `windSpeed_kmh / raw_speed = 1`; v roce 2019 = **3,6**. Existující staging tedy zachovává historickou výjimku. Neprovádět opakovaný převod.

**R4 — květnové srážky 2026 nelze porovnávat bez pokrytí.** Zdroj GW1000 měl 12. 5. na porovnávaných timestampech 131,2 mm a 16. 5. 142,8 mm; rekonstrukce 0,5/0,1 mm. Rozdíl 273,4 mm je dán dvěma řádky, ale **celý měsíční rozdíl** má i jiný počet/NULL řádky; nesčítat rozdíly jako úplný lokální úhrn.

**R5 — `rainRate` nulované v produkci i potenciální ztráty v pracovní rekonstrukci.** Produkce vs GW1000: 2019–2025 **36 520** kladných zdrojových intenzit proti produkční 0; auditní batch `rainrate-restore-2009-2025-v1` obsahuje **58 936 applied** změn ve pracovní DB. V jiných dobách však nebyly všechny intenzity zachovány: cílený nový live JOIN našel **13 řádků v roce 2023 a 15 v roce 2024**, kde `GW1000.rainRate > 5 cm/h` a `reconstruction.rainRate = 0`. To je **28 kandidátů revize**, nikoli oprávnění zkopírovat hodnoty bez meteorologického důkazu.

**R6 — duben 2022: RH versus její odvozeniny.** Live SQL s Magnusovou diagnostickou aproximací pro UTC 2022-04-01 až 2022-05-01 našlo **1 077** řádků s `|dewpoint - diagnostic_dewpoint| > 2 °C` (z 7 068 s vypočitatelnou hodnotou), maximum 13,51 °C. Nevyvozovat automaticky, že přesná náhrada je Magnusova hodnota: použít dobovou verzi WeeWX algoritmu, vstupní T/RH a zachovat derivation metadata.

**R7 — 2026 tlak není jediný konstantní offset.** Live párové srpnové statistiky našly `AVG(reconstruction.barometer - GW1000.barometer) ≈ -3,9 hPa` a rozdíl `pressure` ≈ -12,7 hPa. Známé změny offsetu vyžadují samostatné ověření tlaku na stanovišti, nadmořské výšky, QFF/QNH a konfigurace. Převzít GW1000 jako automaticky „správný“ zdroj je chybné.

**R8 — před instalací nejsou nuly měřením.** WH1080 historicky obsahuje nuly UV/radiace/soil i tehdy, když neexistoval fyzický senzor. `maxSolarRad` je model. Live 2026: **179** vyplněných `lightning_noise_count` je shodných se strike a `lightning_disturber_count` obsahuje hodnoty v rozsahu Unix epoch; vysoká pravděpodobnost mapovací chyby. Rozhodovat o opravě kódu, nikoli domýšlet náhradní meteorologické hodnoty.

**R9 — oddělené časové značky nejsou nezávislá měření.** Z původních 70 746 raw WH1080 časových záznamů bez shody na 5min mřížce vzniklo 49 796 **jen vybraných staging kandidátů**: ostatní nepřevádět automaticky. `pocasi-loucka.eu_old` má mnoho timestampů posunutých o sekundy/minuty. Zarovnání bez kontroly `interval` a sousedů může způsobit duplicitní či přesunuté měření.

## 5. Stav datových zásahů a bezpečné deduplikace

Aktuální live kontrola (2026-10-30) z `loucka_reconstruction`:
- `archive`: **1 679 802** řádků; `rain` v lokálním červenci 2021 ~**42,567 mm**.
- Zálohy Fáze A: `rain_daily_reset_backup_2009_2011_v1` **328**; `rain_phase_a_201006_backup_20261030_v1` **30**; `rain_phase_a_backup_20261030_v1` **2**.
- `reconstruction_changes` audit: tři nové Fáze A balíčky aplikované (328 + 30 + 2 `rain`, plus 1 `rainRate`); obnovení `rainRate` 58 936 aplikovaných změn.
- `wh1080_missing_5min_candidates_20261030`: **49 796**, statusy **47 737 pressure_only_review**, **1 301 frozen_sensor_review**, **758 needs_validation**. Dosavadní `archive` nebyl touto syntézou modifikován.

Každý nový návrh musí testovat kolize s `reconstruction_changes`, historickou zálohou a aktuální `archive`. Neinterpretovat staré dokumentační `pending` statusy jako živý stav.

## 6. Jistota: diagnostika versus konkrétní oprava

**Potvrzené datové stavy (HIGH, bez dalšího zápisu):** půlnoční resety a současný stav Fáze A; zásadní změna raw převodu 2013; historické větrné měřítko; systémové nuly produkční `rainRate`; 49 796 staging položek bez kolizí; 1 077 diagnostických nesouladů rosného bodu; 28 zdrojových špiček ztracených v rekonstrukci; GW1000 extrémy 2026; divergující tlak 2026; shodnost lightning_noise/strike 2026.

**Pravděpodobné poruchy s neznámou přesnou náhradou (MEDIUM):** 2013 a 2011 zamrznutí; historická podměřená RH 2015–2019; chybné tlakové hodnoty WH1080 v části mezer; PM saturované 2024; extrémy UV/radiace 2026; dlouhé nuly půdy při platném signálu; 29 případů `windGust < windSpeed`.

**Nepotvrzené hypotézy (LOW / REQUIRES SOURCE):** násobit staré `rain` ×10 nebo ×2; automaticky doplnit `pressure` do 47 737 mezer; přebírat 758 úplných řádků; určit přesný firmware z kvantování; přičíst denní ČHMÚ SRA přesný pětiminutový impuls; opravit 2026 barometr konstantním offsetem; globálně odvodit `rainRate` z `rain × 12`. **Žádná z nich není schválenou hodnotou pro UPDATE.**

Podrobný registr: [CONFIRMED_CANDIDATES.md](CONFIRMED_CANDIDATES.md). V něm „potvrzený kandidát“ znamená **potvrzený problém ke zpracování**, nikoli automaticky potvrzenou náhradní hodnotu.

## 7. Prioritní plán, oddělený od vykonání

| Priorita | Úloha | Rozsah | Gate před změnou |
|---|---|---|---|
| **P0** | Zabránit duplicitní aplikaci Fáze A, zavést verifikované identity a QC u opravených řádků | 360 timestampů a jejich audit | Chráněná provenience a schválené QC, **bez nového** rain UPDATE |
| **P0** | Zkontrolovat `dewpoint` po RH 2022-04 a možné `heatindex`/`appTemp` | 1 077 diagnostických neshod | Dobová formule, snapshot, schválení per-variable kandidátů |
| **P0** | Prověřit 28 rekonstruovaných nul `rainRate` proti zdrojovým >50 mm/h | 2023:13, 2024:15 | Meteo event + původ intenzity + provenance; neslepě kopírovat |
| **P0** | Opravit interpretaci lightning noise/disturber v mapperu a QC | 179 shodných noise hodnot, epoch-like disturber | Raw payload JSON, test mapování, změna kódu v samostatném PR |
| **P1** | Validovat pressure-only WH1080 | 47 737 kandidátů (28 sousedních >2 hPa podle reportu 04) | Ověřená `pressure`/barometer sémantika, holdout časové testy, schválení jednotlivých veličin |
| **P1** | Rozřešit jednotkový přechod 2013 a rainRate kontext | 2009–2013 | Originální driver/konfigurace + externí měsíční ČHMÚ |
| **P1** | 758 WH1080 kandidátů a 1 301 frozen, omezení importu | 2009, 2011, 2019, 2020 | Antifreeze, 2 nezávislé kontroly, bez automatického full-row importu |
| **P1** | Časové zarovnání 2014–2018 a senzory 2022 | ~70 tis. WH bez grid shody, různé datum změn | Jeden interval = jeden zdrojový observation ID; DST regresní test |
| **P1** | Tlaková divergence březen–říjen 2026 | tisíce rozdílných bodů | Konfigurace QFE/QFF/QNH a nezávislá reference, bez konstantního přičtení |
| **P1** | PM, UV a půda, detekce saturation/frozen | PM 2024, solar 2026, soil 2024–25 | Servis a hardware data, validované QC příznaky |
| **P2** | Homogenizace staré RH, větru, teploty podle čidla/epochy | 2009–2022 | Chybějící zdroj a nezávislé reference, explicitní intervalová nejistota |

Návrhy kandidátů **nejsou** příkazy k zápisu; provádí se teprve v samostatném schváleném apply/rollback workflow.

## 8. Povinné SQL kontroly a testy před každou opravou

1. **Čas:** identita `target_time` jako UTC epoch, `interval`, hranice `(start,end]`, CET/CEST, datum a hodina ve dvojznačné podzimní hodině.
2. **Provenience:** `source_db`, `source_table`, `source_time`, raw hodnota, kvalita čidla, hash původního exportu; nezávislost druhé reference doložit, ne předpokládat.
3. **Předpodmínka:** aktuální `archive` hodnota je přesně očekávaný `old_value` (`<=>` pro `NULL`), jednotky a délka intervalu sedí; žádná kolize s dřívějším aplikovaným auditním záznamem.
4. **Bez duplicit:** počty kandidátů se rovnají počtu **unikátních dvojic (`target_time`, `variable`)**; zdrojový čas nesmí mapovat na více cílů; pro INSERT musí být cílový timestamp volný.
5. **Výpočet a fyzika:** převody cm/mm a m/s/km/h podle epochy; `pressure` ≠ `barometer`; `rainRate` ≠ `rain×12`; `dewpoint` podle validované formule; `NULL` ≠ `0`; hodnoty a jejich sousedé fyzikálně přiměřené.
6. **Referenční důkaz:** krátké sousední okno, druhý nezávislý senzor nebo oficiální zdroj, správný čas agregace; jasně oddělit confidence diagnózy a confidence náhrady.
7. **Záloha:** neměnný before-image v samostatné pracovní tabulce, SHA-256 exportu a manifest s SQL hashem/commitem; produkční/historické DB jen SELECT.
8. **Transakce a fail-closed:** SQL `START TRANSACTION`, abort při rozdílném počtu/old values/schema; nikdy plošný UPDATE bez klíče. Po COMMIT ověřit přesně zasažené `dateTime`, `variable` a součty.
9. **Audit a rollback:** append-only audit změn, idempotentní batch ID, důvod, zdroj, QC, schvalující, oddělený rollback s CAS podmínkou `current=new_value`.
10. **Regrese:** žádná změna mimo schválený čas/veličinu, zachovat červenec 2021 42,567 mm a Fázi A, nulové zápisy do `pocasi-loucka.eu` i čtyř zdrojových archivů; kontrola přechodů CET/CEST a porovnání před/po.

Příklady konkrétních **read-only** kontrol: [MASTER_QC_READONLY.sql](MASTER_QC_READONLY.sql). Spouštět na `loucka_reconstruction` po krátkých časových úsecích; některé celoroční JOINy historicky narážejí na `max_statement_time`.

## 9. Návrh datového modelu kvality a původu pro budoucí web

Neuvádět kvalitu pouze na úrovni celého řádku. Jeden interval může mít platnou teplotu, neplatný vítr a tlak pouze jako odhad.

**Doporučené entity (návrh schématu, NIC nevytvořeno):**
- `observation_source`: `source_id, station_id, physical_sensor_id, hardware_model, config_version, calibration_id, source_db, source_table, unit_epoch_id, installed_from_utc, installed_to_utc, evidence_uri`.
- `observation_raw_ref`: `raw_ref_id, source_id, source_time_utc, interval_start_utc, interval_end_utc, variable, raw_value, raw_unit, payload_sha256, record_sha256, imported_at`. Původní hodnotu neměnit.
- `measurement_qc`: `(target_time_utc, variable, version)`, `raw_ref_id`, `stored_value`, `display_value`, `canonical_unit`, `quality_status`, `quality_flags[]`, `diagnosis_confidence`, `replacement_confidence`, `algorithm_version`, `validated_at`, `reviewer`, `evidence_links`.
- `reconstruction_manifest`: `batch_id, created_at, approved_at, applied_at, rollback_at, sql_sha256, before_export_sha256, after_export_sha256, source_commit, row_count_expected, row_count_actual, previous_batch_id`. Vazba na existující `reconstruction_changes`, nikoli jeho přepis.
- `sensor_epoch`: časově omezená sémantika jednotek, ovladače a přesnosti, včetně výjimek 2009–2013 a 2020/2022/2026.

**Stavy:** `MEASURED_VALID`, `MEASURED_SUSPECT`, `NOT_INSTALLED`, `MISSING_ROW`, `MISSING_VALUE`, `INVALID_SENSOR`, `FROZEN`, `ESTIMATED_EXTERNAL`, `DERIVED`, `CORRECTED`, `UNRESOLVED`. Příznaky zvlášť: `COUNTER_RESET`, `SOURCE_DIVERGENCE`, `UNIT_EPOCH_UNRESOLVED`, `SATURATED`, `DERIVED_STALE`, `CLOCK_SHIFT`, `BAD_MAPPING`.

**Frontend:** uvádět původ, kvalitu a stav měření; ve statistických grafech odlišovat plné měřené body, odhad a mezery. Pro extrémy a klimatologické trendy uvádět pokrytí; obecně nepospojovat dlouhé chybějící bloky lineární interpolací. Podmínka publikování: QC per-variable, dohledatelný `raw_ref` a `calibration/version`.

## 10. Vykonávací rozhodnutí

**Závěr: žádná nová náhradní meteorologická hodnota není touto syntézou schválena k automatickému zápisu.** Potvrzené incidenty jsou evidovány v registru; některé vyžadují přednostně opravu mapperu nebo QC prezentační vrstvy, nikoli zásah do `archive`. Část Fáze A je již aplikována a nesmí být použita jako pending kandidát. Neprovádět žádný merge do `main` bez výslovného pokynu.

**Otevřené podklady:** historické `weewx.conf`/driver verze, datalogger a servisní protokoly, nezávislé meteorologické reference správně časově zarovnané, specifikace zpracování 2026 lightning/WS80. Tyto chybějící důkazy jsou skutečné limity, nikoli důvod vymýšlet korekce.
