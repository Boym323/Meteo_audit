# Audit venkovní teploty, relativní vlhkosti a odvozenin (2009–2026)

**Datum:** 30. 10. 2026 · **Režim:** pouze SELECT přes Weather MCP; **DB beze změn**. **Pracovní zdroj:** `loucka_reconstruction.archive`. Měsíční rating je v [05-temperature-humidity-monthly.csv](05-temperature-humidity-monthly.csv) (212 místních měsíců včetně prázdných).

## 1. Rozsah a metodika

Bylo ověřeno šest archivních databází: `loucka_reconstruction`, `pocasi-loucka.eu`, `pocasi-loucka.eu_old`, `pocasi-loucka.eu_GW1000`, `old_weewx`, `weewx_WH1080`. Pracovní archiv má **1 679 802** záznamů (2009-03-29T16:45:00Z až 2026-10-29T15:10:00Z); produkce **1 680 077** (poslední záznam 2026-10-30T14:10:00Z). V pracovní DB je 18 294 NULL teplot a 161 275 NULL vlhkosti, přičemž **0 °C není totéž jako NULL**. U `outHumidity` ve pracovní DB nejsou nulové ani mimo rozsah hodnoty; to však nedokazuje věrohodnost nenulových RH. Převážná většina záznamů má `interval=5` (1 677 705 záznamů), menší část `interval=6` (2 090).

`usUnits=16` v pracovní a produkční kopii znamená WeeWX **METRIC**, `usUnits=17` ve starších `old_weewx` a `weewx_WH1080` znamená **METRICWX**. V obou se teplota ukládá ve °C; mění se zejména jednotky větru (km/h vs m/s) a srážek (cm vs mm). Metodika: [WeeWX units](https://weewx.com/docs/5.0/reference/units/), [WeeWX archive](https://www.weewx.com/docs/5.1/custom/introduction/).

**Měsíce:** hraniční epochy byly vypočteny z IANA `Europe/Prague`; časová podmínka je `dateTime > start_utc AND dateTime <= end_utc`, protože WeeWX archivní čas označuje konec intervalu. MariaDB `CONVERT_TZ('…','UTC','Europe/Prague')` zde vrací NULL (nedostupná tz databáze), proto byly přesné hranice CET/CEST vytvořeny mimo SQL. Sken probíhal v **18 ročních dávkách** pro 212 měsíců (2009-03 až 2026-10). Každá měsíční tabulka zahrnuje počet řádků, očekávané pětiminutové sloty, NULL teploty/RH a RH ≤15 %.

## 2. Nejvážnější závady

**2009–2013 / historické zdroje:** žádné archivní řádky **2011-09 až 2012-02**; `weewx_WH1080` také nemá překlenovací měření. V `old_weewx` bylo v srpnu 2011 **3 264 souběžných `outTemp=0` a `outHumidity=0`**, zatímco `weewx_WH1080` má v odpovídající části `outHumidity=NULL`. Dalších 120 nul RH je v `old_weewx` roku 2014. `weewx_WH1080` obsahuje jeden extrém **1 662 011 % RH** (2011) a několik RH nad 100 % v letech 2019–2020. Takové hodnoty nelze bez validace převzít. Ve dnech 2013-01-25 00:00–11:55 UTC (T=−4,5 °C; RH=89 %), 2013-02-15 12:00–23:55 (2 °C; 96 %), 2013-03-02 00:00–11:55 (1,2 °C; 94 %), 2013-03-27 00:00–11:55 (−4,6 °C; 80 %) a 2013-04-03 12:00–23:55 (−0,7 °C; 87 %) se obě veličiny **144 po sobě jdoucích 5min bodů neměnily**. Jde o velmi silný indikátor zamrzlých údajů. Samotná konstantní RH 99–100 % ve vlhku není důkaz vadného senzoru.

**2015–2019 / RH:** celoroční počet NULL RH: 2015 **5 993**, 2016 **13 416**, 2017 **24 936**, 2018 **35 892**, 2019 **19 721**. Vedle nich řada nenulových hodnot pravděpodobně podměřuje: RH ≤15 % bylo roku 2015 **2 970** měření, 2016 **2 963**, 2017 **2 226** a 2018 **3 594**; přesných 10 % bylo 349, 437, 263 a 451. Měsíční průměry Loučka vs LuhaMet (nikoli synchronní párová měření): **2015-08 38,85/67,80 %**, **2016-07 39,75/71,36 %**, **2017-01 46,08/79,65 %**, **2018-04 29,00/65,61 %**. Důkaz systematického podezření, ne oprávnění prostě kopírovat měření jiné obce. V únoru 2018 je v pracovním archivu pouze **614** řádků, což samo znamená těžký výpadek.

**2022 / RH a rosný bod:** leden **8 485 NULL RH / 8 499 řádků**, únor **8 058/8 058**, březen **8 003/8 681**, květen **8 851/8 902**, červen **8 379/8 577**. V dubnu už pracovní RH částečně rekonstruována; proti produkci se roku 2022 liší **3 578 hodnot RH**, zatímco žádné uložené `outTemp` na shodných časových značkách. Podkladová tabulka `reconstruction_humidity_202204`: 2 194 `estimate_ready/frozen`, 1 299 `estimate_ready/missing`, 85 `invalidate_frozen/frozen`, 156 `missing_unresolved/missing`. Změny RH zahrnují **1 299 doplněných NULL**, **85 zneplatněných původních RH** a ostatní změny platných hodnot. Po rekonstrukci je **1 077 dubnových řádků** s rozdílem `dewpoint` proti Magnusovu diagnostickému vzorci více než **2 °C**, protože `dewpoint` pochází ze starší RH. Zkoumat stejný problém pro `heatindex`, `appTemp`, případně `humidex`. Od srpna 2022 jsou RH téměř úplné. Pro 2022-04 mají měsíční průměr RH Loučka 70,66 %, LuhaMet 75,65 %, ILOUKA4 70,40 %; souhlas průměrů není časová validace jednotlivých návrhů.

**Rok 2015 / teplotní extrém:** 40,2 °C v Loučce, zatímco přesně současná LuhaMet 33,4 °C. Rozdíl +6,8 °C je silný kandidát na ohřev čidla/sluncem nebo rozdílnou expozici; neprohlašovat bez metadat a dalších referencí za prokázanou chybu. Absolutní pracovní minimum −18,75 °C. Sken skoků při rozestupu 1–15 minut nenašel `|ΔT|≥7 °C`, ale zaznamenal teplotní skoky 4–5 °C a RH až 75,6 procentního bodu za 5 minut.

**Referenční kvalita:** `reference_observations` obsahuje LuhaMet/Sehradice **1 157 794** bodů a ILOUKA4 **494 844**. Historický LuhaMet má **15 678 hodnot `relative_humidity_pct=0`** (2015–2021), které je nutné označit za neplatné; zejména 2019 3 620 a 2020 4 936. ILOUKA4 začíná až koncem roku 2021. LuhaMet v novějších datech nemusí mít přesnou 5min mřížku a ILOUKA4 bývá posunut o několik sekund; při párování používat nearest timestamp s tolerancí a vyloučit neplatné nuly.

## 3. Konkrétní podezřelé okamžiky

V tabulce jsou UTC timestampy. U opakovaného „tam a zpět“ je významně vyšší jistota anomálie než u jednotlivého velkého rozdílu proti jiné stanici.

| Čas UTC | Veličina | Zjištění | Doporučení |
|---|---|---|---|
| 2015-08-10T12:35:00Z | T | 40,2 °C; LuhaMet 33,4 °C, rozdíl +6,8 °C | podezření na ohřev stanice, ne automaticky neplatné |
| 2021-01-18T02:20:00Z | T | −18,75 °C | historické minimum, nutné ověřit okolní hodnoty |
| 2021-10-31T09:20:00Z | RH | 9,7 %; LuhaMet 59 % | silný rozdíl; rosný bod −15,47 °C vypočtený z podezřelé RH |
| 2016-12-26T16:30:00Z | T | 0 → 5 °C za 10 min | 0 °C není automaticky chybějící údaj |
| 2026-08-29T00:25:00Z | T | 21,26 → 16,31 °C za 5 min | ověřit déšť, vítr a externí reference |
| 2019-04-17T01:50:00Z | T | −0,8 → 4,1 °C za 5 min | souběžně RH=NULL |
| 2016-11-13T03:25:00Z | T | −2,7 → 1,8 → −2,7 °C v 10 min | izolovaný artefakt velmi pravděpodobný |
| 2021-08-05T16:40:00Z | T | 15,75 → 11,375 → 15,75 °C v 10 min | izolovaný artefakt velmi pravděpodobný |
| 2021-11-29T09:35:00Z | RH | 94,6 → 19 % za 5 min | při téměř neměnné T |
| 2015-04-05T13:00:00Z | RH | 93 → 27,5 % za 5 min | podezřelá nestabilita |
| 2019-04-28T06:20:00Z | RH | 79 → 25 → 79 % během 10 min | při téměř neměnné T |
| 2022-04-06T09:20:00Z | Td | T=11,375, RH=76,64 %, Td uložen 9,63 °C; oček. ~7,42 °C | zastaralá odvozenina po opravě RH |
| 2014-06-16T17:39:00Z | T a RH (old_weewx) | 0 °C a 0 % RH | falešné nuly ve zdrojové kopii |

## 4. Rozdíly historických archivů

Při JOIN na identický `dateTime` je **ve všech letech nula rozdílů `outTemp` mezi `loucka_reconstruction` a produkcí**. U RH je rozdíl pouze v roce 2022 (3 578 hodnot). Neplatí, že jsou kopie totožné počtem časů: produkce má více nejnovějších záznamů, historické zdroje mají jiná období a někdy jiné `usUnits`.

`weewx_WH1080` na přesně shodných timestamp nabízí validně vypadající RH (1–100 %) na místech NULL pracovní RH: rok 2013 **5 632** kandidátů, 2014 **1 407**, 2016 **2 096**, 2017 **9 058**, 2018 **6 013**, 2019 **7 453**. Teplotní obdobné kandidáty 2013 **5 651**, 2017 **215**, 2019 **293**. Počty neznamenají, že jde o nezávislá měření; před rekonstrukcí ověřit synchronní freeze, původ zařízení, shodu v okolí a správné mapování jednotek.

## 5. Hodnocení kvality měsíc po měsíci

Kompletní tabulka: [**05-temperature-humidity-monthly.csv**](05-temperature-humidity-monthly.csv).

Stupně dostupnosti pro teplotu a RH zvlášť: **A** = ≥98 % očekávaných slotů a ≤0,2 % NULL; **B** ≥95 % a ≤2 % NULL; **C** ≥85 % a ≤10 % NULL; **D** ≥50 % a ≤50 % NULL; jinak **E**. Výsledná známka je horší z obou. U známých vad byl stupeň snížen: 2013-01–04 kvůli konstantním blokům; 2015-03–2019-04 kvůli systematickým podezřením RH; 2021-10–11 kvůli skokům RH; 2022-04 kvůli chybným odvozeninám. `P` označuje krajní částečné měsíce 2009-03 a 2026-10. **Výsledky: A=71, B=29, C=31, D=54, E=25, P=2** (212 měsíců). **A neznamená ověřenou přesnost čidla.** U měsíců bez řádků v CSV použij 0 a známku E, nikdy neimputuj teplotu jako 0 °C.

## 6. Metody rekonstrukce a priority — nic neaplikovat

1. **P0: 2013 frozen a historické RH=0 / mimo rozsah.** Rozlišit status `invalid` a hodnotu. Chybné 0/1 662 011 % RH lze vysoce jistě odmítnout, nikoli vysoce jistě nahradit.
2. **P0: 2022-04 dewpoint.** Po schválené, reverzibilní opravě RH zvlášť navrhnout nový výpočet `dewpoint` podle konkrétní verze WeeWX; zkontrolovat také `heatindex`, `appTemp`, `humidex`; zatím neprovádět UPDATE.
3. **P1: 2015–2019 RH.** Přednostně originální validované hodnoty z `weewx_WH1080` jen pro skutečně odlišné a fyzikálně uvěřitelné záznamy; zbytek robustní, epochově kalibrované odhady LuhaMet, vyloučit referenční RH=0, případně model z teploty/rosného bodu **jen není-li Td odvozen ze stejné chybné RH**.
4. **P1: 2022-01 až 2022-07 RH.** Krátké mezery interpolovat jen s lokální návazností a úzkou nejistotou; dlouhé bloky pouze reference LuhaMet+ILOUKA4 s denní a sezónní validací, ukládat širší nejistotu. Nikdy nevyrábět falešně přesná 5min měření pro úplně chybějící měsíc.
5. **P1: 2013 a 2017–2019 T.** Propojit původní timestampy a navrhnout přenos jen z měření, které projde validací freeze, fyzikálního průběhu a původu kopie.
6. **P2: 2011-09 až 2012-02.** Bez obnovitelného originálního archivu ponechat NULL/mezery. LuhaMet a ILOUKA4 pro toto období neexistují.
7. **P2: extrémy a skoky.** Kontrola sousedních 2–12 h, meteorologických front, srážek, radiace, času dne a okolních stanic; neodstranit absolutní extrém jen proto, že se liší od souseda.

Každý budoucí návrh evidovat: UTC čas, veličina, zdrojový archiv, původní hodnota (včetně NULL), navržená hodnota (může být NULL), jednotka, metoda/verze, důkaz, nejistota, confidence diagnózy zvlášť od confidence náhrady, stav revize a možnost rollbacku. Žádné změny databáze nebyly autorizovány ani provedeny.

## 7. Reprodukovatelnost, limity a další ověření

Použité výhradně `list_databases`, `list_tables`, `get_table_schema` a read-only `execute_sql`. V ročních dávkách se souhrny agregovaly do místních měsíců pomocí číselných hranic a primárního klíče `archive.dateTime`. Skoky byly detekovány přes `LAG` pro mezeru 60–900 s. Dvanáctihodinové konstantní bloky přes `GROUP BY FLOOR(dateTime/43200)`, alespoň 100 nenulových měření a `MIN=MAX`; přelomové bloky přes 00:00/12:00 UTC lze touto metodou přehlédnout.

Magnusova kontrolní aproximace: `gamma = LN(RH/100)+17.625*T/(243.04+T)`, `Td=243.04*gamma/(17.625-gamma)`, použitá jen pro RH 1–100 % a fyzikálně uvěřitelnou T. Přepočet je diagnostický, nikoli záměna za přesný historický WeeWX algoritmus.

**Limity:** Referenční plošný 5min JOIN přes rok 2022 vypršel na `max_statement_time`, proto jsou uvedeny spolehlivé celoměsíční průměry a bodové příklady, **ne úplná párová korelace**. Kontrola 12h konstantních bloků nemusí najít všechny zaseklé úseky. Bez instalačních logů nelze přesně přiřadit zdroj vady konkrétní dubnové/zářijové/srpnové výměně techniky; měsíční změna sama o sobě není důkaz hardwarového biasu. Pro konečné rozhodnutí doplnit nearest-time měsíční párové statistiky a revizi 5min exportu problematických dnů.

**Bezpečnost:** žádné INSERT, UPDATE, DELETE nebo změny grantů v žádné databázi. Změněn pouze tento auditní dokument na samostatné GitHub větvi.

## 8. Přídavný screening odvozených veličin

Plošná agregace `dewpoint`, `heatindex`, `windchill`, `appTemp` podle kalendářního roku UTC:

| Rok | NULL dewpoint | NULL heatindex | NULL windchill | NULL appTemp | Interpretace |
|---|---:|---:|---:|---:|---|
| 2015 | 5 993 | 5 993 | 3 | 5 994 | Odvozeniny závislé na RH chybí současně s RH; windchill je většinou dostupný |
| 2016 | 13 436 | 13 436 | 212 | 13 451 | Převážně ztracená RH a částečně teplota |
| 2017 | 24 967 | 24 967 | 330 | 25 000 | Rozsáhlá ztráta RH-dependentních odvozenin |
| 2018 | 35 892 | 35 892 | 55 | 35 897 | Deficit RH při většinou uložené T/windchill |
| 2019 | 19 722 | 19 722 | 339 | 19 767 | Výpadky RH pokračují do jara |
| 2020 | 6 112 | 6 112 | 13 140 | 14 523 | Významné další NULL windchill a appTemp: kontrola zdroje větru |
| 2022 | 45 070 | 45 070 | 3 176 | 45 392 | Rekonstruovaná RH neznamená přepočtené odvozeniny |
| 2026* | 2 | 2 | 520 | 521 | Dostupnost do aktuálního konce pracovní kopie |

\*Rok 2026 je průběžný. Při fyzikálním screeningu celého pracovního archivu bylo **0** případů `windchill > outTemp + 0,5 °C`, **0** případů `windchill < outTemp − 35 °C`, **0** případů `heatindex < outTemp − 4 °C` a **0** případů `heatindex > outTemp + 20 °C`. U `appTemp` je **0** překročení `outTemp − 35 °C` a `outTemp + 25 °C`. Jde o hrubé prahy, nikoli o důkaz přesnosti; každá z odvozenin může být interně konzistentní i tehdy, když základní RH/T senzor měří chybně.

Rok 2020 zvlášť vyžaduje kontrolu dostupnosti a jednotek `windSpeed` po změně techniky: `windchill` má více chybějících bodů než `dewpoint`. Pro validaci správného algoritmu `heatindex` a `appTemp` je potřeba historická konfigurace a verze WeeWX, zejména zjištění, zda a kdy byly jednotlivé veličiny ukládány jako pevný archivní derivát.
