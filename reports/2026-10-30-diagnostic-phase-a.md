# Diagnostika LXC a audit srážkových případů — běh 2026-10-30

> **Revizní upřesnění 30. 10. 2026 (bez nového SQL):** Tento report zachycuje historicky provedený read-only běh. Původní interpretace denních ČHMÚ `SRA` jako oken končících ve zdrojovém `DT=06:00 UTC` **není doložena**. ČHMÚ popisuje ranní 24hodinové měření připsané předchozímu dni; bez mapování `DT`/`TIMEFUNC` na přesná časová okna nelze denní řadu použít jako přímý důkaz pětiminutové události ([metodika SRA](../docs/chmi-daily-sra.md)). `HIGH_CONFIDENCE` pro chybný impuls není důkazem přesné náhrady `rain=0`. Starší statistiky používají původní hranice `[start,end)`; WeeWX hranice `(start,end]` popisuje [pozdější oprava](2026-10-30-code-review-stabilization.md). Původní data a CSV se nemění.


## Rozsah, metoda a bezpečnost

- Časové rozmezí databázového inventáře: produkční `archive` od Unix času `1238345100` do `1793350200`; pracovní archiv do `1793286600`.
- Diagnostika systému a schémat proběhla 2026-10-30. Případy Fáze A: místní dny 1.–3. 6. 2010, místní čas 28. 3. 2011 08:50 CEST a 27. 2. 2025 21:15 CET.
- SQL se spouštělo s `START TRANSACTION READ ONLY`; byly použity jen SELECT/SHOW a `information_schema`. Počty jsou skutečné `COUNT(*)`, ne odhad `information_schema.TABLE_ROWS`.
- Časy byly porovnány číselně jako Unix sekundy. Místní čas se převádí pomocí `Europe/Prague`; pro červnové místní dny jsou hranice UTC `2010-06-01` analogicky +02:00, tedy epoch rozsahy `1275343200–1275429600`, `1275429600–1275516000`, `1275516000–1275602400`.
- `usUnits=16` bylo zjištěno u všech intervalových skupin v produkčním `archive`. WeeWX konfigurační soubory v LXC nebyly nalezeny, proto interpretace rain jako cm a rainRate jako cm/h zůstává založena na dodaném historickém kontextu, nikoli na ověřené konfiguraci driveru.
- Změna databázových měření: **0 řádků**.

## Stav LXC a projektu

| Položka | Zjištění |
|---|---|
| OS | Debian GNU/Linux 13.7 (trixie) |
| CPU / paměť | 2 vCPU; RAM 8.0 GiB, dostupných přibližně 7.5 GiB; swap 0 |
| Disk | 10 GiB, použito 1.2 GiB, volno 8.9 GiB |
| Nástroje | Python 3.13.5, Git 2.47.3, MariaDB klient 11.8.6 |
| MariaDB | Server 11.8.6-MariaDB-0+deb13u1; síťové spojení funkční |
| Přihlášení | `.env` existuje s právy 600, klíče jsou vyplněny; tajemství nebylo vypsáno |
| Původní projekt | Pouze README/AGENTS/.env/example a archiv dokumentace; Git repozitář inicializován na větvi `main`, zatím bez commitu, WeeWX konfigurace nenalezena |
| Účet OS | Původní shell běžel jako root. Byl založen systémový neprivilegovaný účet `meteo-audit`; projekt a `.env` mu náleží, `.env` zůstává 600. |

Síťová adresa DB nebyla odvozována ani vypisována. Spojení bylo otestováno údaji, které již byly v lokálním `.env`.

## Databáze a struktura

Na serveru jsou dostupné databáze `pocasi-loucka.eu`, `loucka_reconstruction`, `old_weewx`, `pocasi-loucka.eu_GW1000`, `pocasi-loucka.eu_old`, `weewx_WH1080` a `information_schema`.

| Archiv | Řádků | MIN(dateTime) | MAX(dateTime) |
|---|---:|---:|---:|
| produkční `pocasi-loucka.eu.archive` | 1 680 013 | 1 238 345 100 | 1 793 350 200 |
| pracovní `loucka_reconstruction.archive` | 1 679 802 | 1 238 345 100 | 1 793 286 600 |

Produkční hodnoty intervalů (`usUnits=16`):

| `interval` min | Záznamů |
|---:|---:|
| 5 | 1 677 916 |
| 6 | 2 090 |
| 10 | 1 |
| 30 | 3 |
| 40 | 1 |
| 55 | 1 |
| 75 | 1 |

Oba archivy mají `dateTime int(11)` jako primární klíč, dále `usUnits int`, `interval int` a měřené veličiny typu `double NULL`; jiný index na `archive` zjištěn nebyl. Produkční databáze obsahuje i denní souhrnné tabulky WeeWX. `archive` v pracovním schématu není totožná kopie produkce: v kontrolních případech má jinou hodnotu `rainRate` u 27. 2. 2025.

V `loucka_reconstruction` byly potvrzeny tabulky července 2021 (včetně `rain_qc_202107`, `rain_qc_daily_202107`, `rain_archive_original_202107`, `rain_reconstruction_202107_chmi_v1`), `reconstruction_humidity_202204`, `reconstruction_batches`, `reconstruction_candidates`, `reconstruction_changes`, `reference_observations`, `reference_daily`, `reference_stations`.

Aktuální auditní historie `reconstruction_changes`: 80 749 řádků — 62 907 `applied`, 17 842 `reverted`, 0 `pending`. Při prvním čtení téhož běhu bylo zjištěno 24 `pending` řádků; v závěrečném čtení už chyběly, bez zápisu z tohoto auditu. Kandidátní batche pro tyto tři případy jsou stále `pending`; nejsou důkazem, že produkční oprava proběhla. Dále je v historii evidence aplikovaného obnovení `rainRate` pro 2025-02-27 21:15, která změnila pouze pracovní archiv (`0 → 0.0053333333` cm/h). Produkční archiv stále má `rainRate=0`. `loucka_audit` má v pracovní DB také INSERT/UPDATE/DELETE/DDL práva; současný běh je chráněn read-only transakcí, ale dlouhodobě se má vytvořit SELECT-only účet.

Předchozí jmenovaný balíček `loucka-rain-phaseA-201006-review-20261030-v1` není v souborech LXC. Jeho 16 kandidátů a 3 kandidáti potvrzovacího balíčku byly nalezeny přímo v DB.

## Červen 2010 — místní občanské dny

Při `usUnits=16` odpovídá součet v tabulce standardní interpretaci WeeWX v cm; níže je převod na mm násobením 10. Datové mezery jsou počítány proti 288 pětiminutovým intervalům na den.

| Místní datum | Záznamů / očekáváno | Pokrytí | Rain NULL | Uložený součet | Převedený součet | Maximum jednoho intervalu |
|---|---:|---:|---:|---:|---:|---:|
| 2010-06-01 | 279 / 288 | 96.88% | 0 | 10.002 cm | 100.02 mm | 2.568 cm = 25.68 mm |
| 2010-06-02 | 288 / 288 | 100% | 0 | 3.066 cm | 30.66 mm | 0.705 cm = 7.05 mm |
| 2010-06-03 | 258 / 288 | 89.58% | 0 | 5.952 cm | 59.52 mm | 0.768 cm = 7.68 mm |
| Celkem | 825 / 864 | 95.49% | 0 | 19.020 cm | 190.20 mm | — |

Zjištěné denní úhrny přesně odpovídají předchozímu kontextu. 39 záznamů chybí v uvedených místních dnech; chybějící řádek nebyl započítán jako nula.

### 16 evidovaných extrémních intervalů

Všech 16 existuje v produkci, má `rainRate=0` a je stále totožných v raw archive `pocasi-loucka.eu_GW1000`. Hodnoty `old_weewx` a `weewx_WH1080` při stejných časech vykazují prudké skoky/resetové vzory; tyto raw hodnoty jsou čítače, nikoli intervalové mm. Stávající batch navrhuje `rain=0` u všech 16, ale zatím čeká.

| Místní čas | Rain (cm) | Převod původního rain (mm) |
|---|---:|---|
| 2010-06-01 12:40 | 1.554 | 15.54 mm |
| 2010-06-01 12:45 | 2.331 | 23.31 mm |
| 2010-06-01 13:10 | 2.568 | 25.68 mm |
| 2010-06-01 23:15 | 1.536 | 15.36 mm |
| 2010-06-01 23:20 | 0.384 | 3.84 mm |
| 2010-06-02 02:00 | 0.705 | 7.05 mm |
| 2010-06-02 14:50 | 0.606 | 6.06 mm |
| 2010-06-03 12:10 | 0.384 | 3.84 mm |
| 2010-06-03 12:15 | 0.576 | 5.76 mm |
| 2010-06-03 15:10 | 0.768 | 7.68 mm |
| 2010-06-03 15:50 | 0.768 | 7.68 mm |
| 2010-06-03 16:05 | 0.576 | 5.76 mm |
| 2010-06-03 16:10 | 0.384 | 3.84 mm |
| 2010-06-03 17:50 | 0.384 | 3.84 mm |
| 2010-06-03 21:10 | 0.768 | 7.68 mm |
| 2010-06-03 21:25 | 0.768 | 7.68 mm |

Součet kandidátních hodnot je 15.06 cm = 150.6 mm. Raw čítačové hodnoty na stejných 16 časech zůstávají např. 174.9 → 408 → 256.8; u pozdějších intervalů jsou kroky nekonzistentní a jednotlivé přenosy nemusejí být nezávislými měřeními.

### Nezávislá data ČHMÚ

Oficiální denní řada `SRA`, `TIMEFUNC=06:00`, stanice Vizovice (`0-203-0-11777`), uvádí:

| Datum záznamu v UTC | Úhrn | Příznak | Kvalita |
|---|---:|---|---:|
| 2010-06-01 06:00Z | 48.6 mm | prázdný | 0.0 |
| 2010-06-02 06:00Z | 3.9 mm | prázdný | 0.0 |
| 2010-06-03 06:00Z | 2.0 mm | prázdný | 0.0 |

Kladná‑Žilín (`0-203-0-11778`) má ve stejném typu denního záznamu 57.0, 3.1 a 4.6 mm. Tyto denní řádky naznačují regionální srážky. **Původní tvrzení o 24hodinovém okně končícím v `DT=06:00 UTC` nebylo ověřeno**: ČHMÚ úhrny připisuje předchozímu dni a význam `DT`/`TIMEFUNC` je třeba doložit. Žádný zde uvedený SRA řádek proto nepotvrzuje ani nevylučuje konkrétní pětiminutový impuls a neopravňuje k plošnému dosazení nuly. ČHMÚ distribuuje desetiminutové a hodinové soubory až od roku 2018, proto pro rok 2010 tato poddenní kontrola z daného veřejného archivu chybí.

## 28. března 2011, 08:50 CEST

- Produkce: `rain=3.072 cm` (30.72 mm), `rainRate=0`; sousední intervaly 08:45, 08:55 a 09:00 místního času mají `rain=0`.
- `old_weewx.archive` a `weewx_WH1080.archive`: čítač skáče 0 → 307.2 → 384, rainRate zůstává 0. Hodnota 307.2 odpovídá 1 024 krokům po 0.3 mm, přesně jak uváděl předchozí audit.
- ČHMÚ: ve zdrojovém CSV pro `DT=2011-03-28T06:00Z` mají Vizovice `SRA=0.0 mm` a Kladná-Žilín `SRA=0.0 mm` s příznakem `T` (stopové srážky). **Bez ověření časového okna tyto hodnoty nedokazují počasí v 06:50 UTC**, kdy nastal posuzovaný impuls. `API30` nebylo v hodnocení použito.
- V DB je pending kandidát `rain: 3.072 → 0` s metodou `suspected-anomaly`; žádná odpovídající aplikovaná změna nebyla nalezena. Produkce stále nese původní hodnotu.

Revidované hodnocení: **HIGH_CONFIDENCE pro podezření na chybu čítače** (skok a nuloví sousedé), ale **NEOVĚŘENÁ náhrada `rain=0`**. Původní tvrzení o přímé časové podpoře denní ČHMÚ je pozastaveno. Změna se neaplikuje.

## 27. února 2025, 21:15 CET

- Produkce: `rain=3.05 cm` (30.5 mm), `rainRate=0`, předchozí interval má `rain=NULL`, následující `rain=0`; během výpadku jsou venkovní teplota/vlhkost/vítr NULL.
- Místní den produkce má 288 řádků, z toho 5 s `rain=NULL`; doslovný součet uložených hodnot je 3.89 cm = 38.9 mm. Bez impulzu by činil 8.4 mm.
- Reference: ILOUKA4 poskytuje 288 bodů a denní kumulativní hodnota 8.81 mm; hodnota se opakuje, nesmí se sčítat. LuhaMet Sehradice poskytuje 288 bodů a běžící čítač roste od 0.03 do 8.45 mm; jeho rozdíly a denní reset je nutné respektovat. Hodnoty kolem času incidentu: LuhaMet 8.44 mm, ILOUKA4 8.81 mm.
- ČHMÚ: pro zdrojové `DT=2025-02-27T06:00Z` uvádí Vizovice `SRA=5.6 mm` a Kladná-Žilín `7.4 mm`. **Časová vazba těchto řádků na incident v 20:15 UTC není doložena**; při hodnocení konkrétního impulzu jsou bez ověřeného 24hodinového okna pouze kontextem. Místní výpadek a další souběžné stanice zůstávají oddělenými indikacemi.
- Rekonstrukční batch navrhuje `rain=3.05 → 0` a `rainRate=0.005333… → 0`, čeká na vyhodnocení. Produkce má nyní `rainRate=0`; pracovní archiv má `rainRate=0.005333…` z dříve aplikovaného obnovení intenzity. Automatické přepsání tohoto dříve aplikovaného výsledku by bylo druhým a konfliktním zásahem.

Revidované hodnocení: **HIGH_CONFIDENCE pro podezření na chybný impuls 30.5 mm**, ale **NEOVĚŘENÁ přesná náhrada `rain=0`**. `rainRate` vyžaduje samostatné řešení, protože historická sémantika není doložena a v pracovní DB existuje konfliktní aplikovaná změna. Změna se neaplikuje.

## Návrhy a současný běh

- Červen 2010: zachovat 16 kandidátů `rain → 0` jako `SUSPECTED/UNRESOLVED`; neaplikovat hromadně. Nejdřív ověřit původní datalogger/receiver logy a přesné časy stanice, pak posuzovat každý interval vůči okolním srážkám.
- 2011-03-28: původní pending kandidát `rain → 0`; vysoká jistota *diagnózy anomálie*, náhrada nulou **není potvrzena**.
- 2025-02-27: původní pending kandidát `rain → 0`; vysoká jistota *diagnózy anomálie*, náhrada nulou **není potvrzena**. `rainRate` samostatně neřešit automaticky.
- Nebyla vytvořena duplikátní auditní tabulka, nebyly zapisovány databázové kandidáty ani historii.

Dotazy pro reprodukci jsou uloženy v `sql/readonly/phase_a_cases.sql`; inventář v `sql/readonly/inventory.sql`. Měsíční čtený průchod používá `src/meteo_audit/monthly.py`, jeho souhrn je `reports/monthly_rain_coverage.csv` a agregace po letech `reports/yearly_rain_coverage.csv`. Rozdíl proti předchozímu běhu: rozšířen audit na kompletní dostupný měsíční rozsah; žádný zápis do databáze.

## Nejdůležitější další priority

1. Získat aktuální WeeWX konfiguraci a zdokumentovat ovladače, jednotky a `rainRate` sémantiku v historických obdobích.
2. Rozebrat již aplikovaných 62 907 a vrácených 17 842 změn po batchech; určit oddělení pracovních a produkčních zásahů. Zatím je k dispozici pouze agregovaný stav.
3. Zkontrolovat jednotkový přechod 2013, září 2020 a srpen 2022 přes zdrojové databáze/driver logs, ne plošnou konverzí.
4. Vypočítat měsíční a roční pokrytí s místními hranicemi a nepravidelnými intervaly, pak hledat čítačové restarty po jednotlivých stanicích.
5. Prověřit červenec 2021 déšť a duben 2022 vlhkost proti původním a pracovním tabulkám.
6. U ČHMÚ pro 2009–2017 využít dostupné denní stanice; poddenní srovnání označit jako nedostupné, dokud nebude získán nezávislý archiv.

### Zdroje a konkrétní opakovatelnost

- ČHMÚ historické denní CSV stanice Vizovice: `dly-0-203-0-11777-SRA.csv`; stanice Kladná‑Žilín: `dly-0-203-0-11778-SRA.csv`. Zachycené řádky včetně flag/quality jsou v `reports/chmi_daily_incident_rows.csv`.
- Identita stanic a jejich časové intervaly byly ověřeny v oficiálním [metadatovém souboru ČHMÚ](https://opendata.chmi.cz/meteorology/climate/historical_csv/metadata/meta1.csv). Data byla načtena z [adresáře historických denních srážek ČHMÚ](https://opendata.chmi.cz/meteorology/climate/historical_csv/data/daily/precipitation/).
- Pozorovací řady 10min a 1h srážek v oficiálním archivu začínají rokem 2018; viz [10min srážky](https://opendata.chmi.cz/meteorology/climate/historical_csv/data/10min/precipitation/) a [1h srážky](https://opendata.chmi.cz/meteorology/climate/historical_csv/data/1hour/precipitation/).
- Denní CSV sloupce `DT`, `VALUE`, `FLAG`, `QUALITY`; porovnávány pouze `SRA`. `API30` nebylo považováno za naměřený denní úhrn.

## Plošné měsíční pokrytí

Přehled načetl lokální měsíce 2009-01 až 2026-10 po jednom dotazu na měsíc, s podmínkou na `dateTime` a primární klíč. Je to přibližně 1.68 milionu čtených řádků; výpočet má paměť omezenou na jeden měsíc. Pro prázdné měsíce uvnitř skutečného globálního rozsahu se očekávání odvozuje od globálního nejčastějšího `interval` (5 min); měsíce před prvním a po posledním archivním čase jsou označeny mimo rozsah. První a poslední měsíc jsou částečné. Pokrytí je hrubý početní odhad podle nejčastějšího intervalu v měsíci, nikoli potvrzení kvality měření.

- Měsíční řádky: 214 (včetně 2 měsíců před začátkem historie); načteno 1 680 012 řádků. Výstupní CSV uvádí rozsah a odhad pokrytí samostatně. Roční agregace je v druhém CSV.
- Prázdné měsíce uvnitř historického rozsahu: 2011-09 až 2012-02 (6 celých měsíců); nejsou vykazovány jako nuly.
- Další kompletní měsíce pod 80% odhadovaným pokrytím jsou vypsány v CSV, zejména 2014-06, 2017-01/05/06 a 2018-02/03. Roční pokrytí odhadem klesá na 59.794% v 2011, 71.469% v 2012 a 73.077% v 2017. Významné výpadky jsou prioritou pro časovou rekonstrukci zdrojů.
- Součet `rain` po převodu ×10 při `usUnits=16`: 11 585.028 mm přes dostupné období. Jde o **historický výsledek původního běhu**, nikoli ověřený očištěný úhrn. Pozdější kontrola zjistila poškozený/neúplný původní měsíční CSV export; pro další analýzu použij čerstvý reprodukovatelný zdrojově označený export.
- Rozpis `interval` při závěrečném čtení: 1 677 916 řádků po 5 min, 2 090 po 6 min a 7 řádků po 10–75 min. `rainRate` není NULL v žádném řádku, pouze 2 761 hodnot je nenulových (maximum 5.72 uložených jednotek); současně je 38 244 záznamů s `rain>0` a `rainRate=0`. Jde o výrazný časový/driverový signál k auditu, ale bez sémantiky `rainRate` není tato neshoda sama o sobě důkaz chyby. Archiv se během online čtení doplňoval: kompletní měsíční průchod čítal 1 680 012 řádků; poslední živý `COUNT(*)` poté 1 680 013. To ukazuje na nové archivní záznamy během čtení; kvůli minimálnímu dopadu nebyl držen dlouhý konzistentní snapshot.

## Dosavadní zásahy a rekonstrukce července 2021

Byly zjištěny a pouze čteny všechny požadované artefakty. Pro místní interval 2021-07-01 00:00 až 2021-08-01 00:00 CEST:

- Produkční archiv i `rain_archive_original_202107`: 8 921 řádků; produkční uložený součet 70.10146 cm = 701.0146 mm. Maximum intervalu 0.39116 cm.
- `rain_qc_daily_202107`: 31 dní; suma `original_rain_mm` 701.0146 mm; `screened_unverified_mm` 525.8308 mm; 304 podezřelých intervalů se součtem 175.1838 mm, 332 plausibilních a 674 unresolved klasifikací. `verified_daily_rain_mm` je NULL ve všech 31 dnech; žádný denní závěr tedy není označen za ověřený. Celkem zaznamenáno 146 chybějících `rain` a 243 chybějících `rainRate` intervalů.
- `rain_audit_202107`: klasifikace řízená pouze vlhkostním screeningem (`humidity_screen_only`): 332 `possible_rain_both_humid`, 304 `strong_suspicion_both_dry`, 674 `unresolved`. Navržené náhrady jsou NULL; soubor sám o sobě neobsahuje hodnoty nezávislé stanice pro každý interval.
- `rain_reconstruction_202107_chmi_v1`: 8 928 plánovaných bodů; 8 905 mají metodu `chmi10m_idw2`, 23 počáteční body metodu `initial_archive_zero_no_june_csv`. Součet `rain_cm` je 4.25672658 cm (42.5673 mm). Pro všech 8 921 timestampů, které existují v produkčním i pracovním archivu, odpovídá pracovní `archive.rain` této tabulce přesně.
- Pracovní `archive` má za stejný měsíc 4.25672658 cm, zatímco produkce 70.10146 cm; rozdíl činí zhruba 658.45 mm. V pracovním archivu je 1 172 timestampů s rain>0 v produkci a rain=0 v rekonstrukci a 258 timestampů s opačným vztahem. To je skutečná již existující změna pracovního datasetu, nikoli zápis tohoto běhu.
- `reconstruction_changes` eviduje `rain-jul2021-quarantine-v1` jako 8 921 reverted změn (nová hodnota NULL v historii) a `rain-jul2021-dryday-22-24-v1` jako 146 applied změn pro rain a 243 pro rainRate. Současně batch `loucka-rain-jul2021-chmi-dualrh-20261029-v1` je stále `pending` s 71 kandidáty. Stav batch ani `reverted` v historii proto sám nevysvětluje, proč pracovní archive rain přesně odpovídá CHMI kandidátní tabulce. Nutné je rozplést provenienci změn ještě před jakoukoli další prací.

Přehled přesných SQL dotazů: `sql/readonly/july_2021_review.sql`. Produkce nebyla upravena; pracovní archive nebyl upraven. Tato zjištěná neshoda vyžaduje nezávislou kontrolu backupu a logů změn, ne další import.
