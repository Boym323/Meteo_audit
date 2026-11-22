# Cumulus → WeeWX: forenzní zpřesnění historické časové osy (22. 11. 2026)

**Issues:** #20 (časové zdroje), #21 (jednotkové epochy); návaznost na #15/#16.
**Režim:** živé dotazy MariaDB pouze SELECT, veřejný archiv původního webu, přímé informace vlastníka a oficiální dokumentace WeeWX. Žádné historické databázové opravy, změny WeeWX či živého GW3000 sběru.

## 1. Důležitá metodická hranice

Rozlišujeme tři odlišné skutečnosti:

1. **Generátor webu:** software uvedený na archivované HTML stránce. Sám o sobě neurčuje fyzický datalogger ani počátek nové DB.
2. **Získávání a výpočet měření:** program, driver a konkrétní fyzický senzor, jen pokud jsou doložené původním logem, konfigurací nebo autentizovaným zdrojem.
3. **Import/zpracování historických hodnot:** databázové exporty a konverze; název databáze obsahující `weewx` není důkazem, že měření původně zaznamenal WeeWX.

WeeWX má oficiálně dokumentovaný import měsíčních logů Cumulusu; při importu může podle konfigurace doplnit `usUnits`, `interval` a odvozené hodnoty. To **dokazuje možnost**, nikoliv že se konkrétní import v Loučce provedl. Viz [historická dokumentace WeeWX 3.9](https://weewx.com/docs/3.9/utilities.htm#Importing-from-Cumulus).

## 2. Historický web: co je skutečně ověřeno

| Důkaz | Stav | Závěr |
|---|---|---|
| [30. 8. 2009 – pomykal.eu/pocasi](https://web.archive.org/web/20090830152549/pomykal.eu/pocasi) | **Přímo načten archivovaný HTML obsah** | Zápatí uvádí `Cumulus software v1.8.7 by Steve Loft`. Stanice `Watson-8681 / Fine Offset`, zobrazované jednotky vítr km/h, srážky mm, tlak hPa; web se aktualizoval po 1 min, denní souhrny o půlnoci. |
| Rok 2013 | **Hlášení vlastníka podle archivovaného webu, přesný snímek nedostupný** | Cumulus ještě uveden; dosud bez přesného capture timestampu, HTML a verze. |
| Rok 2017 | **Hlášení vlastníka podle archivovaného webu, přesný snímek nedostupný** | WeeWX už uveden; dosud bez přesného capture timestampu, HTML a verze. |
| [Současná historie stanice](https://pocasi-loucka.eu/about/) | Veřejný současný web, nikoli dobový snapshot | Start měření 29. 3. 2009 s Watson W-8681, GW1000 od 20. 8. 2022; nemůže sám datovat přechod na WeeWX. |

Dostupný Wayback index uvádí **9 capture** dané staré URL mezi květnem 2009 a srpnem 2018; přesnou časovou řadu ostatních snímků se nyní nepodařilo načíst (kalendář vyžaduje JavaScript, automatický CDX přístup selhal). Datum přechodu na WeeWX proto **není ověřené přímo z HTML**.

## 3. Nejsilnější nová stopa: konec června / začátek července 2014

Základ: reprodukovatelné read-only dotazy [`sql/readonly/cumulus_weewx_transition_pivot.sql`](../sql/readonly/cumulus_weewx_transition_pivot.sql).

| Zdroj | Poslední timestamp před společnou mezerou (UTC) | První timestamp po mezeře (UTC) |
|---|---|---|
| `old_weewx.archive` | **2014-06-20 22:49:00** (`1403304540`) | **2014-07-03 17:00:00** (`1404406800`) |
| `weewx_WH1080.archive` | **2014-06-20 22:49:00** | **2014-07-03 17:00:00** |
| `pocasi-loucka.eu.archive` | **2014-06-20 22:50:00** (`1403304600`) | **2014-07-03 17:00:00** |

Při obnovení dat dne **3. 7. 2014 17:00 UTC** se v `old_weewx` také poprvé objevuje nenulově přítomné `pressure`. Před tímto timestampem bylo v daném zdroji `pressure` NULL, **ale `weewx_WH1080` obsahuje některé hodnoty `pressure` již od roku 2009**. Jde tedy o změnu podoby *konkrétního zdrojového archivu*, nikoli automaticky počátek tlakových měření stanice.

Dne **6. 7. 2014 13:00:01 UTC** (`1404651601`) se současně v `old_weewx` i `weewx_WH1080` poprvé objeví `dateTime` mimo celé minuty. První archivní `interval != 5` v těchto zdrojích je **25. 7. 2014 18:29:54 UTC**. Do konce července má `old_weewx` 8 406 zdrojových řádků, ale jen 7 615 vazeb na hypoteticky nejbližší pětiminutové produkční timestampy; samotné zaokrouhlení tedy nezaručuje jednoznačné ani fyzicky ekvivalentní párování.

**Závěr:** první červencový týden 2014 je nejsilnější dosud doložená **technická změna archivní pipeline**. Je slučitelná s hypotézou Cumulus → WeeWX, ale nedokazuje instalaci nebo definitivní vypnutí jednoho loggeru. Přechod pro archivní jednotky **nesmíme natvrdo nastavit na 2014-07-03** bez dalšího zdroje.

## 4. Jednotky větru se změnily už v dubnu 2013 — jiná událost

Čtecí porovnání `old_weewx.windSpeed` s `pocasi-loucka.eu.windSpeed` na nejbližší pětiminutové mřížce, s tolerancí rozdílu <0,1, pro **kladné** rychlosti:

| Omezené UTC okno | Páry s kladným větrem | Zdroj/produkce numericky shodné | Produkce ≈ zdroj × 3,6 |
|---|---:|---:|---:|
| Březen 2013 | 4 802 | **4 801** | 0 |
| Květen–červenec 2013 | 6 259 | 0 | **6 259** |
| Květen–20. červen 2014 | 11 525 | 0 | **11 524** |
| 3.–31. červenec 2014 | 7 068 | 4 | **6 815** |

Poslední doložený kladný numericky shodný pár v dubnu 2013 je **6. 4. 2013 15:10 UTC** (`1365261000`), první doložený pár s faktorem 3,6 po mezeře **12. 4. 2013 17:55 UTC** (`1365789300`). Samotný poměr odpovídá konverzi m/s ↔ km/h. Nejde o certifikaci fyzických jednotek všech hodnot a nelze vyloučit odchylky v jednotlivých datových sériích.

**Kritický závěr pro #21:** změna numerického režimu v dubnu 2013 je **samostatná**, podstatně starší než červencová změna časové struktury v roce 2014. Z uživatelsky hlášeného Cumulusu na webu v roce 2013 nelze bez dalšího ztotožnit tento převod s výměnou softwaru.

Zdroj `old_weewx` vykazuje `usUnits=17` již v roce 2009 a také v roce 2017, zatímco produkční `archive` má v těchto obdobích `usUnits=16`. Tato metadata popisují formát uložených dat, ne nutně původní software a fyzické jednotky jeho numerických polí.

## 5. Co je připraveno jako kód a evidence

- [`reports/data/2026-11-22-cumulus-weewx-transition-evidence.json`](data/2026-11-22-cumulus-weewx-transition-evidence.json): oddělené přímé webové důkazy, hlášení vlastníka za celý rok a SQL markery; žádné jednotlivé meteorologické hodnoty ani tajné údaje.
- [`src/meteo_audit/logger_lineage.py`](../src/meteo_audit/logger_lineage.py): fail-closed interpretace historie, nikdy nevypočítává datum změny dataloggeru z fingerprintu DB ani z pouhého názvu webového generátoru.
- [`tests/test_logger_lineage.py`](../tests/test_logger_lineage.py): test, že hlášení „2013“ a „2017“ nejsou vydávána za přesné datované snímky, že DB marker nelze zaměnit za logger a že datum přechodu zůstane neověřené.
- [`sql/readonly/cumulus_weewx_transition_pivot.sql`](../sql/readonly/cumulus_weewx_transition_pivot.sql): dotazy pro původní a přepočítané UTC epochy a změnu numerického měřítka větru.

## 6. Co ještě potřebujeme pro definitivní výsledek

1. **První přímo ověřený Wayback snapshot s WeeWX** a **poslední přímo ověřený snapshot Cumulusu** v letech 2013–2017. Uložit jejich přesné capture timestampy a HTML stopy, ne pouze rok. I přesné webové datum dokládá *generátor stránky*, ne nutně originalitu starých DB hodnot.
2. Ze starých disků/NAS záloh případný `Cumulus.ini`, `dayfile.txt`, `*log.txt`, `cumulus.conf` (WeeWX import konfigurace) a datované WeeWX logy. Názvy odpovídají obecně známým formátům; **jejich existence v Loučce není nyní prokázaná**.
3. V rekonstruovaných archivech vyhodnotit skupinu 2014-06/07 po jednotlivých veličinách a konfliktních časových slotech, nikoliv hromadným nearest-slot přepisem. Před a po technickém zlomu vyhodnotit odvozené veličiny včetně `dewpoint` a srážkovou sémantiku separátně.
4. `#20`: propojit s aktuálním baseline 49 796 WH1080 kandidátů (PR #57), bez přepisování již obsazených timestampů. `#21`: propojit s fail-closed kontrolou fyzických jednotek (PR #58), bez automatického odemykání epoch.
5. `#15/#16`: používání dřívějšího Cumulusu **neříká nic** o vzorci WeeWX pro RH duben 2022 ani o RainRater špičkách 2023–2024; jejich nezávislá validace stále chybí.

**Rozhodnutí:** `logger_switch_date = UNVERIFIED`, kandidát na technickou změnu = počátek července 2014; `db_writes = 0`. Finální migrační karanténa zůstává beze změny.
