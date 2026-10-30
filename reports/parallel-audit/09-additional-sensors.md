# Audit 09 — další senzory Počasí Loučka (2009–2026)

**Datum:** 2026-10-30. **Metoda:** pouze SELECT přes Weather MCP; žádné UPDATE/INSERT/DELETE ani změny oprávnění. **Stav:** forenzní screening a prioritizace, nikoli schválení rekonstrukce.  
**Zdroje:** `loucka_reconstruction.archive` (pracovní), `pocasi-loucka.eu.archive` (produkce), `pocasi-loucka.eu_GW1000.archive`, `pocasi-loucka.eu_old.archive`, `old_weewx.archive`, `weewx_WH1080.archive`. SQL identifikátory DB s tečkou/pomlčkou vždy uzavírat do zpětných apostrofů.

## 1. Metodika, pokrytí a omezení

- Přes MCP bylo ověřeno všech šest databází; struktura sloupců z `information_schema.COLUMNS`, primární profil `dateTime`, `usUnits` a `interval`. Časové značky jsou Unix UTC; uvedené časy incidentů jsou **UTC**. `FROM_UNIXTIME` ve zjištěné DB relaci využívá `@@session.time_zone='SYSTEM'`; server 30. 10. 2026 vracel lokální čas UTC+1. Roční/měsíční seskupení je tedy podle **serverového místního času**; pro finální kalendářní výstupy explicitně nastavit `Europe/Prague`, zejména při přechodech CET/CEST. WeeWX archivuje konce intervalů; pro přesné denní vyhodnocení používat `(start,end]`.
- Produkce vykazovala během živého běhu přibližně **1 680 082** řádků (počet se během dotazování měnil); zjištěno `usUnits=16` u všech řádků produkce. Z toho **nevyvozujeme**, že historické vnější archivy mají shodné jednotky či semantiku. Rok 2026 je neúplný, údaje přibližně do 30. 10. 2026 14:30 UTC. Číselné roční počty níže pocházejí z jednotlivých okamžiků běhu a mohou se o nové příchozí řádky mírně lišit.
- `COUNT(x)` zahrnuje i neplatné nuly; `COUNT(*)` sám nedokládá instalaci senzoru. Reálné instalace jsou pouze **inference z dostupnosti a nenulového rozptylu**, přesné datum fyzické montáže vyžaduje `weewx.conf`/servisní historii. Chybějící senzor nekvalifikovat jako výpadek.
- Nezávislá data o PM2.5/UV/slunečním záření z okolní stanice v těchto šesti archivech identifikována nebyla. `loucka_reconstruction` je často **kopie produkčních hodnot**, nikoli nezávislý senzor. `GW1000` se do roku 2025 na překryvu ve sledovaných polích zpravidla shoduje s produkcí a sama o sobě nepotvrzuje fyzikální správnost.
- Historické `soilTemp*` a `extraTemp*` se **nespojují, neinterpretují napříč obdobími a neopravují** (možné změny názvů/umístění sond). Ani ostatní data nebyla upravena.

### 1.1 Časové režimy a věrohodnost senzoru

| Období | Co je skutečně doloženo | Doporučené zacházení |
|---|---|---|
| 2009–2020 | `weewx_WH1080` má `radiation`, `UV`, `soilMoist1–4` vyplněné na každém archivním řádku, ale **všechny hodnoty jsou 0**. `old_weewx` má jen 222 nenulových? **Ne:** 222 vyplněných záznamů roku 2014 jsou také **všechny 0**, mimo to NULL. | Placeholder, **nikoli historické skutečné měření**. Nesmí se použít ke zpětnému doplnění NULL do produkce. |
| 2009–26 | `maxSolarRad` je v produkci vyplněno u každého archivního řádku (včetně období bez `radiation`); maximum cca 942,74. | Odvozená geometrická/modelová veličina; nenahrazuje fyzické sluneční čidlo. |
| 2020–2022-08 | V produkci existují např. pozdější stavové/WS80 položky, ale `radiation`, `UV`, PM2.5, blesky a `soilMoist1` jsou stále NULL. | Neindikovat jejich výpadek; před instalací/aktivací není záznam. |
| **2022-08-27 09:40 UTC** | První nenulově proměnlivé `radiation`, `UV`, `pm25_1`, `soilMoist1`, první záznam `lightning_strike_count` i řady stavových polí; u bleskové vzdálenosti první záznam **2022-09-08 15:45 UTC**. | Začátek nové měřicí epochy; datum *prvního záznamu*, nikoli ověřená montáž. |
| 2023–2025 | Měření jsou běžná, ale s odpojením půdní sondy, výpadky PM, saturovanými PM hodnotami a rozdílnými signály/bateriemi. | Pro každý kanál samostatný příznak kvality. |
| **2026-03-08** a dále | `soilad1` poprvé **2026-03-08 12:15 UTC**; `wh51_ch1_rssi` a `wh57_rssi` od cca 12:25 UTC. V překryvu začíná divergence produkce vs. GW1000. | Samostatná metadata změny stanice/pipeline, **neautomaticky** chyba senzoru. |
| **2026-05-11** a dále | Nové významy `lightning_noise_count`, `lightning_disturber_count` (viz oddíl 5). | Před použitím opravit mapování názvů/metadat ve zpracování, historická data ponechat. |

## 2. Roční dostupnost produkčních senzorů

Hodnoty v buňce jsou **počty nenulově přítomných SQL hodnot** (tj. `NOT NULL`, zahrnuje i číselné nuly); jmenovatel je počet archivních řádků daného roku. 2009–2021: u všech uvedených reálných senzorů **0 platně dostupných hodnot**; sloupec `maxSolarRad` je vyplněn i v těchto letech, ale jde o model.

| Rok | Řádků | radiation | UV | pm25_1 | soilMoist1 | lightning_strike_count |
|---|---:|---:|---:|---:|---:|---:|
| 2022 | 104 140 | 36 089 | 36 089 | 36 158 | 33 752 | 36 352 |
| 2023 | 104 434 | 104 251 | 104 253 | 101 509 | 86 456 | 104 421 |
| 2024 | 104 935 | 104 572 | 104 572 | 90 917 | 82 124 | 104 654 |
| 2025 | 102 946 | 101 517 | 101 517 | 99 033 | 98 735 | 102 944 |
| 2026* | ~87 168 | ~86 648 | ~86 648 | ~87 148 | ~87 167 | 85 222 |

**Poznámky:** `soilMoist2–4` **v produkčním schématu neexistují**; `old_weewx` a `weewx_WH1080` je sice mají, ale jejich historická data jsou NULL nebo pouze nuly. `pocasi-loucka.eu_old` (do 2023) má sledované sluneční/půdní/bleskové hodnoty převážně NULL, tudíž není pozitivní historický zdroj. `pocasi-loucka.eu_GW1000` od 2022 vykazuje stejné roční pokrytí radiace, UV a půdy jako produkce; neobsahuje `pm25_1`. `loucka_reconstruction` vykazuje pro společné značky včetně roku 2026 shodné sledované hodnoty, ale méně aktuálních řádků.

## 3. Záření `radiation`, `maxSolarRad` a UV

### 3.1 Rozsah a hodnoty

| Rok | maximum `radiation` | maximum UV | `radiation > maxSolarRad+20` (intervaly) | `radiation > 1400` |
|---|---:|---:|---:|---:|
| 2022 | 801,03 | 7,2 | 138 | 0 |
| 2023 | 1 079,09 | 9,91 | 853 | 0 |
| 2024 | **1 638,14** | 12,14 | 842 | 1 |
| 2025 | **1 454,55** | 12,2 | 395 | 1 |
| 2026 | **2 248,85** | 14,8 | 358 | 2 |

Jednotka `radiation` se podle obvyklé sémantiky WeeWX očekává **W/m²**, UV index je bezrozměrný; je nutno potvrdit v aktuálním `weewx.conf` a surové bráně, zejména po změně z března 2026. `maxSolarRad` se chová jako vypočítané záření za jasné oblohy (max ~943 W/m²); **nejde o univerzální tvrdou mez fyzikálně možného okamžitého ozáření** (krátké zesílení oblačností je možné).

**Vysokoprioritní jednotlivé extrémy** (UTC):
- 2024-06-16 09:45: `radiation=1638,14`, UV=12,14, `maxSolarRad=912,23`.
- 2025-07-30 06:35: `radiation=1454,55`, UV=12,2, `maxSolarRad=436,81`.
- **2026-08-23 06:10:** `radiation=2248,85`, UV=14,8, model=275,70; o 5 minut později `radiation=1642,47`, UV=13,21, model=291,16. V GW1000 ve stejných intervalech radiace 2211,86 a 1577,31; společný původ, ne nezávislé potvrzení. Tak vysoký ranní vzestup je **silně podezřelý** (jednotky, elektronika, integrace, souběžný UV). Neodstraňovat bez surových dat.
- Kontrola základního denního cyklu: při lokálních hodinách 00–03 a 22–23 nebyla v produkci 2022–26 nalezena `radiation >100` ani UV>1. Nebyly nalezeny řádky s `UV>0` při `radiation=0`. Celkové denní chování tedy není plošně invertované.

**Konkrétní hodinový profil (místní čas, průměr `radiation`):** v červnu 2023: 06 h =72,3; 09 h =434,4; 12 h =542,7; 15 h =459,1; 18 h =188,4 W/m², 00 h =0. V prosinci 2023: 09 h =34,0; 12 h =64,5; 15 h =8,1 W/m², 00/18 h =0. Slučuje se se sezonností, neprokazuje absolutní kalibraci.

**UV vazba:** Vysoká radiace s UV=0 při radiaci>350 nebyla nalezena v ročních souhrnech 2022–26. Samotná UV/radiace není konstantní poměr (spektrum, oblačnost, úhel Slunce); nepoužívat pevný přepočet. Extrémy roku 2026 vyžadují profil po minutách, kontrolu čidla a surových dat.

## 4. PM2.5 `pm25_1`

Předběžná jednotka dle běžného Ecowitt/WeeWX: **µg/m³**; doložit konfigurací a přesným modelem čidla. **Ne všechny extrémy jsou automaticky nemožné**; rozhodující je saturace, dlouhá opakovatelnost a kontext vlhkosti.

| Rok | Dostupných | Průměr z nenulově přítomných | Maximum | Počet >100 | Počet >500 |
|---|---:|---:|---:|---:|---:|
| 2022 | 36 158 | 25,01 | 534,56 | 632 | 5 |
| 2023 | 101 509 | 16,98 | 652 | 926 | 7 |
| **2024** | **90 917** | **41,67** | **999,9** | **4 348** | **2 126** |
| 2025 | 99 033 | 14,47 | 643 | 677 | 2 |
| 2026* | ~87 148 | 11,89 | 928 | 336 | 9 |

**Akutní datový incident září–říjen 2024:**
- Samotné **září 2024**: 2 064 záznamů `pm25_1>500`; měsíční průměr z přítomných měření ~279,2; v říjnu dalších 61 >500, v květnu jeden.
- Celý rok **1 401 hodnot `>=999,8`** na horní hranici 999,9. Jde o výstražný znak saturace/sentinel, nikoli důkaz skutečného koncentrátu aerosolu.
- Souvislý běh **446 pětiminutových intervalů nad 500** od **2024-09-13 20:05 UTC do 2024-09-15 09:10 UTC**, při souvislosti časových značek 300 s; přibližně **37 h 10 min**. Dne 14. 9. všech 288 pětiminutových záznamů přes 500; denní průměr ~958,3. Relativní vlhkost v části tohoto období ~95–97 %, ale nelze tím bez dalšího prokázat příčinu.
- Extrémní PM se nevyskytují při všeobecném výpadku: roku 2024 **2 126/2 126** PM>500 současně má dostupnou radiaci a **2 105/2 126** i venkovní teplotu. Ukazuje na senzorově specifické selhání nebo extrém, nikoli primárně výpadek celé stanice.
- Výpadky přenosu PM: **2024-08: 1 296 NULL**, **2024-10: 8 390 NULL z 8 934 řádků**, **2024-12: 3 771 NULL**; 2025-03: 2 650 NULL. Některé výpadky jsou současné s absencí bateriové telemetrie, jiné nikoli.

**Rozhodnutí:** Nezapočítávat bez QC příznaku do kvalifikovaných dlouhodobých statistik AQI. Bez nezávislé stanice nebo servisního logu však **automaticky nemazat ani nenahrazovat nulou**.

## 5. Bleskové čidlo a sémantika polí

- První `lightning_strike_count`: 2022-08-27 09:40 UTC; první `lightning_distance`: 2022-09-08 15:45 UTC. `lightning_distance` v produkci do 2025 nabývá přibližně 1–40 (jednotku nutno potvrdit); počet přítomných hodnot podle roku 2022: 17, 2023: 526, 2024: 615, 2025: 371, 2026: **40**, s posledním záznamem **2026-03-07 20:10 UTC**.
- Maximální `lightning_strike_count` za archivní interval: 2022 = 2, 2023 = 133, 2024 = 131, 2025 = 53, 2026 = 72. Kladných intervalů: 15 / 289 / 473 / 232 / 179. Bez popisu API nelze určit, zda jde o intervalové počty, rozdíly čítače, nebo po výpadku akumulovaný údaj; nepřepočítávat rovnou na počet skutečných úderů.
- `lightning_energy` je v produkci **v celé historii NULL**. **Netvrdit**, že čidlo měřilo energii.
- Nové `lightning_noise_count` má od **2026-05-11 18:45 UTC** celkem **179 nenulově přítomných záznamů**, v **každém z těchto 179** přesně odpovídá `lightning_strike_count`. Je to silný signál chybného mapování nebo duplikace, nikoli nezávislá diagnostika šumu.
- `lightning_disturber_count` má od stejného data **47 599 záznamů**, rozmezí ~1 778 528 640 až 1 790 006 633, tedy **řádově unixové epochy**, nikoli počet rušivých impulsů. První záznam `dateTime=1778525100`, `disturber_count=1778528640`. Nepoužívat jako čítač; nutné prověřit parsování a zdrojové mapování.
- Archiv GW1000 má roku 2026 **5 426** nenulově přítomných hodnot `lightning_distance`, zatímco produkce jen 40; v GW jsou například opakované hodnoty vzdálenosti 34 i při `strike_count=0` dne 2026-04-07. Mohou být **stale last-distance**; ani jejich kopie do produkce není automaticky správná. Rozdíl mezi zdroji vyžaduje revizi timestampů, TTL a nulovacích pravidel.
- Kontrolovat `lightning_Batt` (2022–26 hodnoty cca 1–5, význam stupnice neověřen) a od března 2026 `wh57_rssi`; v říjnu 2026 postupně chybí část strike/battery záznamů při stále dostupných jiných měřeních.

## 6. Půdní vlhkost a baterie

**Schéma:** produkce/rekonstrukce má `soilMoist1`, `soilMoistBatt1`, později `soilad1`, `wh51_ch1_sig` a `wh51_ch1_rssi`, **nemá `soilMoist2–4`**. Staré `weewx_WH1080` má `soilMoist1–4` vždy 0 po celou dostupnou historii a `old_weewx` je jinak NULL (222 nulových údajů 2014). Nulové historické hodnoty **neznamenají měřených 0 % půdní vlhkosti**. `soilMoist1` v produkci 2022–26 obecně 0–100; rozsah sám o sobě není dostatečná kontrola.

| Rok | `soilMoist1` přítomno | Nulové záznamy | Rozsah | `soilMoistBatt1` rozsah |
|---|---:|---:|---:|---|
| 2022 | 33 752 | 0 | 7–67 | 1,4–1,6 |
| 2023 | 86 456 | 1 237 | 0–100 | 0,8–1,6 |
| 2024 | 82 124 | 1 687 | 0–100 | 1,4–1,6 |
| **2025** | **98 735** | **16 068** | 0–96,67 | 1,3–1,4 |
| 2026* | ~87 167 | 0 | 20–86 | ~1,3 |

- Rok **2024-01**: `soilMoist1` NULL v celém měsíci (ostatní archivní veličiny měřeny). Prosinec 2023 měl velmi vysoký podíl NULL a `wh51_ch1_sig=0`.
- **2025-02**: 5 350 nul z 7 866 přítomných měření; **2025-03**: 7 398 nul z 8 869 přítomných. Nejdelší přesná pětiminutová nulová série: **2 088 hodnot od 2025-03-17 12:20 UTC do 2025-03-24 18:15 UTC**, přibližně **7 dnů 6 h**. Další délky 1 032, 856, 645 intervalů. Dlouhodobá nula v zimě/jaru je podezřelá na čidlo/kalibraci či zdrojový nulový kód; **nelze bez půdního kontextu prohlásit každou nulu za fyzikálně nemožnou**.
- U **15 652** nulových záznamů roku 2025 je současně `wh51_ch1_sig>0`, tedy přenos signálu funguje; naproti tomu `soilMoist1 IS NULL AND wh51_ch1_sig=0` bylo 2023: 17 391, 2024: 8 823, 2025: 4 211 případů. Tyto dvě skupiny (NULL+ztráta signálu vs. nula+příjem signálu) je nutné posuzovat odděleně.
- V roce 2026 se `soilad1` objevuje až **8. 3. 2026 12:15 UTC** a má rozsah 134–306; `wh51_ch1_rssi` od 12:25 UTC. Změna režimu se kryje s výraznou divergencí se zdrojem GW1000. Bez mapovacího souboru čidla nelze bezpečně porovnávat raw ADC a procenta ani spojovat sondy.
- `soilMoistBatt1` je ~1,3–1,6 podle období (historické minimum 0,8); **nepoužívat absolutní hranici vybitého čidla** bez potvrzení, zda jde o napětí, jeho průměr, či přepočtený indikátor. `batteryStatus1` je ve všech jeho 409 560 přítomných řádcích 0 (status/placeholder, nikoli voltmetr). `pm25_Batt1` a `lightning_Batt` mají různé škály 0–5/1–5, **nepovažovat za volty**.

## 7. Propojení výpadků mezi kanály a porovnání zdrojů

### 7.1 Souběžné výpadky (produkce)

| Rok | `PM NULL`, radiace i UV OK | `soil NULL`, PM i radiace OK | radiace i UV NULL, PM OK |
|---|---:|---:|---:|
| 2022 (od aktivace) | 209 | 2 584 | 278 |
| 2023 | 2 911 | 16 761 | 167 |
| 2024 | **13 999** | **22 763** | 344 |
| 2025 | 3 783 | 4 110 | 1 299 |
| 2026* | 20 | 0 | 520 |

Interpretace: mnohé výpadky jsou **jednotlivého přijímače/kanálu**, ne odstavení celé základní stanice. Příčinou mohou být signál, baterie, parser, chybějící agregace; pro určení je potřeba surová telemetrie a servisní historie.

### 7.2 Párový JOIN produkce ↔ GW1000 na přesném `dateTime`

| Rok | Shodných časových značek | Rozdílná radiation | Rozdílné UV | Rozdílné soilMoist1 | Rozdílná lightning_distance |
|---|---:|---:|---:|---:|---:|
| 2022 (po aktivaci) | 36 610 | 0 | 0 | 0 | 0 |
| 2023 | 104 434 | 0 | 0 | 0 | 0 |
| 2024 | 104 935 | 0 | 0 | 0 | 0 |
| 2025 | 102 946 | 0 | 0 | 0 | 0 |
| **2026*** | **81 621** | **36 464** | **10 770** | **62 409** | **5 269** |

Pro rok 2026 jsou první dva měsíce na překryvu beze změny; rozdíly se objevují **od března**. Ve společných řádcích za 2026 je `pocasi-loucka.eu` ↔ `loucka_reconstruction` pro `radiation`, `pm25_1`, `soilMoist1` **beze změn hodnot** (odlišný je pouze počet posledních časových záznamů). Rozdíl GW1000 proto *může* souviset s přepnutím pipeline/stanice a přepočty, nikoli být automaticky fyzikální vadou.

Specificky 2026-08-23 06:10 UTC: `soilMoist1=29` v produkci a **0** v GW1000 při současném solárním extrému. Roční GW1000 má v roce 2026 **29 368 nul** půdní vlhkosti, zatímco produkční řada roku 2026 nemá žádnou. Bez potvrzení zdroje a kalibrace nelze přenést hodnotu z jednoho archivu do druhého.

## 8. Priorita a návrhy oprav (nic neaplikováno)

| Priorita | Věc | Doporučený krok | Stav jistoty |
|---|---|---|---|
| **P0** | Historické `weewx_WH1080` hodnoty solar/UV/`soilMoist1–4` jsou čisté placeholder nuly | Dát historickým hodnotám kvalifikační flag `NOT_MEASURED` v analytickém výstupu, nikdy neplnit hlavní archiv nulami | **Vysoká** pro nepoužitelnost jako fyzická měření; datum montáže neznámé |
| **P0** | `lightning_disturber_count` v roce 2026 obsahuje epochy, `lightning_noise_count` zrcadlí strike | Ověřit mapper po 11. 5. 2026, syrové MQTT/Ecowitt JSON a významy polí, opravit **kód/metodiku**, ne DB bez schválení | **Vysoká** pro nesprávné interpretování |
| **P1** | PM2.5 září–říjen 2024 saturované a dlouhodobě >500 | Zavést QC flag `SATURATED_OR_SUSPECT`, porovnat servis, déšť/RH, případně okolní PM stanice, ponechat originál | **Vysoká** pro problém kvality; náhradní koncentrace **neznámá** |
| **P1** | Záření/UV 2024–26 extrémy, zejména ráno 23. 8. 2026 | Prozkoumat předchozí a následující sekundy, surový GW3000, UV čidlo, převod jednotek a volitelné filtrování 5min maxima | **Vysoká** pro podezření, korekce nejistá |
| **P1** | Půdní NULL a vícedenní nuly 2024–25 | Oddělit `NULL & signal=0`, `0 & signal>0`; ověřit kalibraci WH51, sondu/umístění a výměny baterií, sestavit seznam intervalů | **Střední/vysoká** pro incident, žádná bezpečná náhrada |
| **P1** | Divergence po 8. 3. 2026 mezi GW1000 a produkcí | Ověřit schéma/konfiguraci, `usUnits`, vzorkovací a agregační pravidla, TTL bleskových vzdáleností, provenance zdrojů | **Vysoká** pro rozdílnost, příčina neověřená |
| **P2** | Chybějící PM 2024-10 a 2024-12; `soilMoist1` 2024-01 | Spárovat období se signálem, baterií, restartem brány a ostatními kanály | **Vysoká** pro dostupnost |
| **P2** | Historický katalog instalací a režimů | Doplnit ověřené datum montáže/swap, model, hloubku půdní sondy, umístění, mapování kanálů a jednotky z WeeWX configů | Zatím **neurčené** |

**Explicitně zakázáno v tomto auditu:** zápis do jakékoli DB; přejmenování nebo slučování `soilTemp*` / `extraTemp*` napříč epochami; převod historických nul na skutečné měření; automatické vymazání extrémů, doplňování `lightning_distance` z GW1000 či nahrazování PM a půdních nul.

## 9. Reprodukovatelné kontrolní SELECT dotazy

**A — rok, pokrytí a rozlišení NULL/0** (stejným vzorem s jinými poli pro všech šest zdrojů):

```sql
SELECT YEAR(FROM_UNIXTIME(dateTime)) AS yr, COUNT(*) AS total,
       COUNT(radiation) AS radiation_n, SUM(radiation = 0) AS radiation_zero,
       COUNT(UV) AS UV_n, COUNT(pm25_1) AS pm_n,
       COUNT(soilMoist1) AS soil_n,
       COUNT(lightning_strike_count) AS lightning_n
FROM `pocasi-loucka.eu`.`archive`
GROUP BY yr ORDER BY yr;
```

**B — GW1000 a produkce, přesná společná časová značka; `NULL`-safe porovnání:**

```sql
SELECT YEAR(FROM_UNIXTIME(p.dateTime)) yr, COUNT(*) matched,
       SUM(NOT (p.radiation <=> g.radiation)) rad_diff,
       SUM(NOT (p.UV <=> g.UV)) uv_diff,
       SUM(NOT (p.soilMoist1 <=> g.soilMoist1)) soil_diff,
       SUM(NOT (p.lightning_distance <=> g.lightning_distance)) lightning_dist_diff
FROM `pocasi-loucka.eu`.`archive` p
JOIN `pocasi-loucka.eu_GW1000`.`archive` g
  ON p.dateTime = g.dateTime
WHERE p.dateTime >= 1661500000
GROUP BY yr ORDER BY yr;
```

**C — saturované PM a sezonnost; rok 2024:**

```sql
SELECT DATE(FROM_UNIXTIME(dateTime)) AS d,
       COUNT(pm25_1) AS present, SUM(pm25_1 >= 999.8) AS saturated,
       SUM(pm25_1 > 500) AS over500, MAX(pm25_1) AS max_pm,
       AVG(outHumidity) AS humidity_avg
FROM `pocasi-loucka.eu`.`archive`
WHERE dateTime >= 1725148800 AND dateTime < 1729296000
GROUP BY d
HAVING over500 > 0 ORDER BY d;
```

**D — dlouhé skutečně sousedící pětiminutové epizody (nelze zaměnit s kalendářním seskupením):**

```sql
WITH hits AS (
 SELECT dateTime, dateTime - 300 * ROW_NUMBER() OVER (ORDER BY dateTime) AS island
 FROM `pocasi-loucka.eu`.`archive`
 WHERE dateTime >= 1725667200 AND dateTime < 1728864000
   AND pm25_1 > 500
)
SELECT COUNT(*) AS n, MIN(dateTime) AS start_utc,
       MAX(dateTime) AS end_utc
FROM hits GROUP BY island ORDER BY n DESC LIMIT 20;
```

**E — test sémantiky bleskových polí po přechodu 2026:**

```sql
SELECT COUNT(lightning_noise_count) AS noise_present,
       SUM(lightning_noise_count = lightning_strike_count) AS identical,
       COUNT(lightning_disturber_count) AS disturber_present,
       MIN(lightning_disturber_count) AS min_disturber,
       MAX(lightning_disturber_count) AS max_disturber
FROM `pocasi-loucka.eu`.`archive`
WHERE dateTime >= 1778525100;
```

Další doporučené kroky: ověřit místní denní hranice při CET/CEST, zdokumentovat provozní `weewx.conf` pro všechny epochy, získat raw JSON a servisní záznamy, případně připravit samostatné **read-only** CSV incidentů a porovnání s nezávislými sítěmi. V tomto běhu **neproběhl úplný validovaný model oslunění ani kalibrace PM či půdních čidel**, proto jsou extrémy značeny jako kandidáti, nikoli definitivně opravené hodnoty.
