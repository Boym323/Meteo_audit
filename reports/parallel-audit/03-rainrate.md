# 03 – Forenzní audit historického `rainRate` (2009–2026)

**Datum měření:** 2026-10-30. **Stav:** READ-ONLY / dokončený průzkumný audit se zdokumentovanými omezeními. **Výstup:** samostatná větev `audit/parallel-03-rainrate-2009-2026`. **Zásada:** žádné změny DB; žádné plošné `rainRate = rain × 12`.

## 1. Rozsah, provenience a metoda

Přímo přes Weather MCP byly přečteny archivy `loucka_reconstruction.archive`, `pocasi-loucka.eu.archive` (produkce), `pocasi-loucka.eu_old.archive`, `pocasi-loucka.eu_GW1000.archive`, `old_weewx.archive` a `weewx_WH1080.archive`. SQL bylo výhradně `SELECT`, vždy s omezením `dateTime` na historické období nebo dílčí rok/měsíc/událost, včetně meziarchivních spojení dle **identického unixového `dateTime`**. Pro některé auditní agregace byl použit `YEAR(FROM_UNIXTIME(dateTime))` v relaci `@@session.time_zone=SYSTEM`, `@@system_time_zone=CET`. Jde o analytické **roční skupiny podle časové zóny DB**; pro formální finální roční publikaci je třeba znovu vyčíslit přesné lokální hranice `Europe/Prague` a konvenci WeeWX `(start,end]` (viz již existující `src/meteo_audit/rainrate.py`). Hraniční půlnoční řádky se mohou lišit. Hlavní párové rozdíly 2019–2025 a jednotlivé incidenty tím nejsou zaměňovány za čisté UTC roky.

Přehled pokrytí a jednotek:

| Archiv | Počet řádků ve vymezeném období | `usUnits` | Kladné `rainRate` | Maximální uložený `rainRate` |
|---|---:|---:|---:|---:|
| `loucka_reconstruction` | 1 679 802 | 16 | 59 222 | 5,72 |
| `pocasi-loucka.eu` | 1 680 076 | 16 | 2 761 | 5,72 |
| `pocasi-loucka.eu_old` | 1 336 195 | 16 | 39 588 | 45,12 |
| `pocasi-loucka.eu_GW1000` | 1 674 765 | 16 | 62 407 | 45,12 |
| `old_weewx` | 1 104 422 | 17 | 29 423 | 451,2 |
| `weewx_WH1080` | 1 112 201 | 17 | 29 779 | 451,2 |

První dostupné měření je z března 2009, rok 2009 není celý. Rok 2026 je pouze do data auditu, počet záznamů mezi zdroji se liší a některé pozdní GW1000 záznamy chybí. Vyšší počet `rainRate>0` automaticky neznamená přesnější zdroj.

## 2. Jednotky a význam proměnné

Ve WeeWX `usUnits=16 (0x10)` znamená **METRIC**: `rain` je v **cm** a `rainRate` v **cm/h**. `usUnits=17 (0x11)` znamená **METRICWX**: `rain` v **mm**, `rainRate` v **mm/h**. K normalizaci na `mm/h` násobit `rainRate` z archivů s `usUnits=16` **10**, z archivů s `usUnits=17` **1**; analogicky `rain` (cm→mm). Přímo změřeno: při shodném `dateTime` dosahují hodnoty `old_weewx.rainRate / 10` shody s `GW1000.rainRate` téměř ve všech překryvech; pro roky 2009–2015 v porovnání např. 2009 jen 1 odchylka z 74 425 shodných timestampů, 2010 0/102 127, 2015 0/55 297. Staré `old_weewx` a `weewx_WH1080` jsou na společných timestampech shodné v nenulových hodnotách `rainRate` (roční počty rozdílů 0), liší se mimo jiné v `NULL`/0 (2014: 59 starých NULL, 2015: 41).

WeeWX dokumentace: https://weewx.com/docs/5.0/reference/units/ a https://www.weewx.com/docs/latest/reference/weewx-options/stdwxcalculate/. `RainRater` může vytvářet **klouzavý průměr za posledních 1800 sekund** (výchozí konfigurace), zatímco některé stanice dodávají **vlastní intenzitu**. Tyto mechanizmy se nesmějí bez původního `weewx.conf`, záznamu LOOP packetů a nastavení driveru automaticky prohlásit za prokázané pro každou éru. Zjištěné přetrvávání intenzity i v suchém intervalu je slučitelné s klouzavým oknem, ale samo jej nedokazuje. `rain` naopak typicky představuje úhrn archivního intervalu; historické výjimky jsou níže.

**Odvozený intervalový průměr (nová výpočetní veličina, nikoli náhrada `rainRate`):** pro správný nekumulativní `rain_mm` a skutečný `interval_min` platí `rate_interval_avg_mm_h = rain_mm × 60 / interval_min`; jen při intervalu 5 min je to `rain_mm × 12` (u `rain_cm`: `rain_cm × 120`). Není to nutně okamžitá/30minutová intenzita přístroje. Použití na kumulativní starý čítač nebo na nesprávně rekonstruovanou srážku je **nesprávné**. U 5min intervalu 0 mm, ale kladného `rainRate` nemusí být rozpor – předchozí déšť může stále ležet v okně výpočtu.

## 3. Historické režimy a doporučené zacházení

| Období | Empirický režim | Důsledek pro zdroj |
|---|---|---|
| Březen 2009 – červen 2014 | Ve starých `usUnits=17` archivech se `rain` chová jako kumulativní/stavový čítač; `rainRate` má samostatné hodnoty odpovídající metrickému zdroji po dělení deseti. Ukázka 2010-05-01: `old_weewx.rain` se drží na 3 mm při `GW1000.rain=0` a `rainRate=0`. V lednu 2014 na překryvu 1 767 starých kladných `rain` při nulovém GW úhrnu; v červenci 2014 již **0** takových případů. | Starý `rain` **nesčítat** bez odvození inkrementů a resetů. `rainRate` lze po konverzi jednotek použít jako původní historický signál, validovat extrémy. |
| Červenec 2014 – 2018 | `rain` se v kontrolovaném překryvu starého a GW archivu již shoduje co do kladných intervalů. `rainRate` často pokračuje po dešti i při nulovém úhrnu; 2016–2018 však také vysoké izolované nulově-srážkové špičky. | Čerpat původní `rainRate` z GW/old/WH, chybné špičky označit, ne slepě eliminovat všechny hodnoty nad limitem. |
| 2019–2020 | Produkce zapisuje pouze 0, GW1000 a rekonstrukce mají shodné nenulové intenzity. | `rainRate` přednostně **GW1000** nebo totožná rekonstrukce. Produkční nula je důkaz chybějící intenzity v této kopii, ne nulového deště. |
| 2021, mimo červenec | Stejná systémová produkční nula. Mimo červenec se zjištěné párové `rainRate` GW a rekonstrukce shodují. | GW/rekonstrukce po kontrole událostí. |
| Červenec 2021 | Rekonstrukce srážek podle ČHMÚ změnila i `rainRate`; v 3 027 řádcích jiná intenzita proti GW. | Používat opravený úhrn, ale **neobnovovat staré GW špičky** bez důkazu; u nových intenzit rozlišit měření a odhad. |
| 2022 | GW/rekonstrukce se liší jen ve 2 nenulových hodnotách `rainRate`, produkce stále nuly. | GW s kontrolou extrémů; rekonstrukce obvykle použitelná. |
| 2023–2024 | Produkce stále nula; rekonstrukce vynulovala **13 a 15 vysokých GW intenzit, ačkoli `rain > 0`**; `rain` v těchto letech mezi GW a rekonstrukcí beze změn. | **Neprioritizovat slepě rekonstrukci.** U ověřených bouřek zvážit původní GW rate, kontroly s okolními stanicemi/radarem. |
| 2025 | Produkce nuly, GW a rekonstrukce téměř totožné (1 rozdílná intenzita; 1 rozdílný úhrn). | GW primární pro `rainRate`; prověřit výjimku. |
| 2026 | První nenulový produkční `rainRate` **2026-03-21 06:40 UTC**; na společných řádcích se rekonstrukce v `rainRate` shoduje s produkcí, nikoli vždy s GW. V GW jsou závažné impulzy 12./16. května. | Přednostně ověřená produkce/rekonstrukce pro aktuální data, GW pouze jako srovnávací zdroj; nelze automaticky přebírat žádný údaj z okolí resetů. |

Přechody srážkového rozlišení (duben 2013, září 2020, srpen 2022) nelze automaticky převést na změnu definice `rainRate`. Než se bude určovat konkrétní metoda výpočtu, je potřeba rekonstruovat verzi driveru, `weewx.conf`, `RainRater.rain_period` a původní konzolové jednotky. Uložená příznaková jednotka přitom zůstává 16 pro GW/rekonstrukci/produkci a 17 pro oba staré archivy.

## 4. Roční nesrovnalosti (uložené hodnoty bez přepočtu)

Definice: `W0` = počet `rain>0 AND rainRate=0`; `D+` = `rain=0 AND rainRate>0`; `R+` = počet kladných `rainRate`. Roční skupiny dle `YEAR(FROM_UNIXTIME(dateTime))` a časově omezeného skenu, viz časová metodická poznámka výše. `D+` **není automaticky chyba** (klouzavé okno). `W0` na produkci 2009–2025 je zvláštní systémový výpadek intenzity.

| Rok | Prod W0 | Prod R+ | GW W0 | GW D+ | GW R+ | Rek W0 | Rek D+ | Rek R+ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2009 | 2397 | 0 | 211 | 1 | 2189 | 92 | 1 | 2188 |
| 2010 | 3424 | 0 | 269 | 51 | 3206 | 115 | 49 | 3195 |
| 2011 | 1647 | 0 | 144 | 8 | 1511 | 76 | 8 | 1503 |
| 2012 | 1675 | 0 | 150 | 5 | 1530 | 151 | 4 | 1528 |
| 2013 | 1556 | 0 | 61 | 16 | 1511 | 64 | 7 | 1499 |
| 2014 | 1586 | 0 | 12 | 1 | 1575 | 15 | 1 | 1572 |
| 2015 | 1198 | 0 | 12 | 890 | 2076 | 12 | 890 | 2076 |
| 2016 | 1152 | 0 | 7 | 1715 | 2860 | 7 | 1685 | 2830 |
| 2017 | 1281 | 0 | 0 | 2242 | 3523 | 0 | 2140 | 3421 |
| 2018 | 932 | 0 | 0 | 1710 | 2642 | 0 | 1702 | 2634 |
| 2019 | 1540 | 0 | 0 | 2343 | 3883 | 0 | 2343 | 3883 |
| 2020 | 1888 | 0 | 204 | 2529 | 4222 | 204 | 2529 | 4222 |
| 2021 | 2678 | 0 | 628 | 2756 | 4810 | 617 | 1185 | 2336 |
| 2022 | 2352 | 0 | 103 | 2202 | 4453 | 103 | 2200 | 4451 |
| 2023 | 4559 | 0 | 0 | 2569 | 7128 | 13 | 2569 | 7115 |
| 2024 | 4371 | 0 | 0 | 2379 | 6753 | 15 | 2379 | 6738 |
| 2025 | 3375 | 0 | 0 | 1894 | 5271 | 0 | 1894 | 5270 |
| 2026* | 633 | 2761 | 7 | 1216 | 3264 | 633 | 1064 | 2761 |

*2026 neúplný. Roční podklad `pocasi-loucka.eu_old` končí v srpnu 2023, od roku 2023 tam chybí `rain`; nelze počítat nulový úhrn. Staré METRICWX zdroje mají kumulativní `rain` před polovinou 2014 – jejich `W0` proto není stejná veličina. Jejich archivní kontrolní statistiky jsou níže.*

| Rok | `old_weewx` W0 / D+ | `weewx_WH1080` W0 / D+ | `pocasi-loucka.eu_old` W0 / D+ |
|---|---:|---:|---:|
| 2009 | 23197 / 0 | 23197 / 0 | 224 / 1 |
| 2010 | 25803 / 51 | 25803 / 51 | 277 / 51 |
| 2011 | 18056 / 8 | 18056 / 8 | 148 / 8 |
| 2012 | 17787 / 4 | 17787 / 4 | 154 / 5 |
| 2013 | 26223 / 12 | 26223 / 12 | 63 / 16 |
| 2014 | 11358 / 1 | 11358 / 1 | 13 / 1 |
| 2015 | 12 / 939 | 12 / 939 | 12 / 938 |
| 2016 | 7 / 1772 | 7 / 1777 | 7 / 1718 |
| 2017 | 1 / 2402 | 1 / 2405 | 1 / 2244 |
| 2018 | 0 / 1727 | 0 / 1727 | 0 / 1710 |
| 2019 | 0 / 2370 | 0 / 2370 | 0 / 2343 |
| 2020 | 0 / 1412 | 4 / 1603 | 204 / 2529 |
| 2021 | mimo rozsah | mimo rozsah | 633 / 3092 |
| 2022 | mimo rozsah | mimo rozsah | 94 / 2051 |
| 2023 | mimo rozsah | mimo rozsah | `rain=NULL`, rate R+=0 |
| 2024–2026 | mimo rozsah | mimo rozsah | mimo rozsah |

Pozn.: rozdílné počty mezi zdroji souvisejí i s odlišným pokrytím. `old_weewx` 2020 končí v srpnu; `weewx_WH1080` v září 2020. `pocasi-loucka.eu_old` ve 2023 nepovažovat za zdroj původního deště.

## 5. Přímé párové srovnání produkce ↔ GW1000 ↔ rekonstrukce

| Rok | `prod=0, GW>0` | `rek ≠ GW` v `rainRate` | `rek ≠ GW` v `rain` (oba nenulové) |
|---|---:|---:|---:|
| 2019 | 3883 | 0 | 0 |
| 2020 | 4222 | 0 | 0 (navíc 2 původní NULL převedené na hodnotu) |
| 2021 | 4810 | 3027 | 1568 |
| 2022 | 4453 | 2 | 0 |
| 2023 | 7128 | 13 | 0 |
| 2024 | 6753 | 15 | 0 |
| 2025 | 5271 | 1 | 1 |
| **2019–2025** | **36 520** | **3 058** | — |
| 2026 (jen párované řádky) | 967 | 3473 | 502 |

Přesně **36 520** případů bylo potvrzeno přímým `JOIN ON dateTime` (ne pouze rozdílem součtů); v letech 2019–2025 se v párovaných řádcích nevyskytl opačný případ `prod>0, GW=0`. V roce 2026 se již naopak vyskytuje 278 `prod>0, GW=0`; rekonstrukce v tomto roce kopíruje produkční `rainRate` na všech 81 621 společných párovaných řádcích.

**Červenec 2021:** v samotném červenci `GW1000` vykazuje `SUM(rain)=70,10146 cm = 701,0146 mm`, rekonstruovaná DB `4,25673 cm = 42,5673 mm`. `rainRate` se liší na **3027** řádcích; z toho **2631** případů původně kladná GW intenzita nyní 0, **157** případů původně 0 nyní kladná rekonstruovaná intenzita. Některé opravy tak **nepřevzaly fyzikální intenzitu senzorového měření**, nýbrž vytvořily odlišnou časovou řadu. Tyto nové hodnoty nutno označit jako odhad/rekonstrukci, dokud nebude ověřena jejich metodika.

## 6. Extrémy, trvání a možné resetové artefakty

Prah `rainRate > 5 cm/h` = **nad 50 mm/h** je pouze vyhledávací práh, nikoli fyzikálně odůvodněná hranice neplatnosti:

| Rok | GW nad 50 mm/h | Z toho při `rain=0` | GW maximum |
|---|---:|---:|---:|
| 2009 | 1 | 0 | 92,04 mm/h |
| 2010 | 11 | 2 | 230,4 mm/h |
| 2011 | 8 | 0 | 184,1 mm/h |
| 2012 | 2 | 1 | 86,4 mm/h |
| 2013 | 12 | 9 | 244,8 mm/h |
| 2014 | 3 | 0 | 68,86 mm/h |
| 2015 | 0 | 0 | 33,6 mm/h |
| 2016 | 30 | 30 | 345,6 mm/h |
| 2017 | 102 | 102 | 451,2 mm/h |
| 2018 | 8 | 8 | 271,2 mm/h |
| 2019–2021 | 0 | 0 | maxima pod 50 mm/h |
| 2022 | 2 | 2 | 66 mm/h |
| 2023 | 13 | **0** | 108,84 mm/h |
| 2024 | 15 | **0** | 93,81 mm/h |
| 2025 | 0 | 0 | 44,08 mm/h |
| 2026* | 6 | 2 | 163,31 mm/h |

**2017:** 2017-08-15 21:25–21:35 UTC jsou tři po sobě následující pětiminutové záznamy s extrémem až **451,2 mm/h**, při `rain=0` ve všech třech. Rekonstrukce všechny tři nastavila na `rainRate=0`. Délka **15 minut záznamů**, nikoli prokázané reálné bouřky. Podobná krátká seskupení: 2017-04-10 (2 záznamy, max 441,6 mm/h), 2017-05-04 (2, 436,8 mm/h). Všech **102** GW intenzit >50 mm/h v roce 2017 při `rain=0` jsou v rekonstrukci vynulovány.

**2023 – vysoce důležitý možný falešný zásah:** 2023-08-26 10:00 UTC: GW `rain=1,18 cm` (**11,8 mm/5 min**) a `rainRate=10,884 cm/h` (**108,84 mm/h**), zatímco rekonstrukce `rainRate=0`, ale `rain=1,18 cm` zachovává. Z úhrnu vychází **5min průměr 141,6 mm/h**, který se od původního rate liší, ale podporuje plausibilitu intenzivního deště. **Nelze jej bez dalšího označit za chybný rate.**

**2024:** 2024-05-28 16:25 UTC: GW `rain=0,72 cm` (**7,2 mm/5 min**) a `rainRate=9,38143 cm/h` (**93,81 mm/h**), rekonstrukce `rainRate=0` při nezměněném `rain`. Z úhrnu vychází **86,4 mm/h jako 5min průměr**. V letech 2023 a 2024 celkem **28** takto vynulovaných GW hodnot >50 mm/h, **všechny během skutečně kladného uloženého srážkového úhrnu**. Nutný samostatný přezkum (radar ČHMÚ / sousední stanice / kontext prázdných intervalů).

**Květen 2026:** v GW1000 2026-05-12 04:35 UTC **131,2 mm/5 min** (`rain=13,12 cm`) při velmi nízké přímé intenzitě, následně 04:40 UTC `rain≈0,02 cm` a `rainRate≈105,16 mm/h`; produkční `rain=0,05 cm` v čase velkého impulsu a `rainRate=0`. Dne 2026-05-16 21:15 UTC GW `rain=14,28 cm` (**142,8 mm**), produkce jen 0,01 cm; 21:20 UTC GW `rain=0`, `rainRate=152,32 mm/h`; 21:30 UTC GW `rain=0`, `rainRate=163,31 mm/h`. Rekonstrukce u všech těchto příkladů sleduje produkční intenzitu. Velmi silná indicie resetové/čítačové kontaminace GW intenzity. **Není definitivní důkaz**, že proces způsobil reset; prokázat původ v nativních stavových čítačích/logu driveru.

**2026 jiný případ:** 2026-06-01 05:50 UTC má rekonstrukce `rain=0,26 cm` a `rainRate=5,72 cm/h`, tedy **57,2 mm/h**, odpovídá skutečně kladnému intervalu a nemá být plošně zakázán limitem 50 mm/h.

## 7. Pravidla doporučeného přebírání

1. **Zachovat původní hodnotu a provenienci.** `rainRate_sensor_original`, `rainRate_curated`, `rainRate_interval_avg` by měly být rozlišitelné logické veličiny nebo evidované návrhy změny. Nikdy nepřepsat měřené `rainRate` pouhým `rain × 12`.
2. **Zdroje:** 2009–2014 původní METRICWX (`old_weewx`/`weewx_WH1080`, dělit rate 10 při převodu na METRIC), alternativně GW; 2015–2018 GW/old, ale vyloučit **jen jednotlivě ověřené** falešné špičky; 2019–2020 GW = rekonstrukce; 2021 mimo červenec GW/rekonstrukce, v červenci rekonstrukce pouze s příznakem *modelová/intenzita po opravě*; 2022 GW/rekonstrukce po kontrole 2 výjimek; **2023–2024 GW pro prověřené mokré extrémy** (rekonstrukce je zde podezřelá z příliš agresivního filtru), rekonstrukce jinak; 2025 GW (1 rozdíl); 2026 primárně produkce/rekonstrukce s validací, GW jen jako diagnostická reference.
3. **Nulové `rain` a kladný `rainRate` nevynulovávat automaticky:** vyžaduje kontrolu posledních minimálně 30 minut, podle konfigurace driveru případně dalšího okna. Korelovat výskyt se záznamy jednotlivých překlopení, změnou čítače a `rainRate` během výpadku.
4. **Kladné `rain` a nulový `rainRate`:** pro historickou produkci 2009–2025 **nebrat jako důkaz nulové intenzity**; pro původní GW mohou být přijatelné až po ověření metody senzoru a archive intervalů. Zvlášť červenec 2021 / 2023 / 2024.
5. **Odvozenou 5min intenzitu** dopočítat výhradně do **nového** sloupce/pohledu, jen při `interval=5`, důvěryhodném nekumulativním `rain`, známé jednotce a potvrzené úplnosti intervalu. Nelze z něj rekonstruovat intenzitu uvnitř pětiminutovky, okamžité špičky ani 30minutovou metodiku. U jiných `interval` použít obecný vztah `60/interval`.
6. **Formální ověření k případnému dalšímu auditu:** analyzovat jednotlivé `weewx.conf` a driver verze (WH1080/GW1000/GW3000); propojit 2023/2024 extrémy s radarem ČHMÚ; event-level kontroly s dešťovými čítači; validovat původ rekonstruovaných červencových kladných intenzit; přesně ročně vyčíslit `Europe/Prague` `(start,end]`.

## 8. Reprodukovatelné časově omezené SQL (příklady; jen SELECT)

```sql
-- Systémová ztráta intenzity; přímé párování jen let 2019–2025.
SELECT YEAR(FROM_UNIXTIME(p.dateTime)) AS yr,
       SUM(p.rainRate=0 AND g.rainRate>0) AS prod_zero_gw_positive,
       SUM(p.rainRate>0 AND g.rainRate=0) AS reverse_case
FROM `pocasi-loucka.eu`.archive p
JOIN `pocasi-loucka.eu_GW1000`.archive g
  ON g.dateTime=p.dateTime
WHERE p.dateTime>=1546300800 AND p.dateTime<1767225600
GROUP BY YEAR(FROM_UNIXTIME(p.dateTime))
ORDER BY yr;

-- Červenec 2021: intenzity, průkazný dopad rekonstrukce.
SELECT COUNT(*) AS common_rows,
       SUM(ABS(g.rainRate-r.rainRate)>0.000001) AS changed_rate,
       SUM(g.rainRate>0 AND r.rainRate=0) AS source_positive_recon_zero,
       SUM(g.rainRate=0 AND r.rainRate>0) AS source_zero_recon_positive
FROM `pocasi-loucka.eu_GW1000`.archive g
JOIN loucka_reconstruction.archive r ON r.dateTime=g.dateTime
WHERE g.dateTime>=1625097600 AND g.dateTime<1627776000;

-- Mokré špičky v letech 2023 a 2024 bez plošného cenzurování.
SELECT g.dateTime, g.rain, g.rainRate, r.rain AS rec_rain,
       r.rainRate AS rec_rainRate
FROM `pocasi-loucka.eu_GW1000`.archive g
JOIN loucka_reconstruction.archive r ON g.dateTime=r.dateTime
WHERE g.dateTime>=1672531200 AND g.dateTime<1735689600
  AND g.rain>0 AND g.rainRate>5 AND r.rainRate=0
ORDER BY g.dateTime;
```

## 9. Omezení a integrita

- **Žádná databáze nebyla změněna.** Šlo pouze o Weather MCP `execute_sql` (read-only), `list_databases`, `get_table_schema` a čtení zdrojového kódu z GitHubu.
- Pokus o agregované korelované 30minutové zpětné vyhledávání pro více celých let překročil `max_statement_time`; tyto poměry **nejsou ověřeny**, nedopočítáváme je odhadem. Audit neobsahuje přesnou rekonstrukci LOOP packetů ani proof root-cause resetu.
- Extrémní hodnoty mohou být skutečné při lokálním přívalovém dešti. Vynulování rekonstruovaných hodnot 2023–2024 představuje **otevřený incident kvality dat**, nikoli potvrzeně správnou opravu.
- SQL `YEAR(FROM_UNIXTIME)` je vhodné pro úvodní souhrn, ale pro definitivní publikované roční statistiky a kalendářní výkazy je třeba použít přesné hranice `Europe/Prague` a WeeWX `(start,end]`, včetně změn CET/CEST a hraniční půlnoci.
- Nejsou zde vyvozovány konkrétní hodnoty `RainRater.rain_period` ze živého serveru; dokumentovaný výchozí interval 1800 s je **hypotéza**, kterou musí potvrdit konfigurace použité historické instalace.

**Verdikt:** Historický `rainRate` nelze bezpečně hromadně převzít ani z produkce, ani z rekonstrukce. Pro léta 2019–2025 byla prokázána systémová nulová produkční kopie; pro 2023–2024 naopak možné zničení věrohodných intenzivních událostí rekonstrukčním filtrem. Kurátorský výběr musí být řízen **obdobím, jednotkou, zdrojovým záznamem a per-event QC**, s důslednou proveniencí.
