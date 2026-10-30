# 04 — Forenzní audit obnovy historických měření (WH1080)

**Datum:** 2026-10-30. **Režim:** výhradně čtení, Weather MCP `execute_sql`; žádný INSERT/UPDATE/DELETE, beze změn `archive` i `wh1080_missing_5min_candidates_20261030`. **Pracovní schéma:** `loucka_reconstruction`. **Zdroje:** `weewx_WH1080`, `old_weewx`, `pocasi-loucka.eu_old`; pro srovnání `loucka_reconstruction.archive`. **Charakter výstupu:** screening všech kandidátů pomocí agregovaných SQL a kontrolních vzorků, nikoli potvrzení každé jednotlivé hodnoty nezávislou meteorologickou stanicí. Žádná hodnota není tímto reportem schválena k automatickému importu.

## 1. Populace, čas a jednotky

Přípravná tabulka obsahuje přesně **49 796** kandidátů. Každý má `source_db=weewx_WH1080`, `source_usUnits=17`, `source_interval_min=5`, `time_offset_sec=0` a `source_time=target_time`. Žádný z 49 796 cílových timestampů nyní neexistuje v `loucka_reconstruction.archive`. Každý ze zdrojových timestampů je dohledatelný v `weewx_WH1080.archive`. To dokazuje *chybějící přesný řádek*, ne automaticky skutečně chybějící meteorologické pozorování ani správnost jeho hodnot.

| Rok podle lokálního *konce* archivu | Stav | Počet | Souvislé úseky kandidátů (pětiminutová návaznost) |
|---:|---|---:|---:|
| 2009 | frozen_sensor_review | 100 | 2 |
| 2011 | frozen_sensor_review | 1 201 | 2 |
| 2016 | pressure_only_review | 5 728 | 436 |
| 2017 | pressure_only_review | 24 543 | 1 366 |
| 2018 | pressure_only_review | 17 466 | 153 |
| 2019 | needs_validation | 267 | 18 |
| 2020 | needs_validation | 491 | 78 |
| **Celkem** | | **49 796** | |

**Pozor na hranici roku:** SQL seskupení výše používá `YEAR(FROM_UNIXTIME(target_time))` v místní zóně serveru (ověřeno `@@system_time_zone=CET`). WeeWX ukládá čas **konce** intervalu a kalendářní příslušnost určuje otevřený začátek a uzavřený konec `(start,end]`. Např. `2017-01-01 00:00 CET` (`1483225200`) patří intervalu z roku **2016** a `2019-01-01 00:00 CET` (`1546297200`) patří intervalu z roku **2018**. Při finální roční agregaci musí být přepočet podle explicitních hranic `Europe/Prague`, nikoli prostý `YEAR(FROM_UNIXTIME(t))`. UTC epocha je primární klíč; CET/CEST se týká zobrazení a občanských hranic.

`usUnits=17` je WeeWX **METRICWX**, rekonstrukční `archive` má v posuzovaných historických obdobích `usUnits=16` (**METRIC**). Teplota [°C], RH [%] a tlak [hPa] se číselně nemění. METRICWX rychlost větru [m/s] → METRIC [km/h]: **× 3,6** (ověřeno na současných zdrojových/rekonstrukčních záznamech; kandidátní `windSpeed_kmh` již tento převod obsahuje). Pokud se prokáže, že `rain` je skutečně *úhrn daného intervalu*, METRICWX [mm] → METRIC [cm]: **÷ 10**; podobně intenzita [mm/h] → [cm/h] dělením 10, ale **až po ověření dobové sémantiky**. Samotné číslo `0` u srážek není důkaz správného senzoru.

## 2. Výsledky po letech a veličinách

| Rok | Teplota `outTemp` | Vlhkost `outHumidity` | Staniční `pressure` | `barometer` | Vítr | Srážky |
|---:|---|---|---|---|---|---|
| 2009 (100) | 0 použitelných bez dalšího důkazu — zmrzlé | 0 | Blokovat; tlak téměř statický | Blokovat | Blokovat | Blokovat; často kladná statická `rain` při nulové `rainRate` |
| 2011 (1 201) | 0 — zmrzlé rozsáhlé série | 0 | **Odděleně prověřit**; 143 odlišných kandidátních hodnot, nelze přijmout celý řádek | Neschvalovat bez kalibrace | Blokovat | Blokovat; podezření na čítač |
| 2016 (5 728) | 0 — falešná 0 °C | 0 — NULL | **5 728 potenciálních**, 9 s hraniční odchylkou > 2 hPa | Nepřebírat bez ověření výpočtu z vadné teploty | 0 | 0 |
| 2017 (24 543) | 0 — falešná 0 °C | 0 — NULL | **24 543 potenciálních**, 19 s hraniční odchylkou > 2 hPa | Nepřebírat bez ověření | 0 (i extrémy) | 0 |
| 2018 (17 466) | 0 — falešná 0 °C | 0 — NULL | **17 466 potenciálních**, 0 s hraniční odchylkou > 2 hPa | Nepřebírat bez ověření | 0 | 0 |
| 2019 (267) | 267 fyzikálně v rozsahu; 1 časově sousední odchylka > 3 °C | **235 předběžně shodných** s `old_weewx`; 20 konfliktů, 12 bez druhé hodnoty | **1 předběžně konzistentní**, zbývajících 266 alternativních tlaků zamítnout pro nesoulad | 1 z WH1080 k potvrzení; ostatní staré hodnoty nesou velkou odchylku | 267 rychlostí/nárazů k validaci; 171 směrů = 22,5° k revizi | 37 kladných `rain`; 64 kladných `rainRate`; zatím nepřebírat |
| 2020 (491) | 491 fyzikálně v rozsahu; 1 časově sousední odchylka > 3 °C | **0 bezpečně schválených**; jen 2 shody s alternativou, 147 rozporů a 342 bez alternativní RH | **1 předběžně konzistentní**, 489 rozporných, 1 bez použitelného zdroje | 7 z WH1080 k potvrzení; stará alternativa výrazně posunutá | 491 rychlostí/nárazů k validaci (483 časově potvrzených ve druhém exportu) | 19 kladných `rain`; 45 kladných `rainRate`; zatím nepřebírat |

Čísla v tabulce představují **možnosti podle veličiny**, nikoli schválené počty importu. Zdrojové archivy jsou historické kopie dat z příbuzných řetězců: jejich shoda není nezávislé potvrzení správnosti čidla.

### 2.1 Kandidáti 2019–2020: všech 758

* Všech **758** má fyzikálně přijatelný základní rozsah teploty a vlhkosti (0–100 %), žádný záporný vítr a žádný poryv menší než průměrná rychlost. U 53 mezer jsou současně oba pětiminutoví sousedé v rekonstrukčním archivu (13 v roce 2019, 40 v roce 2020; z nich 12, respektive 39 má obě referenční teploty). Pro 12/39 teplot je průměrná absolutní odchylka od středu sousedů **0,974/0,901 °C**. Dva výrazné případy: **2019-06-30 17:15** (33,4 °C vs. okolí 29,7/29,5; rozdíl 3,8 °C) a **2020-08-14 15:15** (34,13 °C vs. 28,5/27,8; rozdíl 5,98 °C). Tyto dva body označit k manuální revizi. Časové údaje jsou zobrazené lokálně serverem.
* **Vlhkost 2019:** `old_weewx` má 255 polí RH různých od SQL NULL ze 267 kandidátů; 235 souhlasí se zdrojem, 20 se liší o více než 20 procentních bodů (8 v červnu, 12 v říjnu), 12 je NULL. U jednotlivých mezer může být chybný také **sousední archiv**: 2019-05-14 11:25 chybějící bod uvádí 29 %, zatímco bezprostřední rekonstrukční sousedé mají konstantních 78 %, ale starý archiv v sousedství ukazuje dynamických ~28–31 %. Nevyřazovat jen na základě interpolace z chybného sousedství.
* **Vlhkost 2020:** v únoru 56 kandidátů přesně 96,9 %, v březnu 187 přesně 75,9 % a v květnu 116 přesně 94,64 %, přestože teplota uvnitř úseků výrazně kolísá. Nejdelší souvislý kandidátní úsek stejné RH má 49 pětiminutových záznamů při 29 různých teplotách. Z 491 bodů souhlasí s ne-NULL `old_weewx` jen **2** (2020-03-01 17:00 a 22:20), **147** nesouhlasí a **342** nemá v alternativním exportu RH vůbec. Opakované 75,9/94,64/96,9 jsou varováním před zadrženou/podsunutou hodnotou; všech 491 RH blokovat pro automatické převzetí, ne označovat za fyzikální nulu.
* **Vítr 2019–2020:** `windSpeed` zdrojového METRICWX souhlasí s druhým exportem na 267/267 bodů v 2019 a 483/483 překryvech v 2020, ale to samo nedokazuje nezávislost. V 2019 je **171/267 směrů přesně 22,5°**: kandidátní směr vane nelze přijmout bez kontroly dlouhých konstantních úseků a korelace s rychlostí. Klidný vítr je platná nula, pokud je ověřen senzor, nikoli automaticky doplněná nula.

### 2.2 Zamrzlá čidla 2009 a 2011

* Rok 2009: **14** souvislých bodů s konstantní teplotou 4,8 °C, RH 62 %, větrem 2,5; dalších **86** s 22,2 °C, RH 90 %, větrem 8,6. V těchto dvou blocích tlak vykazuje jen 2 a 2 různé hodnoty. Pozitivní `rain_source_raw` na všech 100 kandidátech není důkaz déšťového úhrnu: hodnoty se opakují při převážně nulové `rainRate`.
* Rok 2011: bloky **909 + 292** pětiminutových bodů. Uvnitř prvního je **856** bodů se současně stejnou teplotou, RH a větrem; druhý má **292** prakticky zcela zamrzlých bodů. Staniční tlak se v celém roce kandidátů mění (143 různých hodnot) a nelze proto automaticky předpokládat zamrznutí barometru, ale jeho samostatná použitelnost zatím není doložena. Celých **1 301** starších kandidátů vyřadit pro **automatické obnovení kompletního řádku a venkovní teploty/RH/větru**; tlak z roku 2011 ponechat pro zvláštní manuální audit, ne pro import.

### 2.3 Období 2016–2018: oddělený tlak

U **47 737** kandidátů je `outTemp_C=0` a `outHumidity_pct IS NULL`. Vítr je navíc v **47 662/47 737** případech nulový (2016: 5 723; 2017: 24 475; 2018: 17 464) a v roce 2017 se vyskytuje **9 rychlostí nad 120 km/h** a **23 nárazů nad 120 km/h** (v roce 2018 další 2 extrémní nárazy). **Tyto veličiny neobnovovat**.

Staniční `pressure` má oproti tomu **1 759 / 2 984 / 2 716 odlišných hodnot** (2016/2017/2018) a je v rozsahu přibližně 921,85–970,57 hPa v celém období. Z návazných pětiminutových dvojic (5 292 / 23 177 / 17 313) jsou průměrné absolutní rozdíly tlaku **0,049 / 0,051 / 0,053 hPa**. Pouze **1** návazná dvojice (2017-06-23 04:15, +1,44 hPa) překročila 1 hPa; žádná nepřekročila 2 hPa. Pro srovnání s bezprostředním tlakem v rekonstrukci na jedné nebo druhé hranici chybějícího úseku je **9 / 19 / 0 jedinečných kandidátů** s rozdílem > 2 hPa a **1 / 1 / 0** s rozdílem > 5 hPa. Těchto **28** výjimek oddělit k ruční kontrole; ostatních **47 709** pouze prošlo *touto dílčí hraniční kontrolou*, nikoli kompletním schválením.

V existujících časově přesných překryvech WH1080 × pracovní archiv se tlak liší průměrně o **0,75 / 0,60 / 0,64 hPa (MAE)** za roky 2016–2018 a vykazuje nenulový systematický bias; jde tedy o důvod pro kontrolu kalibrace/senzoru, nikoli pro slepé kopírování. `old_weewx.pressure` na všech **47 737** kandidátech **přesně souhlasí** s WH1080, patrně jde o odvozený společný původ, **nikoli nezávislé měření**. `barometer` vzniká korekcí vůči hladině moře a při chybně nulové teplotě může být jeho výpočet chybný, byť se hodnoty mění. **Potenciál: obnovit až 47 737 staničních tlaků po dodatečné kalibraci, nikoli 47 737 kompletních meteorologických řádků.**

### 2.4 Závažný konflikt tlaků 2019–2020

Přípravná tabulka z WH1080 uvádí tlak jen v **8/758** řádcích (1 v 2019, 7 v 2020). Starší `old_weewx` nabízí dalších 266 hodnot v 2019 a 483 v 2020, avšak při bezprostředním porovnání s rekonstrukčními sousedy se `old_weewx.barometer` liší v průměru o **~26,4–28,1 hPa**. Stejný rozdíl je systémový i v přesně souběžných existujících záznamech: například v květnu 2019 je staré `pressure` vůči pracovnímu archivu průměrně **−24,46 hPa**, `barometer` **−25,46 hPa**; v srpnu 2020 je rozdíl **−33,18 / −34,52 hPa**. Může jít o jinou kalibraci/stanici, nikoliv o běžný pětiminutový výkyv. Tyto hodnoty **neimportovat bez doložení režimu stanice**.

Ani 8 tlaků přímo ve WH1080 není automaticky spolehlivých: **2020-08-14 15:15, 20:25, 20:35, 20:40, 20:45 a 2020-08-29 09:25** je zdrojový staniční tlak zhruba **34 hPa níže** než okolní pracovní archiv, ačkoli hodnoty `barometer` jsou okolí blízko. Potenciálně konzistentní jsou jen **2019-01-01 00:00** (pozor: interval patří kalendářně roku 2018) a **2020-08-12 13:00**. Tedy pro tlak z těchto 758 kandidátů: **2 k detailnímu ověření, 755 rozporných, 1 bez tlakové hodnoty**. Pro `barometer` existuje 8 WH1080 hodnot k individuální revizi (1 v 2019, 7 v 2020); neodvozovat je ze zjevně chybného staničního tlaku. Časová blízkost a číselná podobnost nestačí k definitivnímu schválení.

## 3. Dodatečné zdánlivé mezery: posunutý timestamp a nepravidelný interval

Mimo přípravnou tabulku leží velmi rozsáhlá skupina WH1080 záznamů s `MOD(dateTime,300)<>0`. U záznamů, kde samotný `interval=5`, jsou počty podle roku koncového timestampu:

| Rok | WH1080 mimo přesnou 5min mřížku | Má v rekonstrukci alespoň jednu sousední hraniční značku floor/ceil | Nemá ani jednu z těchto značek |
|---:|---:|---:|---:|
| 2014 | 11 006 | 10 621 | 385 |
| 2015 | 47 276 | 46 036 | 1 240 |
| 2016 | 68 705 | 58 710 | 9 995 |
| 2017 | 14 374 | 11 338 | 3 036 |
| 2018 | 1 089 | 1 087 | 2 |
| 2019 | 495 | 456 | 39 |
| 2020 | 959 | 684 | 275 |
| **Součet 2014–2020** | **143 904** | **128 932** | **14 972** |

Velká část odchylek zahrnuje posuny **+1, +2, +3 s**, ale také **+60/+120/+180/+240 s** a jiné fáze. Roky 2015–2016 jsou dominantní. Při samotném porovnání `w.dateTime = main.dateTime` by tak byly označeny jako „chybějící“, přestože se může jednat o stejný interval v jiné časové fázi nebo o jiné skutečné pozorování. Odpovídající sousední mřížkový timestamp často *již existuje*, a proto by slepé zaokrouhlení způsobilo duplicitní či časově chybně přiřazené měření. Tabulkových **14 972** bez sousední mřížky jsou pouze **nové případy k posouzení**, nikoliv 14 972 schválených chybějících pěti minut.

Existují také skutečné archivní intervaly **6 minut** (2014: 64, 2015: 782, 2016: 1 170, 2017: 199, 2018: 24, 2019: 22, 2020: 77 v WH1080), v roce 2014 navíc **5 intervalů délky 30 minut**. Tyto řádky nesmí být uměle vydávány za pětiminutová pozorování ani mechanicky rozdělovány. Z časových údajů samotných nelze odlišit korekci systémových hodin, nesynchronní archivaci a druhé senzorové měření: nutný je důkaz z posloupnosti a obsahu (hash/tolerance několika nezávisle proměnlivých veličin) a znalost aktivního zařízení. Pro změny CET/CEST je identita záznamu vždy UTC epocha.

## 4. Počty vyřazení a jistota

**Vzájemně výlučné skupiny na úrovni kandidátního řádku** (součet 49 796): **1 301** zamítnutých pro automatickou obnovu kompletního řádku z důvodu zmrzlých vícečidel; **47 737** zamítnutých pro kompletní řádek, ale s možným dílčím staničním tlakem; **758** podmíněných kandidátů s nestejnou kvalitou jednotlivých veličin. **Počet kompletních řádků schválených k okamžitému importu: 0.** To neznamená, že všechny hodnoty ve 49 796 řádcích jsou nepoužitelné.

**Vyloučení podle veličiny (nejsou sčitatelná napříč veličinami):**
- Teplota/RH/vítr: **1 301** starších vícečidlově zmrazených řádků; **47 737** řádků z let 2016–2018 s falešnou nulou, NULL a převážně falešným bezvětřím.
- `pressure` u 758 nejnovějších: **755** hodnot rozporuplných (266 staré 2019 + 483 staré 2020 + 6 přímých WH1080 2020), **1** bez hodnoty a **2** k další validaci.
- `outHumidity` u 2019: **20** konfliktů exportů, **12** bez druhého údaje, **235** shodných v historických kopiích; u 2020: **147** konfliktů, **342** bez alternativy, **2** shodné, ale nikoliv dostatečně potvrzené. Nemáme oprávnění nazvat shodu kopií nezávislou validací.
- Hraniční test `pressure` 2016–2018: **28 kandidátů** s rozdílem > 2 hPa vůči alespoň jednomu existujícímu pětiminutovému sousedovi (2016: 9, 2017: 19); **2** z nich > 5 hPa. Nejde ještě o definitivní vyřazení měřené hodnoty, nýbrž zadržení ke kontrole.
- Venkovní teplota 2019–2020: **2 časové odchylky > 3 °C** při dostupnosti obou bezprostředních sousedů; neoznačovat automaticky za fyzikálně nemožné.
- Srážky ve skupině 2009/2011 a ve skupině 2016–2018: bez samostatného auditu inkrementů/čítání nelze `rain` ani `rainRate` převzít.

**Čtyři různé stavy v budoucí evidenci:** (a) **MISSING_ROW** — žádný cílový timestamp; (b) **MEASURED_ZERO** — prokazatelně platné měření přesně nula; (c) **INVALID_SENSOR** — existuje numerická hodnota, ale zamrzlé/poškozené čidlo; (d) **ESTIMATE/RECONSTRUCTED** — odhad nebo rekonstruovaná hodnota odlišná od přímého měření. Dále rozlišit **NULL_SENSOR** (řádek existuje, ale veličina chybí), **RAW_ORIGINAL** a **CROSS_SOURCE_UNVERIFIED**. Nikdy nevydávat odhad za změřený údaj.

## 5. Bezpečný algoritmus případného importu (pouze návrh)

1. **Oddělené read-only mapování:** vytvořit mimo zdrojové `archive` návrhy na úrovni `(target_time, variable)` s `source_db`, `source_time`, `source_interval`, `source_usUnits`, originálním číslem, cílovým číslem a jednotkou, typem důkazu, kódem schvalovacího pravidla, skóre a explicitními důvody. Kandidátní tabulku z 30. 10. **neměnit**.
2. **Přiřazení časů:** důkaz UTC a intervalu `(start,end]`, lokální hranice z `Europe/Prague`. `source_interval=5` je nutný, ne dostatečný pro pětiminutový cíl. Nezaokrouhlovat ±1..240 s, pokud nejsou prokázány totožné koncové intervaly a jednoznačný nenásilný převod. Jeden zdrojový interval smí mapovat na nejvýš jeden cílový a obráceně.
3. **Per-variable QC:** kalibrace tlaku podle období; `outTemp=0` s `outHumidity IS NULL` a statickým větrem v 2016–2018 znamená **NULL pro teplotu/vítr** a nezávislé zkoumání tlaku. RH z dlouhých konstantních úseků nepřebírat. Výstupy nesmí obsahovat neočekávané NULL, sentinel ani neověřený výsledek odvozený ze zamrzlého senzoru.
4. **Kontrolní dávka:** exportovat neměnný manifest všech **výslovně schválených** `target_time` + veličin, kontrolní součty a čitelný diff; testovat zkušební import proti jednorázové kopii databáze (nikoliv `archive`). Doložit počet záznamů před/po a případné kolize.
5. **Transakční pravidlo pro budoucí schválený zápis:** předem záloha + kontrolní checksumy, izolovaná transakce, `INSERT ... SELECT ... WHERE NOT EXISTS (SELECT 1 FROM archive WHERE dateTime=target_time)` **jen s vyjmenovanými schválenými sloupci** a `usUnits=16`, `interval=5`. Primární klíč `dateTime` musí zůstat pojistkou; při kolizi **ROLLBACK a manuální revize**, žádné `REPLACE`, `ON DUPLICATE KEY UPDATE`, plošný `UPDATE` ani tiché `INSERT IGNORE`. U neplatných veličin ukládat SQL `NULL` (pokud schéma dovoluje), nikoliv nulu. Neexistuje-li schválená veličina, **nevkládat prázdný řádek**. Všechny odvozené veličiny (rosný bod, rainRate, barometer) až podle samostatných schválených pravidel.
6. **Po zápisu (jen při budoucím explicitním povolení):** přesné porovnání počtu a kontrolních hashů všech **původně existujících** řádků; ověřit `COUNT(DISTINCT dateTime)`, chybějící a duplicitní epochy, pokrytí intervalů, časové hranice a fyzikální statistiky; samostatný changelog a obnovitelný rollback pro nové vložené řádky. Audit a tento report žádný takový zápis neprovedly.

## 6. Navržené regresní/integrační testy

1. **Identita a idempotence:** žádný z existujících `dateTime` se nepřepíše, opětovné přehrání manifestu nevytvoří nový řádek; závod při duplicitě selže a rollbackuje.
2. **Rok a DST:** konkrétní `1483225200` a `1546297200` náleží právě končícímu období před půlnocí; opakovaná podzimní hodina má rozdílnou UTC epochu; jarní neexistující hodina se nesyntetizuje.
3. **Intervaly:** 5min, 6min a 30min mají rozdílnou sémantiku; žádný `interval=6` se bez explicitního resamplingu nevkládá jako 5.
4. **Jednotky:** METRICWX `windSpeed=6.233364...` → METRIC `22.440111...` km/h; `rain=0.3` mm → `0.03` cm *pouze pokud jde o skutečný 5min inkrement*. Rozlišit `NULL`, `0`, chybný senzor a neověřený odhad.
5. **Zamrznutí:** 2009 14/86 a 2011 856/292 dlouhé série se označí; pressure-only 2016–2018 nesmí automaticky povolit teplotu 0 nebo vítr 0.
6. **Tlak:** 2017-06-23 04:15 (+1,44 hPa/5 min) označit; 28 hraničních rozdílů >2 hPa vyžaduje revizi; 2020-08-14 `pressure≈930` proti okolí `≈965` zamítnout, i když barometer ≈1013 působí správně. Kalibrovat zvlášť `pressure` a `barometer`.
7. **Vlhkost:** květen 2019, 29 % vs. zamrzlí sousedé 78 % nesmí být automaticky odsouzeno bez druhé série; RH 96,9 / 75,9 / 94,64 v roce 2020 se nesmí bez validačního důkazu převzít; nikdy nesměšovat chybějící s nulou.
8. **Posun času a kolize:** 1s/60s/240s neznamená automatickou opravu; dva zdroje nesmějí mapovat na jeden cílový interval; potvrzené shodné měření pouze referencovat, neduplikovat.
9. **Provázanost a důkazy:** shoda `old_weewx` s `weewx_WH1080` není nezávislé potvrzení; používat nezávislé okolní reference jen při stejné veličině, čase, výšce a známém přístrojovém režimu. U pressure-only úseků 2016–2018 vyžadovat ověření několika reprezentativních období proti nezávislému tlaku.
10. **Statistika a report:** součet 100+1201+5728+24543+17466+267+491=49796; žádný náhodný pokles/zvýšení během auditu; jmenné a jednotkové filtry explicitní.

## 7. Reprodukovatelné SELECT dotazy (základ)

Spouštět proti `loucka_reconstruction` s SELECT-only přístupem; velké dotazy segmentovat podle roků/dnů a hlídat timeout. Databázové vzorky byly získány 30. 10. 2026; související rozšířený screening proběhl agregací celé přípravné tabulky, porovnáním přesných kolizí a sousedů.

```sql
-- Počty, stav, jednotky a posun podle koncové lokální značky.
SELECT YEAR(FROM_UNIXTIME(target_time)) AS y, status, COUNT(*) AS n,
       COUNT(DISTINCT outTemp_C) AS distinct_temp,
       COUNT(DISTINCT pressure_hPa) AS distinct_pressure,
       COUNT(barometer_hPa) AS barometer_present
FROM wh1080_missing_5min_candidates_20261030
GROUP BY y, status ORDER BY y;

-- Všechny kandidátní cílové časy nyní nejsou v archive; zdroj existuje.
SELECT c.status, COUNT(*) AS n,
       SUM(a.dateTime IS NOT NULL) AS exists_target,
       SUM(w.dateTime IS NOT NULL) AS exists_source
FROM wh1080_missing_5min_candidates_20261030 c
LEFT JOIN archive a ON a.dateTime=c.target_time
LEFT JOIN `weewx_WH1080`.archive w ON w.dateTime=c.source_time
GROUP BY c.status;

-- Prověřit nezávisle dostupnost a konflikt RH starého exportu.
SELECT YEAR(FROM_UNIXTIME(c.target_time)) y, COUNT(*) n,
       SUM(o.outHumidity IS NULL) old_rh_missing,
       SUM(o.outHumidity IS NOT NULL AND ABS(c.outHumidity_pct-o.outHumidity)>20)
           AS rh_conflict_gt20
FROM wh1080_missing_5min_candidates_20261030 c
LEFT JOIN `old_weewx`.archive o ON o.dateTime=c.target_time
WHERE c.status='needs_validation'
GROUP BY y;

-- Kontrola tlaku vůči nejbližším pětiminutovým sousedům hlavní rekonstrukce.
SELECT YEAR(FROM_UNIXTIME(c.target_time)) y,
       COUNT(*) n,
       SUM((p.pressure IS NOT NULL AND ABS(c.pressure_hPa-p.pressure)>2)
        OR (nx.pressure IS NOT NULL AND ABS(c.pressure_hPa-nx.pressure)>2))
           AS adjacent_pressure_conflicts_gt2
FROM wh1080_missing_5min_candidates_20261030 c
LEFT JOIN archive p ON p.dateTime=c.target_time-300
LEFT JOIN archive nx ON nx.dateTime=c.target_time+300
WHERE c.status='pressure_only_review'
GROUP BY y;

-- Vedlejší hledání časově posunutých pěti minut:
-- floor/ceil mají význam pouze kandidátů na kolizi, NIKOLIV automatické mapování.
SELECT YEAR(FROM_UNIXTIME(w.dateTime)) y,
       COUNT(*) off_grid,
       SUM(f.dateTime IS NULL AND ce.dateTime IS NULL) no_grid_neighbor
FROM `weewx_WH1080`.archive w
LEFT JOIN archive f ON f.dateTime=(w.dateTime DIV 300)*300
LEFT JOIN archive ce ON ce.dateTime=((w.dateTime DIV 300)+1)*300
WHERE w.dateTime>=1388534400 AND w.dateTime<1609459200
  AND MOD(w.dateTime,300)<>0 AND w.`interval`=5
GROUP BY y ORDER BY y;
```

**Závěr:** primární další práce má být **pressure-only validace let 2016–2018**, protože zde existuje největší šance obnovit autentické měření bez kopírování poškozených meteorologických veličin. Samostatně pokračovat ve zdrojové forenzní analýze 2019–2020 a časových posunů v letech 2014–2017. Všechny současné návrhy zůstávají **READ-ONLY / NOT APPROVED FOR IMPORT**.
