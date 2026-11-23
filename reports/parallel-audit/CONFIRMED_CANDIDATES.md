# CONFIRMED_CANDIDATES — registr ověřených problémů a návrhů další práce

**Verze:** 2026-10-30 · **Syntéza:** [MASTER_AUDIT.md](MASTER_AUDIT.md)  
**Pozor:** „potvrzený kandidát“ znamená **potvrzenou anomálii/datovou nekonzistenci**, nikoli ověřenou opravenou hodnotu. Ve sloupci „náhrada“ je `UNRESOLVED`, pokud neexistuje externě podložená numerická náhrada. **ŽÁDNÝ Z NÍŽE UVEDENÝCH NOVÝCH KANDIDÁTŮ NENÍ SCHVÁLEN K UPDATE.**

**Aktualizace 23. 11. 2026:** C002 již nemá 28 otevřených databázových rozdílů `GW1000.rainRate>5` proti nulové rekonstruované hodnotě. Všechny 28/28 nyní přesně odpovídají zdroji i zaznamenanému `applied` auditu dávky `rainrate-2023-2024-wet-source-review-v1`. [Read-only důkazy](C002-rainrate-resolved-readonly-20261123.md). Tato shoda neprokazuje fyzikální pravost vysokých intenzit a nic nového neschvaluje. Původní část registru je historický stav k 30. 10. 2026.

**Aktualizace Fáze A 23. 11. 2026:** původních 360 aplikovaných oprav `rain` není správné kontrolovat pouze proti původní nule: 19 z nich bylo 12. 11. 2026 legitimně supersedováno dávkou `rain-2010-2011-phaseA-unknown-null-review-v1` (`old=0` → `new=NULL`, protože pravý lokální úhrn je neznámý). Kontrola napojení auditu i současného archivu vyšla 19/19, zbývajících 341 rain odpovídá původní nule. [Read-only doklad](phase-a-supersessions-readonly-20261123.md). **NULL nikdy neměnit automaticky na 0**.

**Historická diagnostika C001 23. 11. 2026 (nyní odloženo):** odchylky 1 077 dewpointů >2 °C proti výpočtu z *nově rekonstruované* RH na živých datech stále existují; jejich uložené hodnoty odpovídají naopak výpočtu ze *staré RH*. Viz [live read-only C001 report](C001-dewpoint-stale-readonly-20261123.md). Zastarávání odvozeniny je silně potvrzeno; náhrady dál nejsou autorizované.

**Rozhodnutí vlastníka 23. 11. 2026:** `dewpoint` je odvozená veličina počítaná WeeWX, proto C001 **není blokující opravná kandidatura** a jeho individuální numerické opravy se v této etapě **nevytvářejí**. Fokus zůstává na primárních měřeních (T, RH, srážky atd.). Po dokončení rekonstrukce se samostatně ověří a spustí dobový/reprodukční přepočet odvozenin nad historickým archivem, včetně nenulových starých hodnot; samotné generování reportů nebo `rebuild-daily` nenahrazuje přepočet sloupce `archive.dewpoint`. Do té doby zachovat [read-only důkaz C001](C001-dewpoint-stale-readonly-20261123.md) bez SQL UPDATE.

**Celý tlakový archiv 23. 11. 2026:** Read-only audit [pressure-2009-2026-chmi-readonly-20261123.md](pressure-2009-2026-chmi-readonly-20261123.md): 198 175 chybějících pressure, 135 990 alespoň s přímou hodnotou ze starších kopií, 62 185 bez přímého zdroje. Externí ČHMÚ datové zdroje Holešov/Mošnov jsou nalezené a dostupné ke stažení, ale **CSV nebyly numericky parsované/porovnané**, tedy žádný kandidát není externě potvrzený. WH1080 a old_weewx jsou pro C004 75 074× identicky duplicitní; old_weewx má velký chybný posun od dubna 2019 a GW kopie jiné tlakové redukce od roku 2024. Bez přepisu dat.

**Forenzní tlakové zlomy 2013/2019 (23. 11. 2026):** [nový read-only report](pressure-epoch-forensics-2013-2019-20261123.md) zpřesnil epochu `barometer`: **8. 8. 2013 v 15:30–15:40 UTC** +15,9 hPa v pracovním archivu a **26. 4. 2019 v 14:45 UTC** +25,400 hPa během 5 min ve WH1080 oproti stále původnímu old_weewx; WH station `pressure` se přepnul až v 14:50. Mezi lednem 2018 a dubnem 2019 měsíční ČHMÚ `barometer−P_hm` rezidua lineárně driftovala vůči Holešovu o −5,58 a Mošnovu o −5,50 hPa/rok. To dokládá více kalibračních/senzorových epoch, **ne konkrétní hardware příčinu**; bez dobových konfigurací/raw logů ji nelze dokázat. Kandidátní per-field SQL náhrady zůstávají 0; žádná plošná korekce.

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
| C001 | **ODLOŽENO — odvozená veličina** | `dewpoint` po RH 2022-04 | Potvrzené zastaralé odvozeniny (původní read-only nález 1 077 odchylek >2°C; detail v [C001 reportu](C001-dewpoint-stale-readonly-20261123.md)) | **HIGH** pro stale derived | **NEPŘIPRAVOVAT náhradní per-field batch v issue #26** | Po dokončení primárních T/RH hodnot provést řízený přepočet odvozených veličin ve WeeWX nad archivem; běžné generování nových záznamů není retroaktivní a samotný `rebuild-daily` nemění uložený `archive.dewpoint`. Před spuštěním ověřit konfiguraci a režim přepočtu existujících non-NULL hodnot. |
| C002 | P0 historicky; **datová divergence již odstraněna** | rainRate v letech 2023–2024 | Původně 13 + 15 GW1000 intervalů >5 cm/h s nulou v rekonstrukci; aktuálně všech 28/28 shodných se zdrojem a aplikovaných v auditu | **HIGH** pro historický rozpor | **Fyzikální správnost špiček stále UNRESOLVED** | **NEOPAKOVAT UPDATE**; viz [read-only ověření 23.11.2026](C002-rainrate-resolved-readonly-20261123.md); zvlášť lze řešit meteorologickou validitu vysokých intenzit |
| C003 | P0 | `lightning_noise_count` a `lightning_disturber_count` | 2026: 179/179 shod noise=strike; disturber podobný UTC epoch | **HIGH** pro chybnou/nejistou sémantiku | Nejde o numerickou DB náhradu | Prověřit raw JSON, opravit mapper v odděleném code PR |
| C004 | P1 | `pressure` – celý historický archiv 2009–2026, zvláště 2016–2018 | 198 175 NULL, 135 990 s alespoň jednou numerickou kopií, 75 074 WH1080 source 2016–2018; ČHMÚ PR #89 + WH pilot PR #92: v 2018 ~−23hPa deficit na nezávislých referencích. [Forenzní důkazy](pressure-epoch-forensics-2013-2019-20261123.md): skok 2013-08-08 +15,9hPa; 2019-04-26 14:45 UTC +25,4hPa v `barometer`, 14:50 ve WH `pressure`; trend 2018–2019 −5,5hPa/rok. | **HIGH** pro změny epoch a historický drift; **příčina (HW/SW) neověřená** | **UNRESOLVED/NOT_APPROVED** | Neprovádět hromadný WH import ani +23hPa. Dohledat dobové `weewx.conf` a raw/servisní logy; testovat samostatné kalibrační epochy na dvou ČHMÚ a holdoutu. Oddělit skutečné měření od odhadu. |
| C005 | P1 | WH1080 2019–2020 | 267 + 491 `needs_validation` kandidátů | **HIGH** pro prázdné target_time, kvalita po veličinách nejistá | **UNRESOLVED** | Kontrola původu, času, teploty/RH/větru a přítomných tlaků |
| C006 | P1 | WH1080 frozen 2009, 2011 | 100 + 1 201 `frozen_sensor_review`, rozsáhlé konstantní série | **HIGH** pro frozen | **UNRESOLVED** | Blokovat full-row import; pressure oddělit, jen s nezávislým důkazem |
| C007 | P1 | Starý déšť 2009–2013, změna v dubnu 2013 | Raw/interval poměr ~10 před, ~1 po 19. 4. 2013; historické `rainRate` má další změnu | **HIGH** pro změnu režimu | **UNRESOLVED** (×10/×2 nepovolit) | Originální `weewx.conf`, driver, měsíční ČHMÚ, rozlišení sensor vs SW |
| C008 | P1 | Historické větrné hodnoty a směr | Staré `usUnits=17` numericky km/h do dubna 2013, poté m/s; 29 `gust<speed` v produkci | **HIGH** pro jednotkové režimy, MEDIUM pro jednotlivé extrémy | **UNRESOLVED** | Validovaná `sensor_epoch`, QC směru a freeze, ne plošné násobení |
| C009 | P1 | Tlakové divergence od 2024 (GW1000 kopie vs pracovní archiv) | Source GW kopie mění `barometer-pressure` ~51,4 → 44,4 (2024) → 39,4 hPa (2026), zatímco pracovní archiv ~48–53 hPa podle sezóny; mean pracovní minus GW pressure 2023 +0,878 / 2024 −2,676 / 2025 −6,310 / 2026 −11,602 hPa | **HIGH** pro změnu redukčního režimu zdroje, **příčina stále neověřena** | **UNRESOLVED** | Dobová výška a driver, porovnat s ČHMÚ Holešov P_hm, [celohistorický tlakový audit](pressure-2009-2026-chmi-readonly-20261123.md); GW není univerzální kanonický pressure source. |
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
