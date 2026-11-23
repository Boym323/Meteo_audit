# Forenzní audit tlakové řady Loučka: zlomy v srpnu 2013 a dubnu 2019

**Datum:** 23. 11. 2026. **Režim:** pouze SELECT nad existujícími MariaDB archivy a zpracování již uložených výsledků ČHMÚ z PR #89 a #92.

**Status:** CONFIRMED PRESSURE EPOCH DISCONTINUITIES / CONFIRMED PRESSURE DRIFT / EXACT HARDWARE OR CONFIG ROOT CAUSE UNRESOLVED / NO APPROVED REPLACEMENTS.

## 1. Přesný zlom 26. dubna 2019 v 14:45 UTC (16:45 CEST)

V přímém porovnání `weewx_WH1080.archive`, `old_weewx.archive` a `loucka_reconstruction.archive` se našel první nenulový rozdíl >2 hPa mezi dvěma archivními `barometer` řadami právě v 14:45 UTC.

| UTC | WH barometer | old_weewx barometer | WH pressure | old_weewx pressure | WH RH | old RH |
|---|---:|---:|---:|---:|---:|---:|
| 14:40 | 980,334 | 980,334 | 933,600 | 933,600 | NULL | NULL |
| 14:45 | 1005,734 | 980,380 | 933,600 | 933,600 | 43 % | NULL |
| 14:50 | 1005,780 | 980,351 | 957,467 | 933,600 | 44 % | NULL |
| 15:00 | 1005,708 | 980,185 | 957,405 | 933,517 | 44 % | NULL |

- Lokální WH `barometer` skočí mezi 14:40 a 14:45 o **+25,400 hPa**. Starý archiv za stejný úsek pouze **+0,046 hPa**. Mezi řadami v 14:45 vzniká **+25,354 hPa** rozpor.
- WH `pressure` přechází na novou hladinu **o jeden archivní interval později** (14:50). V pracovní rekonstrukci je už v 14:45 `pressure≈957,41` a `barometer=1005,734` hPa. Zpoždění WH ukazuje rozdílný výpočetní/archivní průchod, nedokazuje však implementaci konkrétního softwaru.
- WH1080 a old_weewx se v těchto časech přesně shodují v `outTemp`, `inTemp` a `windSpeed`; WH ale začíná obsahovat `outHumidity=43–44 %`, kde old_weewx stále ukládá NULL. To silně ukazuje na **selektivní změnu nebo opravu konkrétních senzorových/odvozených polí**, nikoliv na kompletně odlišné meteorologické pozorování.
- Průměr `old_weewx.barometer − WH1080.barometer` pak činí cca −25,40 hPa na konci dubna 2019, −29,57 v červnu 2019, −31,55 v srpnu 2019, −27,48 v prosinci 2019 a −34,35 hPa v červenci 2020. **Starý archiv není automaticky validní tlakový zdroj po oddělení větví.**

Srovnání s ČHMÚ z PR #89 nezávisle vykazuje zlom `barometer − P_hm` o +25,337 hPa mezi měsíčními mediány duben/květen 2019. Toto měsíční porovnání není přesné časové vysvětlení mechanismu, ale je v souladu se zjištěným okamžikem.

## 2. Zlom 8. srpna 2013 v 15:30–15:40 UTC (17:30–17:40 CEST)

| UTC | Reconstruction barometer | Reconstruction pressure | outTemp | outHumidity |
|---|---:|---|---|---|
| 15:25 | 997,3 hPa | NULL | NULL | NULL |
| 15:30 | 1006,6 hPa | NULL | NULL | NULL |
| 15:40 | 1013,2 hPa | NULL | NULL | 18 % |
| 16:25 | 1013,1 hPa | NULL | NULL | 19 % |

- Jde o celkový vzestup **+15,9 hPa za 15 minut**, dvoukrokově +9,3 a +6,6. Neexistuje archivní timestamp 15:35; neodvozovat z absence jinou rychlost meteorologického vzestupu.
- Zdrojové `old_weewx` a `weewx_WH1080` mají krátkou mezeru okolo změny; později se znovu shodují s novou řadou. Chybí současně venkovní teplota i cílový station pressure. Příčina zůstává nejistá, ale změna datové/kalibrační epochy je silně podezřelá.
- Již hotový nezávislý **měsíční denní** kontext ČHMÚ z PR #89 indikuje Holešov výškově upravený residuál −16,69 hPa v červenci 2013 a −1,87 hPa v srpnu 2013. **Nejde** o přesné hodinové spojení ČHMÚ s 15:30/15:40, pouze doplňující signál.

## 3. Velmi výrazný lineární drift leden 2018 – duben 2019

Z již publikovaného `hourly_monthly_stats.csv` v PR #89 bylo samostatně vybráno **16 měsíčních mediánů** pro `reconstruction.barometer − ČHMÚ P_hm` ve stejných UTC hodinách a quality=0. Jednoduchá lineární regrese nad měsíčními mediány:

| Referenční stanice | Sklon hPa/měsíc | Sklon hPa/rok | R² | První (2018-01) → poslední (2019-04) medián |
|---|---:|---:|---:|---|
| Holešov 11774 | −0,46512 | −5,581 | 0,9914 | −21,078 → −27,891 hPa |
| Mošnov 11782 | −0,45825 | −5,499 | 0,9494 | −20,478 → −28,576 hPa |

Dvě fyzicky nezávislé referenční stanice vykazují prakticky stejný sklon reziduí. To je **silný důkaz driftu celé tlakové měřicí/výpočetní větve** před výše doloženým dubnovým skokem; nevylučuje souběh kalibrační závady, hardwaru a softwaru. Odhad lineárního driftu je **diagnostický**, nikoli přepisovací koeficient. Dubnový medián zahrnuje i 4,5 dne po zlomu, takže nejde o čistý předzlomový měsíc.

Pro kontext: nezávislý PR #92 pilot 8 055 hodin z roku 2018 potvrdil mediánový deficit historického WH tlaku po diagnostickém výškovém transportu oproti ČHMÚ P cca **−23,064 hPa (Holešov)** a **−22,809 hPa (Mošnov)** v cílových NULL intervalech. Ani těchto 3 835 přesných hourly WH source bodů proto není schváleno k UPDATE.

## 4. Pravděpodobné epochy, nikoliv definitivní hardwarová historie

- 2009–2011: starší zdánlivě mírně záporný CHMI bias, pak delší archivní mezera.
- Od obnovení 2012 až 8.8.2013: výrazný záporný bias.
- 8.8.2013 15:30–16:25 UTC: pravděpodobná změna tlakového zdroje/zpracování, s datovou mezerou a náhlým skokem.
- 2013-08-08 později až 2019-04-26 14:40 UTC: další období, v němž narůstá záporný kalibrační bias; zejména 2018-01 až 2019-04 ~−5,5 hPa/rok vůči dvěma ČHMÚ stanicím.
- 2019-04-26 14:45–14:50 UTC: přesně potvrzená selektivní změna tlakového/RH řetězce.
- Pozdější historie (2022 GW1000, 2024–2026 změny tlakových redukcí v GW kopii) je **oddělená etapa** a neřešit ji automaticky stejným offsetem.

Oficiální stránka stanice https://pocasi-loucka.eu/about/ uvádí začátek měření 29.3.2009 s Watson W-8681 a výměnu za GW1000 20.8.2022, ale **žádný servisní zásah k přesným datům v letech 2013/2019 zde uveden není**.

**Nepodařilo se prokázat konkrétní fyzickou příčinu** (výměna senzoru, kalibrace konzole, historický offset ve WeeWX, úprava driveru či opravný import). Pro takové tvrzení jsou třeba dobové `weewx.conf`, servisní logy, raw packets nebo provozní deník.

## 5. Navržené další kroky — bez zápisu do meteorologických dat

1. Formální **epochový registr**: interval UTC, pozorované pole, odchylka vůči Holešovu a Mošnovu, původ zdroje, informace o T/RH, nejistota, příčina (UNKNOWN, dokud nejsou logy).
2. **Kalibrační model pouze mimo SQL**: ověřit rezidua zvlášť podle období, odlišit přímá měření od odhadů, testovat na časově oddělených měsících a obou referenčních stanicích. Pozor na společnou meteorologickou změnu obou ČHMÚ stanic, i když silný drift tady opravdu vypadá instrumentálně.
3. Prověřit existující dobové konfigurace WeeWX/WH1080 a raw zprávy kolem 2013-08-08 a 2019-04-26, pokud skutečně existují; **aktuální 2026 konfigurace GW3000 není historická evidence**.
4. Nedoplňovat `pressure` jako `barometer−50`, nedělat globální +23hPa ani hromadný `COALESCE(WH1080.pressure)`. Pro Q1 2018 trvá ochrana všech meteorologických veličin.
5. Až po nezávislém holdoutu a per-field důkazu připravit neměnný read-only manifest (target UTC, expected_old, proposed_new, unit_epoch, source_time/source_database, confidence, batch SHA-256). **Žádný APPLY, žádné schválené náhrady.**

**Bezpečnost:** žádný GRANT, SQL účet, CREATE, INSERT, UPDATE, DELETE, APPLY/ROLLBACK. Nedotčena živá produkční MariaDB, WeeWX v jiném LXC ani denní agregace.
