# Hloubkový audit senzorů, PM2.5 a mapování GW1000 (navazuje na 26 kohort)

**Datum:** 2026-11-23; **fixní horní časová hranice produkčního archivu:** UTC `1795415700` (06:35).  
**Základ:** [inventář 26 kohort](2026-11-23-production-anomaly-reconstruction-inventory.md), sloučený do `main` jako PR #68.  
**Reprodukce:** [12 SELECT-only kontrol](../sql/readonly/production_sensor_mapping_pm25_followup_20261123.sql) A–L, testované přímo proti živé MariaDB pouze pro čtení.  
**Politika:** kandidát ≠ schválená oprava; dvě shodné DB mohou pocházet ze stejného senzoru. Žádná DML, DDL, „NULL→0“, interpolace ani nasazení. Všechny počty níže jsou snapshot nebo explicitně vymezená historická období, nikoliv hodnoty až do aktuálního okamžiku.

## 1. P1: dlouhodobá PM2.5 saturace v září–říjnu 2024

Srovnání produkční `pm25_1` a staré `pocasi-loucka.eu_GW1000.pm2_5`:

| Rozsah 2024 | Počet |
|---|---:|
| Srovnatelných hodnot s totožnou časovou značkou | **90 917** |
| Stejných hodnot do tolerance 0,001 | **90 917 / 90 917** |
| Intervalů `pm25_1 >= 500` (celý 2024) | **2 128** |
| Intervalů `pm25_1 >= 990` (celý 2024) | **1 419** |
| Intervalů `ABS(pm25_1 - 999.9)<0.001` | **1 401** |

Po měsících: září 2024 **2 066** intervalů ≥500 a **1 362** na hranici ~999,9; říjen dalších **61** ≥500 a **39** ~999,9; jeden interval ≥500 byl v květnu. Zářijový měsíční průměr uložené řady je ~**280 µg/m³**, ale bez validace je to **nedůvěryhodný průměr**, nikoliv podklad do klimatologie/imisních rekordů.

Nejdelší souvislé běhy při ≥500:

- 2024-09-13 **20:05** až 2024-09-15 **09:10 UTC**: **446× 5 min**, průměr **920,4**.
- 2024-09-09 **08:35** až 2024-09-10 **10:30 UTC**: **312× 5 min**, průměr **995,5**.
- Další desítky dlouhých běhů se soustřeďují do poloviny a konce září 2024.

Opakovaná přesná horní hodnota ~999,9 a hodinové až denní bloky jsou **silný kandidát saturace/driver limitu/senzorové poruchy**, nikoli nezávislý důkaz, že žádná extrémní událost ve vzduchu neprobíhala. Archiv GW má doslova stejná data, proto **neposkytuje nezávislou náhradní PM hodnotu**. Rozhodnutí: `FLAG_PM_RANGE_SATURATION / HOLD`, nepřevádět na 0 ani mazat před doložením originálního payloadu a lokální referenční kvality ovzduší. Do ověřených PM statistik nevkládat jako necenzurované přesné měření.

## 2. P1: důkaz, že půdní senzory v GW1000 mají JINÉ názvy kanálů

Porovnávaly se **společné přesné UTC timestampy** a tolerance `ABS(delta)<0,15 °C`. V **letech 2022, 2023, 2024 a 2025** platí toto mapování **na 100 % všech porovnatelných dvojic**:

| Archiv `pocasi-loucka.eu_GW1000` | Produkční `pocasi-loucka.eu` | Doklad 2023 | Doklad 2025 |
|---|---|---:|---:|
| `soilTemp1` | `soilTemp3` | 103 036 / 103 036 | 102 343 / 102 343 |
| `soilTemp2` | `soilTemp4` | 103 117 / 103 117 | 102 149 / 102 149 |
| `soilTemp3` | `soilTemp5` | 103 130 / 103 130 | 102 343 / 102 343 |
| `soilTemp4` | `soilTemp6` | 103 091 / 103 091 | 102 343 / 102 343 |

V roce 2026 mapování stále dominantně platí, ale už není úplně přesné: `GW soilTemp1 → produkční soilTemp3` **76 312 / 76 810** porovnatelných, `GW soilTemp3 → produkční soilTemp5` **75 064 / 76 813**, `GW soilTemp4 → produkční soilTemp6` **74 884 / 76 817**. Rozdíly se objevují v období nového sběru od března 2026, včetně extrémních chyb čidel. Neznamená to však samo o sobě, že se změnilo fyzické pořadí všech senzorů.

**Kritické praktické pravidlo:** Při rekonstrukci **NIKDY nespojovat stejnojmenné `soilTemp1` produkce a GW jako stejný senzor**. Produkční `soilTemp1` je jiný kanál než GW `soilTemp1`. Například 2026-06-29 má produkce `soilTemp1=-28,5 °C`, GW `soilTemp1=+23,0 °C`, ale produkční `soilTemp3=+23,0 °C`: záměna vytvoří falešnou „obnovenou půdní teplotu“.

Dále **11** hodnot produkční `soilTemp1<-20 °C` v roce 2026 (plus **2** v roce 2022) a **31** hodnot `soilTemp5/6<-40 °C` v roce 2026 (10 v soil5, 21 v soil6). Dříve zdokumentovaných šest pod −50 °C je **podmnožinou těchto 31**, ne dalších šest. Jednotlivé záporné čtení při letní venkovní teplotě 27–38 °C a ostatních půdních sondách kolem 20–24 °C je konkrétní kandidát chyby čidla/driveru. Bez jiného **správně mapovaného, nezávislého** zdroje: `SENSOR_ERROR_REVIEW`, ne RESTORE.

## 3. P1: `bgt` je konstantní a současně se mění okolní podmínky

Mezi **2026-03-08 12:15 UTC** a **2026-04-27 16:03 UTC** existuje **1 551** neprázdných záznamů `bgt`; všechny jsou přesně **−0,1 °C** (`COUNT(DISTINCT)=1`). U stejných řádků nabývá venkovní teplota 172 různých hodnot v rozsahu **−0,5…+17 °C**. Nápadné je, že první `bgt` se objevil v okamžiku začátku rozdílů mezi produkcí a paralelní větví GW1000 (8. března 2026 12:15 UTC).

Závěr: **silný kandidát placeholderu/nedostupného black-globe senzoru**, ale fyzická definice `bgt` a jeho původ v aktuálním WeeWX skinu/driveru se musí ověřit. Pro klimatologické modely `WBGT` zatím nelze automaticky tvrdit validní přímé `bgt` měření. `HOLD`.

## 4. P1: `extraTemp2` má pravděpodobně různé epochy významu

- **2022-09-02 08:45 až 2022-09-08 12:30 UTC:** 1 765 záznamů, rozsah **27,57…99**, z toho **1 204** nad 60 (možné hodnoty RH mapované do kanálu teploty); nelze ověřit pouze podle čísla.
- **2023:** 26 445 neprázdných, rozsah **11,72…34,13**.
- **2024-02-17 14:25–15:30 UTC:** **14** řádků `extraTemp2≈822,4`, v tomtéž období 2 řádky `extraTemp1>80`. V GW větvi `extraTemp2` u těchto časů NULL a `extraTemp1` blízko skutečné venkovní teploty.
- **2025:** 17 396 hodnot, přibližně **15,27…30,49**.
- **2026:** 17 876 hodnot, přibližně **15,02…36,40**.

2022 série má **neprokázanou sensor/unit epochu**. Vyloučit ji z ověřených teplotních rekordů do ověření instalace/field_map, nikoli pouze 776 řádků přes 80 °C. 2024 epizoda je jasně chybně zapsaný extrémní kanál: `SENSOR_ERROR_REVIEW`; **bez automatického nahrazení GW `extraTemp1`**, protože identita čidla není potvrzená.

## 5. P2: potenciálně chybné jednotky/slovní význam `sunshine_time` a `sunshineDur`

V roce 2026 mají po **73 617** neprázdných záznamů. V **10 555** případech `sunshineDur > 60×interval`, v **16 690** případech `sunshine_time > 60×interval`. Pro kontrolu `rainDur` ve stejném období **0** případů přesahujících délku intervalu. Pozor: **NEPROKAZUJE to vadné údaje**, pokud `sunshineDur` či `sunshine_time` není definováno jako počet sekund slunečního svitu *v příslušném archivním intervalu*. Příklad `sunshine_time` postupně rostoucí přes celý den naznačuje jinou sémantiku (např. astronomický/sluneční čas). Rozhodnutí: `VERIFY_FIELD_SEMANTICS`, žádné mazání.

## 6. P1/P2: od 2026-03-08 12:15 UTC dochází k výrazné divergenci zpracování

Stejný přesný čas **2026-03-08 12:15 UTC** je prvním zjištěným případem rozdílu `barometer` >0,5 hPa a `windSpeed` >1 km/h mezi produkcí a GW1000 po začátku března. Následně je první rozdíl `soilTemp5` (p) vs `soilTemp3` (GW) >0,15 °C **15:25 UTC** a PM2.5 >1 jednotku **16:35 UTC**. V lednu a únoru byla `barometer` vůči zrcadlu identická. **Není** správné předpokládat, že produkční tlak je horší: různé vzorce převodu na tlak u stanice a na hladinu moře mohou vysvětlit část odchylek. Vlastní `pressure` se mezi zdroji lišil i před 8. březnem, cca 8–12 hPa; nelze jej prostým srovnáním považovat za chybu.

Další limit: historické GW1000 `archive` končí **2026-10-29 10:10 UTC**; produkční řada pokračuje minimálně do **2026-11-23 06:35 UTC**. „GW1000 mirror“ není aktuální garantovaný duplicitní živý zdroj pro listopad. Samotný název schématu nedokládá, že hardware GW1000 produkoval záznamy už od 2009: v tomto schématu jsou i starší importované řádky.

## 7. Diagnostická kontrola, která NEPŘIKAZUJE opravu

`lightning_distance` má v 2026 jen **40** neprázdných bodů, vždy **34**, bez současného kladného `lightning_strike_count`. To může být úplně legitimní poslední známá vzdálenost výboje, nikoli aktuální vzdálenost nového výboje. Bez přímé definice driveru/telemetrie nedává smysl vynucovat změnu na 0 ani jej vykreslovat jako nový úder.

## 8. Důkazy vs. dovolené operace

| Kandidát | Doporučený stav | Schválený DB zápis |
|---|---|---|
| PM25 2024 nad limit/999,9 | `PM_SENSOR_SATURATION_REVIEW` | **NE** |
| `bgt=-0.1` opakovaně | `UNVERIFIED_PLACEHOLDER` | **NE** |
| Fyzické mapování GW `soilTemp1..4` | `MAPPING_EVIDENCE_ONLY`, nepoužívat stejné názvy | **NE** |
| `soilTemp1/5/6` záporné letní spiky | `SENSOR_ERROR_REVIEW` | **NE** |
| `extraTemp2` 2022 a 2024 | `UNIT_OR_CHANNEL_EPOCH_REVIEW` | **NE** |
| Sluneční „duration“ >interval | `SEMANTICS_UNKNOWN` | **NE** |
| Zdrojový split od 2026-03-08 | `DRIVER_CALIBRATION_REVIEW` | **NE** |
| Historické GW mirror po 2026-10-29 | `MIRROR_UNAVAILABLE` | **NE** |

**Navržené konkrétní kroky:** #24 doplnit potvrzené PM/soil QC a blokovat neověřené zdánlivé absolutní rekordy; #22 při posuzování tlaku/zemních sond zohlednit zdrojovou změnu 8. března, ověřit nasazenou konfiguraci; #25 doplnit per-field sensor identity/epoch registry. Jakákoli změna hodnot teprve po izolovaném backup+restore (#26) a samostatně schváleném manifestu. Tato etapa **nezasahovala** do produkce, rekonstrukce ani běžící GW3000 synchronizace.
