# 07 — Forenzní audit větru Počasí Loučka (2009–2026)

**Běh:** 2026-10-30, Weather MCP / MariaDB 11.8.6; **režim:** výhradně čtecí SQL; **cílová pracovní DB:** `loucka_reconstruction`.  
**Stav:** analytický nález, žádné opravy databázových řádků ani schválení rekonstrukce. Časy jsou UTC, není-li uvedeno jinak. `dateTime` je Unix epoch na konci intervalu; denní bloky níže jsou vyhodnoceny podle `FLOOR(dateTime/86400)`, nikoli podle místních kalendářních dnů. U měsíčních tabulek pochází kalendář z `FROM_UNIXTIME`, tj. ze systémové časové zóny MariaDB (`@@session.time_zone = SYSTEM`, v okamžiku auditu UTC+01:00).

## Rozsah a struktura

Dostupné databáze a souhrny `archive` (počty platné v okamžiku dotazu):

| Archiv | `usUnits` | Počet řádků | max uložené `windSpeed` | max uložené `windGust` |
|---|---:|---:|---:|---:|
| `loucka_reconstruction` | 16 | 1 679 802 | 79,632 | 92,16 |
| `pocasi-loucka.eu` | 16 | 1 680 077 | 79,632 | 92,16 |
| `pocasi-loucka.eu_GW1000` | 16 | 1 674 765 | 79,632 | 92,16 |
| `pocasi-loucka.eu_old` | 16 | 1 336 195 | 79,632 | 92,16 |
| `old_weewx` | 17 | 1 104 422 | 99,4 | 164 |
| `weewx_WH1080` | 17 | 1 112 201 | 99,4 | 164 |

Všechny archivy mají `windSpeed`, `windGust`, `windDir`, `windGustDir`, `windchill`; v části archivů jsou také `windrun`, `windBatteryStatus` a v novějších `ws80_batt`, `ws80_sig`, `ws80_rssi`. **Výše uvedená maxima jsou syrové hodnoty; jednotky mezi zdroji nejsou jednotné.** Tabulky představují překrývající se kopie/migrace, nikoliv šest nezávislých měřicích stanic.

## Nejdůležitější zjištění

### A. Numerická sémantika `usUnits=17` je historicky nekonzistentní — vysoká jistota

Párování identických `dateTime` proti produkčnímu archivu s `usUnits=16` pro `old_weewx.windSpeed`:

| UTC období | Poměr produkce / starší zdroj při nenulové rychlosti | Důkaz |
|---|---:|---|
| 2009 | 1,0000 | 73 757 přesně shodných nenulových párů |
| 2010 | 0,9999 váženě | 97 057 přesně shodných; šest odlišných párovaných hodnot |
| 2011 | 1,0000 | 60 847 shodných |
| 2012 | 1,0000 | 65 396 shodných |
| 2013 do 6. 4. | 1,0000 | poslední nenulová shoda 2013-04-06 15:10 UTC |
| od 2013-04-12 17:55 UTC | 3,6000 | první přesný nenulový pár s faktorem 3,6 |
| 2014–2020 (překryv) | 3,6000 | v každém roce všechny nenulové páry odpovídají 3,6 v toleranci 0,0001 |

U `windGust` je poslední doložená nenulová shoda bez převodu 2013-04-06 14:55 UTC a první ×3,6 také 2013-04-12 17:55 UTC. Před změnou obsahuje `old_weewx` a `weewx_WH1080` čísla **numericky v km/h**, byť označená `usUnits=17`, který by běžně indikoval m/s. Po změně jde o skutečné m/s. Při přímém párování `old_weewx` ↔ `weewx_WH1080` jsou hodnoty rychlosti i nárazů shodné všude, kde jsou v obou archivech vyplněny (348 335 shodných párů rychlosti před přechodem; 684 279 po přechodu). Není to nezávislé ověření meteorologické správnosti, ale potvrzení společné sémantiky kopií.

**Nevyřešená mezera:** mezi 2013-04-06 15:10 a 2013-04-12 17:55 UTC nejsou doložené rozhodující nenulové páry. Čas hardwarové/software změny neurčovat přesněji než touto hranicí. Ani na samotném `usUnits` nelze postavit globální konverzi.

### B. Změny režimu / rozlišení / hardware — časová osa

| UTC období | Datově zjištěný režim | Jistota a omezení |
|---|---|---|
| 2009–2013-04-06 | `usUnits=17` ve starých zdrojích, ale rychlosti numericky km/h | vysoká, přímé párování |
| 2013-04-06 až 2013-04-12 | přechod a mezera | přesný okamžik neznámý |
| od 2013-04-12 17:55 | staré zdroje numericky m/s, produkční kopie km/h | vysoká, faktor ×3,6 |
| do 2020-09-01 15:05 | starší numerické mřížky; např. v srpnu 2020 byly všechny kladné nárazy násobkem 0,36 km/h | vysoká pro numerický vzor, ne pro typ čidla |
| 2020-09-02 až 2020-09-21 (UTC) | výpadek větrných veličin: v 5 052 archivních řádcích `windSpeed`, `windGust`, `windDir` všechny NULL | vysoká |
| od 2020-09-22 12:40 | nové nenulové větrné záznamy a jiné kvantování: např. 23. 9. je jen cca 32,3 % nenulových nárazů násobkem 0,36 km/h oproti 100 % před výpadkem | vysoká pro změnu režimu, hardware neprokázán |
| 2022-08-27 09:40 | první nenulové `ws80_batt`; současně zjemnění `windSpeed` a návrat nárazů na kroky 0,36 km/h | silná indicie změny WS80 / ovladače, nikoli dokumentace výměny |
| od 2026-03-08 12:15 | GW1000 se v rychlosti a směru odlišuje od produkčního a rekonstrukčního archivu, které se shodují | vysoká pro rozdíl; příčina neprokázána |
| od 2026-03-08 12:25 | první vyplněný `ws80_rssi` v produkci | metadata, nikoliv důkaz fyzické výměny |

**Rozlišení 2022 podrobně:** 1.–26. 8. 2022 bývá ~95–97 % nenulových `windSpeed` násobkem 0,12 km/h, zatímco u nárazů jen ~25–38 % odpovídá 0,36. Dne 27. 8. nastává přechod; 28. 8. je rychlost na mřížce 0,12 jen u ~14,2 % vzorků, zatímco nárazy jsou v 100 % na 0,36. Nemusí to být čisté rozlišení senzoru: `windSpeed` je průměr přes archivní interval a kvantování může ovlivnit počet vzorků a algoritmus agregace.

### C. Nemožné extrémy a poškozený směr — vysoká jistota chyby u směru, podezření u nárazů

Po přechodu na skutečné m/s obsahuje `weewx_WH1080` zejména 2014–2018 extrémy. Příklady:

| UTC timestamp | WH1080 `windSpeed` | WH1080 `windGust` | Náraz po převodu | Produkční `windGust` |
|---|---:|---:|---:|---|
| 2015-09-30 10:58 | 23,5 m/s | 85,0 m/s | 306,0 km/h | NULL |
| 2017-01-18 00:35 | ~9,967 m/s | 83,0 m/s | 298,8 km/h | NULL |
| 2017-10-09 05:20 | ~45,200 m/s | ~65,600 m/s | ~236,2 km/h | NULL |
| 2016-09-05  | ~14,8 m/s (příklad z téhož dne) | ~75,1 m/s | ~270,4 km/h | NULL |

Poslední řádek je orientační interval dne, nikoli reprodukovaná přesná hodina: rozhodující čas `dateTime=1473077400`. **Takové nárazy nepřebírat automaticky do `loucka_reconstruction`**; některé jsou opakované v sousedních intervalech a produkční archiv je již má jako NULL. V `weewx_WH1080` během 2017: 52 intervalů s rychlostí >35 m/s, 103 s nárazem >40 m/s a 34 s nárazem >60 m/s. Případný skutečný extrém musí potvrdit další stanice a kontext.

`windDir` obsahuje v původních kopiích fyzikálně nemožná čísla jako **14 210 854 715 202°**, **430 612 770 827 565°** a **28 421 709 430 404°** (v různých letech 2014–2020). Počty hodnot mimo [0,360] ve `weewx_WH1080`: 2014: 4, 2015: 2, 2016: 1, 2017: 1, 2018: 1, 2019: 2, 2020: 1. Stejné typy artefaktů jsou v `pocasi-loucka.eu_old` a GW1000, zatímco produkce a pracovní archiv mají na dotčených místech NULL. Neodvozovat z čísel směry operací modulo 360: neplatný směr označit a zachovat originál.

### D. Zaseknutá čidla a dlouhé nulové série

Při denní kontrole produkce (`FLOOR(dateTime/86400)`, alespoň 250 archivních a nenulově *vyplněných* `windSpeed` záznamů v rámci každého dne) bylo **118 celých UTC dnů se stále nulovou rychlostí**; 107 z nich mělo po celý den rovněž nulový náraz. Nejdelší souvislé denní běhy:

| Období v UTC | Celé dny | Stav |
|---|---:|---|
| 2015-11-19 až 2015-12-22 | 34 | `windSpeed = windGust = 0` |
| 2015-12-28 až 2016-01-18 | 22 | `windSpeed = windGust = 0` |
| 2020-01-25 až 2020-02-07 | 14 | `windSpeed = windGust = 0` |
| 2010-12-26 až 2010-12-31 | 6 | `windSpeed = windGust = 0` |
| 2013-07-02 až 2013-07-05 | 4 | `windSpeed = windGust = 0` |

25.–26. 1. 2013 je jiná forma zamrznutí: plný počet 288 pětiminutových záznamů za každý UTC den má **`windSpeed = windGust = 17,3 km/h` a `windDir = 1°`**. Společný výskyt na archivních kopiích neznamená nezávislé potvrzení.

Nuly mohou znamenat skutečné bezvětří v krátkém intervalu, ale **vícetýdenní nepřerušené nuly nelze považovat za validní bez potvrzení**. Nezaměňovat za NULL ani automaticky nedoplňovat.

### E. Fyzikální vztahy a dostupnost veličin

- V produkci je **29 záznamů s `windGust < windSpeed`**: 6 v roce 2014, 18 v roce 2016 a 5 v roce 2017; příklady `dateTime=1406113800` (`windSpeed≈60,48 km/h`, `windGust≈34,2 km/h`) a `1456856400` (`78,48 km/h`, náraz 0). Jsou to konkrétní kandidáti k revizi algoritmu/zdroje.
- `windSpeed=0, windGust>0` je v datech časté; samo o sobě nemusí být chybou (průměr a maximum nemusí mít stejný režim). Nezaměňovat s `windGust<windSpeed`.
- Směr je v části historie neúplný: v roce 2020 má 23 439 záznamů `windSpeed>0` a `windDir IS NULL`, v roce 2021 dokonce 44 129. To vylučuje spolehlivou rekonstrukci větrných růžic pro tato období bez dalších dat.
- `windGustDir` není ve starých letech k dispozici, v produkci se poprvé objevuje až 2019-04-26 14:45 UTC. Nenahrazovat ho automaticky `windDir`: jde o odlišný jev.
- `windrun` je v produkční tabulce přesně odvozen: ve **1 664 151** řádcích, kde jsou k dispozici `windSpeed`, `windrun` a kladný `interval`, platí `windrun = windSpeed × interval / 60` bez jediné numerické odchylky > 0,000001. Není to nezávislý důkaz správné rychlosti.
- `windchill` je odvozená meteorologická veličina; nynější audit ji neopravuje a neinterpretuje jako samostatný anemometr.

WeeWX definuje `windSpeed` jako průměr během archivního intervalu, `windGust` jako jeho maximum, `windDir` podle režimu agregace, `windGustDir` jako směr při nárazu. Dokumentace: https://weewx.com/docs/latest/custom/cheetah-generator/ a https://weewx.com/docs/latest/reference/weewx-options/accumulator/.

### F. Rozdíl v roce 2026: pracovní/produkční archiv ↔ GW1000

`loucka_reconstruction` a `pocasi-loucka.eu` mají na **1 679 802 párovaných dateTime identické** `windSpeed`, `windGust`, `windDir` i `windGustDir`; pracovní kopie končí o něco dřív než produkce. Produkce a `pocasi-loucka.eu_GW1000` mají 1 674 534 společných časů. Rozdíl ve větru se projevuje od **2026-03-08 12:15 UTC**, nikoli plošně v historických letech: celkem **61 190** párovaných řádků s rozdílným `windSpeed`, **23 524** s rozdílným `windGust`, **62 112** s rozdílným `windDir` a **49 849** s rozdílným `windGustDir`.

| Měsíc 2026 (časová zóna DB) | Páry | rozdílná rychlost | prům. absolutní rozdíl rychlosti (km/h) |
|---|---:|---:|---:|
| leden | 8 913 | 0 | 0 |
| únor | 8 044 | 0 | 0 |
| březen | 8 569 | 6 271 | 0,648 |
| duben | 5 359 | 5 305 | 0,923 |
| květen | 7 489 | 7 334 | 0,978 |
| červen | 8 631 | 8 293 | 0,273 |
| červenec | 8 882 | 8 680 | 0,317 |
| srpen | 8 921 | 8 738 | 0,379 |
| září | 8 635 | 8 506 | 0,377 |
| říjen do auditu | 8 166 | 8 063 | 0,454 |

První rozdílný záznam `dateTime=1772972100`: produkce/pracovní archiv `windSpeed=11,88`, GW1000 `8,712` km/h, `windGust=19,44` km/h shodný, směr 234° vs 231,316°. Velké procento rozdílných *pětiminutových výstupů* při mnohem menším rozdílu měsíčních průměrů je slučitelné s jinou agregací vstupních LOOP dat nebo ovladače; zatím nelze označit jednu větev za správnou. V dubnu je současně neúplný překryv a odlišný průměr nárazů.

`pocasi-loucka.eu_old` se od produkce liší v 91 757 párech rychlosti z 1 189 955 společných časů; jde o další verzi historické linie, nikoli nezávislou referenci. `old_weewx` vs `weewx_WH1080` má v 1 104 416 společných časech 71 713 rozdílů rychlosti hlavně kvůli NULL v jedné z kopií. **Neslučovat tabulky na principu „ber první nenulovou hodnotu“.**

## Návrh bezpečné normalizace (bez provedení)

1. **Originály beze změny.** Připravit odvozený dataset nebo SELECT/view s `source_database`, `source_dateTime`, `source_usUnits`, `raw_value`, `normalized_kmh`, `regime_id`, `qc_status`, `evidence` a `uncertainty`; never overwrite `archive`.
2. **Rozhodovat současně podle databáze a časového režimu:** zdroje `old_weewx` a `weewx_WH1080` před prokazatelným přechodem interpretovat číselně jako km/h (**nikoli ×3,6**); od 2013-04-12 17:55 UTC, při potvrzeném režimu, interpretovat hodnoty jako m/s a násobit 3,6. Přechodová mezera = `UNRESOLVED_UNITS`; ověřit zvlášť první záznamy.
3. **U `usUnits=16` s potvrzenou sémantikou** považovat rychlost a náraz za km/h bez opakované konverze. Normalizace `windrun` pouze následný přepočet z rychlosti a přesného `interval`, žádné druhé násobení.
4. **QC flagy místo nulování:** `IMPOSSIBLE_DIRECTION`, `GUST_BELOW_MEAN`, `FROZEN_ZERO`, `FROZEN_CONSTANT`, `SUSPECTED_GUST_SPIKE`, `MISSING_DIRECTION`, `SOURCE_DIVERGENCE`, `UNRESOLVED_UNITS`. Samostatně evidence jistoty chyby a jistoty případné náhradní hodnoty.
5. **Směry:** interval 0–360° je geometrická doména, ale při nulovém větru může být 0° jen placeholder; neinterpretovat automaticky jako sever. Neplatné astronomické hodnoty musí zůstat v raw + QC, neprovádět modulo. Zacházet s `windGustDir` samostatně.
6. **Referenční kontrola:** záznamy 2015–2016, 2020 a extrémy WH1080 porovnat s dostupnými dobovými anemometry LuhaMet / ILOUKA4 a archivem ČHMÚ, včetně časové osy změn čidla, jeho výšky, kalibrace a WeeWX konfigurace; při ztrátě nezávislé reference nepřidělovat konkrétní náhradní hodnotu.
7. **Před případnou aplikací:** separátní CSV kandidátů s `dateTime`, raw, QC a proveniencí; test převodů 1 a 3,6 na vzorcích; kontrola známých hranic; záloha, rollback a výslovné schválení. Toto zadání **neschvaluje žádný zápis do DB**.

## Reprodukovatelnost — vybrané pouze SELECT dotazy

Názvy databází obsahují pomlčku a tečku, proto jsou v SQL citovány zpětnými apostrofy; všechny časy v důkazních dotazech jsou Unix epoch v UTC.

```sql
-- Soupis a význam jednotek:
SELECT usUnits,COUNT(*) AS n,MIN(dateTime),MAX(dateTime),
       MAX(windSpeed),MAX(windGust),MAX(windDir)
FROM `weewx_WH1080`.`archive` GROUP BY usUnits;

-- Párování starého zdroje s produkcí a identifikace jednotkových režimů:
SELECT YEAR(FROM_UNIXTIME(a.dateTime)) AS yr, COUNT(*) AS overlap,
 SUM(a.windSpeed>0 AND ABS(a.windSpeed-b.windSpeed)<0.00001) AS equal_nonzero,
 SUM(a.windSpeed>0 AND ABS(a.windSpeed-3.6*b.windSpeed)<0.0001) AS x36_nonzero
FROM `pocasi-loucka.eu`.`archive` a
JOIN `old_weewx`.`archive` b ON a.dateTime=b.dateTime
GROUP BY YEAR(FROM_UNIXTIME(a.dateTime));

-- Denní úplně nulové nebo konstantní úseky; d = přesně UTC den:
SELECT FLOOR(dateTime/86400) AS d, COUNT(*) AS n, COUNT(windSpeed) AS ns,
 MIN(windSpeed) AS min_speed, MAX(windSpeed) AS max_speed,
 MIN(windGust) AS min_gust, MAX(windGust) AS max_gust
FROM `pocasi-loucka.eu`.`archive`
GROUP BY FLOOR(dateTime/86400) ORDER BY d;

-- Fyzikální nesoulad gust < mean:
SELECT dateTime,windSpeed,windGust,windDir
FROM `pocasi-loucka.eu`.`archive`
WHERE windGust < windSpeed - 0.001 ORDER BY dateTime;

-- Divergence roku 2026 (NULL-safe porovnání):
SELECT COUNT(*) AS overlap,
 SUM(NOT(a.windSpeed<=>g.windSpeed)) AS speed_diff,
 SUM(NOT(a.windGust<=>g.windGust)) AS gust_diff,
 SUM(NOT(a.windDir<=>g.windDir)) AS dir_diff
FROM `loucka_reconstruction`.`archive` a
JOIN `pocasi-loucka.eu_GW1000`.`archive` g ON g.dateTime=a.dateTime
WHERE a.dateTime>=1767225600;
```

**Závěr:** Zjistili jsme zásadní chybu předpokladu o jednotkách starých archivů, větrné výpadky, chybné extrémy a tři významné změny režimu (duben 2013, září 2020, srpen 2022) i divergence v březnu 2026. Dostupná data zatím nestačí pro bezpečnou automatickou náhradu podezřelých měření. Žádný databázový řádek nebyl změněn.
