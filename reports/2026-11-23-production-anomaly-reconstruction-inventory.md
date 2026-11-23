# Produkční archiv Počasí Loučka: inventura anomálií pro rekonstrukci

**Datum auditu:** 23. 11. 2026, pevný UTC řez **06:35:00 / `1795415700`**.  
**Zdroj:** skutečná MariaDB `pocasi-loucka.eu.archive` (80 sloupců, usUnits=16). Porovnáno s `loucka_reconstruction.archive`, `pocasi-loucka.eu_old`, `old_weewx`, `weewx_WH1080` a `pocasi-loucka.eu_GW1000` podle konkrétního pravidla.  
**Reprodukovatelný screening:** [`sql/readonly/production_anomaly_inventory_20261123.sql`](../sql/readonly/production_anomaly_inventory_20261123.sql), 18 samostatných read-only SELECTů A–R, včetně WH placeholderů, teplot, RH, srážek a mapování senzorů.

**ZÁSADNÍ:** Nejde o seznam 100% certifikovaných chybných měření. Jde o úplný inventář *nálezů daných definovanými pravidly*, nikoli o vyřešení každé možné latentní chyby čidla. Anomální bod je kandidát do QC, **není to automatický UPDATE**. Bez originálních payloadů nelze určit každou historickou závadu. Součty kategorií se překrývají, proto je nesčítat na jediné číslo k přepsání.

## 1. Invarianty zdroje a kontrola rekonstrukce

| Kontrola | Zjištění |
|---|---:|
| Produkční `archive` | **1 686 896** řádků |
| UTC první / poslední | `1238345100` (2009-03-29) / `1795415700` (2026-11-23 06:35 UTC) |
| Unikátní `dateTime` | **1 686 896**, žádná duplicita klíče |
| `usUnits` | **16** u všech zkoumaných produkčních řádků |
| `dateTime % 300 != 0` | **390**, všechny 2026 |
| `interval != 5` | **2 097**; **2 090× interval=6** v období 2014–2019, další 30/10/40/55/75 minut |
| Kolize při zaokrouhlení na nejbližších 300 s (2026) | **43** nominálních slotů po dvou záznamech |
| Teoretických slotů mezi první a poslední epochou včetně | **1 856 903** |
| Orientační nezastoupené nominální 5min sloty | **170 050** = teoretické sloty minus počet různých nejbližších slotů; nevyjadřuje 170 050 nezávisle obnovitelných měření |

Ověřená produkce vs rekonstrukce na 1 686 896 překryvných timestampů k této hranici: `outTemp` **47**, `outHumidity` **20 422**, `rain` **2 201**, `rainRate` **59 595** rozdílů. Ostatních 75 neklíčových sloupců bylo v předchozím úplném 80sloupcovém auditu beze změny, včetně těch nyní nově nalezených chybných čidel. V cíli je navíc historických 10 399 řádků a žádné schválení převést je všechny do `MEASURED` neexistuje.

## 2. Matice anomálií a rozhodnutí

| Priorita | Pole / období | Přesný nález (produkce) | Stav vůči rekonstrukci | Pravidlo |
|---|---|---|---|---|
| **P0** | `rainRate`, 2009–2025 | **1 592 925 nulových záznamů**, přesto **37 611** řádků s `rain>0` a `rainRate=0`; první kladný rate až **2026-03-21 06:40 UTC** | část historického rainRate rekonstruována, ale nezaručuje původní senzorový vzorec | **HOLD** původní rate jako neověřený/nedochovaný, žádný auto-restore |
| **P0** | `rain`, červenec 2021 | produkční intervalové úhrny **701,015 mm** vs pracovní rekonstrukce **42,567 mm**; přibližně 1 568 společných záznamů má jinou `rain` | opravy provedeny, ale 146 záznamů `rain=0` nesedí s poslední `applied` auditovanou `NULL` | **AUDIT_CONFLICT / HOLD** před certifikací, nejdříve receipt |
| **P0** | `lightning_disturber_count`, 2026 | **54 154** epoch-like hodnot namísto počtu; průběžně přibývají | stejné hodnoty v rekonstrukci; web nyní pole blokuje | **SENSOR_MAPPING_ERROR**, zjistit aktivní driver/payload |
| **P0** | `lightning_noise_count`, 2026 | **179/179** nenulově přítomných hodnot shodných se strike count | stejné hodnoty v rekonstrukci; web nyní pole blokuje | **HOLD** do ověření mapperu |
| **P0** | `dewpoint` po opravách RH, 2022-04 | původní dewpoint je pro originální RH matematicky konzistentní; **1 077** hodnot v rekonstrukci odpovídá *staré*, ne nově opravené RH | nová odvozenina nespočtena | **RECALCULATE_REVIEW**, jen s doloženou dobovou metodou |
| **P1** | `outTemp`, 2013 | **5 659 NULL**; WH1080 má **5 651** numerických kandidátů (12 nulových), kopie staré produkce 1 946 | rekonstrukce vyplnila **1** | **SOURCE_REVIEW** po čase/jednotkách, bez plošného kopírování |
| **P1** | `outHumidity`, 2018 | **35 892 NULL**; WH1080 má **6 013**, z nich **418 přesně 10 %** | 1 374 NULL doplněno v rekonstrukci | **SOURCE_REVIEW**, zdroj WH má floor hodnoty |
| **P1** | `outHumidity`, 2019 | **19 721 NULL**; WH1080 má **7 459**, z nich 297 přesně 10 % a **6 nad 100 %** | 4 826 NULL doplněno | **SOURCE_REVIEW**, 6 hodnot invalid; kopie neprokazují nezávislost |
| **P1** | `outHumidity` + `pressure`, 2022 | **44 516 NULL RH**, z toho **44 509** před skutečnou GW1000 epochou (a současně NULL pressure), ve GW1000 zdroji **0** náhradních RH | RH v 2 874 těchto původně NULL řádků doplněna | **HOLD / ESTIMATE_ONLY_WITH_QC**, původní RH většinou nedochována |
| **P1** | `rain`, 2020 | **8 126 NULL**; ve WH1080 `rain` jen u **4** shodných timestampů, zároveň **8 103** má chybějící vítr | pouze 2 NULL doplněny | **HOLD**, žádné `NULL → 0` bez důkazu sucha |
| **P1** | `outHumidity=10`, 2015–2018 | **1 500** přesných 10% hodnot (349/437/263/451), některé při 25–35 °C; **všech 1 500** zůstává v rekonstrukci | historické WH kopie opakují 10 % | **SENSOR_CLIP_REVIEW**, nikoli automaticky 10 → jiná hodnota |
| **P1** | `outTemp=4.25`, 2020–2022 | 499/539/185 = **1 223** přesných hodnot; dlouhé sekvence v listopadu 2020 až **62 po sobě jdoucích 5min bodů** | ve staré produkční kopii se 4,25 opakuje; WH se v roce 2020 často liší | **FROZEN_SENSOR_REVIEW** |
| **P1** | `extraTemp1/2`, 2022/2024 | **790** řádků mimo −50 až +80 °C; 776 v září 2022 v `extraTemp2=80–99`; **14** v únoru 2024 `extraTemp2=822.4`, 2 extrémy `extraTemp1>80` | totožné s rekonstrukcí; 2024 GW1000 `extraTemp2=NULL` | **BAD_CHANNEL_OR_MAPPING_REVIEW**; 2022 rozsah je „humidity-like“, ne prokázaná RH |
| **P1** | `soilTemp5/6`, 2026 | **6** záznamů mimo −50 až +80 °C, cca −58,75 až −61,75 °C | stejné v rekonstrukci | **SENSOR_ERROR_REVIEW**, možný sentinel |
| **P1** | `windSpeed`, 2014–2019 | **15** pětiminutových skoků přes 60 km/h; **11** řádků má průměrný vítr o >15 km/h vyšší než náraz (např. 2016-03-01 18:20 UTC: 78,48 vs 0) | stejné v rekonstrukci | **SPIKE_OR_MAPPING_REVIEW** |
| **P1** | `barometer`, 2013–2019 | **9** skoků >8 hPa za 5 min, maximum **25,4 hPa** 2019-04-26 14:45 UTC | stejné v rekonstrukci | **PRESSURE_TRANSITION_REVIEW** |
| **P1** | `outHumidity`, 2015/2019/2021 | **8** sousedních změn >50 procentních bodů, 2021-11-29 opakovaně 19–95 % | stejné v rekonstrukci | **SHORT_SPIKE_REVIEW** |
| **P1** | `radiation`, 2024/2026 | **3** hodnoty >1 500 W/m², maximum **2 248,85** (2026-08-23 06:10 UTC); celkem **10** hodnot >2× výpočtový `maxSolarRad` v letech 2023/25/26 | stejné v rekonstrukci | **SOLAR_SENSOR_REVIEW**, prah modelu není fyzikální certifikace |
| **P1** | `rain`, různá léta | **100** intervalů nad 5 mm/5min, z nich **11 ≥10 mm**; největší 2011-03-28 **30,72 mm**, 2025-02-27 **30,5 mm** | některé staré špičky v rekonstrukci NULL, 2025 30,5 mm → 0; jiné ponechány | **EXTREME_RAIN_REVIEW**, validovat po intervalech, ne plošný limit |
| **P1** | časová řada, 2009–2026 | **44** mezer ≥24 h, **5** ≥7 dní, nejdelší 198,56 dne (2011–2012); další v 2014/16/17 | většina bez nezávisle validního zdroje | **GAP_LEDGER**, obnovovat jednotlivé veličiny, ne fiktivní úplné řádky |
| **P2** | `dateTime`, 2026 | **390** timestampů mimo 5min mřížku a **43** kolizí po zaokrouhlení; 277 s reziduem 240s, 43 s 60s, 39 se 180s, 31 se 120s | stejné v rekonstrukci | **NO_ROUNDING**, zachovat raw timestamp, vysvětlit timer |
| **P2** | `interval`, 2014–2019 | **2 090× 6 min**, 3× 30 min a 4 další nestandardní intervaly 2024/25 | stejné v rekonstrukci | **UNIT/TIME_EPOCH_REVIEW**, ne automatická chyba |
| **P2** | vítr, duben 2013 | stará kopie vs produkce březen numericky 4 801/4 802 cca ×1, květen–červenec 6 259/6 259 cca ×3,6 | rekonstruovaný vítr nezměněn | **UNIT_EPOCH_REVIEW**; důkaz změny numerického měřítka, nikoli data WeeWX instalace |

### Nejdůležitější blokace importu nulových placeholderů

U časových mezer, které nemají žádné produkční řádky, není shodná historická značka důkazem platné fyzikální hodnoty:

| Mezera | `weewx_WH1080.archive` řádků | Falešně nulových venkovních teplot | Co je případně k přezkoumání |
|---|---:|---:|---|
| 2011-08 až 2012-03 | 3 560 | **3 264** | zbylých 296 s RH/tlakem, vnitřní senzor; nezávislý původ chybí |
| 2016 leden–únor | 5 344 | **5 343** | tlak a vnitřní teplota; 0 timestampů na přesné 5min mřížce |
| 2017 leden | 2 261 | **2 261** | tlak a vnitřní teplota |
| 2017 květen | 4 810 | **4 810** | tlak a vnitřní teplota |
| 2014 červen–červenec | 0 | 0 | v porovnávaných zdrojích nezachována samotná data |

Tyto nulové teploty nesmí žádný WH1080 import považovat za původní pozorování: jinak zrekonstruujeme falešné denní a absolutní mrazy. Uživatelsky dostupné historické archivy mohou být odvozené ze společného exportu. Nejdřív provenance; teprve pak fyzikální validace.

## 3. Kontroly, které nezakládají opravu

- Všech **1 523 368** produkčních, plně porovnatelných kombinací `outTemp/outHumidity/dewpoint` sedí na diagnostický Magnusův výpočet s rozdílem menším než 1 °C, **0** přes 2 °C. Výpočtový problém vzniká v rekonstrukci až po změně RH, ne ve zdrojovém `dewpoint`.
- V produktovém archivu nebyla identifikována teplota mimo −50…60 °C, vlhkost mimo 0…100 %, záporné srážky ani tlak mimo 800…1100 hPa. Tím se však nevylučují chybné *uvěřitelné* hodnoty.
- Ve 2020/2021 je přesně RH=100 v 4 546 / 2 920 záznamech. Nejdelší souvislý běh má **778× 5 min = 64,83 h** (prosinec 2020). Možné skutečné nasycení vzduchu; zatím **SCREEN_ONLY**, ne prokázaný senzor freeze.
- Ze 77 hodnotových/odvozených polí jsou `extraHumid1`, `extraHumid2` a `lightning_energy` úplně prázdné. To **není** důkaz ztráty dat: bez epoch instalace jde o `UNKNOWN_INSTALLATION / NOT_INSTALLED_REVIEW`.
- Senzory poprvé připojené v roce 2022 či 2026 (PM2.5, UV, radiation, RSSI, další půdní sondy) nesmí být automaticky označeny za historicky chybějící od roku 2009. Evidovat první neprázdný čas samostatně.
- Produkční denní agregáty `archive_day_*` jsou **79 tabulek**. `archive_day_rain` červenec 2021 při kontrole **31 dní** přesně odpovídá aktuální *produkční* (poškozené) řadě, nikoliv 42,567 mm rekonstrukce. Další dílčí měsíční kontroly 2018-01, 2022-04 a 2026-08 našly 0 denních rain mismatch; jeden den v 2026-08 vykazoval `outTemp` max >0,3 °C proti dostupným 5min archivním bodům, což může být z platného okamžitého LOOP maxima. **Plošný všech 6114 dní nebyl dokončen**, těžký globální join časově vypršel, neopakovat jej v provozu. Opravovaná rekonstrukce zatím nemá 79 `archive_day_*` přepočtů.

## 4. Co skutečně doporučuji rekonstruovat, co ponechat

### Podložené kandidáty do přísného per-field QC (žádný současný autoapply)

1. Venkovní T chybějící v roce 2013: nejprve WH1080 **5 639 nenulových kandidátů** bez 12 zástupných nul, s kontrolou období, originálních jednotek a nezávislého důkazu.
2. RH 2018/2019: vyřadit alespoň 715 kandidátních WH hodnot přesně 10 %, 6 nad 100 % a další časově/senzorově nekonzistentní body; zbylé číselné hodnoty dále ověřit, ne hromadně RESTORED.
3. Tlak a vnitřní teplotu během fyzických 2016/2017 výpadků posoudit **odděleně** od venkovní T/RH; nejdřív vyřešit off-grid zdroj 2016 a nezávislost kopií.
4. Jednotlivé fyzikálně podezřelé krátké intervaly tlaku/větru/RH, solar, soil a extraTemp zapsat jako `SENSOR_ERROR_REVIEW`; obnovit pouze ověřenou referenční hodnotu/zdroj, jinak zachovat původní číslo s QC vyloučením z certifikovaných rekordů.
5. Hist. srážky včetně 2021 držet jako chráněné; nejdřív reconcile aktuální hodnota/poslední auditovaná změna a nezávislá evidence. Nepoužívat nulové `rainRate` pre-2026 jako důkaz, že nepršelo.

### Bez nezávislého důkazu NEVYPLŇOVAT

- 170 050 teoreticky neobsazených nominálních slotů, především dlouhé celé výpadky; žádná globální interpolace.
- 44 509 pre-GW1000 chybějících RH v roce 2022 bez dostupné alternativy; případné modelové odhady výslovně jako `ESTIMATED`, nikoli `MEASURED`.
- 8 126 NULL intervalů srážek 2020 nulou, zejména při současném výpadku větru.
- Falešné WH1080 venkovní T=0 uvnitř historických mezer.
- Číselné lightning noise/disturber, dokud není ověřen aktivní GW3000 mapper (ochrana webu už hotová).
- Originální `dewpoint` jen proto, že se změnila RH až v pracovní rekonstrukci; budoucí přepočet musí mít vlastní per-field provenance.

## 5. Implementační pořadí a definice hotového stavu

1. **P0 čítače a ochrana současného sběru (#17/#24):** zachovat stávající webové filtrování, ověřit skutečný driver a raw payload; opravu aktivního mappingu oddělit od historie.
2. **P0 QC registry (#25):** materiálový seznam `(dateTime,variable,reason,source_ref,epoch,confidence,status)`, kde `NULL`, `NOT_INSTALLED`, `SENSOR_ERROR` a `ESTIMATED` nejsou zaměňovány.
3. **P0 backup/restore (#26):** konzistentní snapshot celé `loucka_reconstruction` na izolovanou MariaDB + ověřený rollback a explicitní manifest approval před jakýmkoli novým historickým zápisem.
4. **P1 source-specific triage (#18–#23):** teplota 2013, RH 2018–2019, chráněné srážky 2021, jednotkové epochy; u každého kandidáta rozhodnout RESTORE_VERIFIED / CORRECT_VERIFIED / HOLD_SOURCE_CONFLICT / UNRECOVERABLE, žádné falešné jistoty.
5. **P1 web (#25):** klimatologie a rekordy až z autorizovaných hodnot s CET/CEST denní agregací; skutečně neobnovitelné období zůstává transparentní mezerou.

**Bezpečnostní stav po auditu:** `db_writes=0`; `production_cutover=NO_GO`; `quarantined_manifest_operations=92366` beze změny. Živá synchronizace GW3000 a původní produkční data nebyly dotčeny. Žádná skupina kandidátů z této zprávy nebyla na základě pouhého prahového screeningu automaticky povýšena na schválenou opravu.
