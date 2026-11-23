# C004 a celá historie tlaku Loučky 2009–2026 — read-only inventura a plán validace ČHMÚ

**Datum:** 23. 11. 2026. **Režim:** výhradně SELECT na existující MariaDB.
**SQL host:** lo-infra-db-mariadb01; pracovní archiv loucka_reconstruction.archive.
**Rozsah:** celý existující archiv od března 2009 do aktuálního podzimu 2026; čerstvě přibývající poslední rok je pohyblivý.
**Stav:** SOURCE_CANDIDATES_IDENTIFIED / INDEPENDENT_CHMI_NUMERICAL_VALIDATION_NOT_YET_DONE / NO_APPROVED_REPLACEMENTS.

## Závěr v pěti bodech

1. Přesně **198 175 NULL** <BT>pressure<BT> v pracovním archivu
   pro období 2009–2026. Přesné hranice let jsou UTC.
2. Pro **135 990** z těchto timestampů existuje alespoň jeden
   nenulový <BT>pressure<BT> v historických kopiích, ale
   **62 185** žádnou přímou hodnotu nemá ani ve všech pěti srovnaných archivech.
   Přítomnost zdroje **není** validací náhradní hodnoty.
3. V letech 2016–2018 (C004) chybí **90 556** tlakových hodnot,
   <BT>weewx_WH1080<BT> nabízí na **75 074** z těchto timestampů nenulovou
   hodnotu, která je u **všech 75 074 identická** s <BT>old_weewx<BT>.
   Jde o **stejnou datovou linii**, nikoli dvě nezávislá měření.
4. <BT>old_weewx.pressure<BT> se v dubnu 2019 začne prudce odchylovat
   od <BT>weewx_WH1080<BT>; květen až prosinec 2019 vykazuje v průměru
   rozdíl přibližně −25 až −29,4 hPa. **Přenos hodnot z tohoto období
   je NO-GO** do vysvětlení zdrojové epochy.
5. Kopie <BT>pocasi-loucka.eu_GW1000<BT> v letech 2024–2026 postupně
   mění redukční rozdíl <BT>barometer-pressure<BT> asi z 51,4 přes
   44,4 na 39,4 hPa. Naopak pracovní archiv ukazuje sezónně proměnlivý
   rozdíl přibližně 48–53 hPa. Zdrojová kopie není univerzální
   kanonická hodnota tlaku, zvláště ne po roce 2024.

**Žádná změna počasí ani SQL práv nebyla provedena.** Nejde o
schválení žádného UPDATE. Denní souhrny a živá produkční DB zůstávají nedotčeny.

## Výpadky po letech (UTC)

Sloupec „má zdroj“ znamená alespoň jednu číselnou hodnotu
ze současně srovnaných kopií: weewx_WH1080, old_weewx,
pocasi-loucka.eu_GW1000, pocasi-loucka.eu_old a produkční
pocasi-loucka.eu. WH a GW jsou samostatně uvedeny
kvůli pokrytí, **nikoliv jako nezávislé fyzické stanice**.

| Rok UTC | NULL pressure | Alespoň jeden zdroj | Bez přímého zdroje | WH1080 | GW1000 kopie |
|---|---:|---:|---:|---:|---:|
| 2009 | 882 | 759 | 123 | 408 | 756 |
| 2010 | 702 | 700 | 2 | 674 | 639 |
| 2011 | 849 | 847 | 2 | 764 | 669 |
| 2012 | 1 029 | 1 026 | 3 | 797 | 997 |
| 2013 | 8 216 | 8 215 | 1 | 8 062 | 7 320 |
| 2014 | 3 189 | 3 188 | 1 | 2 426 | 3 015 |
| 2015 | 6 809 | 4 145 | 2 664 | 3 315 | 1 835 |
| 2016 | 15 727 | 8 006 | 7 721 | 3 764 | 7 374 |
| 2017 | 28 287 | 26 618 | 1 669 | 25 189 | 13 089 |
| 2018 | 46 542 | 46 319 | 223 | 46 121 | 6 780 |
| 2019 | 20 049 | 19 803 | 246 | 19 350 | 7 874 |
| 2020 | 10 406 | 7 929 | 2 477 | 404 | 4 486 |
| 2021 | 2 858 | 1 082 | 1 776 | 0 | 1 082 |
| 2022 | 46 305 | 1 236 | 45 069 | 0 | 1 163 |
| 2023 | 781 | 589 | 192 | 0 | 589 |
| 2024 | 1 767 | 1 752 | 15 | 0 | 1 752 |
| 2025 | 3 739 | 3 739 | 0 | 0 | 3 739 |
| 2026 | 38 | 37 | 1 | 0 | 37 |
| **Celkem** | **198 175** | **135 990** | **62 185** | — | — |

Pozor: „GW1000 kopie“ obsahuje i data **před instalací fyzické
brány GW1000 v srpnu 2022**. Pro roky 2009–2021 jde o
historickou databázovou kopii, nikoliv nezávislé GW1000
fyzické měření. Původně použitá stanice Watson W-8681
měřila už od 29. 3. 2009. Zdrojová provenience musí být
vždy po hardwarových epochách.

## C004: test kvality source WH1080 v chybějících intervalech

Rok | WH1080 dostupných | Přímá shoda s old_weewx | WH1080 minus existující target pressure na společných nenulových hodnotách | Rozdíl barometer minus WH pressure při cílovém pressure NULL
:--|--:|--:|--:|--:
2016 | 3 764 | 3 764/3 764 | průměr −0,724 hPa, SD 0,452 | průměr 51,95 hPa, SD 2,41
2017 | 25 189 | 25 189/25 189 | průměr −0,538 hPa, SD 0,496 | průměr 50,26 hPa, SD 2,52
2018 | 46 121 | 46 121/46 121 | průměr −0,601 hPa, SD 0,493 | průměr 48,46 hPa, SD 1,87

Rozdíl <BT>barometer-pressure<BT> má v chybějícím pressure
období plausibilní rozsah pro výšku stanice kolem 425 m.
U žádného z 75 074 WH kandidátů nebyl <BT>pressure<BT> mimo
900–1050 hPa a na existujícím přesném předchozím 5minutovém
WH záznamu nebyl skok >3 hPa. Toto jsou pouze kontrolní
filtry; **neprokazují měřicí správnost**.

Překryv WH1080 a GW1000 není bez konfliktů: u chybějícího
cílového pressure je rozdíl >2 hPa v **80/370/24**
případech (2016/2017/2018). Zdroje jsou vzájemně
metodicky rozdílné a nelze sestavit hromadný <BT>COALESCE<BT> UPDATE.

**Na všechna data 2018–2022 navazují zásadní zdrojové změny:**
- leden–březen 2019: old_weewx.pressure přesně odpovídá
  WH1080 na zhruba 8,6k / 8,0k / 8,9k shodách měsíčně;
- květen 2019: rozdíl old minus WH −24,94 hPa,
  červen −27,43, srpen −29,41, prosinec −26,96 hPa;
- leden 2020: −27,0 hPa; od starého zdroje tedy žádná
  automatická oprava bez prokázané nové senzorové epochy.
- 2022: **46 305** NULL pressure, z toho **45 069**
  bez přímé numerické hodnoty ve všech pěti porovnaných
  archivech. Tento rok nelze vyřešit prostým obnovovacím JOINem.

## Moderní kopie GW1000: měnící se redukce tlaku

Na společných vyplněných intervalech r.pressure a gw.pressure:
- 2023: průměr r−gw = **+0,878** hPa;
- 2024: **−2,676** hPa;
- 2025: **−6,310** hPa;
- 2026 (dostupný překryv): **−11,602** hPa.

U GW kopie se měsíční rozdíl barometer−pressure posouvá
z ~51,4 hPa během 2023/začátku 2024 na ~47,3 (06/2024),
~44,4 (08/2024–01/2026), ~39,4 hPa (od 03/2026).
V pracovní rekonstrukci je rozdíl v daném období sezónně
~48–53 hPa. To je **silná indicie změny výškového
parametru nebo algoritmu přepočtu**, ne důkaz samotný.
Provozní konfigurace GW3000/WeeWX uvádí výšku 425 m,
ale historické epochy je nutné ověřit.

Důsledek: **neopravovat tlak z GW kopie automaticky ani
v novějších letech**; je nutný externí referenční
barometrický průběh.

## Nezávislá validace: ČHMÚ a okolní stanice

Oficiální metadata ČHMÚ:
https://opendata.chmi.cz/meteorology/climate/historical/metadata/meta1.json

**Primární referenční stanice Holešov**, WSI 0-20000-0-11774,
současná výška 222,25 m (změna umístění v červnu/červenci 2009).
Souřadnice 49.320556 N, 17.5700 E.

- Denní **staniční tlak P** (7/14/21 místní střední sluneční
  čas a denní průměr, u každé položky nutno ověřit definici):
  https://opendata.chmi.cz/meteorology/climate/historical_csv/data/daily/air_pressure/dly-0-20000-0-11774-P.csv
- Hodinové **P (staniční)** a **P_hm (redukovaný na hladinu
  moře)** od roku 2018 do uzavřeného 2025, veřejné adresáře:
  https://opendata.chmi.cz/meteorology/climate/historical_csv/data/1hour/synop/
- ČHMÚ datový popis a časové standardy:
  https://opendata.chmi.cz/meteorology/climate/Klimatologicka_data_popis.pdf

**Sekundární stanice Mošnov**, WSI 0-20000-0-11782,
současná výška 252,8 m (přesun v květnu 2016),
49.691944 N, 18.112778 E:
https://opendata.chmi.cz/meteorology/climate/historical_csv/data/daily/air_pressure/dly-0-20000-0-11782-P.csv

**Další blízké metadata ČHMÚ**: Zlín 0-203-0-11775
(49.236667 N, 17.643333 E, 283 m) a Vsetín
0-203-0-11788 (49.3442 N, 17.9961 E, 387 m).
Tyto stanice mohou pomoci hodnotit další prvky, nicméně
v prozkoumaném adresáři <BT>daily/air_pressure/<BT> jsme
nenalezli soubory staničního tlaku pro jejich WSI.
**Nepředpokládat, že mají tlakové reference dostupné.**

**Důležité omezení současného auditu:** veřejné odkazy,
stanice, výšky, datové složky a typy P/P_hm byly na
oficiálním webu ČHMÚ ověřeny. **Celý CSV obsah zatím
nebyl parsován ani číselně porovnán** s daty Loučky,
protože aktuální webový čtecí nástroj odmítá binární
Content-Type <BT>application/octet-stream<BT> a lokální
runtime nemá DNS pro opendata.chmi.cz. Nic z tohoto
reportu se tedy nesmí označit jako „CHMI_NUMERIC_VALIDATED“.

## Přesná metodika pro následující datový průchod

1. Na LXC s funkčním internetem **pouze stáhnout**
   do soukromého pracovníka oficiální Holešov/Mošnov
   denní CSV a (2018–2025) hodinové P/P_hm. Uložit
   SHA-256, datum souboru, origin URL, hlavičku/legendu
   a počet řádků. Pokud LXC není online, analyzovat
   samostatně lokální kopie; nikdy nezkoušet měnit produkci.
2. Respektovat **UTC** archivních dat WeeWX a **místní
   střední sluneční čas** denních ČHMÚ termínů;
   na hodinových ČHMÚ jsou časy UTC. Deník ČHMÚ
   neporovnávat naivně s Unix midnight.
3. Srovnat tři různé veličiny správně:
   - Loučka <BT>pressure<BT> = staniční tlak na ~425 m;
   - Loučka <BT>barometer<BT> = tlak redukovaný na hladinu moře;
   - ČHMÚ Holešov <BT>P<BT> = staniční tlak na ~222,25 m;
     ČHMÚ <BT>P_hm<BT> = redukovaný tlak.
   Rozdíl staničních tlaků při odlišné nadmořské výšce
   je **očekávaný**, nikoli chyba.
4. Pro 2018–2025 porovnat Loučka <BT>barometer<BT> proti
   ČHMÚ <BT>P_hm<BT> ve shodném UTC čase a případně
   tepelně redukovaný hypotetický Loučka station P
   podle validované hypsometrické formule. Neodhadovat
   fixní kalibrační offset přes všechny epochy.
5. Pro 2009–2017 použít kontrolu tlakového průběhu
   Holešov denní P s výškovým převodem a korekcí
   časového úseku; Mošnov jako nezávislé potvrzení.
   Vyhodnotit median bias/MAD, outliers, drift a bodové
   zvraty podle hardwarové epochy.
6. Teprve poté vybrat individuální přesné target_time
   a konkrétní přímý source WH1080 (kde validovaný);
   odděleně diskutovat, zda a jak opravovat
   roky bez přímého zdroje. Neznámé hodnoty
   **neimputovat** jako automatické 0 ani nepodložené
   „odhadované pressure“.
7. Připravit první read-only manifest a before-image
   bez jakéhokoli UPDATE/INSERT/DELETE. Každé následné
   APPLY jen po novém explicitním schválení přesného
   batch ID, old/new, SHA-256 a podepsaného receipt.

Další pravidla: neměnit živý WeeWX běžící v jiném LXC,
nevytvářet SQL účty nebo instance, neřešit PBS ani zálohy,
nepřepočítávat denní souhrny ručně.

## Reprodukovatelné SQL kontrolní dotazy

Roky UTC, žádné přepisy:

    SELECT YEAR(DATE_ADD('1970-01-01 00:00:00',
                         INTERVAL r.dateTime SECOND)) AS utc_year,
           COUNT(*) AS missing_pressure,
           SUM(wh.pressure IS NOT NULL) AS wh_source,
           SUM(gw.pressure IS NOT NULL) AS gw_source,
           SUM(pold.pressure IS NOT NULL) AS previous_copy
    FROM loucka_reconstruction.archive r
    LEFT JOIN weewx_WH1080.archive wh ON wh.dateTime=r.dateTime
    LEFT JOIN `pocasi-loucka.eu_GW1000`.archive gw ON gw.dateTime=r.dateTime
    LEFT JOIN `pocasi-loucka.eu_old`.archive pold ON pold.dateTime=r.dateTime
    WHERE r.pressure IS NULL
    GROUP BY utc_year ORDER BY utc_year;

Srovnání historické shody mezi dvěma kopií zdrojů:
pro přesné timestampy 2016–2018 s r.pressure IS NULL,
porovnat WH1080.pressure a old_weewx.pressure pomocí
NULL-safe shody a vyžadovat jednotkovou/provenienční
epochu. Tyto kopie zde odpovídají na 75 074/75 074
párech, tedy jde o jedinou sdílenou datovou linii.

### Závazný stav

**NO-GO na data APPLY.** Ze zdejší analýzy není
schválena ani jediná numerická náhradní hodnota.
