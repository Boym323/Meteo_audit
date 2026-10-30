# 06 — Specializovaný audit tlaku vzduchu (2009–2026)

**Datum auditu:** 2026-10-30. **Režim:** pouze SELECT přes Weather MCP; žádná data, kandidáti ani kalibrace nebyly změněny. **Stav:** DÍLČÍ FORENZNÍ AUDIT; vyžaduje doplnění konfigurace hardwaru, nezávislé řady ČHMÚ a detailního testu délek konstantních běhů.

## Shrnutí rozhodnutí

- **Pro běžné zobrazení webu:** používat `loucka_reconstruction.archive.barometer` (případně současný produkční `barometer`, po kontrole aktuální synchronizace) jako **tlak redukovaný na hladinu moře, hPa**, s příznakem kvality a s upozorněním na dlouhodobé historické kalibrační nejistoty. Nezaměňovat za stanovištní tlak.
- **`pressure`** je dle standardní sémantiky WeeWX stanovištní/absolutní tlak; **nepoužívat** jej v běžných meteorologických srovnáních s tlakem ČHMÚ přepočteným na hladinu moře. V letech 2016–2018 a 2022 má mnoho NULL hodnot.
- **`altimeter`** je nastavení výškoměru podle standardní atmosféry; není automaticky shodné s `barometer`, byť číselně bývá blízké. Používat samostatně pro letecké účely jen s doloženým algoritmem a kalibrací; zatím **nedoporučeno** jako jediný historický referenční tlak.
- **`pocasi-loucka.eu_GW1000.archive.pressure` nesmí být automaticky považován za opravu stanovištního tlaku**, protože v roce 2026 má přibližně o 11–13 hPa vyšší hodnoty než pracovní archiv, zatímco jeho `barometer-pressure` je trvale jen 39,4 hPa. Je nutné ověřit původ hodnot, konfiguraci redukce i výšku v každé pipeline.
- **Žádné automatické přepočty nebo korekce**. Zaznamenaný trend mezi Loučkou a LuhaMet může pocházet i ze změn metodiky referenční stanice. Samotné shody mezi kopiemi historických DB nepředstavují nezávislé ověření.

## 1. Datové zdroje, sémantika, jednotky

Prohledáno šest schémat: `loucka_reconstruction`, `pocasi-loucka.eu`, `pocasi-loucka.eu_GW1000`, `pocasi-loucka.eu_old`, `old_weewx`, `weewx_WH1080`; klíčovým zdrojem je `archive(dateTime,usUnits,interval,pressure,barometer,altimeter)`. Epoch `dateTime` znamená konec archivního intervalu (UTC v sekundách). Časový údaj SQL `FROM_UNIXTIME()` byl zjištěn jako lokální dle systémové zóny připojení (kontrola: [{"system_tz":"CET","summer":"2026-06-01T02:00:00","autumn":"2025-10-26T02:00:00"}]); denní tabulky níže používají **místní kalendářní den databázového serveru (CET/CEST)**. Pro striktní opakování mimo toto prostředí se vyžaduje explicitní zóna `Europe/Prague`. Na začátku a konci sledovaného okna jde o neúplné dny.

Význam dle dokumentace WeeWX:
- `pressure`: station/gauge pressure, tlak na stanovišti, bez redukce výšky (přibližně QFE, nikoli nadmořský tlak).
- `barometer`: sea-level pressure, tlak redukovaný na hladinu moře podle výšky a teplotních korekcí (meteorologicky QFF/SLP).
- `altimeter`: altimeter setting, redukce podle standardní atmosféry (přibližně QNH); algoritmus závisí na `StdWXCalculate`.
- `usUnits=16` = **METRIC**, `usUnits=17` = **METRICWX**. **V obou systémech je tlaková jednotka mbar (= hPa)**; rozdíly těchto kódů se týkají zejména deště a větru. Ověřené jednotky přímo v datech: `loucka_reconstruction`, produkce, GW1000 a `pocasi-loucka.eu_old` používají 16; `old_weewx`, `weewx_WH1080` používají 17. Žádný převod hPa/mbar se nesmí násobit faktorem 10 ani 100.
- V `old_weewx` chybí původně v letech 2009–2013 hodnoty `pressure` a `altimeter` (v ročních přehledech počet nenulových 0), ač je přítomen `barometer`. Nelze zde dovodit zpětnou kalkulaci bez konfigurace.

Ověření se opírá o: [WeeWX – Meteorological problems](https://weewx.com/docs/latest/usersguide/troubleshooting/meteo/), [WeeWX – Units](https://www.weewx.com/docs/5.4/reference/units/), [ČHMÚ – tlak vzduchu](https://www.chmi.cz/namerena-data/data-z-mericich-stanic/tlak-vzduchu). ČHMÚ výslovně publikuje v mapě tlak redukovaný na hladinu moře, který se nesmí srovnávat přímo se stanovištním `pressure`.

Poznámka o výšce: obec Loučka (okres Zlín) má uváděnu nadmořskou výšku 438 m n. m. ([Regionální informační servis](https://www.risy.cz/cs/vyhledavace/uzemi/585432-loucka/869830-loucka)); **to není ověřená výška samotného tlakového senzoru**. Přibližný odstup `barometer - pressure` 49–51 hPa je s polohou řádově slučitelný, sám ale neurčuje kalibrační správnost ani algoritmus redukce. Pro potvrzení je potřeba historický `weewx.conf` se `[Station] altitude`, `[StdCalibrate]`, `[StdWXCalculate]`, `[PressureCooker]` a nastavením GW1000/GW3000.

## 2. Pokrytí a historické rozdíly mezi šesti archivy

Pracovní i produkční DB mají pro každé roční období 2009–2026 shodný počet nenulových tlakových hodnot ve sledované roční sumarizaci; produkce má roku 2026 o 275 řádků více (87 164 vs. 86 889), což nepředstavuje automatický důkaz stejného obsahu v jednotlivých řádcích. Archiv GW1000 obsahuje zpětně data už od 2009 a nelze jej proto považovat za nezávislé měření hardwaru GW1000 pro celý tento čas. `old_weewx` končí v roce 2020 a `pocasi-loucka.eu_old` má v roce 2023 pouze fragment s NULL tlakem. `weewx_WH1080` má `usUnits=17` a pokrývá 2009–2020.

| Rok | Pracovní řádky | Platný `pressure` | Platný `barometer` | Průměr `barometer-pressure` (hPa) | GW1000 `barometer-pressure` (hPa) |
|---|---:|---:|---:|---:|---:|
| 2009 | 78 093 | 77 211 | 78 093 | 49,75 | 50,04 |
| 2010 | 104 090 | 103 388 | 104 088 | 50,35 | 50,30 |
| 2011 | 62 855 | 62 006 | 62 853 | 50,34 | 50,38 |
| 2012 | 75 334 | 74 305 | 75 334 | 49,07 | 49,38 |
| 2013 | 95 491 | 87 278 | 95 401 | 49,89 | 49,50 |
| 2014 | 95 774 | 92 585 | 95 774 | 50,02 | 50,70 |
| 2015 | 101 261 | 94 464 | 101 261 | 50,19 | 51,94 |
| 2016 | 87 914 | 72 175 | 87 914 | 49,90 | 51,75 |
| 2017 | 76 819 | 48 532 | 76 815 | 49,74 | 51,71 |
| 2018 | 87 624 | 51 163 | 87 624 | 48,97 | 51,15 |
| 2019 | 104 749 | 84 701 | 104 306 | 49,88 | 50,14 |
| 2020 | 102 995 | 92 641 | 98 505 | 50,48 | 50,42 |
| 2021 | 103 459 | 100 618 | 101 715 | 50,54 | 50,73 |
| 2022 | 104 140 | 57 890 | 102 577 | 50,21 | 50,78 |
| 2023 | 104 434 | 103 843 | 104 432 | 50,45 | 51,32 |
| 2024 | 104 935 | 103 168 | 104 935 | 50,33 | 47,63 |
| 2025 | 102 946 | 99 207 | 102 946 | 50,74 | 44,43 |
| 2026* | 86 889 | 86 851 | 86 888 | 50,13 | 39,99 |

*2026 je neúplný rok, stav k okamžiku auditu. Údaje GW1000 pro rok 2026 nezahrnují zcela stejné časové pokrytí jako pracovní databáze, proto roční mezisloupcové průměry nejsou párové rozdíly.*

## 3. Časová osa zjištěných a podezřelých změn

| Období | Pozorování | Interpretace / jistota |
|---|---|---|
| 2009-03-29 | Počátek měření Watson W-8681; tlak `barometer` přítomen, staré `old_weewx.pressure` chybí | Historie hardwaru potvrzena webem stanice; stará derivace není doložena |
| 2011-04-30 až 2011-05-03 | **23 extrémních bodů** `old_weewx.barometer` = 1136,5–1142,1 hPa; ve stejných časech `weewx_WH1080.barometer` = 1001,3–1006,9 hPa, průměr rozdílu −135,2 hPa | **Potvrzený artefakt jednoho archivu**, nikoliv klimatický rekord; v pracovní řadě nejsou hodnoty >1060 hPa |
| 2015–2018 | Velký záporný posun denních průměrů `barometer` Loučka vůči `reference_observations.pressure_hpa` LuhaMet, až ~−24,56 hPa v roce 2018 | **Potvrzený rozdíl řad**, ale bez jisté původní sémantiky referenční veličiny a dalších ČHMÚ hodnot **neprokazuje jednoznačně závadu Loučky** |
| 2017-06 až 2017-08 | 10 bezprostředních pětiminutových skoků pracovní `barometer` o nejméně 5 hPa, maximum +8,56 hPa (2017-08-17 09:55 lokální čas) | Vysoká pravděpodobnost přenosového / odvozeného artefaktu, pro jednotlivé body ověřit sousedy a WH1080 |
| 2020-09 | Historicky uváděná změna sestavy, bez úplného konfiguračního důkazu výšky/kalibrace tlaku | Potenciální bod změny; nerozšiřovat tvrzení bez dokumentace |
| 2022-08-20 | Web stanice uvádí výměnu za GW1000 | Potvrzený hardware milník, **nikoli** potvrzený počátek všech řádků DB s názvem GW1000 |
| **2024-05-26 19:45 lokálně** | GW1000 `barometer-pressure` klesá z asi 51,1 na **47,3 hPa** | **Silný důkaz změny zpracování tlaku v archivu**, příčina dosud neurčena |
| **2024-07-29 19:35 lokálně** | Další skok téhož rozdílu na **44,4 hPa** | Silný důkaz druhé změny |
| **2026-02-03 16:05 lokálně** | Další skok na **39,4 hPa** (předchozí poslední hodnota >42 hPa v 15:55) | Silný důkaz třetí změny; porovnat `pressure`, výšku, absolutní/relativní nastavení konzole |
| **2026-03-08 13:15 lokálně** | **První nenulový rozdíl `barometer`** v párech pracovní ↔ GW1000 po předchozích 18 983 přesných shodách od 2026-01-01 do 2026-03-07 | Zdokumentovaný rozchod pipeline; `pressure` se v archivech lišil už před tím (před 8. 3. průměr −10,125 hPa) |
| Léto 2026 | Měsíční párové `barometer` rozdíly (pracovní minus GW1000) −2,601 v červnu, −3,088 v červenci, **−3,896 v srpnu** | Numericky potvrzeno; neaplikovat průměr jako korekční konstantu |

Pro milníky měření: https://pocasi-loucka.eu/about/ . Časy změn byly zjištěny ze změn mezisloupcového rozdílu, nikoliv z logu servisního zásahu, který chybí.

## 4. WH1080: záznamy mimo pracovní archiv (2016–2018)

V přípravné tabulce `wh1080_missing_5min_candidates_20261030` je přesně **47 737** záznamů se statusem `pressure_only_review`, všem odpovídá `source_db=weewx_WH1080`, `source_usUnits=17`, pětiminutový interval a `time_offset_sec=0`. **Všech 47 737 časů je nepřítomných v `loucka_reconstruction.archive`** (LEFT JOIN `COUNT(r.dateTime)=0`), nikoliv jen NULL v existujících řádcích. Všech 47 737 má `pressure_hPa` i `barometer_hPa`, nulový počet testovaných hodnot mimo hrubé meze `pressure<880 OR >1020`, resp. `barometer<950 OR >1060`.

| Rok | Kandidáti | Rozsah `pressure_hPa` | Rozsah `barometer_hPa` | Průměr `barometer-pressure` |
|---|---:|---|---|---:|
| 2016 | 5 728 | 932,50–970,57 | 983,42–1023,57 | 52,15 |
| 2017 | 24 543 | 923,07–968,37 | 973,47–1021,25 | 51,86 |
| 2018 | 17 466 | 921,85–961,47 | 972,19–1013,97 | 51,44 |

Denní srovnání kandidátů s LuhaMet pouze tam, kde existuje aspoň 5 kandidátů a 20 referenčních hodnot v den, vychází 2016: 57 dnů/−13,006 hPa; 2017: 197 dnů/−16,427 hPa; 2018: 72 dnů/−21,068 hPa. **Nedoporučuje se import** žádné celé kandidátní řady, dokud nebude doložená sémantika a validita nezávislé reference, stabilita čidla a návaznost na sousední známé intervaly. Tlak může být použit jako časový diagnostický signál, ne automaticky jako ověřená rekonstrukce.

Zbylí kandidáti: `frozen_sensor_review` 1 301 (2009, 2011) a `needs_validation` 758 (2019, 2020), z nich jen 8 má tlak; tyto skupiny nejsou schváleny.

## 5. Odchylky mezi pracovní databází a GW1000 od 8. března 2026

**Metodika:** INNER JOIN na přesném `dateTime`, rozdíl vždy **pracovní minus GW1000**. `NULL` se vynechává z příslušného AVG. Rozdíly za stejné časy, nikoli rozdíly nezávisle zprůměrovaných měsíců. Rozdělení dní a měsíců odpovídá systémovému lokálnímu času MariaDB (ověřeno CET/CEST). Začátek okna 2026-03-08T00:00Z, konec 2026-10-30T00:00Z, konec exkluzivní.

| Měsíc | Párovaných řádků | Δ barometer (hPa) | Δ pressure (hPa) | Δ altimeter (hPa) | Min až max Δ barometer |
|---|---:|---:|---:|---:|---|
| 2026-03 | 6543 | 0.53 | -11.131 | -11.598 | -1.99 až 2.707 |
| 2026-04 | 5359 | 0.262 | -11.179 | -11.647 | -2.465 až 3.18 |
| 2026-05 | 7489 | -1.316 | -11.429 | -11.907 | -3.46 až 1.79 |
| 2026-06 | 8631 | -2.601 | -11.873 | -12.37 | -5.267 až -0.145 |
| 2026-07 | 8882 | -3.088 | -12.266 | -12.78 | -5.393 až -0.773 |
| 2026-08 | 8921 | -3.896 | -12.7 | -13.232 | -5.727 až -2.033 |
| 2026-09 | 8635 | -2.439 | -12.672 | -13.202 | -5.199 až -0.407 |
| 2026-10 | 8166 | -1.285 | -12.501 | -13.024 | -3.573 až 0.793 |

**Význam:** GW1000 má po 2026-02-03 `barometer-pressure` téměř **konstantně 39,4 hPa** (od 8. 3. přes 62 tisíc vzorků průměr 39,4 hPa), ale `altimeter-pressure` přibližně 50,84 hPa. V pracovní DB je za 2026 `barometer-pressure` přibližně 50,13 hPa a `altimeter-pressure` 50,28 hPa. Tato nesourodost je silný signál odlišné konfigurace či odvození a vyžaduje prokázání skutečné výšky senzoru a algoritmu; samotný rozdíl **neříká**, který kanál je absolutně kalibračně správný.

### Denní párové průměry (místní CET/CEST)

Úplná denní tabulka včetně počtu párovaných měření; jde o denní průměry **rozdílů v přesně stejném epoch**, nikoli o denní úhrn ani o medián.

| Den | Páry n | Δ barometer (hPa) | Δ pressure (hPa) | Δ altimeter (hPa) |
|---|---:|---:|---:|---:|
| 2026-03-08 | 275 | 0.285 | -11.527 | -12.008 |
| 2026-03-09 | 288 | 0.864 | -11.062 | -11.524 |
| 2026-03-10 | 287 | 0.241 | -11.078 | -11.542 |
| 2026-03-11 | 267 | 0.137 | -11.096 | -11.56 |
| 2026-03-12 | 285 | 0.383 | -11.101 | -11.565 |
| 2026-03-13 | 288 | 0.109 | -11.096 | -11.561 |
| 2026-03-14 | 288 | -0.879 | -11.129 | -11.596 |
| 2026-03-15 | 287 | -0.444 | -11.126 | -11.593 |
| 2026-03-16 | 288 | 1.038 | -11.104 | -11.569 |
| 2026-03-17 | 288 | 1.352 | -11.08 | -11.543 |
| 2026-03-18 | 287 | 0.548 | -11.076 | -11.539 |
| 2026-03-19 | 285 | 0.784 | -11.082 | -11.546 |
| 2026-03-20 | 286 | 0.709 | -11.096 | -11.561 |
| 2026-03-21 | 288 | 0.757 | -11.099 | -11.564 |
| 2026-03-22 | 288 | 0.815 | -11.11 | -11.576 |
| 2026-03-23 | 288 | 0.341 | -11.108 | -11.573 |
| 2026-03-24 | 288 | 0.428 | -11.096 | -11.561 |
| 2026-03-25 | 288 | -0.285 | -11.109 | -11.575 |
| 2026-03-26 | 288 | 0.666 | -11.113 | -11.58 |
| 2026-03-27 | 288 | 1.166 | -11.137 | -11.604 |
| 2026-03-28 | 248 | 1.23 | -11.168 | -11.636 |
| 2026-03-29 | 157 | 1.083 | -11.268 | -11.74 |
| 2026-03-30 | 200 | 0.671 | -11.219 | -11.689 |
| 2026-03-31 | 223 | 1.224 | -11.202 | -11.672 |
| 2026-04-01 | 173 | 1.036 | -11.185 | -11.653 |
| 2026-04-02 | 159 | 0.101 | -11.183 | -11.652 |
| 2026-04-03 | 26 | 0.882 | -11.14 | -11.607 |
| 2026-04-04 | 196 | 0.632 | -11.124 | -11.59 |
| 2026-04-05 | 160 | -0.023 | -11.112 | -11.577 |
| 2026-04-06 | 184 | -0.022 | -11.135 | -11.601 |
| 2026-04-07 | 173 | 0.863 | -11.133 | -11.599 |
| 2026-04-08 | 184 | 1.342 | -11.12 | -11.585 |
| 2026-04-09 | 171 | 1.352 | -11.135 | -11.601 |
| 2026-04-10 | 156 | 1.398 | -11.193 | -11.661 |
| 2026-04-11 | 161 | 1.023 | -11.194 | -11.663 |
| 2026-04-12 | 163 | 0.636 | -11.189 | -11.658 |
| 2026-04-13 | 174 | -0.485 | -11.165 | -11.633 |
| 2026-04-14 | 187 | -0.195 | -11.156 | -11.624 |
| 2026-04-15 | 198 | -0.115 | -11.142 | -11.608 |
| 2026-04-16 | 194 | -0.422 | -11.152 | -11.619 |
| 2026-04-17 | 204 | -0.288 | -11.159 | -11.626 |
| 2026-04-18 | 183 | 0.027 | -11.158 | -11.626 |
| 2026-04-19 | 192 | -0.568 | -11.191 | -11.66 |
| 2026-04-20 | 199 | 0.146 | -11.191 | -11.66 |
| 2026-04-21 | 181 | 0.39 | -11.163 | -11.63 |
| 2026-04-22 | 213 | 0.045 | -11.361 | -11.837 |
| 2026-04-23 | 188 | 0.099 | -11.227 | -11.697 |
| 2026-04-24 | 188 | -0.666 | -11.209 | -11.678 |
| 2026-04-25 | 209 | -0.545 | -11.208 | -11.678 |
| 2026-04-26 | 194 | 0.056 | -11.215 | -11.684 |
| 2026-04-27 | 171 | 0.466 | -11.205 | -11.674 |
| 2026-04-28 | 188 | 0.099 | -11.198 | -11.667 |
| 2026-04-29 | 186 | 0.561 | -11.198 | -11.666 |
| 2026-04-30 | 204 | 1.186 | -11.156 | -11.622 |
| 2026-05-01 | 175 | 0.581 | -11.154 | -11.62 |
| 2026-05-02 | 173 | -0.654 | -11.199 | -11.667 |
| 2026-05-03 | 214 | -1.322 | -11.272 | -11.744 |
| 2026-05-04 | 237 | -1.618 | -11.373 | -11.85 |
| 2026-05-05 | 252 | -2.146 | -11.406 | -11.884 |
| 2026-05-06 | 246 | -2.359 | -11.42 | -11.899 |
| 2026-05-07 | 248 | -1.96 | -11.398 | -11.876 |
| 2026-05-08 | 242 | -1.179 | -11.374 | -11.85 |
| 2026-05-09 | 224 | -0.67 | -11.369 | -11.845 |
| 2026-05-10 | 222 | -0.797 | -11.354 | -11.829 |
| 2026-05-11 | 243 | -1.919 | -11.363 | -11.841 |
| 2026-05-12 | 229 | -1 | -11.316 | -11.791 |
| 2026-05-13 | 181 | -0.409 | -11.276 | -11.749 |
| 2026-05-14 | 192 | -1.091 | -11.286 | -11.76 |
| 2026-05-15 | 196 | -1.178 | -11.267 | -11.74 |
| 2026-05-16 | 199 | -0.81 | -11.264 | -11.737 |
| 2026-05-17 | 184 | -0.086 | -11.248 | -11.72 |
| 2026-05-18 | 173 | 0.029 | -11.231 | -11.702 |
| 2026-05-19 | 203 | -0.696 | -11.255 | -11.726 |
| 2026-05-20 | 288 | -0.992 | -11.373 | -11.849 |
| 2026-05-21 | 288 | -1.104 | -11.435 | -11.913 |
| 2026-05-22 | 288 | -1.007 | -11.454 | -11.932 |
| 2026-05-23 | 288 | -1.271 | -11.504 | -11.985 |
| 2026-05-24 | 288 | -1.566 | -11.539 | -12.021 |
| 2026-05-25 | 288 | -1.839 | -11.583 | -12.067 |
| 2026-05-26 | 288 | -1.855 | -11.637 | -12.124 |
| 2026-05-27 | 288 | -2.401 | -11.682 | -12.171 |
| 2026-05-28 | 288 | -1.683 | -11.672 | -12.16 |
| 2026-05-29 | 288 | -1.093 | -11.628 | -12.114 |
| 2026-05-30 | 288 | -1.682 | -11.605 | -12.091 |
| 2026-05-31 | 288 | -2.36 | -11.617 | -12.104 |
| 2026-06-01 | 288 | -2.132 | -11.637 | -12.125 |
| 2026-06-02 | 288 | -1.878 | -11.621 | -12.108 |
| 2026-06-03 | 288 | -2.279 | -11.627 | -12.115 |
| 2026-06-04 | 288 | -2.069 | -11.636 | -12.124 |
| 2026-06-05 | 288 | -1.747 | -11.608 | -12.095 |
| 2026-06-06 | 288 | -1.363 | -11.614 | -12.1 |
| 2026-06-07 | 287 | -1.993 | -11.664 | -12.152 |
| 2026-06-08 | 288 | -2.033 | -11.74 | -12.232 |
| 2026-06-09 | 288 | -2.584 | -11.779 | -12.273 |
| 2026-06-10 | 288 | -1.704 | -11.776 | -12.27 |
| 2026-06-11 | 288 | -1.179 | -11.719 | -12.21 |
| 2026-06-12 | 288 | -1.039 | -11.681 | -12.17 |
| 2026-06-13 | 288 | -1.736 | -11.692 | -12.182 |
| 2026-06-14 | 283 | -1.962 | -11.701 | -12.191 |
| 2026-06-15 | 288 | -1.504 | -11.671 | -12.16 |
| 2026-06-16 | 288 | -1.406 | -11.658 | -12.146 |
| 2026-06-17 | 288 | -2.078 | -11.705 | -12.196 |
| 2026-06-18 | 288 | -2.371 | -11.764 | -12.256 |
| 2026-06-19 | 288 | -3.013 | -11.849 | -12.345 |
| 2026-06-20 | 288 | -3.437 | -11.943 | -12.443 |
| 2026-06-21 | 288 | -3.34 | -11.992 | -12.494 |
| 2026-06-22 | 288 | -3.248 | -12.071 | -12.575 |
| 2026-06-23 | 288 | -3.286 | -12.123 | -12.63 |
| 2026-06-24 | 288 | -3.011 | -12.108 | -12.615 |
| 2026-06-25 | 288 | -3.511 | -12.137 | -12.646 |
| 2026-06-26 | 287 | -3.933 | -12.217 | -12.729 |
| 2026-06-27 | 287 | -4.332 | -12.335 | -12.851 |
| 2026-06-28 | 287 | -4.555 | -12.359 | -12.876 |
| 2026-06-29 | 288 | -4.727 | -12.364 | -12.882 |
| 2026-06-30 | 288 | -4.588 | -12.406 | -12.926 |
| 2026-07-01 | 288 | -4.509 | -12.445 | -12.967 |
| 2026-07-02 | 288 | -3.365 | -12.414 | -12.934 |
| 2026-07-03 | 288 | -2.868 | -12.319 | -12.835 |
| 2026-07-04 | 286 | -2.477 | -12.231 | -12.742 |
| 2026-07-05 | 288 | -2.437 | -12.133 | -12.641 |
| 2026-07-06 | 288 | -2.222 | -12.078 | -12.583 |
| 2026-07-07 | 285 | -3.002 | -12.07 | -12.576 |
| 2026-07-08 | 287 | -3.202 | -12.147 | -12.656 |
| 2026-07-09 | 288 | -2.462 | -12.116 | -12.623 |
| 2026-07-10 | 285 | -2.585 | -12.116 | -12.623 |
| 2026-07-11 | 282 | -2.784 | -12.13 | -12.638 |
| 2026-07-12 | 281 | -2.802 | -12.143 | -12.651 |
| 2026-07-13 | 288 | -2.853 | -12.142 | -12.65 |
| 2026-07-14 | 287 | -3.291 | -12.186 | -12.696 |
| 2026-07-15 | 287 | -3.304 | -12.229 | -12.741 |
| 2026-07-16 | 285 | -3.34 | -12.286 | -12.8 |
| 2026-07-17 | 282 | -4.004 | -12.335 | -12.852 |
| 2026-07-18 | 286 | -3.679 | -12.355 | -12.873 |
| 2026-07-19 | 287 | -3.178 | -12.368 | -12.887 |
| 2026-07-20 | 288 | -2.559 | -12.363 | -12.881 |
| 2026-07-21 | 288 | -2.682 | -12.316 | -12.832 |
| 2026-07-22 | 287 | -2.327 | -12.305 | -12.82 |
| 2026-07-23 | 288 | -2.565 | -12.267 | -12.781 |
| 2026-07-24 | 287 | -2.117 | -12.217 | -12.728 |
| 2026-07-25 | 285 | -2.627 | -12.215 | -12.726 |
| 2026-07-26 | 284 | -3.89 | -12.265 | -12.779 |
| 2026-07-27 | 288 | -3.667 | -12.317 | -12.834 |
| 2026-07-28 | 288 | -2.763 | -12.325 | -12.841 |
| 2026-07-29 | 288 | -3.279 | -12.396 | -12.914 |
| 2026-07-30 | 288 | -4.204 | -12.459 | -12.98 |
| 2026-07-31 | 287 | -4.694 | -12.565 | -13.092 |
| 2026-08-01 | 288 | -4.949 | -12.663 | -13.194 |
| 2026-08-02 | 285 | -4.108 | -12.674 | -13.205 |
| 2026-08-03 | 288 | -4.517 | -12.712 | -13.245 |
| 2026-08-04 | 288 | -5.324 | -12.763 | -13.298 |
| 2026-08-05 | 288 | -5.382 | -12.832 | -13.369 |
| 2026-08-06 | 288 | -5.127 | -12.852 | -13.39 |
| 2026-08-07 | 287 | -4.223 | -12.846 | -13.384 |
| 2026-08-08 | 288 | -3.647 | -12.817 | -13.354 |
| 2026-08-09 | 288 | -3.566 | -12.782 | -13.317 |
| 2026-08-10 | 287 | -4.311 | -12.777 | -13.312 |
| 2026-08-11 | 288 | -4.224 | -12.792 | -13.327 |
| 2026-08-12 | 287 | -3.102 | -12.723 | -13.255 |
| 2026-08-13 | 288 | -2.987 | -12.657 | -13.186 |
| 2026-08-14 | 288 | -3.351 | -12.613 | -13.141 |
| 2026-08-15 | 287 | -4.083 | -12.646 | -13.176 |
| 2026-08-16 | 288 | -4.434 | -12.678 | -13.209 |
| 2026-08-17 | 288 | -4.263 | -12.71 | -13.243 |
| 2026-08-18 | 288 | -3.3 | -12.653 | -13.183 |
| 2026-08-19 | 288 | -3.406 | -12.556 | -13.083 |
| 2026-08-20 | 288 | -4.28 | -12.603 | -13.132 |
| 2026-08-21 | 288 | -4.197 | -12.661 | -13.192 |
| 2026-08-22 | 288 | -3.533 | -12.672 | -13.203 |
| 2026-08-23 | 288 | -2.54 | -12.612 | -13.14 |
| 2026-08-24 | 288 | -2.706 | -12.595 | -13.122 |
| 2026-08-25 | 288 | -3.243 | -12.586 | -13.113 |
| 2026-08-26 | 288 | -3.157 | -12.6 | -13.128 |
| 2026-08-27 | 288 | -3.477 | -12.674 | -13.205 |
| 2026-08-28 | 288 | -4.082 | -12.726 | -13.259 |
| 2026-08-29 | 288 | -3.79 | -12.745 | -13.279 |
| 2026-08-30 | 288 | -3.551 | -12.735 | -13.269 |
| 2026-08-31 | 288 | -3.926 | -12.737 | -13.271 |
| 2026-09-01 | 288 | -3.338 | -12.753 | -13.287 |
| 2026-09-02 | 288 | -2.946 | -12.726 | -13.258 |
| 2026-09-03 | 288 | -3.058 | -12.674 | -13.205 |
| 2026-09-04 | 288 | -3.406 | -12.668 | -13.199 |
| 2026-09-05 | 288 | -3.551 | -12.721 | -13.253 |
| 2026-09-06 | 288 | -2.594 | -12.706 | -13.238 |
| 2026-09-07 | 288 | -2.254 | -12.662 | -13.192 |
| 2026-09-08 | 288 | -3.661 | -12.701 | -13.233 |
| 2026-09-09 | 287 | -4.706 | -12.796 | -13.333 |
| 2026-09-10 | 288 | -3.144 | -12.83 | -13.367 |
| 2026-09-11 | 288 | -2.016 | -12.738 | -13.272 |
| 2026-09-12 | 288 | -1.653 | -12.708 | -13.24 |
| 2026-09-13 | 288 | -2.173 | -12.657 | -13.186 |
| 2026-09-14 | 288 | -2.609 | -12.664 | -13.194 |
| 2026-09-15 | 288 | -2.439 | -12.713 | -13.245 |
| 2026-09-16 | 287 | -3.057 | -12.758 | -13.293 |
| 2026-09-17 | 288 | -3.124 | -12.784 | -13.319 |
| 2026-09-18 | 288 | -2.533 | -12.762 | -13.297 |
| 2026-09-19 | 288 | -2.493 | -12.753 | -13.286 |
| 2026-09-20 | 288 | -2.68 | -12.746 | -13.279 |
| 2026-09-21 | 288 | -2.181 | -12.722 | -13.254 |
| 2026-09-22 | 287 | -1.263 | -12.629 | -13.157 |
| 2026-09-23 | 288 | -1.24 | -12.581 | -13.108 |
| 2026-09-24 | 288 | -1.024 | -12.516 | -13.04 |
| 2026-09-25 | 286 | -1.459 | -12.476 | -12.998 |
| 2026-09-26 | 288 | -1.282 | -12.505 | -13.028 |
| 2026-09-27 | 288 | -1.492 | -12.489 | -13.011 |
| 2026-09-28 | 288 | -1.866 | -12.538 | -13.062 |
| 2026-09-29 | 288 | -1.947 | -12.579 | -13.105 |
| 2026-09-30 | 288 | -1.991 | -12.604 | -13.131 |
| 2026-10-01 | 288 | -2.155 | -12.635 | -13.163 |
| 2026-10-02 | 288 | -1.762 | -12.625 | -13.152 |
| 2026-10-03 | 288 | -1.66 | -12.621 | -13.149 |
| 2026-10-04 | 288 | -1.729 | -12.625 | -13.152 |
| 2026-10-05 | 288 | -2.008 | -12.609 | -13.136 |
| 2026-10-06 | 288 | -2.063 | -12.619 | -13.147 |
| 2026-10-07 | 288 | -2.476 | -12.598 | -13.126 |
| 2026-10-08 | 288 | -3.205 | -12.619 | -13.148 |
| 2026-10-09 | 288 | -2.021 | -12.631 | -13.16 |
| 2026-10-10 | 288 | -2.02 | -12.563 | -13.09 |
| 2026-10-11 | 288 | -2.017 | -12.56 | -13.087 |
| 2026-10-12 | 288 | -0.665 | -12.508 | -13.032 |
| 2026-10-13 | 288 | -0.222 | -12.453 | -12.973 |
| 2026-10-14 | 288 | -0.03 | -12.412 | -12.931 |
| 2026-10-15 | 288 | -0.132 | -12.425 | -12.944 |
| 2026-10-16 | 287 | -0.841 | -12.485 | -13.007 |
| 2026-10-17 | 249 | -1.155 | -12.442 | -12.963 |
| 2026-10-18 | 288 | -1.417 | -12.458 | -12.98 |
| 2026-10-19 | 288 | -0.716 | -12.42 | -12.94 |
| 2026-10-20 | 288 | -1.125 | -12.393 | -12.912 |
| 2026-10-21 | 286 | -2.485 | -12.473 | -12.996 |
| 2026-10-22 | 288 | -1.627 | -12.475 | -12.998 |
| 2026-10-23 | 288 | -0.358 | -12.444 | -12.965 |
| 2026-10-24 | 288 | -0.98 | -12.406 | -12.926 |
| 2026-10-25 | 300 | -0.621 | -12.391 | -12.91 |
| 2026-10-26 | 287 | -0.638 | -12.387 | -12.906 |
| 2026-10-27 | 288 | -0.026 | -12.391 | -12.909 |
| 2026-10-28 | 287 | -0.245 | -12.403 | -12.922 |
| 2026-10-29 | 134 | -0.379 | -12.37 | -12.887 |

## 6. Nezávislé reference: LuhaMet, ILOUKA4 a ČHMÚ

`loucka_reconstruction.reference_stations` obsahuje `luhamet_sehradice` (318 m n. m.), `wu_ilouka4` (nadmořská výška nezadána). V `reference_observations` je **1 157 794** časových záznamů LuhaMet, z toho **1 157 664 s nenulovým `pressure_hpa`**, od 2015-04-17 do 2026-10-29; ILOUKA4 má **494 844** řádků, ale **0 záznamů `pressure_hpa`**. Samotný název `pressure_hpa` v referenci **nepotvrzuje**, zda jde o stanovištní nebo redukovaný tlak, a nesmí se bez ověření přejmenovat na QFF.

**Dlouhodobé srovnání denních průměrů `barometer` pracovní − `pressure_hpa` LuhaMet** (min. 100 hodnot Loučka a 50 LuhaMet/den; měnící se pokrytí):
| Rok | Počet porovnaných dnů | Průměrný rozdíl (hPa) |
|---|---:|---:|
| 2015 | 212 | −12,899 |
| 2016 | 324 | −14,179 |
| 2017 | 295 | −18,354 |
| 2018 | 165 | −24,556 |
| 2019 | 333 | −7,891 |
| 2020 | 361 | −3,092 |
| 2021 | 357 | −3,474 |
| 2022 | 363 | −0,183 |
| 2023 | 365 | +1,756 |
| 2024 | 366 | +2,051 |
| 2025 | 361 | +4,761 |

**Varování:** tyto velké změny nelze považovat za prokázaný kalibrační drift Loučky bez kontroly původní sémantiky a konfigurační historie LuhaMet, homogenity obou stanic a nezávislé ČHMÚ řady. Srovnání denních průměrů není synchronizovaný párový test.

V roce 2026 (místní dny s ≥200 záznamy Loučky a ≥100 LuhaMet/den) je následující srovnání **rozdílů denních průměrů**, nikoliv přesných pětiminutových párů:
| Měsíc 2026 | Dnů | Pracovní barometer − LuhaMet (hPa) | GW1000 barometer − LuhaMet (hPa) |
|---|---:|---:|---:|
| březen | 31 | −1,637 | −2,025 |
| duben | 30 | −1,576 | −1,783 |
| květen | 31 | −2,464 | −1,246 |
| červen | 30 | −3,161 | −0,560 |
| červenec | 31 | −2,501 | +0,589 |
| srpen | 31 | +0,409 | +4,306 |
| září | 30 | +1,190 | +3,630 |
| říjen | 28 | +1,811 | +3,104 |

**ČHMÚ:** oficiální stránka ČHMÚ uvádí pro mapu **tlak redukovaný na hladinu moře (hPa)** a interval měření 10 min: https://www.chmi.cz/namerena-data/data-z-mericich-stanic/tlak-vzduchu . Archiv ČHMÚ s rozlišením 1 h / 10 min existuje, např. https://opendata.chmi.cz/meteorology/climate/historical/data/1hour/ ; zde ale **nebyla stažena, validována a numericky spárována konkrétní historická tlaková řada ČHMÚ s identifikátorem stanice**. Úkol nezávislého číselného potvrzení kalibračních zlomů vůči ČHMÚ tedy zůstává otevřený, a tato zpráva žádnou takovou shodu nepředstírá. Pro další krok je nutné určit blízkou stanici s tlakem, ověřit prvky měřeného `P` a případného `P_hm`, časový údaj, kvalitu, výšku senzoru a režim redukce. Porovnávat `barometer` pouze s potvrzeným tlakem přepočteným na hladinu moře, `pressure` pouze s tlakem v nadmořské výšce příslušného stanoviště po fyzikálně odůvodněné změně výškové reference.

## 7. Skoky, konstantní čidla, přenosové artefakty

- **Potvrzený izolovaný archivní extrém:** `old_weewx.barometer` z 2011-04-30 až 2011-05-03 obsahuje 23 vzorků 1136,5–1142,1 hPa. Ve shodných časech WH1080 poskytuje běžné hodnoty 1001,3–1006,9 hPa. Nevydávat extrém za tlakový rekord.
- **Pracovní 2017:** self-join `dateTime-300` našel **10** skoků `barometer` ≥5 hPa mezi sousedními pětiminutovými záznamy a **0** obdobných skoků `pressure`; vybrané časy (lokální): 2017-06-11 07:50 (+6,49), 2017-06-11 08:00 (−6,64), 2017-08-02 08:00 (−8,47), 2017-08-17 09:55 (+8,56). V některých z těchto intervalů je `pressure=NULL`. Doporučena ruční validace s referencí a zdrojovým WH1080.
- **Pracovní 2011:** 0 skoků `barometer` ≥5 hPa v sousedních 5min záznamech, **2017** viz výše, **pracovní 2026:** 0 takových skoků u `barometer`, `pressure` i `altimeter` (86 794 sousedních pětiminutových párů).
- **Celodenní konstantní tlak:** kontrola denních rozpětí `MAX(barometer)-MIN(barometer)≤0,1 hPa` s více než 200 body/den nenašla žádný takový den v pracovní DB v letech 2016–2018 ani v roce 2026. **Nevylučuje to kratší zamrznutí po hodiny**; přesný run-length test zůstává otevřený.
- **Hrubé fyzikální meze:** pracovní DB v letech 2009–2026 nenalezena `barometer<950 OR >1060`, `pressure<880 OR >1020`, `altimeter<950 OR >1060`; jde o velmi široký screening, nikoliv potvrzení bezchybnosti. Úseky s `NULL` a nenápadnějšími artefakty se tím nevyřazují.

## 8. Prioritizovaný postup, bez zásahu do DB

1. Získat původní konfiguraci pro milníky 2009, 2013, 2020, 2022, 2024-05-26, 2024-07-29 a 2026-02-03: `altitude`, `StdCalibrate`, `StdWXCalculate`, `PressureCooker`, relativní a absolutní tlak brány/konzole, algoritmus, výška senzoru, datum změny firmware.
2. Zvolit stanici ČHMÚ s ověřenými časovými historickými daty (ideálně 2015–2026), **prokázat sémantiku P/P_hm** a porovnat souběžné UTC hodiny/dny s LuhaMet a Loučkou. Kvantifikovat bias, MAD, trend a skoky po změně zařízení, včetně sezónnosti a nejistoty reference.
3. Pro 47 737 WH1080 kandidátů provést test sousedních známých intervalů (zejména `pressure` vs `barometer`), korelace změn s ČHMÚ, stability a nezávislé kontroly; *žádný import* bez výslovného schválení.
4. Provést úplné časové scanování po samostatných rocích a zdrojích: >2/>5 hPa za 5 minut, opakované hodnoty s run-length 30/60/180 minut, hodinové odchylky vůči referencím, výpadky; odlišovat skutečný meteorologický vývoj a výpadek telemetrie.
5. Nechat historické hodnoty nezměněné. Pro web zobrazovat `barometer` + jasný QC příznak a zdroj; pro historické extrémy/roční trendy srovnatelného tlaku používat až validované úseky nebo metadata kvality. Nevyvozovat klimatický trend z nehomogenizované série.

## 9. Reprodukovatelné čtecí SQL

V SQL vždy identifikovat citlivé názvy schémat backticky. Příklad jednotek a roku:

```sql
SELECT YEAR(FROM_UNIXTIME(dateTime)) yr, usUnits, COUNT(*) rows_n,
       COUNT(pressure) np, COUNT(barometer) nb, COUNT(altimeter) na,
       ROUND(AVG(barometer-pressure),2) bp
FROM `loucka_reconstruction`.archive
GROUP BY YEAR(FROM_UNIXTIME(dateTime)), usUnits
ORDER BY yr;
```

Přesně párované denní rozdíly 2026 (testované rozsahy a původní SQL použité k vytvoření této tabulky):

```sql
SELECT DATE(FROM_UNIXTIME(r.dateTime)) AS d,COUNT(*) AS n, ROUND(AVG(r.barometer-g.barometer),3) AS db, ROUND(AVG(r.pressure-g.pressure),3) AS dp,ROUND(AVG(r.altimeter-g.altimeter),3) AS da,ROUND(MIN(r.barometer-g.barometer),3) AS dbmin,ROUND(MAX(r.barometer-g.barometer),3) AS dbmax FROM `loucka_reconstruction`.archive r JOIN `pocasi-loucka.eu_GW1000`.archive g ON r.dateTime=g.dateTime WHERE r.dateTime>=1772928000 AND r.dateTime<1793404800 GROUP BY DATE(FROM_UNIXTIME(r.dateTime)) ORDER BY d;
```

Přesně párované měsíční rozdíly:

```sql
SELECT DATE_FORMAT(FROM_UNIXTIME(r.dateTime),'%Y-%m') AS ym,COUNT(*) AS n,ROUND(AVG(r.barometer-g.barometer),3) AS db,ROUND(AVG(r.pressure-g.pressure),3) AS dp,ROUND(AVG(r.altimeter-g.altimeter),3) AS da,ROUND(MIN(r.barometer-g.barometer),3) AS dbmin,ROUND(MAX(r.barometer-g.barometer),3) AS dbmax FROM `loucka_reconstruction`.archive r JOIN `pocasi-loucka.eu_GW1000`.archive g ON r.dateTime=g.dateTime WHERE r.dateTime>=1772928000 AND r.dateTime<1793404800 GROUP BY DATE_FORMAT(FROM_UNIXTIME(r.dateTime),'%Y-%m') ORDER BY ym;
```

Kontrola WH kandidátů vůči existujícím cílovým řádkům (bez možnosti zápisu):

```sql
SELECT COUNT(*) candidates, COUNT(r.dateTime) matched
FROM `loucka_reconstruction`.wh1080_missing_5min_candidates_20261030 c
LEFT JOIN `loucka_reconstruction`.archive r ON r.dateTime=c.target_time
WHERE c.status='pressure_only_review';
```

Pozn.: dlouhodobé a referenční souhrny používají `AVG` přes ne-NULL hodnoty. Referenční denní srovnání agreguje dva zdroje po samostatných občanských dnech a pak porovnává průměry; nikdy nepředstavuje důkaz korekce jednotlivého intervalu.

**Verdikt:** Zdokumentované změny tlakových veličin a historické mezizdrojové rozdíly jsou významné, **ale příčinná kalibrace není potvrzena**. Povolený zásah: pouze doplnění tohoto read-only reportu do GitHubu. Změny DB: **0**.
