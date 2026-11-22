# Kompletní technický audit `loucka_reconstruction` — 22. 11. 2026

**Stav:** READ-ONLY, ověřená databáze MariaDB 11.8.6 na `lo-infra-db-mariadb01`. Neproveden žádný DDL, DML, přepis produkce, změna WeeWX, aktivního sběru ani průběžného GW3000 synchronizéru. Technická konzistence je jiný pojem než fyzikální správnost měření.

**Reprodukovatelný bod paritní kontroly:** UTC `2026-11-22T20:20:00Z`, epoch `1795378800`. Zbylé agregace byly provedeny průběžně kolem tohoto času a živá produkce se mezi dotazy měnila. Přesné SQL je zde: [nový read-only kontrolní soubor](../sql/readonly/reconstruction_comprehensive_quality_20261122.sql), starší [80sloupcová parita](../sql/readonly/reconstruction_v1_all_80_columns_parity.sql).

## Executive decision

- **PASS:** technická parita hodnot s očekávaným historickým diffem; struktura a PK; úplné pokrytí historických produkčních timestampů k pevnému řezu; přítomnost auditních událostí; poslední průběžná synchronizace.
- **FAIL / BLOCK:** fyzikální certifikace historických odhadů; konzistence 146 rain auditů 2021; odvozené dewpoint po RH; mapování bleskových čítačů; přepočet denních tabulek; ověřená izolovaná záloha/restore.
- **GO:** pokračovat ve vývoji webu s `original_unverified` a jasným označením chybějících/nejistých dat.
- **NO-GO:** produkční cutover, tvrzení o ověřených klimatologických rekordech, masové odblokování historických změn, full-row import legacy archivů.

## A. Struktura, časové záznamy, hodnota a diff — PASS s výhradami

| Kontrola | Výsledek |
|---|---:|
| Zdroj `pocasi-loucka.eu.archive` do cutoff | **1 686 773** |
| Cíl `loucka_reconstruction.archive` do cutoff | **1 697 172** |
| Produkční timestamps chybějící v cíli do cutoff | **0** |
| Historické target-only timestampy | **10 399** |
| Target-only bez `reconstruction_changes` | **0** |
| Shodné timestampy, porovnané se všemi 80 sloupci | **1 686 773** |
| Počet nezměněných sloupců včetně primárního klíče | **76/80** |
| `outTemp` změněné hodnoty | **47** |
| `outHumidity` změněné hodnoty | **20 422** |
| `rain` změněné hodnoty | **2 201** |
| `rainRate` změněné hodnoty | **59 595** |
| Změněná pole + přidané celé řádky | **82 265 + 10 399 = 92 664** |

Všechny tři `SELECT` bloky `<=>` přes 79 neklíčových sloupců proběhly úspěšně s **identickým** počtem 1 686 773 překryvných řádků; 75 neklíčových sloupců má nulový rozdíl. `dateTime` má v obou tabulkách unikátní `PRIMARY KEY`, InnoDB. Výsledek shody přesně odpovídá poslednímu manifestu, **neznamená** ale nezávislé přijetí 92 664 operací. Z nich je nadále **92 366 QUARANTINE** a **298 ALREADY_APPLIED**. Ochrana Q1 2018 / roku 2021 je zachována.

## B. Pokrytí po letech a fyzické mezery — P1

| UTC rok | Záznamy | Přibližné pokrytí 5min slotů | Chybějící `outHumidity` uvnitř řádků |
|---|---:|---:|---:|
| 2009 (od 29. 3.) | 78 105 | 97,80 % | 3 |
| 2010 | 104 090 | 99,02 % | 63 |
| 2011 | 62 843 | **59,78 %** | 171 |
| 2012 | 75 346 | **71,48 %** | 420 |
| 2013 | 95 488 | 90,84 % | 5 636 |
| 2014 | 95 780 | 91,11 % | 1 658 |
| 2015 | 101 261 | 96,33 % | 3 658 |
| 2016 | 87 902 | 83,39 % | 12 810 |
| 2017 | 76 831 | **73,09 %** | 24 334 |
| 2018 | 97 704 | 92,95 % | **44 306** |
| 2019 | 104 751 | 99,65 % | 15 099 |
| 2020 | 103 047 | 97,76 % | 6 041 |
| 2021 | 103 464 | 98,42 % | 1 034 |
| 2022 | 104 207 | 99,13 % | **41 792** |
| 2023 | 104 624 | 99,53 % | 332 |
| 2024 | 104 935 | 99,55 % | 1 020 |
| 2025 | 102 946 | 97,93 % | 1 881 |

Procenta jsou přibližná, založená na počtu řádků proti teoretické pětiminutové mřížce. Pro rok 2026 ji **nelze** smysluplně získat pouhým `COUNT(*)`, viz níže.

Z `LAG(dateTime)` přímo v rekonstrukci: **44** přerušení >=24 hodin, **5** >=7 dní. Největší:
- **15. 8. 2011 20:05 UTC → 1. 3. 2012 09:25 UTC** (198,56 dne, 57 183 chybějících nominálních slotů);
- **18. 1. 2016 → 6. 2. 2016** (18,6 dne, 5 358 slotů);
- **12. 5. → 28. 5. 2017** (16,7 dne, 4 810 slotů);
- **20. 6. → 3. 7. 2014** (12,8 dne, 3 673 slotů);
- leden 2017 (7,9 dne, 2 261 slotů).

### Legacy zdroje uvnitř gapů: neplést záznam s měřením

- **2011–2012:** `old_weewx` má uvnitř hlavní mezery 3 560 řádků, ale **3 264 mají venkovní teplotu = 0 a RH = 0 současně** (podezřelé zástupné nuly); nezávislý průkaz chybí.
- **2016 leden–únor:** 5 344 starých řádků s proměnlivým tlakem a vnitřními senzory, ale **jen 1** s `outTemp` / `outHumidity`; všechny staré timestampy jsou mimo přesnou pětiminutovou mřížku.
- **2017 leden:** 2 261 legacy řádků; `pressure` a `inTemp` přítomny, venkovní T/RH chybí zcela.
- **2017 květen:** 4 810 legacy řádků; `pressure` a `inTemp` přítomny, venkovní T/RH chybí zcela.
- **2014 červen–červenec:** mezi hranicemi mezery žádný z šesti porovnávaných archivů nemá záznam.

**Možnost budoucí obnovy je selektivní po senzoru**, zejména `pressure/inTemp` v 2016–2017, až po jednotkovém a časovém ověření. `weewx_WH1080` a `old_weewx` mohou být kopie stejného zdroje, nikoliv dvě nezávislá měření. Nevytvářet syntetickou venkovní teplotu, RH ani srážky.

## C. Přesnost moderních timestampů — P1

- Archivní `dateTime % 300 != 0`: **390** řádků, všechny z roku 2026; všech 390 existuje pod stejným časem také v produkci.
- `interval != 5`: **2 097** řádků (zejména **2 090** šestiminutových 2014–2019, dále 30/55/10/40/75min); odpovídají původnímu archivu.
- K aktuálnímu kontrolnímu řezu 2026 je **43** kolizních nominálních pětiminutových slotů po zaokrouhlení na nejbližších 300 s, každá se dvěma řádky. Samotný celkový počet řádků může být >= očekávaný počet, a přesto jsou jiné nominální sloty nepokryté; kontrola ve stejném běhu ukázala 40 nepokrytých nominálních slotů.

Nepřepisovat datové časy automatickým `ROUND(dateTime/300)`: změnilo by to původní metadata a vytvořilo kolize. U grafik vyžadovat skutečné UTC epochy/intervaly.

## D. Auditní historie a důkazy obnov — P0 pro certifikaci

- `reconstruction_changes`: **95 252** událostí `applied`, **17 842** označených `reverted`, **0** událostí bez odpovídajícího řádku archivu. Události označené reverted nejsou nynější zápis hodnoty, nesmějí být nesprávně testovány proti `new_value`.
- U **146** `rain` timestampů v červenci 2021 poslední aplikovaný auditovaný návrh ukládá `NULL`, ale aktuální archiv obsahuje **0**. Jde o cílenou „dry-warm“ epizodu; dřívější jiná událost je označena jako reverted. Je nutné dohledat následný proces (případně už existující oddělený receipt), nikoliv z těchto 146 bez důkazu vyvozovat nesprávný fyzický úhrn.
- **Červenec 2021:** `SUM(rain)*10` produkce **701,015 mm** (8 921 řádků), pracovní rekonstrukce **42,567 mm** (8 928 řádků), bez `rain IS NULL` v tomto období. 42,567 mm je historicky chráněná kontrolní hodnota, **nikoliv** nezávisle potvrzené měření.
- **Q1 2018:** **10 080** historických target-only řádků s `insert: ESTIMATED`, nemohou automaticky určovat klimatické extrémy.
- **Celý archiv:** 10 101 historických vložení označeno `ESTIMATED`, 290 `RESTORED`, 1 `RECOVERED_SOURCE`, 7 dočasných bootstrapů později opravených na prostorové srážkové odhady. Nejméně **10 108** target-only timestampů obsahuje nějakou odhadnutou veličinu. První INSERT status se nesmí mechanicky vztáhnout na všech 80 sloupců.
- Čekající staging: **20 pending batches, 272 kandidátů**; z nich **264** pouze QC review bez náhradní číselné hodnoty, **7** číselných návrhů už dříve auditovaně aplikováno, **1** chybějící rain časový bod `1663246500` bez nezávislého důkazu. Neměnit.
- WH1080 staging 49 796 návrhů: **10 111** targetů nyní již obsazených, **39 685** stále chybí. Velká část má status `pressure_only_review` nebo `frozen_sensor_review`; nelze použít full-row INSERT.

## E. Odvozené hodnoty po rekonstrukci RH — P0 pro rekordy

Dubnový 2022 screen diagnostickou Magnusovou formulí `a=17.625, b=243.04`: z **2 194** porovnatelných RH korekcí má **1 077** uložený `dewpoint` odlišný od výpočtu podle *nové* RH o více než **2 °C**. Všech 1 077 naopak odpovídá výpočtu podle *staré* RH do **0,1 °C**. Max rozdíl od nového screeningu **13,5068 °C**.

Nelze automaticky aktualizovat `dewpoint`, `heatindex`, `appTemp`, `humidex`, VPD ani denní extrémy: autentická dobová výpočetní konfigurace není doložena. Screening je diagnostický, nikoli původní algoritmus.

## F. Blesková data GW3000 — P0 oprava mapperu, issue #17

**Kritický nález:** `lightning_disturber_count` má **54 031** hodnot v rozsahu unixových epoch (~1,77–1,79 miliardy) v květnu–listopadu 2026. Všech 54 031 je shodných s produkční databází. To **není počitadlo rušení**; silně to naznačuje chybné namapování timestampu posledního blesku do počitadla. Původní raw payload/mapper musí potvrdit správný klíč.

Dále pouze **179** záznamů má `lightning_noise_count`; v **179/179** je přesně totožné s `lightning_strike_count`. Ani tento sloupec nelze považovat za nezávisle ověřený noise counter. `lightning_energy` neobsahuje nikdy hodnotu.

**Okamžitá publikační zásada:** do opravy mapperu `lightning_disturber_count` a `lightning_noise_count` na webu nezobrazovat jako potvrzený počet událostí. Zdrojová chyba je přítomna i v produkci; automatickými historickými UPDATE nezachraňovat bez původního payloadu.

## G. Meteo-fyzikální screening ostatních senzorů — omezený PASS

- Žádné teploty mimo -50 až +60 °C, RH mimo 0–100 %, záporné srážky/rychlosti, negativní PM2.5 nebo hodnoty `pressure/barometer` mimo 800–1100 hPa.
- **4** `rainRate>10 cm/h` (2013 ×2, 2023 ×2), maximum **18 cm/h**; jsou doložené v GW1000, nikoliv nezávisle fyzikálně certifikované. Není to automatický důkaz chyby, ale vyžaduje kontrolu RainRater, okolních intervalů a dalších zdrojů.
- **3** `radiation>1500 W/m²` (jeden v 2024 a dva v 2026), maximum **2 248,85 W/m²**, v produkci rovněž. Podezření na chybu měření/mapování.
- V roce 2020 při 103 target `outTemp=NULL` v kopii `pocasi-loucka.eu_old` jen dvě numerické hodnoty **0 a 4,25 °C**, zatímco 102 odpovídajících WH záznamů má 96 různých hodnot; dvě starší kopie WH se shodují, nejsou nezávislým důkazem.
- Z 77 hodnotových/senzorových sloupců (mimo `dateTime/usUnits/interval`) nemá **žádnou** archivní hodnotu `extraHumid1`, `extraHumid2`, `lightning_energy`. Z toho bez instalace epoch nelze vyvozovat `NOT_INSTALLED`.
- Počty měření `lightning_noise_count=179`, `lightning_distance=1569`, `bgt=1551` ukazují vysokou neúplnost těchto speciálních kanálů.

## H. Denní agregace, API a web — P0 před schválením klimatologie

Produkční DB obsahuje **79** `archive_day_*` tabulek; `loucka_reconstruction` jich obsahuje **0**. Denní minima, maxima, dešťové úhrny a klimatické rekordy nejsou tedy z rekonstruovaných řádků přepočtené a opatřené per-field QC. Nelze přepnout web na `approved_reconstruction` a tvrdit certifikované historické rekordy.

Vývojové zobrazení nad `original_unverified` je bezpečně oddělitelné. Pro budoucí rekonstruované statistiky musí být každá veličina/záznam `MEASURED/CORRECTED/ESTIMATED/MISSING/SENSOR_ERROR/UNVERIFIED`, s původním senzorem/časovou epochou a pravidly pro lokální CET/CEST den. Odhady nesmějí být bez další revize automaticky zahrnuté do extrémů.

## I. Synchronizace, kontrolní součty, infra a backup — PASS/P1

- `archive_sync_audit` **6 971** přenesených řádků, `archive_sync_verification` **732** dávek a `SUM(row_count)=6 971`. **0** dávek bez auditovaných řádků, **0** nesouladů počtu a **0** chybějících zdrojových/target časových značek v auditovaných řádcích.
- **684/732** batchů má shodné `source_payload_sha256` a `verified_target_postimage_sha256`. **48** nejstarších dávkových hash párů z **15. 11. 2026** se liší (4 651 auditovaných řádků). V aktuální databázi na těchto 4 651 řádcích není rozdíl ve čtyřech polích, která jinak tvoří celý schválený historický diff. Příčinu rozdílu hashů je třeba potvrdit z původní kanonikalizace/receiptů; **není doložena fyzická ztráta měření**. `archive_sync_audit.verified_target_postimage_sha256` je NULL na úrovni jednotlivých řádků, postimage hash je správně přítomný na úrovni verifikované dávky; neporovnávat per-row NULL proti source hash.
- `archive_sync_cursor` pravidelně postupuje; poslední kontrolovaný watermark `1795378800`, ověřený 22. 11. 2026 20:22 UTC.
- Produkce a rekonstrukce leží na **stejném serveru** `lo-infra-db-mariadb01`, MariaDB 11.8.6, `@@read_only=0`. Nejde o izolovanou cílovou instanci pro destruktivní migrační zkoušku.
- V `loucka_reconstruction` jsou **4 dílčí srážkové backup tabulky**, ale žádná prokázaná konzistentní fyzická záloha **celé** DB ani úspěšný restore test na oddělené instanci. Žádný takový test nebyl tímto auditem proveden.
- `reference_stations=2`, `reference_observations=1 652 638` a `reference_daily=32` jsou podpůrné zdroje; nejsou automaticky původními naměřenými hodnotami Loučky.

## J. Uzavírací plán podle priority

| Priorita | Předmět | Akceptační důkaz |
|---|---|---|
| **P0** | Mapa kvality po veličině; zejména 10 108 odhadovaných timestampů a 2018 Q1 | Per-field původ/senzor, read-only API, odstranění odhadů z certifikovaných extrémů |
| **P0** | GW3000 bleskový mapper a duplicated noise/strike | Původní payload → field mapping → regresní test → bezpečná oprava jen pro ověřené hodnoty |
| **P0** | 146 červencových 2021 srážek `NULL` v auditu vs `0` v archivu | Nezpochybnitelný navazující audit/rollback receipt, nikoli slepý UPDATE |
| **P0** | Dewpoint po RH duben 2022 a další odvozeniny | Verifikovaná dobová formule/zdroj; oddělený manifest s rollbackem |
| **P0** | Denní souhrny a klimatologie | Vývojový rebuild 79 denních agregací s QC, CET/CEST a kontrolou rekordů |
| **P0** | Backup / izolace / migrační pipeline | Konzistentní backup SHA, izolovaný restore test, transakční CAS a rollback test, approval dávky |
| **P1** | Velké mezery 2011–2017 | Časový a jednotkový ledger, per-field kandidáti pressure/inTemp, nulové placeholdery nevydávat za měření |
| **P1** | 390 off-grid a 43 kolizí slotů v roce 2026 | Původní timer/WeeWX timestamp a mapování intervalů, bez hromadného rounding |
| **P1** | 48 historických batch hash odchylek | Přezkoumání kanonických payloadů a obnovení receipts, bez změny měření |
| **P1** | Solar 3 výstřelky, rainRate 4 prudké špičky | Původní raw/senzorové a externí intervalové důkazy |
| **P2** | Přechod Cumulus → WeeWX, 2013 jednotky, 2014 pipeline | Zúžené zdokumentované epochy; nejistý den označit `UNVERIFIED`, nedoplňovat z odhadu |

**Závěr:** `loucka_reconstruction` je **technicky konzistentní s historickým manifestem**, ale **není fyzikálně ani publikačně certifikovaná**. V tomto běhu nebyly provedeny historické zápisy do žádné DB, nebyla prokázána úplná záloha ani její obnova. Teprve po uzavření P0 lze rozhodnout o publikaci schválené rekonstrukce; kód webu lze mezitím vyvíjet nad poctivě označenými původními daty.
