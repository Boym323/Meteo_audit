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

## Empirický překryv SRA/SRA10M (2018; není autoritativní definice)

Lokální reprodukovatelná kontrola dvou stanic porovnala denní SRA s dvěma kandidátními 24h okny desetiminutového SRA10M. SRA10M součet v okně `(DT, DT+24h]` se shodl s denním SRA na 305/328 QC-validních dnech ve Vizovicích a 316/334 v Kladné-Žilín; okno končící v DT mělo podstatně horší shodu. Jde o silnou empirickou indicii exportního indexování pro rok 2018, ne o autoritativní časovou definici, nezávislou referenci ani pravidlo pro starší roky. Denní hodnota proto zůstává `REFERENCE_WINDOW_UNVERIFIED`, dokud ČHMÚ nepotvrdí význam DT/TIMEFUNC a assigned day. Metoda a omezení: `reports/2026-11-13-chmi-sra-window-empirical.md`; konkrétní otázka ER-27.



## Upřesnění 2018 okna pomocí 07:00 místního středního slunečního času

Oficiální metadata datasetu výslovně stanoví 24hodinový úhrn odečítaný v 07:00 místního středního slunečního času a přiřazený předchozímu dni ([metadata ČHMÚ/Geoportálu](https://geoportal.gov.cz/php/micka/record/basic/6a589302-99f4-47f9-a4ee-152508c0a8017c), [popis denního úhrnu ČHMÚ](https://www.chmi.cz/namerena-data/data-z-mericich-stanic/denni-uhrn-srazek)). Popis Open Data portálu uvádí desetiminutová SRA10M data od roku 2018 a formát historických souborů, avšak neurčuje mapování sloupců `DT` a `TIMEFUNC` denního CSV ([PDF ČHMÚ](https://opendata.chmi.cz/meteorology/climate/Klimatologicka_data_popis.pdf)). Proto obecné mapování `DT` je nadále `REFERENCE_WINDOW_UNVERIFIED`.

Nový lokální test převádí 07:00 LMT pomocí longitude z uložených metadat stanic a nejbližšího desetiminutového endpointu. Pro hypotézu, že `DT` označuje přiřazený den, vychází odečet následující ráno na 05:48:37Z ve Vizovicích a 05:48:50Z v Kladné-Žilín; nejbližší dostupný SRA10M endpoint je 05:50Z (`DT+23h50m`). Tento 24hodinový součet odpovídá 328/328 QC-validním dnům Vizovice a 333/334 Kladná-Žilín, včetně všech 260 mokrých denních hodnot. Fixní `DT+24h` odpovídá 305/328 a 316/334. Jde o velmi silnou empirickou podporu přiřazovacího dne plus následujícího LMT odečtu pro tato dvě místa v roce 2018; nezaměňovat ji za formální specifikaci exportu nebo pravidlo pro starší roky či Loučku. Reprodukce/manifestační hashe: `reports/2026-11-13-chmi-sra-lmt-offset.md`, `.csv`, `.summary.csv`, `.manifest.json`, skript a validator; ER-27.

## Co zůstává otevřené

- Doplnit a ověřit přesné časové okno původních ČHMÚ řádků včetně zdrojových `FLAG` a `QUALITY`.
- Vyžádat případné poddenní zdroje (radarové odhady jsou **odhady**, nikoli přímé místní měření), kontrolovat jejich rozlišení a omezení.
- Revidovat `HIGH_CONFIDENCE` pro **náhradní hodnotu**, nejen pro rozpoznání anomálie; automatický apply není povolen.
