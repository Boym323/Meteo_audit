# ČHMÚ — interpretace denních úhrnů SRA a párování s WeeWX

## Pramen a status

ČHMÚ popisuje denní úhrn jako **24hodinové množství srážek měřené ráno**, které se **připisuje předchozímu dni**. Zdroje:
- [ČHMÚ: Denní úhrn srážek](https://www.chmi.cz/namerena-data/data-z-mericich-stanic/denni-uhrn-srazek) — měření přibližně v 7 hodin místního středního slunečního času, přiřazení předchozímu dni.
- [Metadata historického CSV, denní SRA](https://geoportal.gov.cz/php/micka/record/basic/6a589302-99f4-47f9-a4ee-152508c0a8017c?dlang=cze) — denní úhrn za 24 hodin, připsání předchozímu dni.
- [Historické CSV ČHMÚ](https://opendata.chmi.cz/meteorology/climate/historical_csv/data/daily/precipitation/) — zdrojové soubory SRA pro stanice.

**Neověřeno pro tento audit:** jak přesně jsou `DT` a `TIMEFUNC=06:00` ve stažených historických CSV mapovány na *datum přiřazení*, *čas měření* a *konec 24hodinového okna*. Není správné bez této definice tvrdit ani „řádek `DT=D 06:00Z` pokrývá předchozích 24 h“, ani „stačí k `DT` přičíst den“. Místní střední sluneční čas také není automaticky totožný s `Europe/Prague` včetně letního času.

## Povinný postup před porovnáním

1. Ulož identifikaci stanice, URL originálního CSV, datum získání, názvy zdrojových sloupců a ideálně hash souboru. Historická CSV z tohoto běhu nepřepisuj.
2. Dolož z autoritativní specifikace přímo pro historický formát význam `DT`, `TIMEFUNC`, přiděleného dne a časové pásmo; je-li potřeba, vyžádej si metodické upřesnění ČHMÚ.
3. Pro **každý** referenční řádek vytvoř explicitní `window_start_utc` (včetně/vyloučení hranice) a `window_end_utc` s uvedenou metodou odvození. Při neověřeném mapování ponech oba konce `NULL`/neznámé.
4. Vlastní WeeWX archiv agreguj jako intervaly končící na `dateTime` s konvencí `(start,end]`; při porovnání se zdrojem agreguj pouze časově shodné 24hodinové okno, nikoli automaticky občanský den.
5. Rozlišuj **regionální déšť**, **chybný lokální čítač**, **skutečné lokální srážky** a **jistotu náhradní hodnoty**. Rozdíl dvou stanic a denní číslo nedokazuje absenci krátkého lokálního deště.
6. Jakmile chybí definice období, označ výsledek `REFERENCE_WINDOW_UNVERIFIED`; nedávej samotnému dennímu SRA váhu rozhodující pro `rain = 0`.

## Důsledky pro fázi A (bez nového čtení DB)

V `reports/chmi_daily_incident_rows.csv` jsou hodnoty `DT` zapsané jako `date_time_utc`. Tento název **nesmí být vykládán jako ověřený čas ukončení 24hodinového měření**. CSV ponecháváme beze změny jako historický doklad, nikoli normalizovanou tabulku časových oken.

- **2010-06-01 až 2010-06-03:** záznamy ukazují deštivé regionální období, ale zatím nejsou časově zarovnány na jednotlivé pětiminutové impulsy. Všech 16 návrhů `rain: původní → 0` zůstává **neschválenými DB kandidáty**.
- **2011-03-28 08:50 místně (06:50Z):** prudký skok zdrojového čítače a okolní intervaly podporují podezření na chybný impuls. ČHMÚ řádek z `2011-03-28T06:00Z` **není ověřeným časovým důkazem** tohoto incidentu. Ani silná diagnóza poruchy nepotvrzuje `rain=0`.
- **2025-02-27 21:15 místně (20:15Z):** lokální výpadek a dvě okolní stanice podporují podezření na chybných 30,5 mm. ČHMÚ řádek `2025-02-27T06:00Z` nelze bez ověření časového okna použít k potvrzení incidentu. `rainRate` má samostatný konflikt v pracovní DB.

## Co zůstává otevřené

- Doplnit a ověřit přesné časové okno původních ČHMÚ řádků včetně zdrojových `FLAG` a `QUALITY`.
- Vyžádat případné poddenní zdroje (radarové odhady jsou **odhady**, nikoli přímé místní měření), kontrolovat jejich rozlišení a omezení.
- Revidovat `HIGH_CONFIDENCE` pro **náhradní hodnotu**, nejen pro rozpoznání anomálie; automatický apply není povolen.
