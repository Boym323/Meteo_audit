# Počasí Loučka — živé brány pro publikaci historických rekordů

**Datum:** 2. 11. 2026. **Zdroj:** přímé read-only SQL přes Weather MCP v `loucka_reconstruction`; historické audity `reports/parallel-audit/MASTER_AUDIT.md` a `CONFIRMED_CANDIDATES.md`. **Bez změny dat**.

## Snímek pracovní databáze

| Položka | Výsledek | Význam |
| --- | ---: | --- |
| Rekonstrukční `archive` | 1 679 809 řádků | Konec `dateTime=1793286600`, 29. 10. 2026; není živou produkční kopií ke 2. 11. |
| `outHumidity IS NULL` | 154 896 | Nelze dopočítat bez důvěryhodného vstupu |
| `outTemp IS NULL` | 18 301 | Nelze považovat za dny bez mrazu |
| `reconstruction_batches` | 20 pending / 4 cancelled | 272 pending a 93 cancelled návrhů; staging ≠ aplikace |
| Pending podle veličiny | 207 rainRate, 25 outTemp, 13 outHumidity, 14 rain, 5 windSpeed, 4 radiation, 1 pm25_1, 2 soilTemp1, 1 barometer | Součty podle typů zahrnují i různé `rule`, ověřit individuálně |
| `reconstruction_changes` | 62 252 applied rainRate, 9 964 applied RH, 789 applied rain; 8 921 reverted rain + 8 921 reverted rainRate | Historie událostí, **neunikátní počet konečných měření** |
| WH1080 staging | 47 737 pressure-only + 1 301 frozen + 758 needs-validation | Celkem 49 796 kandidátů, dosud bez potvrzené číselné náhrady |
| PM2,5 (09–10/2024 UTC) | 1 401 hodnot ≥999,8; 2 125 hodnot >500 | Potvrzená saturace/podezření, ne automatická náhrada |
| Referenční záznamy | LuhaMet 1 157 794, ILOUKA4 494 844 | Referenční série nejsou automaticky totožné s místní meteorologií |

Pozn.: reporty z 30. 10. mají starší počty a stavy oprav. Před dalšími změnami je nutné se opírat o **aktuální** log, zpětné operace a snapshot, nikoliv opakovat historické dávky.

## Potvrzené měřicí epochy bez dohadu o fyzické instalaci

V pracovní DB první dostupné nenulově interpretovatelné hodnoty `soilMoist1`, `pm25_1` a `radiation` spadají na 27. 8. 2022. Samotné `soilTemp1` obsahuje dřívější archivní hodnoty a bez potvrzení fyzického senzoru není důkazem existence půdní sondy. U `lightning_distance` je první záznam ze září 2022. **V posledních 30 dnech rekonstrukce** je `soilTemp2` úplně prázdný (0 z 8 629), zatímco `soilTemp1` má 8 621 řádků, `soilMoist1` 8 629, PM2,5 8 627. `soilTemp3/4` mají měření, jejich fyzické značení není ověřené.

Pozor na názvy: GW3000 LAN API používá `ch_soil.channel=1` a veřejný live kód zobrazuje `soilMoisture1`; WeeWX archivní sloupec je `soilMoist1`. Bez explicitní revizní evidence **nelze tvrdit**, že historická a živá hodnota mají totožnou fyzickou provenienci. Například pojmenování z GW3000 `Půda zahrada` je konfigurovaný štítek, nikoli ověřená hloubka.

## Brány k certifikaci (všechny povinné)

1. **Sjednocení časové struktury:** `dateTime` je konec WeeWX intervalu `(start,end]`, UTC, kalendář `Europe/Prague`. Reálný `interval`, bez double-countingu a kolizí. Zmapovat mezery 2011–2012 i WH1080.
2. **Jednotkové a senzorové epochy:** schválit přechody duben 2013, září 2020, srpen 2022 a rok 2026, včetně větru, deště, PM2,5, RH a skutečně nainstalovaných sond.
3. **Hodnotové QC:** po jednotlivých intervalech potvrdit teploty a zamrzlé bloky, RH 2015–2019 / 2022, rosný bod, tlak, srážky i červencovou rekonstrukci 2021. Oddělit `diagnosis_confidence` od `replacement_confidence`.
4. **Nezávislé reference:** LuhaMet a ILOUKA4 nejsou přímo naše měření; shoda není důkazem přesného srážkového úhrnu. Vždy udržet zdroj, algoritmus, jednotku a timestamp reference.
5. **Schválení aplikace:** pending batche se nesmí automaticky aplikovat, původní hodnoty musí zůstat dohledatelné, opravené mají `applied` log a zpětné `reverted` záznamy se musí vyhodnotit.
6. **Kanonická publikační verze:** zastropovat neměnný cutoff, zveřejnit kontrolní hash/revision, testy přepnutí datasetu `approved` bez zápisu do produkční `archive`, dokumentovat lokální dny a pokrytí po veličinách.

**Stav: `BLOCKED`, schválené historické rekordy NEPUBLIKOVAT.** Web může nadále zobrazovat jasně označené předběžné rekordy z původních denních souhrnů.

## Limity přístupu tohoto ověření

Současný konektor `Weather_MCP` vylistoval šest databází, ale při dotazu na názvy se znakem tečka/pomlčka vrací `Invalid database name provided`. Proto **nebylo možné nově nezávisle porovnat přímo produkci ani GW1000 v tomto běhu**; je nutné opravit allowlist MCP nebo použít existující schválený SELECT-only auditní účet mimo tento konektor. To není důkaz chyby dat a není důvod přidávat zápisové pravomoci.

Tento report je evidence a schvalovací plán, ne prohlášení dokončené rekonstrukce.