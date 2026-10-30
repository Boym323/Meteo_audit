# 01 — Forenzní audit srážek 2009–2013 (read-only)

**Datum šetření:** 2026-10-30 (Europe/Prague). **Rozsah:** šestiarchivní MariaDB přes Weather MCP, výhradně SELECT; měsíční/roční kontrolní okna, krátké CTE a žádný DB zápis. **Stav:** potvrzené technické nálezy, neuzavřená fyzikální kalibrace; žádná oprava navržena k automatickému apply. Autoritativní datum zdroje a času: `archive.dateTime` (Unix sekundy UTC), `interval=5` minut v kontrolovaném rozsahu; archivní timestamp je konec intervalu WeeWX.

## Shrnutí

1. Jednotky jsou **ověřené**: `usUnits=16` (METRIC) ve `loucka_reconstruction`, `pocasi-loucka.eu`, `pocasi-loucka.eu_old`, `pocasi-loucka.eu_GW1000`; v jejich standardním WeeWX archivu je `rain` v **cm** a `rainRate` v **cm/h**. `usUnits=17` (METRICWX) v `old_weewx` a `weewx_WH1080`; standardní jednotkou je **mm**, resp. **mm/h**. V těchto dvou nejstarších archivech je však `rain` **stav kumulativního čítače**, nikoliv intervalový úhrn (maxima 265,5/408/384 mm v letech 2009/2010/2011). Sečtení těchto stavů jako deště je chybné.
2. **Převod před polovinou dubna 2013:** při spárování kladných přírůstků starého čítače 0,3–3,0 mm se stejným timestampem je poměr `Δcounter_mm / (10 × reconstruction.rain_cm)` prakticky **10:1**, zatímco po 19. 4. 2013 je **1:1**. Současně se `12×Δcounter_mm / old.rainRate_mm_h` mění **5:1 → 1:1**. Proto převodový problém není vysvětlitelný pouze jedním desetinným posunem v jednom sloupci.
3. **Neprovádět ×10** nad uloženým intervalovým `rain`: u května 2010 by z nynějších 137,01 mm vzniklo 1 370,10 mm, zatímco krajský květnový průměr ČHMÚ byl 233 mm a největší regionální zaznamenaná hodnota 536,2 mm (Horní Bečva-Kudlačena). Tato jednoduchá rekonstrukce je s klimatologickým kontextem výrazně v rozporu. **Hypotéza ×2** ze vztahu `rainRate / (12×rain_mm)` je konzistentnější, ale samotný `rainRate` mohl být odvozen historickým driverem a vyžaduje externí kalibraci; nejde o schválenou opravu.
4. **Fáze A zůstává zachována**. Její tři nezávislé sady záloh nezahrnují překryv časů: 328 odstraněných půlnočních resetů (175,14 mm), 30 oprav v červnu 2010 (161,76 mm), 1 oprava 28. 3. 2011 (30,72 mm); celkem **359 timestampů, 367,62 mm** historického rozdílu produkce versus pracovní verze za roky 2009–2011. Sady jsou evidovány jako `applied` v `reconstruction_changes`; bez nových důkazů nejsou zpochybněny. Pozor: jde o korekci zjevných datových artefaktů, nikoli o důkaz správnosti všech ostatních hodnot.
5. `old_weewx` a `weewx_WH1080` jsou při shodném timestampu v rozsáhlých měsíčních vzorcích **identické v rain i rainRate**. `pocasi-loucka.eu` a `pocasi-loucka.eu_GW1000` mají ve zkoumaných shodných timestampových záznamech identické `rain`, ale výrazně se liší v `rainRate` (produkce má v období 2009–2013 nulovou intenzitu). Tedy nejde o šest nezávislých srážkoměrů.
6. Pokrytí je neúplné: 2009 začíná 29. března; celý úsek **září 2011 – únor 2012** chybí v hlavních intervalových archivech (starý čítač sahá do konce srpna 2011, nikoliv do těchto chybějících měsíců), další mezery a `NULL` jsou zejména v roce 2013. Roční součty proto nejsou vždy srovnatelné s úplnou klimatologickou řadou.

## Časová osa a primární důkazy

| Období | Zjištění | Jistota |
|---|---|---|
| 2009-03-29 | Počátek dostupného archivního období; starý čítač `usUnits=17` a intervalový archiv `usUnits=16`. | Vysoká |
| 2009–2011 | Půlnoční reset na **00:00:00 UTC** přenesen jako kladný intervalový `rain`. V `rain_daily_reset_backup_2009_2011_v1` přesně **328/328** timestampů má `MOD(dateTime,86400)=0`. Po opravě je ve všech odpovídajících řádcích `archive.rain=0`; zálohované hodnoty představují 175,14 mm. | Velmi vysoká (mechanismus artefaktu) |
| 2010-06-01 až 2010-06-03 (případ Fáze A) | 30 již opravených intervalů včetně 12 červnových binárních anomálií a 6 skoků/resetů s nulovou intenzitou; původní součet 161,76 mm. | Vysoká pro existenci chyby, přesná fyzikální náhrada nemusí být vždy doložitelná |
| 2011-03-28 08:50 CEST | Produkce 30,72 mm, starý čítač náhle 307,2 mm = **1024 × 0,3 mm**, hned poté 384 mm, `rainRate=0`; pracovní hodnota je po Fázi A **0**. Příznaky binárního skoku velmi silné, meteorologická nulová náhrada zůstává nezávisle neověřena. | Vysoká pro diagnostiku artefaktu |
| 2011-09 až 2012-02 | Bez hlavních archivních měření; nepřidělovat nulové srážky. | Velmi vysoká |
| 2013-04-12/13 | Shodné timestampy: 12. 4. 21:20 CEST čítač +0,9 mm, rekonstruovaný interval 0,09 mm, surová intenzita 2,16 mm/h; 12. 4. 22:10 čítač +1,8 mm, interval 0,18 mm, intenzita 4,32 mm/h. 13. 4. 15:05 čítač +0,3 mm, interval 0,03 mm. | Velmi vysoká (datové poměry) |
| 2013-04-14 až 2013-04-18 | Bez průkazných kladných společných intervalů určujících režim. Dne 14. 4. je pět záznamů `rain=NULL` a jeden čítačový přírůstek bez spárovaného `rain`. Není možné určit minutu změny. | Vysoká |
| 2013-04-19/20 | 19. 4. 23:45 a 20. 4. 11:40 CEST: čítač +0,3 mm, rekonstruovaný interval **0,3 mm**, intenzita **3,6 mm/h**. První doložené přírůstky v novém režimu. | Velmi vysoká |
| 2026-10-30 | Potvrzen aplikovaný stav Fáze A v pracovní DB; žádný zápis v rámci tohoto auditu. | Velmi vysoká |

**Podrobnější vzorková kontrola převodu:** omezené měsíční okno, raw delta v (0,3 až 3,0 mm) a kladné intervalové `rain`:

| Okno | Spárované kladné přírůstky | `Δcounter / rain_mm` | `12 Δcounter / rainRate` |
|---|---:|---:|---:|
| 2009-05 | 258 | 10,0 | 5,0 |
| 2010-05 | 618 (617 přesně ×10, jeden odlišný) | průměr 10,002 | průměr 5,007 |
| 2011-07 | 395 | 10,0 | ~4,98 |
| 2012-11 | 123 | 10,0 | 5,0 |
| 2013-03 | 66 | 10,0 | 5,0 |
| 2013-04-01 až 13 | 31 | 10,0 | 5,0 |
| 2013-04-19 až 30 | 3 | 1,0 | 1,0 |
| 2013-05 | 194 | 1,0 | ~1,01 |

**Pozor:** Stejné poměry z různých názvů databází nejsou automaticky nezávislým důkazem fyzikální správnosti. Starý driver mohl násobit čítač, intenzitu a intervalový úhrn různými faktory. Kontrola zdrojových paketů, driveru a původního `weewx.conf` je rozhodující. Hardwarová literatura WH1080 popisuje krok čítače 0,3 mm, ale nemusí přesně odpovídat zde použitým historickým softwarovým transformacím.

## Roční kontrola s nezávislým klimatologickým kontextem

Součty jsou dostupné **uložené** intervaly ×10 (METRIC cm → mm) po již aplikované Fázi A; nejsou kalibrované ani doplněné za výpadky. Orientační hranice jsou místní kalendářní roky dle session TZ a bez úplného ověření meteorologického srážkového dne.

| Rok | Pracovní `rain` mm | Produkční `rain` mm | Zlínský kraj ČHMÚ mm | Interpretace |
|---|---:|---:|---:|---|
| 2009 | 384,58 | 437,50 | 806 | Měření začíná v březnu; oprava artefaktů 52,92 mm |
| 2010 | 552,57 | 783,54 | 1 017 | Oprava artefaktů 230,97 mm; květen 137,01 mm vs kraj 233 mm |
| 2011 | 439,95 | 523,68 | 654 | V pracovní DB končí v srpnu; opravy 83,73 mm, chybí 4+ měsíce |
| 2012 | 308,07 | 308,07 | 778 | Chybí leden/únor a část března, další mezery |
| 2013 | 550,68 | 550,68 | 750 | Smíšené historické režimy, `rain=NULL` a výpadky |

Krajská čísla **nejsou staniční referencí Loučky** a sama o sobě nepotvrzují korekci na jednotlivých dnech. Stanice ČHMÚ Vizovice má za rok 2010 publikován úplný úhrn **884 mm**. V ČHMÚ krajské zprávě vychází květen 2010 **233 mm** a nejvyšší květnový staniční úhrn ve Zlínském kraji **536,2 mm**. Varianta `137,01 × 10 = 1370,1 mm` už v jediném květnu 2010 daleko překračuje i tento regionální extrém. Varianta `×2=274,02 mm` je klimatologicky věrohodnější, nikoli však prokázaná.

**Dostupnost jemných referencí:** v `loucka_reconstruction.reference_daily` nebyl žádný řádek pro roky 2009–2013; existující LuhaMet/ILOUKA4 importy historicky toto období nepokrývají. Zdokumentované ČHMÚ denní `SRA` pro Vizovice a Kladná-Žilín v `reports/chmi_daily_incident_rows.csv` uvádějí např. pro zdrojový řádek 2010-06-01 48,6 a 57,0 mm. Přesná vazba `DT`, `TIMEFUNC=06:00`, přiřazení dne a konce 24hodinového okna **není ověřena**; nemohou potvrdit pětiminutové impulsy. Srovnání dalších staničních měsíčních úhrnů je **neuzavřený úkol**, nikoliv zjištěná shoda.

## Potvrzené chyby versus hypotézy

| Nález / návrh | Jistota chyby | Jistota náhradní hodnoty | Protiargument / omezení |
|---|---|---|---|
| Součet starého `rain` jako intervalové srážky | Velmi vysoká | N/A | Jde o čítač s resety; rozdíly je nutné čistit |
| 328 resetových falešných přírůstků v 00 UTC | Velmi vysoká | Již aplikováno Fází A | Pozor na část srážek přes reset, nepřevést celý den na nulu |
| 2010-06 binární/přenosové artefakty | Vysoká | Již aplikováno Fází A | ČHMÚ potvrzuje déšť v regionu; hodnota nula nemusí být dokonalá meteorologická rekonstrukce |
| 2011-03-28 307,2 mm = 1024 kroků | Velmi vysoká | Již aplikováno v pracovní kopii | Regionální nulové SRA nemá ověřené časové okno a není přímým důkazem 5 min |
| Desetinásobný posun vazby raw→archiv před 2013-04-19 | Velmi vysoká | **Nízká** pro `rain×10` | Raw čítač sám může být softwarově přeškálovaný; `rainRate` je před změnou od raw odvozen faktorem 5 |
| Podhodnocení `rain` zhruba ×2 do dubna 2013 | Střední (hypotéza) | Nízká až střední | Sedí vztah k `rainRate` i krajský kontext 2009/2010; `rainRate` není nezávislé fyzické měření, region ≠ lokalita |
| `rainRate` obnovená z GW1000 v pracovní kopii | Technicky potvrzeno | Nejistá fyzikální sémantika | Může jít o jiné zobrazení téhož zdroje, ne nezávislý ovladač |
| Chybějící 2011–2012 | Velmi vysoká | Není dostupná náhrada | `NULL` / chybějící řádek se nesmí měnit na nulu |

**Doporučení bez zápisu:** zachovat aplikovanou Fázi A, nevydávat roční součty 2009–2013 jako definitivní úhrny, nedělat plošné násobení. Pro Fázi B vyžádat původní WH1080/pywws/WeeWX konfiguraci a kód readeru kolem 2013-04-14 až 19; porovnat provozní logy s ČHMÚ Vizovice/Kladná-Žilín po kalibračních měsíčních oknech (zejména 2010-05, 2010-06, 2013-03/04/05), rozdělit časová období a odlišit přenosové artefakty od skutečných tipů. Návrh změn po jednotlivých časových intervalech doplnit až po důkazech, s kontrolním součtem, rollbackem a odděleným schválením.

## Reprodukovatelné read-only SQL

Vše spouštět přes Weather MCP `execute_sql(database_name="loucka_reconstruction")`. Každý dotaz je čistý SELECT. Pro hranice používat číselné UTC epochy `dateTime`; `FROM_UNIXTIME` slouží pouze k čitelnému výstupu a podléhá session TZ. Pětiminutová WeeWX agregace v místním období správně používá `(start,end]`; níže jsou intervaly `[start,end)` určené **jen pro technický screening podle UTC**, nikoliv finální měsíční účetní součet.

**1. Jednotky a 30denní rozsah v pracovním archivu:**

```sql
SELECT usUnits, `interval`, COUNT(*) n,
       ROUND(SUM(rain)*10, 3) stored_rain_mm,
       SUM(rain IS NULL) null_rain,
       SUM(rain>0 AND rainRate=0) positive_without_rate
FROM `loucka_reconstruction`.`archive`
WHERE dateTime >= 1364774400 AND dateTime < 1367366400
GROUP BY usUnits, `interval`;
```

Zopakovat pro další databáze po jednotlivých měsících; pro `usUnits=17` se čítač **nesčítá**.

**2. Starý čítač, přírůstky a párování změny 2013 (UTC 12.–20. dubna):**

```sql
WITH c AS (
 SELECT dateTime, rain AS counter_mm, rainRate AS raw_rate_mmh,
        LAG(rain) OVER (ORDER BY dateTime) AS prev_counter_mm
 FROM `weewx_WH1080`.`archive`
 WHERE dateTime >= 1365724800 AND dateTime < 1366502400
)
SELECT FROM_UNIXTIME(c.dateTime) local_end_time,
       c.counter_mm, c.prev_counter_mm,
       ROUND(c.counter_mm - c.prev_counter_mm,3) delta_counter_mm,
       ROUND(r.rain*10,3) reconstruction_interval_mm,
       ROUND(r.rainRate*10,3) reconstruction_rate_mmh,
       c.raw_rate_mmh
FROM c LEFT JOIN `loucka_reconstruction`.`archive` r
     ON c.dateTime=r.dateTime
WHERE c.counter_mm > c.prev_counter_mm
ORDER BY c.dateTime LIMIT 100;
```

V jiných obdobích změnit oba epochové parametry na rozsah jednoho měsíce; `LAG` nemá předchozí stav před začátkem okna.

**3. Počty dvojic s faktorem ×10/×5, vždy jeden měsíc (zde květen 2010 UTC):**

```sql
WITH c AS (
 SELECT dateTime, rain AS counter_mm, rainRate AS raw_rate_mmh,
        LAG(rain) OVER (ORDER BY dateTime) AS prev_mm
 FROM `weewx_WH1080`.`archive`
 WHERE dateTime >= 1272672000 AND dateTime < 1275350400
)
SELECT COUNT(*) n_pairs,
 ROUND(AVG((c.counter_mm-c.prev_mm)/(10*r.rain)),3) factor_raw_vs_rain,
 ROUND(AVG(CASE WHEN c.raw_rate_mmh>0
        THEN (c.counter_mm-c.prev_mm)*12/c.raw_rate_mmh END),3) factor_raw_vs_rate,
 SUM(ABS((c.counter_mm-c.prev_mm)/(10*r.rain)-10)<0.01) factor10_pairs,
 SUM(ABS((c.counter_mm-c.prev_mm)/(10*r.rain)-1)<0.01) factor1_pairs
FROM c JOIN `loucka_reconstruction`.`archive` r ON r.dateTime=c.dateTime
WHERE c.counter_mm>c.prev_mm
  AND c.counter_mm-c.prev_mm BETWEEN 0.2999 AND 3.0001
  AND r.rain>0;
```

**4. Ověření Fáze A bez nových změn:**

```sql
SELECT MOD(b.dateTime,86400) second_of_utc_day, COUNT(*) n,
       ROUND(SUM(b.rain_before)*10,2) old_mm,
       SUM(a.rain=0) currently_zero
FROM `loucka_reconstruction`.`rain_daily_reset_backup_2009_2011_v1` b
JOIN `loucka_reconstruction`.`archive` a USING (dateTime)
GROUP BY MOD(b.dateTime,86400);
```

```sql
SELECT variable, batch_key, state, COUNT(*) n
FROM `loucka_reconstruction`.`reconstruction_changes`
WHERE target_time >= 1230768000 AND target_time < 1388534400
  AND variable IN ('rain','rainRate')
GROUP BY variable, batch_key, state
ORDER BY n DESC LIMIT 30;
```

**5. Ověření závislých kopií (pouze duben 2013):**

```sql
SELECT COUNT(*) n,
 SUM(NOT (a.rain <=> b.rain)) raw_rain_mismatch,
 SUM(NOT (a.rainRate <=> b.rainRate)) raw_rate_mismatch,
 SUM(NOT (p.rain <=> g.rain)) prod_gw_rain_mismatch
FROM `old_weewx`.`archive` a
JOIN `weewx_WH1080`.`archive` b USING (dateTime)
JOIN `pocasi-loucka.eu`.`archive` p USING (dateTime)
JOIN `pocasi-loucka.eu_GW1000`.`archive` g USING (dateTime)
WHERE a.dateTime >= 1364774400 AND a.dateTime < 1367366400;
```

## Zdroje a omezení provenance

- WeeWX jednotky: https://www.weewx.com/docs/5.4/reference/units/ (METRIC 16 cm; METRICWX 17 mm).
- WH1080 dekódování a krok 0,3 mm: https://github.com/merbanan/rtl_433/blob/master/src/devices/fineoffset_wh1080.c (reference k typu zařízení, nikoli ověření zde instalovaného firmwaru).
- ČHMÚ historické denní `SRA`: https://opendata.chmi.cz/meteorology/climate/historical_csv/data/daily/precipitation/ ; pravidla denní srážky: https://geoportal.gov.cz/php/micka/record/basic/6a589302-99f4-47f9-a4ee-152508c0a8017c .
- ČHMÚ/INFOMET přehledy ročních/krajských srážek: 2009–2010 https://www.infomet.cz/print/index.php?file=1296075897&id=print ; 2011 https://www.infomet.cz/print/index.php?file=1328820623&id=print ; 2012 https://www.infomet.cz/print/index.php?file=1359754316&id=print ; 2013 https://www.infomet.cz/index.php?id=read&idd=1392069273&pocatecni=1392157490 .
- Předchozí nezměněná metodika projektu: `reports/2026-10-30-diagnostic-phase-a.md`, `docs/rain-audit-methodology.md`, `docs/chmi-daily-sra.md`. Historické `SRA` řádky uchovává `reports/chmi_daily_incident_rows.csv`.
- **Omezení auditu:** neověřeny původní HW/SW konfigurace ani původní binární pakety; přesné ČHMÚ denní časové okno chybí; import lokálních nezávislých srážkových referencí pro 2009–2013 chybí; proběhl jeden SQL timeout u celoročního pětinásobného JOIN roku 2013, úspěšně nahrazen oddělenými měsíčními JOINy. Databáze neupravena.
