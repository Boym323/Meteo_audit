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
