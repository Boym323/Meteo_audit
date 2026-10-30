# Červenec 2021 — nezávislý read-only preflight rekonstrukce ČHMÚ IDW2

**Datum:** 2026-10-30  
**Zdroj ověření:** přímé SELECT přes Weather MCP, pracovní DB `loucka_reconstruction`; dokumentace ČHMÚ a stav `main` v repozitáři.  
**Výsledek:** **NOT VALIDATED — DO NOT REAPPLY**. Neprováděl se žádný zápis do MariaDB.

## 1. Rozsah a bezpečnost

- Šest dostupných schémat: `old_weewx`, `weewx_WH1080`, `pocasi-loucka.eu_old`, `pocasi-loucka.eu_GW1000`, `pocasi-loucka.eu` a `loucka_reconstruction`.
- Všech pět originálních DB zůstalo beze změn; tento běh použil výhradně čtení pracovní DB.
- Rozhodující tabulky: `archive`, `rain_reconstruction_202107_chmi_v1`, `rain_archive_original_202107`, `rain_backup_202107_before_chmi_v1`, `rain_qc_daily_202107`, `reconstruction_changes`, `reference_stations`, `reference_observations`.
- Samotný stav účtu, databázové granty a `MCP_READ_ONLY` nebyly kontrolou SELECT prokázány. Bez dalšího ověření nezapisovat.

## 2. Přímá zjištění

| Metrika | Ověřená hodnota |
|---|---:|
| Původní srážky (záloha `rain_archive_original_202107`) | 701,0146 mm; 8 921 pozic |
| Návrhová tabulka `rain_reconstruction_202107_chmi_v1` | 42,567266 mm; 8 928 pozic |
| Pracovní archiv proti návrhu, přesný `dateTime` JOIN | 8 921 shodných hodnot `rain` i `rainRate`; 0 odchylek nad 1e-6 |
| Interpolace ze 3 stanic (`chmi10m_idw2`) | 8 765 pozic, 40,434660 mm |
| Interpolace ze 2 stanic (`chmi10m_idw2`) | 140 pozic, 2,132606 mm |
| Uměle uložené nuly bez červnového CSV (`initial_archive_zero_no_june_csv`) | 23 pozic, 0 mm |
| Nenulové rekonstruované pětiminutové pozice | 396 |
| Výsledek v `archive` odlišný od předrekonstrukční originální zálohy | 1 568 `rain`, 3 027 `rainRate` |
| Datum vytvoření návrhové tabulky | 2026-10-30 08:42:46 (DB timestamp; časovou zónu sloupce neověřovat z řetězce) |

### 2.1 Modelový rainRate není naměřená intenzita

Pro **všech 396 nenulových** pozic platí při decimal zaokrouhlení `rainRate_cm_h = rain_cm * 12`, maximální rozdíl 0,00000006 cm/h. Všechny sousední dvojice `(dateTime % 600 = 300, dateTime+300)` mají stejný `rain_cm`: 4 463/4 463 párů, včetně 198/198 deštivých párů.

To dokládá rovnoměrné rozdělení desetiminutového odhadu mezi dvě pětiminutové pozice a přepočet na **pětiminutový průměr v cm/h**. Není to důkaz okamžitého `rainRate` senzoru/driveru WeeWX. Jako takový se odhad **nesmí prezentovat ani bez explicitní provenance ukládat do standardního `rainRate`**. Před opravou je třeba definovat samostatnou odvozenou veličinu / QC flag.

### 2.2 Sedm chybějících řádků

V `rain_reconstruction_202107_chmi_v1` existují a v `archive` neexistují tyto lokální časy (DB session `FROM_UNIXTIME` odpovídá Europe/Prague):

- 2021-07-03 15:30:00 (UTC epoch 1625319000)
- 2021-07-03 16:55:00 (1625324100)
- 2021-07-03 17:00:00 (1625324400)
- 2021-07-03 17:05:00 (1625324700)
- 2021-07-03 17:10:00 (1625325000)
- 2021-07-03 17:15:00 (1625325300)
- 2021-07-03 17:20:00 (1625325600)

Odhad pro všech sedm je nula, nikoli skutečné měření. Nezakládat automaticky úplné archivní řádky jen podle interpolované srážky.

### 2.3 Měsíční hranice posunuté oproti intervalu WeeWX

Rekonstrukce má `dateTime` 1625090400 až 1627768500, tj. místně 1. 7. 00:00 až 31. 7. 23:55 — časové body **[start, end)**.

WeeWX však interpretuje `dateTime` jako konec intervalu `(dateTime-interval*60, dateTime]`. Občanský červenec 2021 se má agregovat **(start, end]**, tedy `dateTime > 1625090400 AND dateTime <= 1627768800`. Návrh zahrnuje koncový bod června a chybí mu koncový bod července. Oba tyto body mají v pracovním archivu nulu; při aktuálním součtu nejde o numerický rozdíl, ale jde o metodický nesoulad.

Časy bez červnového CSV 1. 7. 00:00–01:50 (23 pozic) jsou dosazeny jako 0 mm bez potvrzeného srážkového zdroje. Správný stav je nejméně `UNVERIFIED`, ne automaticky změřená nula.

### 2.4 Incident 22.–26. července

| Den | Originální Loučka (mm) | Model ČHMÚ-IDW2 (mm) |
|---|---:|---:|
| 22. 7. | 53,645 | 0 |
| 23. 7. | 92,202 | 0 |
| 24. 7. | 56,718 | 0 |
| 25. 7. | 107,010 | 10,886 |
| 26. 7. | 54,204 | 0,757 |

Poznámka: Oba sloupce jsou pro lokální kalendářní body, nikoli automaticky meteorologický den ČHMÚ. Rozpor silně motivuje prověřit poruchy původního čítače, ale **prostorový odhad s nulou nedokazuje nulovou srážku přímo v Loučce**.

## 3. Nedostatek vstupní provenience

- V pracovní DB jsou v `reference_stations` pouze `luhamet_sehradice` a `wu_ilouka4`. Nebyl nalezen záznam tří konkrétních ČHMÚ stanic použitých při IDW2.
- `rain_reconstruction_202107_chmi_v1` obsahuje jen `dateTime`, `rain_cm`, `rainRate_cm_h`, `station_count`, `method`, `created_at`. **Chybí** ID/WSI, souřadnice, vzdálenost, váhy, zdrojové úhrny 10m, kvalita vstupů, hash a verze kódu.
- Oficiální ČHMÚ CSV pro červenec 2021 jsou zveřejněny jako `10m-{WSI}-SRA10M-202107.csv` v https://opendata.chmi.cz/meteorology/climate/historical_csv/data/10min/precipitation/2021/ . Metadata ČHMÚ vymezují `SRA10M` jako **10min úhrn v mm**, dostupný od roku 2018, nikoli okamžitou intenzitu: https://geoportal.gov.cz/php/micka/record/basic/6a58c5b6-5d38-414a-8496-153c63c0a8017c .
- Oficiální PDF: https://opendata.chmi.cz/meteorology/climate/Klimatologicka_data_popis.pdf . Potvrzuje WSI a CSV strukturu i oddělení historických dat. Pro reprodukci je třeba ověřit přímo u originálních CSV sloupce `DT`, `TIMEFUNC`, `FLAG`, jednotky, časové kotvení desetiminutovky a dostupnost hranice června.
- Během tohoto běhu nebylo možné CSV stáhnout z prostředí klienta a nesmí se z toho tvrdit, že byla provedena numerická reprodukce IDW2.
- V `reference_observations` je pro LuhaMet za červenec 2021 8 928 řádků, ale **0 vyplněných srážkových intervalů a 0 intenzit**. Teplota/RH mohou podpořit QC, ne rekonstruovat lokální úhrn. U LuhaMet jsou 25.–26. 7. podezřelé nulové RH/teploty. Stanice ILOUKA4 nemá naimportovaný červenec 2021.
- `reference_daily` neobsahuje pro červenec 2021 žádný referenční den srážek.

## 4. Auditní historie není synchronizovaná

- `reconstruction_changes` má stále `rain-jul2021-dryday-22-24-v1` jako `applied` (146 `rain` a 243 `rainRate`) a `rain-jul2021-quarantine-v1` jako `reverted`.
- Výsledky vyhledávání dle `chmi` v `batch_key/source_database/reason` jsou pouze stará vrácená měsíční karanténa (2 × 8 921); **nenalezen odpovídající samostatný change batch pro čerstvou IDW2 změnu**.
- `rain_qc_daily_202107` odpovídá staršímu screeningu (28 `not_verified`, 3 `partial_archive_missing`), ne aktuálnímu modelovému archivu.
- **Needitovat historickou hodnotu `applied` tak, že by se ztratil fakt minulého zásahu.** Doplnit oddělenou provenance událost nebo supersession vazbu, aktuální QC verzi a kontrolní převod s immutable originální zálohou.
- Otevřené PR #28 se zabývá fail-closed preflight ochranným mechanismem; nekonkurovat mu novou hromadnou aplikací.

## 5. Reprodukovatelné read-only kontroly

```sql
-- Rekonstrukce a modelová sémantika rainRate:
SELECT method, station_count, COUNT(*) n,
       ROUND(SUM(rain_cm)*10,6) rain_mm,
       SUM(rain_cm>0) positive_intervals
FROM loucka_reconstruction.rain_reconstruction_202107_chmi_v1
GROUP BY method, station_count;

SELECT COUNT(*) n, SUM(rain_cm>0) wet,
       SUM(rain_cm>0 AND ABS(rainRate_cm_h-12*rain_cm)>0.0000002) inconsistent_rate
FROM loucka_reconstruction.rain_reconstruction_202107_chmi_v1;

-- Počet chybějících časových pozic:
SELECT r.dateTime, r.rain_cm, r.rainRate_cm_h
FROM loucka_reconstruction.rain_reconstruction_202107_chmi_v1 r
LEFT JOIN loucka_reconstruction.archive a USING(dateTime)
WHERE a.dateTime IS NULL ORDER BY r.dateTime;

-- Historie změn v lokálním měsíci WeeWX používá (start,end]:
SELECT batch_key,variable,state,COUNT(*) n
FROM loucka_reconstruction.reconstruction_changes
WHERE target_time>1625090400 AND target_time<=1627768800
GROUP BY batch_key,variable,state ORDER BY batch_key;
```

## 6. Doporučené další kroky (bez aplikace)

1. Dohledat a uložit 2–3 přesné stanice ČHMÚ použité v IDW2 včetně WSI, souřadnic, URL a SHA256 originálních červnových a červencových CSV. Použít rovněž hodinové a denní ČHMÚ nezávisle pro QC.
2. Napsat reprodukovatelný test, který nezávisle z CSV přepočte IDW2 (polohy, vzdálenosti, nedostupnost/FLAG, jednotky, 10m časové hranice, 5m split), porovná 8 928 řádků a explicitně vypíše rozdíly.
3. Opravit mřížku podle WeeWX konce intervalu `(start,end]` a vyřešit 23 úvodních nepodložených nul bez záměny nuly s NULL/neznámou.
4. Oddělit modelovou 5min průměrnou intenzitu od historického `rainRate`. Náhradní hodnoty označit kvalitou, nikoli prezentovat jako naměřené.
5. Vytvořit append-only provenance/supersession evidence se starým snapshotem, novou metodou, přílohami a přesnou validací. Nesahat do pěti originálních DB a neaplikovat staré dávky podruhé.
6. Ověřit jednotlivé dny 22.–26. 7. na ČHMÚ a případném radarovém produktu MERGE. Až potom klasifikovat lokální hodnoty jako doložené / plausibilní / nevyřešené.

**Verdikt:** Součet 42,567266 mm je v pracovní DB vypočtený a vkládaný modelový výsledek. Není dosud nezávisle reprodukovaný z originálních zdrojových CSV a nelze ho vydávat za ověřenou skutečnou srážku v Loučce. Další hromadný SQL UPDATE není bezpečně odůvodněný.


## 7. Dodatek po zpřístupnění atomického zápisu Weather MCP (2026-10-30)

Původní audit výše zůstává zachován jako časově označený read-only stav. Následná kontrola úplného seznamu funkcí Weather MCP odhalila samostatnou `reconstruction_apply_corrections`: zapisuje atomicky pouze do pracovního `archive` databáze `loucka_reconstruction`, vyžaduje optimistickou kontrolu původní hodnoty a zaznamenává každé pole do `reconstruction_changes`. Zápis byl autorizován uživatelem.

### Provedená oprava `rainRate`

Přímé porovnání předrekonstrukční zálohy `rain_backup_202107_before_chmi_v1` s archivem potvrdilo:

- záloha pokrývá 8 921 červencových pozic a byla pořízena 2026-10-30 08:42:46;
- všech 8 921 archivních párů `(rain, rainRate)` před opravou přesně odpovídalo návrhové tabulce ČHMÚ;
- `rainRate` se lišil od předrekonstrukční zálohy u 2 784 pozic; u zbylých 6 137 se již rovnal;
- všechny opravy prošly nejprve dry-runem, poté byly zapsány v 56 dávkách (55 × 50 a 1 × 34) s `expected_old_value` kontrolou. Každá dávka skončila stavem `applied`; kontrolní SELECT po zápisu zjistil 0 rozdílů vůči záloze na všech 8 921 pozicích a 0 NULL `rainRate`;
- `rain` se tímto zásahem neměnil. Jeho měsíční součet v archivu proto zůstává 42,5672658 mm, stále však jde o nereprodukovaný prostorový model, nikoli ověřený místní úhrn.

Název auditní dávky má prefix `jul2021-rate-restore-prechmi-v1-`. Změna pouze vrací hodnoty `rainRate` ze zálohy po tom, co byl do standardního pole zapsán modelový přepočet; nevydává hodnoty z této zálohy za nově nezávisle ověřené. Historické záznamy `reconstruction_changes` nebyly přepsány.

### Kontrola srážkového archivu po zápisu

```sql
SELECT COUNT(*) n,
       SUM(a.rainRate <> b.rainRate_before_cm_h) rate_differences,
       SUM(a.rain <> b.rain_before_cm) rain_differences
FROM loucka_reconstruction.archive a
JOIN loucka_reconstruction.rain_backup_202107_before_chmi_v1 b USING(dateTime)
WHERE a.dateTime >= 1625090400 AND a.dateTime < 1627768800;
-- n=8921, rate_differences=0, rain_differences=1422

SELECT COUNT(*) n, SUM(rain*10) monthly_model_mm
FROM loucka_reconstruction.archive
WHERE dateTime >= 1625090400 AND dateTime < 1627768800;
-- n=8921, monthly_model_mm=42.5672658

SELECT r.dateTime, r.rain_cm
FROM loucka_reconstruction.rain_reconstruction_202107_chmi_v1 r
LEFT JOIN loucka_reconstruction.archive a USING(dateTime)
WHERE a.dateTime IS NULL ORDER BY r.dateTime;
-- 7 chybějících záznamů; všechny modelové hodnoty jsou nula
```

Denní součty je nutné při WeeWX konvenci přiřadit podle konce intervalu: pro interval 5 minut seskupit podle `DATE(FROM_UNIXTIME(dateTime - interval*60))`, při měsíčním výběru použít `dateTime > start AND dateTime <= end`. Dne 3. 7. zůstává 281 z očekávaných 288 záznamů; sedm chybějících časů nebylo domyšleno ani vloženo jako nuly.

### Co zůstává neověřeno

Nebyly nalezeny identifikátory WSI, vzdálenosti, váhy ani originální vstupní CSV tří stanic pro IDW2. Sedm časových mezer, 23 počátečních nul a denní měření 22.–26. 7. stále vyžadují nezávislé zdroje a provenienci. Proto není vědecky obhajitelný jeden „finální“ lokální měsíční úhrn ani číselná nejistota. Pět původních databází nebylo tímto zápisem dotčeno.

## 8. Dodatečná nezávislá kontrola a aktuální stav archivu (2026-10-30)

Tato sekce je novější než výše uvedený snapshot. Přepočty jsou řazeny podle místního dne intervalu WeeWX: řádek s koncovým `dateTime` se započítá do dne podle `DATE(FROM_UNIXTIME(dateTime-interval*60))`. Tím se opravuje dřívější posun denních součtů podle samotného koncového timestampu.

### ČHMÚ 10min srážkoměry, 22.–26. 7.

Přímo jsem načetl oficiální historické soubory ČHMÚ `10m-0-203-0-{WSI}-202107.json` pro WSI 11775, 11777 a 11778. Záznamy jsou v UTC; pro místní datum byl použit posun CEST +02:00. Každý den a stanice má 144 záznamů SRA10M, prázdný FLAG a QUALITY=0. U WSI 11777 jsem navíc porovnal všech 744 hodinových SRA1H hodnot s odpovídajícími šesti SRA10M záznamy označenými H, H+10, …, H+50 minut: součet souhlasil přesně ve všech hodinách. To nezávisle potvrzuje přiřazení úhrnu k datovému času SRA10M; místní denní součet proto seskupuje `DT` po převodu UTC→Europe/Prague (bez odečítání 10 minut).

| Místní den | WSI 11775 (mm) | WSI 11777 (mm) | WSI 11778 (mm) | Model v archive (mm) | Původní archive snapshot (mm) |
|---|---:|---:|---:|---:|---:|
| 22. 7. | 0,0 | 0,0 | 0,0 | 0,000 | 54,762 |
| 23. 7. | 0,0 | 0,0 | 0,0 | 0,000 | 91,084 |
| 24. 7. | 0,0 | 0,0 | 0,0 | 0,000 | 56,718 |
| 25. 7. | 14,5 | 8,8 | 14,4 | 11,273 | 107,848 |
| 26. 7. | 0,3 | 1,1 | 1,6 | 0,370 | 53,365 |

Odkazy na zdrojové soubory: [WSI 11775](https://opendata.chmi.cz/meteorology/climate/historical/data/10min/2021/10m-0-203-0-11775-202107.json), [WSI 11777](https://opendata.chmi.cz/meteorology/climate/historical/data/10min/2021/10m-0-203-0-11777-202107.json), [WSI 11778](https://opendata.chmi.cz/meteorology/climate/historical/data/10min/2021/10m-0-203-0-11778-202107.json).

Tři nezávislé srážkoměry tedy silně podporují regionálně suchý charakter 22.–24. 7.; samy však neprokazují místní nulu v Loučce. Dne 25. a 26. 7. mají všechny tři stanice nenulovou srážku a IDW2 součty leží v jejich rozsahu. To podporuje denní meteorologickou věrohodnost modelu, ale **nereprodukuje** jeho konkrétní váhy ani desetiminutové rozdělení.

### Aktuální pracovní archive

Přímý SELECT přes Weather MCP po následných zápisech potvrdil pro WeeWX interval `dateTime > 1625090400 AND dateTime <= 1627768800`:

- 8 928 řádků (288 za každý den), 22 hodnot `rain IS NULL`, 250 hodnot `rainRate IS NULL` a známý součet `SUM(rain)*10 = 42,5672658 mm`.
- Dvacet dva neznámých úhrnů je 1. 7. 00:05–01:50. V záloze před rekonstrukcí mají tyto řádky samostatně zaznamenané `rainRate=0`; dávka `jul2021-start-rainrate-backup-restore-v1` obnovila všech 22 hodnot a append-only `reconstruction_changes` obsahuje 22 událostí. Po zápisu proběhl přímý SELECT: všech 22 se shoduje se zálohou, zatímco `rain` zůstává NULL.
- Sedm časů 3. 7. (15:30 a 16:55–17:20) bylo od posledního reportu vloženo do archivu s `usUnits=16`, `interval=5`, odhadovaným `rain=0` a `rainRate=NULL`. Okolní SRA10M je suchá na všech třech stanicích. Jsou to řídké řádky: jiné veličiny zůstávají NULL a nuly představují prostorový odhad, nikoli lokální měření. Auditní historie zachovává původní vložení, přechod přes NULL i následný odhad nuly.
- Číselné denní hodnoty známé části archive jsou: 1.7. 0,504; 2.7. 0; 3.7. 0,047; 4.7. 0,008; 5.–7.7. 0; 8.7. 1,573; 9.7. 1,666; 10.7. 0; 11.7. 3,207; 12.7. 6,600; 13.7. 0; 14.7. 9,773; 15.–16.7. 0; 17.7. 0,154; 18.–19.7. 0; 20.7. 2,886; 21.7. 0,008; 22.–24.7. 0; 25.7. 11,273; 26.7. 0,370; 27.7. 1,354; 28.7. 2,878; 29.7. 0,222; 30.7. 0; 31.7. 0,044 mm. Součet je známá/modelová část, ne potvrzený lokální měsíční úhrn.
- Z původních 23 nul bez zdroje připadá jedna na hraniční bod 1.7. 00:00, který je mimo interval WeeWX (start,end]; 22 časů uvnitř července zůstává v archive NULL. SRA10M z přelomu měsíce ukazuje nuly na 11775 a 11777 a nulu na 11778 až do 23:10 UTC, 0,1 mm na 11778 v 23:20 UTC a pak opět nuly. Desetiminutový prostorový údaj nestačí k doložení místních pětiminutových úhrnů.
- `rain_qc_202107` má 8 921 řádků a všechna pole `validated_rain_mm` jsou NULL; aktuální archive má 8 928 řádků. `rain_qc_daily_202107` je zastaralá (např. eviduje 281 místo současných 288 řádků 3.7.). Dostupný Weather MCP writer dovoluje měnit jen `loucka_reconstruction.archive`, ne QC tabulky; jejich aktualizace proto dosud nebyla provedena.
- V stagingu zůstávají dvě červencové dávky pending: 3 kandidáty pro manuální přezkum a 71 podezřelých impulzů. Žádný z těchto kandidátů nebyl touto kontrolou automaticky aplikován ani zrušen.

### Aktuální závěr

Číslo 42,5672658 mm je potvrzeno jako známý součet hodnot uložených v pracovním archivu a je meteorologicky věrohodnější než původní čítač pro dny 22.–26. 7. Není to úplný ani nezávisle reprodukovaný lokální součet: 22 úhrnů zůstává NULL, IDW2 zdrojová provenience a váhy chybí, QC souhrny jsou zastaralé a kandidátní dávky nejsou uzavřené. Číselnou horní mez nejistoty nelze z dostupných dat určit.


## 9. Následné opravy a ruční triage (2026-10-30)

Tato sekce zachycuje stav po zápisech provedených autorizovanou funkcí Weather MCP `reconstruction_apply_corrections`. Starší části reportu popisují předchozí okamžiky a nejsou přepisovány.

### 71 podezřelých impulsů převedeno na neznámé hodnoty

Na osmi dnech, kdy tři stanice ČHMÚ 11775/11777/11778 uvádějí denní nulu a lokální LuhaMet RH nevykazuje vlhkou epizodu, se 71 hodnot `rain=0` v archivu změnilo na `rain=NULL`. Hodnoty se nepřepsaly nulou ani interpolovaným odhadem: jde o označení nejistého měření. Zápis proběhl ve dvou dávkách (50 a 21 změn), s kontrolou očekávané původní nuly a ověřením po zápisu. Dávka původních návrhů byla následně označena jako cancelled; kandidátní historie zůstává zachována a skutečné změny jsou auditovány v `reconstruction_changes`.

Dny s nově neznámými intervaly: 7. 7. (11), 13. 7. (15), 16. 7. (3), 19. 7. (9), 22. 7. (8), 23. 7. (6), 24. 7. (7) a 30. 7. (12). Po těchto opravách má archiv za WeeWX interval `dateTime > 1625090400 AND dateTime <= 1627768800` stále 8 928 řádků, 93 `rain IS NULL` (22 původních časných neznámých a 71 nově karantenizovaných), 8 439 nul a 396 nenulových hodnot. Známý součet zůstává 42,5672658 mm, protože 71 nul bylo nahrazeno NULL, nikoli odečteno jako naměřená srážka. Jde o součet známých hodnot / odhadů v archivu, ne úplný lokální úhrn. `rainRate` zůstává NULL u 250 řádků.

### Ruční posouzení tří odlišných starých záznamů

Porovnání těchto časů v `pocasi-loucka.eu_old`, `pocasi-loucka.eu_GW1000`, předrekonstrukčním snapshotu a archivu ukazuje:

| Čas v Loučce | Starší databáze (`rain`) | GW1000 | Původní pracovní snapshot | Rozhodnutí |
|---|---:|---:|---:|---|
| 4. 7. 02:45 | 1,6764 mm | 0 | 0 | neobnovovat starý impuls; archive ponechán 0 |
| 6. 7. 14:30 | 1,6764 mm | 0 | 0 | neobnovovat starý impuls; archive ponechán 0 |
| 18. 7. 14:15 | 5,5880 mm | 0 | 0 | neobnovovat starý impuls; archive ponechán 0 |

V okolí těchto časů obsahuje starší databáze řadu dalších nenulových nebo kolísajících hodnot, které GW1000 v odpovídajících časech nepotvrzuje. U 6. 7. byla současně nízká vlhkost (přibližně 44–46 % RH, teplota kolem 28 °C). Hodinové/denní srážky ČHMÚ pro tyto tři dny ani radarový záznam pro přesné intervaly zde nebyly ověřeny, takže rozhodnutí je konzervativní zdrojové posouzení, nikoli nezávislý meteorologický důkaz nuly. Návrhový kandidátní balík se třemi případy byl po přezkumu označen jako cancelled; archive hodnoty se tímto krokem nezměnily.

### Denní součty známých hodnot po karanténě

Úhrny v mm podle dne WeeWX intervalu jsou: 1.7. 0,504; 2.7. 0; 3.7. 0,047; 4.7. 0,008; 5.7. 0; 6.7. 0; 7.7. 0 (11 neznámých intervalů); 8.7. 1,573; 9.7. 1,666; 10.7. 0; 11.7. 3,207; 12.7. 6,600; 13.7. 0 (15 neznámých); 14.7. 9,773; 15.7. 0; 16.7. 0 (3 neznámé); 17.7. 0,154; 18.7. 0; 19.7. 0 (9 neznámých); 20.7. 2,886; 21.7. 0,008; 22.7. 0 (8 neznámých); 23.7. 0 (6 neznámých); 24.7. 0 (7 neznámých); 25.7. 11,273; 26.7. 0,370; 27.7. 1,354; 28.7. 2,878; 29.7. 0,222; 30.7. 0 (12 neznámých); 31.7. 0,044. Číslo nula u dnů s NULL vyjadřuje pouze součet známé části, nikoli prokázanou suchost celého dne.

### Aktuální omezení

- `rain_qc_202107` a `rain_qc_daily_202107` se dostupnou zapisovací funkcí upravit nedají; nadále vyžadují synchronizaci. Neprovedl se pokus o obejití rozhraní.
- Model IDW2 stále nemá dohledané přesné WSI, souřadnice, vzdálenosti/váhy a uložené vstupní CSV/hashy, takže jeho celý výpočet nelze nezávisle reprodukovat.
- 93 intervalů `rain=NULL` zůstává nevyřešeno z hlediska skutečného místního úhrnu. Nelze z nich odvodit spolehlivou konečnou nejistotu měsíčního úhrnu. 7 chybějících původních časových bodů z 3. 7. zůstává v archivu jako řídké řádky s nulovým odhadem a `rainRate=NULL`, nikoli jako potvrzené měření.
- Počet opravených archivních záznamů v této etapě: 71 změn `rain` z 0 na NULL. Tři posuzované staré impulsy nebyly obnoveny a archive se pro ně nezměnil.
- Pět původních databází zůstalo pouze čteno; zápisy šly výhradně do `loucka_reconstruction.archive`.

**Stav:** archiv je dílčím způsobem opraven a kandidáti pro červenec byly vyhodnoceny, ale měsíc nelze vědecky označit za plně rekonstruovaný ani uzavřít jako definitivní místní srážkový úhrn.


## 10. Oprava po zpětném ověření původních lokálních archivů (2026-10-30)

Tato novější část **nahrazuje závěry sekcí 8–9 tam, kde se týkají původních 22 časných NULL a 71 karantenizovaných hodnot**. Předchozí kroky založené na regionálně suchém ČHMÚ a vlhkosti podcenily přímý důkaz z lokálního archivu.

### Obnovené lokální hodnoty

- U všech **71** intervalů karantenizovaných v dávkách `jul2021-quarantine-suspected-rain-impulses-v1-a/b` byly původní hodnoty `rain` v databázích `pocasi-loucka.eu`, `pocasi-loucka.eu_GW1000` a `pocasi-loucka.eu_old` shodné a nenulové: 71/71 bez jediné neshody. Zápisový archiv je nyní vrací z lokálního zdroje; hodnota odpovídá i uloženému `source_value` v historické karanténní události. To je důkaz lokálního měření, který má přednost před nepřítomností srážek na vzdálenějších ČHMÚ stanicích a nízkou RH.
- U **22** časných hodnot 1. 7. 00:05–01:50 se produkční, GW1000 i starší lokální archive a záloha `rain_backup_202107_before_chmi_v1` shodují na `rain=0` i `rainRate=0` (22/22). Obnoveny proto byly zdrojové nuly; důvod „bez červnového CSV“ se pro tyto místní archivní řádky nepoužije.
- Nejprve proběhl dry-run; pak atomický zápis přes Weather MCP s `expected_old_value=NULL`. Dávky `jul2021-restore-local-source-rain-v1-a` (50), `...-b` (21) a `jul2021-restore-local-start-zero-v1` (22) všechny skončily `applied`; writer ověřil 50/50, 21/21 a 22/22 hodnot. Následný read-only join potvrdil shodu všech 93 obnovených řádků s produkčním, GW1000 a starším archive, bez neshody. Historické karanténní události zůstávají zachovány.

### Aktuální kontrola pracovního archivu

Pro WeeWX měsíční hranice `dateTime > 1625090400 AND dateTime <= 1627768800`:

- 8 928 řádků, 8 928/8 928 očekávaných časových pozic, `rain IS NULL = 0`; 8 461 nula, 467 kladná hodnota; `rainRate IS NULL = 250`.
- `SUM(rain)*10 = 70.5072658 mm`. Oproti předchozímu známému/modelovému součtu 42.5672658 mm přidalo obnovení 71 původních lokálních impulzů přesně 27.94 mm; obnovení časných nul měsíční součet neměnilo.
- Sedm původních mezer 3. 7. zůstává jedinými synteticky doplněnými řádky: žádná z pěti původních databází v těchto časech řádek nemá. V pracovním archivu mají `rain=0`, `rainRate=NULL`, ostatní meteorologická pole jsou prázdná; nula je regionálně podpořený odhad, ne lokální měření.
- Denní součty níže odpovídají WeeWX intervalu: datum se přiřazuje podle začátku pětiminutového intervalu `dateTime-300`. Každý den má 288 intervalů. Součty jsou zapsané v pracovním archivu; zahrnují původní místní měření, ponechané modelové hodnoty a sedm odhadů:

| Den | mm | Den | mm | Den | mm |
|---|---:|---|---:|---|---:|
| 1 | 0,504254 | 2 | 0,000000 | 3 | 0,046670 |
| 4 | 0,008243 | 5 | 0,000000 | 6 | 0,000000 |
| 7 | 3,073400 | 8 | 1,573173 | 9 | 1,665561 |
| 10 | 0,000000 | 11 | 3,207369 | 12 | 6,599863 |
| 13 | 6,985000 | 14 | 9,773180 | 15 | 0,000000 |
| 16 | 1,397000 | 17 | 0,153596 | 18 | 0,000000 |
| 19 | 4,191000 | 20 | 2,886011 | 21 | 0,008243 |
| 22 | 2,514600 | 23 | 1,676400 | 24 | 3,911600 |
| 25 | 11,272554 | 26 | 0,369815 | 27 | 1,354380 |
| 28 | 2,878482 | 29 | 0,221988 | 30 | 4,191000 |
| 31 | 0,043885 |  |  |  |  |

### Význam výsledku a zbývající práce

`70.5072658 mm` je nyní součet uložených známých hodnot v pracovním archive, nikoli plně nezávisle rekonstruovaný lokální měsíční úhrn. Sedm nulových mezer jsou odhady; zbývající modelové hodnoty stále postrádají úplnou provenienci vstupních CSV, WSI, souřadnic, vzdáleností a IDW vah. Číselnou nejistotu proto nelze poctivě vyčíslit a závěr o přesném měsíčním úhrnu zůstává otevřený.

Pole `rainRate` nebylo odvozeno z obnovených `rain`; 250 NULL zůstává zachováno, protože srážkový úhrn intervalu neurčuje okamžitou nebo průměrnou intenzitu. QC tabulky `rain_qc_202107` a `rain_qc_daily_202107` zůstávají zastaralé: Weather MCP nabízí zapisovací korekci pouze pro `loucka_reconstruction.archive`, nikoli pro tyto QC tabulky, a `execute_sql` je výhradně read-only. Originální databáze nebyly upraveny.

**Stav:** 93 chybných NULL bylo nahrazeno doloženými původními lokálními hodnotami. Mřížka je úplná, ale vědecké uzavření měsíčního úhrnu stále vyžaduje nezávislou reprodukci modelu, audit zbývajících modelových intervalů a synchronizaci QC provenance.


## 11. Dodatečná kontrola ČHMÚ po místních dnech (2026-10-30)

Znovu jsem přímo zpracoval oficiální 10minutové historické JSON soubory ČHMÚ pro tři stanice použité v nezávislé prostorové kontrole. Z každého souboru bylo vybráno všech 4 464 záznamů `SRA10M` (31 × 144); den je určen po převodu UTC na Europe/Prague. Hodnoty s neprázdným `FLAG` nebo `QUALITY != 0` nejsou zahrnuty do platného měsíčního součtu.

| WSI / stanice | Platné 10min hodnoty | Vyřazené příznakované hodnoty | Platný součet za červenec |
|---|---:|---:|---:|
| 11775 Zlín | 4 438 | 26 | 43,7 mm |
| 11777 Vizovice | 4 420 | 44 | 40,6 mm |
| 11778 Luhačovice, Kladná-Žilín | 4 464 | 0 | 47,6 mm |

Nezávislé denní srážky pro kritickou epizodu:

| Místní datum | 11775 Zlín | 11777 Vizovice | 11778 Luhačovice, Kladná-Žilín |
|---|---:|---:|---:|
| 22. 7. | 0,0 mm | 0,0 mm | 0,0 mm |
| 23. 7. | 0,0 mm | 0,0 mm | 0,0 mm |
| 24. 7. | 0,0 mm | 0,0 mm | 0,0 mm |
| 25. 7. | 14,5 mm | 8,8 mm | 14,4 mm |
| 26. 7. | 0,3 mm | 1,1 mm | 1,6 mm |

U všech tří stanic je na 22.–26. 7. k dispozici 144/144 záznamů za den bez FLAG a s QUALITY=0. Tato shoda potvrzuje regionálně suchý charakter 22.–24. 7. a déšť 25.–26. 7.; nevylučuje však lokální konvektivní rozdíly v Loučce. Stanice 11775 měla příznakované hodnoty 28.–29. 7. a 11777 4.–5. a 15. 7.; pro platné součty výše byly odečteny. Souřadnice stanic použité pouze pro geografickou orientaci: Zlín 49,2367° N, 17,6433° E; Vizovice 49,2230° N, 17,8436° E; Luhačovice, Kladná-Žilín 49,0842° N, 17,7925° E. Údaje jsou z [profilu Zlín](https://www.mpocasi.cz/stanice/zlin/), [profilu Vizovic](https://www.mpocasi.cz/stanice/vizovice/) a [profilu Luhačovic](https://www.mpocasi.cz/stanice/luhacovice-kladna-zilin/); oficiálním zdrojem naměřených řádků zůstává příslušný ČHMÚ JSON.

Oficiální soubory: [11775](https://opendata.chmi.cz/meteorology/climate/historical/data/10min/2021/10m-0-203-0-11775-202107.json), [11777](https://opendata.chmi.cz/meteorology/climate/historical/data/10min/2021/10m-0-203-0-11777-202107.json), [11778](https://opendata.chmi.cz/meteorology/climate/historical/data/10min/2021/10m-0-203-0-11778-202107.json). Formát a seznam prvků včetně SRA10M popisuje [oficiální dokumentace klimatologických dat ČHMÚ](https://opendata.chmi.cz/meteorology/climate/Klimatologicka_data_popis.pdf).

### Aktuální pracovní archiv — přímý SELECT

Opakovaný SELECT pro WeeWX interval `dateTime > 1625090400 AND dateTime <= 1627768800` nyní vrátil:

- 8 928 řádků; 0 `rain IS NULL`; 8 461 nul; 467 kladných hodnot.
- `SUM(rain)*10 = 70.5072658 mm`; 250 řádků má `rainRate IS NULL`.
- 8 856 hodnot `rain` souhlasí s návrhovou tabulkou IDW2 a 71 obnovených lokálních hodnot se od ní liší.
- Sedm časů 3. 7. je v archive doplněno jako řídké řádky s nulovým prostorovým odhadem a `rainRate=NULL`; nevydávají se za skutečné lokální měření.
- Pro kontrolu zdrojové nezávislosti platí, že zápisy byly omezeny na `loucka_reconstruction.archive`. Originálních databází se zápisové funkce nedotkly.

Původní loučský snapshot dává 701.0146 mm; model IDW2 bez těchto 71 lokálních obnov dává 42.5672658 mm a aktuální archivní součet je jejich kombinací. Validní měsíční součty tří referenčních srážkoměrů jsou 40,6–47,6 mm. Tato čísla poskytují srovnávací scénáře, nikoli statistický interval spolehlivosti skutečného místního úhrnu.

### Co tato kontrola nedoplňuje

Modelová tabulka stále neobsahuje originální vstupní hodnoty, jednoznačnou vazbu každého intervalu na WSI, vzdálenosti ani váhy. Cílové přesné souřadnice srážkoměru Počasí Loučka nebyly v databázi ani v dostupné primární metadatové evidenci ověřeny. Proto nelze tvrdit, že 42.5672658 mm bylo nezávisle numericky reprodukováno ani odvodit obhajitelnou číselnou nejistotu pro místní měsíční úhrn. 70.5072658 mm je ověřený součet aktuálně uložených hodnot, nikoli potvrzený konečný skutečný úhrn. Denní QC tabulky nadále odrážejí starší klasifikační běh; zapisovací funkce Weather MCP má povolený cíl pouze `archive`, zatímco `execute_sql` je read-only. Tento stav se proto nesmí označit za plně vědecky uzavřený.


## 12. Aktuální selektivní vyřazení 71 podezřelých lokálních impulsů (2026-10-30)

Tato část je novější než sekce 10–11 a **nahrazuje jejich hodnoty aktuálního archivu**. Při opětovném auditu 22.–24. 7. bylo zjištěno, že všech 21 obnovených lokálních impulzů v těchto dnech je současně označeno `strong_suspicion_both_dry`, obě RH řady jsou pod 60 % a všechny tři úplné, platné stanice ČHMÚ mají za místní den nulu. Přezkum ostatních lokálně obnovených impulsů našel dalších 50 hodnot na dnech, kdy návrhová tabulka IDW2 uvádí nulu a obě RH řady jsou pod 60 %.

Tři lokální databáze mají u těchto 71 hodnot shodné kopie původního měření, ale nelze je považovat za tři nezávislé srážkoměry. Proto jsem změnil interpretaci: jejich původní kladné záznamy zůstávají zachovány v snapshotu a auditní historii, zatímco pracovní archiv ukládá **nulový prostorový odhad**, ne potvrzené místní měření. Rozhodnutí je založeno na kombinaci IDW2 nuly, nízké RH v Loučce i LuhaMetu a u 22.–24. 7. také tří platných ČHMÚ srážkoměrů. Nelze vyloučit velmi lokální přeháňku, kterou okolní síť nezachytila; tato možnost je součástí nevyřešené nejistoty, nikoli záminkou k zachování pravděpodobného falešného impulsu.

### Zápis a následná kontrola

Přes atomickou funkci Weather MCP jsem zapsal dvě nové dávky do `loucka_reconstruction.archive`:

- `july2021_chmi_dry_days_local_pulses_v1`: 21 hodnot `rain` z nenulové lokální hodnoty na nulu; odebraný součet 8,1026 mm.
- `july2021_dry_pulse_estimates_v1`: 50 hodnot `rain` z nenulové lokální hodnoty na nulu; odebraný součet 19,8374 mm.

Obě dávky před zápisem prošly dry-runem, použily `expected_old_value` a writer po zápisu ověřil 21/21 a 50/50 změněných hodnot. `reconstruction_changes` zachovává staré i nové hodnoty; předrekonstrukční snapshot nebyl měněn. Žádné pole `rainRate` se těmito dávkami nezměnilo.

Přímý kontrolní SELECT po zápisu pro WeeWX interval `dateTime > 1625090400 AND dateTime <= 1627768800` vrací:

| Kontrola | Výsledek |
|---|---:|
| Řádky / úplné pozice | 8 928 / 8 928 |
| `rain IS NULL` | 0 |
| Nulové / kladné srážkové hodnoty | 8 532 / 396 |
| `SUM(rain)*10` | 42,5672658 mm |
| `rainRate IS NULL` | 250 |
| Přesná shoda `rain` s modelem na společných intervalech | 8 927/8 927 |

Porovnávací intervaly se liší hraničním bodem: návrhová tabulka obsahuje začátek 1. 7. 00:00 a končí 31. 7. 23:55; WeeWX výběr `(start,end]` vynechává první bod a zahrnuje 1. 8. 00:00. Obě krajní srážkové hodnoty jsou nulové. Proto se součty shodují i přes jeden modelový bod na začátku a jeden archive bod na konci mimo průnik.

### Aktuální denní úhrny v pracovním archive

Datum odpovídá začátku pětiminutového intervalu WeeWX. Každý den obsahuje 288 archivních intervalů.

| Den | mm | Den | mm | Den | mm |
|---|---:|---|---:|---|---:|
| 1 | 0,504254 | 2 | 0,000000 | 3 | 0,046670 |
| 4 | 0,008243 | 5 | 0,000000 | 6 | 0,000000 |
| 7 | 0,000000 | 8 | 1,573173 | 9 | 1,665561 |
| 10 | 0,000000 | 11 | 3,207369 | 12 | 6,599863 |
| 13 | 0,000000 | 14 | 9,773180 | 15 | 0,000000 |
| 16 | 0,000000 | 17 | 0,153596 | 18 | 0,000000 |
| 19 | 0,000000 | 20 | 2,886011 | 21 | 0,008243 |
| 22 | 0,000000 | 23 | 0,000000 | 24 | 0,000000 |
| 25 | 11,272554 | 26 | 0,369815 | 27 | 1,354380 |
| 28 | 2,878482 | 29 | 0,221988 | 30 | 0,000000 |
| 31 | 0,043885 |  |  |  |  |

### Meze závěru

42,5672658 mm je nyní součet uložených hodnot, které na 8 927 společných časových bodech přesně odpovídají návrhové tabulce IDW2. **Není to nezávisle reprodukovaný ani definitivně ověřený místní úhrn.** Model stále postrádá dohledatelné vstupní CSV, vazby na konkrétní WSI, vzdálenosti a váhy; nelze tudíž vyčíslit vědecky obhajitelnou statistickou nejistotu. Nulové hodnoty u dnů s podezřelými původními impulzy jsou kvalifikované odhady, ne všechna nezávisle naměřená sucha.

Tabulky `rain_qc_202107` a `rain_qc_daily_202107` jsou nadále zastaralé. Kompletní inventář dostupných Weather MCP nástrojů nabízí read-only SQL a zapisovací korekci výhradně pro `archive`; žádná autorizovaná zapisovací funkce pro QC tabulky zde není. Pokusy o synchronizaci přes read-only SQL nebyly provedeny. Pět původních databází zůstalo nedotčeno.


## 13. Dodatečná kontrola QC, denních hranic a významu rainRate (2026-10-30)

Nový SELECT přes Weather MCP znovu ověřil archiv a zároveň odhalil přesný rozsah nesouladu QC:

- Pracovní archiv má ve WeeWX intervalu `dateTime > 1625090400 AND dateTime <= 1627768800` všech 8 928 časových pozic, žádné `rain IS NULL`, 8 532 nul a 396 kladných hodnot. `SUM(rain)*10 = 42,5672658 mm`; `rainRate IS NULL` má 250 pozic.
- Při řazení podle začátku intervalu (`CEIL((dateTime - 1625090400)/86400)`) má každý z 31 místních dnů 288 intervalů. Denní součty v §12 se nezměnily; prosté seskupení podle data koncového `dateTime` by bod o půlnoci chybně přiřadilo následujícímu dni.
- `rain_qc_202107` obsahuje v tomto rozsahu pouze 8 920 řádků. Osm aktuálních archivních časů nemá QC řádek: sedm synteticky doplněných pozic 3. 7. a závěrečný interval končící 1. 8. 00:00. Všech 8 920 existujících řádků má `validated_rain_mm IS NULL`.
- Denní QC má 31/31 dní bez `verified_daily_rain_mm`; jeden uložený počet intervalů je zastaralý (3. 7. uvádí 281 namísto 288) a tři dny mají starý status `partial_archive_missing`. Celkových 243 chybějících intenzit v denní QC je rovněž starý stav.
- Z 71 bodů převedených v §12 na nulový prostorový odhad je v původním archivním `rainRate` 70 kladných hodnot a jedna nula; žádná není NULL. Oficiální dokumentace WeeWX říká, že `rainRate` může být převzat z hardwaru nebo vypočten službou StdRainRater jako klouzavý průměr minulých srážkových událostí (výchozí okno 1 800 s): [WeeWX StdWXCalculate](https://github.com/weewx/weewx/blob/master/docs_src/reference/weewx-options/stdwxcalculate.md). Historické `weewx.conf` a volba `hardware/software/prefer_hardware` nejsou dostupné, proto tyto hodnoty nejsou nezávislým potvrzením, ale jsou relevantní nevyřešenou stopou. Současné nulové `rain` je nadále odhad, ne důkaz lokálního sucha.

Pracovní měsíční součet 42,5672658 mm a citlivostní scénář, kdy by všech 71 původních lokálních impulzů bylo pravých (+27,94 mm; 70,5072658 mm celkem), jsou dvě porovnávané varianty, nikoli statistický interval ani prokázaná dolní/horní mez.

Stále platí technické omezení zápisu: úplný inventář připojených Weather MCP funkcí obsahuje čtecí SQL a atomický writer pouze pro `archive`; žádný dostupný writer nemění `rain_qc_202107` ani `rain_qc_daily_202107`. Tabulky proto nebyly obcházeny přes read-only SQL. Záznamy původních pěti databází zůstaly nedotčené.


## 14. Kontrola veřejného archivu radarových odhadů ČHMÚ

Oficiální popis ČHMÚ uvádí produkt MERGE jako plošný hodinový úhrn kombinující radar a srážkoměry v gridu 1 × 1 km; soubory HDF5 jsou publikovány v [adresáři MERGE](https://opendata.chmi.cz/meteorology/weather/radar/composite/merge1h/hdf5/). Aktuální index tohoto veřejného adresáře obsahuje záznamy od 15. 10. 2026 a při hledání v indexu nebyl nalezen žádný soubor z července 2021. Historický radarový MERGE tedy z tohoto veřejného endpointu nelze pro tuto rekonstrukci ověřit a do srážkových oprav nebyl použit. Tento limit neznamená, že radarová data nemohou existovat v jiném archivu nebo na vyžádání; pouze nejsou v kontrolovaném veřejném indexu.
