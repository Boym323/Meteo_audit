# CONFIRMED_CANDIDATES — registr ověřených problémů a návrhů další práce

**Verze:** 2026-10-30 · **Syntéza:** [MASTER_AUDIT.md](MASTER_AUDIT.md)  
**Pozor:** „potvrzený kandidát“ znamená **potvrzenou anomálii/datovou nekonzistenci**, nikoli ověřenou opravenou hodnotu. Ve sloupci „náhrada“ je `UNRESOLVED`, pokud neexistuje externě podložená numerická náhrada. **ŽÁDNÝ Z NÍŽE UVEDENÝCH NOVÝCH KANDIDÁTŮ NENÍ SCHVÁLEN K UPDATE.**

## A. Již aplikované zásahy — NEOPAKOVAT

| ID | Klíč/rozsah | Aktuální DB | Rozhodnutí |
|---|---|---|---|
| DONE-A1 | `rain-2009-2011-utc-midnight-reset-v1` | 328 `rain` applied; rozdíl 175,14 mm; záloha `rain_daily_reset_backup_2009_2011_v1` | Nevkládat novou kandidaturu pro stejné target_time |
| DONE-A2 | `rain-phaseA-june2010-corrected-20261030-v1` | 30 `rain` applied; 161,76 mm; záloha `rain_phase_a_201006_backup_20261030_v1` | Diagnóza artefaktu silná, nulová náhrada není absolutní meteorologická pravda |
| DONE-A3 | `rain-phaseA-apply-20261030-v1` | 2 `rain` + 1 `rainRate` applied; 61,22 mm; záloha `rain_phase_a_backup_20261030_v1` | 2011-03-28 `1301295000` a 2025-02-27 `1740687300` jsou již nulové |
| DONE-JUL21 | Lokální červenec 2021 | `rain` pracovní ~42,567 mm | Nevracet původních ~701 mm bez nového schváleného důkazu |
| DONE-RH22 | Duben 2022, `reconstruction_humidity_202204` | RH již byla upravena, ale odvozeniny mohou být zastaralé | Žádné opakované plošné dosazení RH |
| DONE-RR | `rainrate-restore-2009-2025-v1` | 58 936 aplikovaných změn `rainRate` | Před jakýmkoliv dalším převzetím GW1000 testovat konflikt a zdrojovou sémantiku |

## B. Živé kandidáty pro další schválený workflow

| ID | Priorita | Veličina / identifikace | Důkazní rozsah | Jistota diagnózy | Jistota náhradní hodnoty | Dále |
|---|---|---|---|---|---|---|
| C001 | P0 | `dewpoint` po RH 2022-04 | 1 077 diagnostických rozdílů >2 °C z 7 068 vypočitatelných | **HIGH** pro fyzikální nekonzistenci | **UNRESOLVED** do verifikace dobové formule | Rozhodnutí per timestamp, samostatně i `heatindex`, `appTemp` |
| C002 | P0 | `rainRate` v 2023 a 2024 | 13 + 15 zdrojových GW1000 intervalů >5 cm/h, rekonstrukce 0 | **HIGH** pro odlišnost; pravost špičky neověřena | **UNRESOLVED** | Kontrola radar/PWS, driver, auditní historie, žádný plošný restore |
| C003 | P0 | `lightning_noise_count` a `lightning_disturber_count` | 2026: 179/179 shod noise=strike; disturber podobný UTC epoch | **HIGH** pro chybnou/nejistou sémantiku | Nejde o numerickou DB náhradu | Prověřit raw JSON, opravit mapper v odděleném code PR |
| C004 | P1 | `pressure` chybějící 2016–2018 | 47 737 `pressure_only_review`; 28 hraničních konfliktů >2 hPa v reportu 04 | **HIGH** pro existenci jiných timestampů, MEDIUM pro tlakovou věrohodnost | **UNRESOLVED** | Srovnat `pressure` a sousedy, kalibraci ČHMÚ; nepřebírat `barometer` z vadné T |
| C005 | P1 | WH1080 2019–2020 | 267 + 491 `needs_validation` kandidátů | **HIGH** pro prázdné target_time, kvalita po veličinách nejistá | **UNRESOLVED** | Kontrola původu, času, teploty/RH/větru a přítomných tlaků |
| C006 | P1 | WH1080 frozen 2009, 2011 | 100 + 1 201 `frozen_sensor_review`, rozsáhlé konstantní série | **HIGH** pro frozen | **UNRESOLVED** | Blokovat full-row import; pressure oddělit, jen s nezávislým důkazem |
| C007 | P1 | Starý déšť 2009–2013, změna v dubnu 2013 | Raw/interval poměr ~10 před, ~1 po 19. 4. 2013; historické `rainRate` má další změnu | **HIGH** pro změnu režimu | **UNRESOLVED** (×10/×2 nepovolit) | Originální `weewx.conf`, driver, měsíční ČHMÚ, rozlišení sensor vs SW |
| C008 | P1 | Historické větrné hodnoty a směr | Staré `usUnits=17` numericky km/h do dubna 2013, poté m/s; 29 `gust<speed` v produkci | **HIGH** pro jednotkové režimy, MEDIUM pro jednotlivé extrémy | **UNRESOLVED** | Validovaná `sensor_epoch`, QC směru a freeze, ne plošné násobení |
| C009 | P1 | Tlak zdrojů od 2026-03-08 | Pracovní minus GW barometer srpen ~−3,9 hPa; `pressure` ~−12,7 hPa | **HIGH** pro divergence | **UNRESOLVED** | Konfigurace výšky/QFF/QNH, nezávislý ČHMÚ, dohodnout kanonický tlak |
| C010 | P1 | `pm25_1` saturace 2024-09/10 | Live v tomto 2měsíčním UTC okně: 1 401 hodnot >=999,8; 2 125 hodnot >500 | **HIGH** pro saturaci/suspektní extrém | **UNRESOLVED** | QC `SATURATED_OR_SUSPECT`, meteorologie + servis PM |
| C011 | P1 | `radiation` a `UV` extrémy | 2026 model/čidlo: radiace až ~2 248,85 W/m² dle reportu 09 | **MEDIUM/HIGH** pro podezření | **UNRESOLVED** | Ověření zdrojových LOOP/ADC, časování a typ pole |
| C012 | P1 | `soilMoist1` nuly/NULL | 2024-01 nedostupnost, 2025 nuly i při známém signálu | **HIGH** pro rozdílnost nuly/NULL, MEDIUM pro příčinu | **UNRESOLVED** | QC `NOT_INSTALLED`/`NO_SIGNAL`/`FROZEN`, ověřit WH51 |
| C013 | P1 | Venkovní RH 2015–2019 | desetitisíce NULL, opakovaně <=15 %, rozdíl proti LuhaMet | **HIGH** pro deficit a podezřelé hodnoty, ne pro přesnou správnou RH | **UNRESOLVED** | Nezávislá homogenizace podle časových bloků a hardwaru |
| C014 | P1 | T/RH zmrazení leden–duben 2013 | Report 05: 5 doložených 12h segmentů se 144 konstantními body | **HIGH** pro freeze | **UNRESOLVED** | QC invalid/frozen, záloha, nevkládat automatickou interpolaci |
| C015 | P1 | Posunované timestampy (2014–2018) | `pocasi-loucka.eu_old` mnoho milisekund/sekund/minut mimo grid; WH1080 extra | **HIGH** pro posun, MEDIUM pro časovou ekvivalenci | **UNRESOLVED** | Epoch + `interval`, payload identity, conflict-free time matching |
| C016 | P2 | Produkční nuly `rainRate` 2019–2025 | 36 520 párů: production=0, GW1000>0 | **HIGH** pro systematickou ztrátu dat v produkci | V produkci **neopravovat** tímto auditem | Využít provenance existujícího pracovní restore; validovat sémantiku |
| C017 | P2 | Starší kopie `pocasi-loucka.eu_old` od 2022-08 | Jiné T, RH, tlak a rain, částečně vyprázdněná řada 2023 | **HIGH** pro mezizdrojový rozpor | N/A, nekanonizovat kopii | Schéma s definicí fyzického zdroje, nepoužít jako jediný důkaz |
| C018 | P2 | GW1000 falešné impulzy v květnu 2026 | 12. 5. 06:35 131,2 vs 0,5 mm; 16. 5. 23:15 142,8 vs 0,1 mm | **HIGH** pro zdrojový artefakt | Rekonstrukce již obsahuje jiné hodnoty, přesná náhrada nemusí být nezávisle prokázaná | **Nevracet extrémy**, nepřepisovat zdrojové archivy |
| C019 | P2 | Nedostupné starší senzory | WH1080 2009–2020 má historicky pouze placeholder nuly solar/UV/soil | **HIGH** pro nepoužitelnost | N/A | QC `NOT_INSTALLED`, žádné doplňování nul |
| C020 | P2 | Chybějící období 2011-09–2012-02 | Výpadek hlavních archivů bez nalezeného nezávislého originálu | **HIGH** pro nepřítomnost | **UNRESOLVED** | Zobrazit datovou mezeru, nikoli nuly či falešnou interpolaci |

## C. Definice důvěry a publikace

- `diagnosis_confidence`: zda je prokázaná nekonzistence/porucha.
- `replacement_confidence`: zda je doložena konkrétní náhradní hodnota. **Nikdy nepřebírat první hodnotu jako druhou.**
- `technical_status`: `APPLIED_BEFORE` / `QC_ONLY` / `PROPOSAL_ONLY` / `NEEDS_EXTERNAL_EVIDENCE` / `BLOCKED`.
- `approval_status`: všechny C001–C020 **NOT_APPROVED**. Aplikované DONE-* nejsou nové návrhy.
- Přesný seznam `dateTime` pro agregované kandidáty se musí vypočítat z read-only dotazů a exportovat do schvalovacího manifestu; žádný počet z roční agregace není automaticky seznamem schválených SQL UPDATE.

## D. Základní povinné testy

Vždy požadovat `target_time`, `variable`, `old_value`, `proposed_value`, `unit_epoch_id`, `source_time`, `source_database`, `rule_version`, `reason`, `diagnosis_confidence`, `replacement_confidence`, auditní batch a rollback. Žádná změna bez `expected_old_value` (NULL-safe `<=>`), nulových kolizí s předchozími aplikovanými změnami a uložené zálohy. U seskupení s tisíci kandidáty používat schvalovací manifest per-variable, nikoliv `UPDATE ... WHERE YEAR(...)`.

Přímé bezpečné ověřovací dotazy (bez zápisu): [MASTER_QC_READONLY.sql](MASTER_QC_READONLY.sql). Zdrojové reporty: [MASTER_AUDIT.md](MASTER_AUDIT.md), sekce 1.
