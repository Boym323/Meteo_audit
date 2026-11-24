# Změny auditního workspace

## 2026-11-24 — finální audit a migrace

- Ověřen read-only SQL časový řez `dateTime <= 1795541700`; shrnutí rozdílů a 60 auditovaných `NULL_CLEAR` událostí je v `FINAL_DATABASE_AUDIT.md`.
- Přímý screening větru potvrdil 318 případů `windGust < windSpeed`, 29 rozdílů nad 1 km/h, 77 988 nenulových rychlostí bez směru a 6 nulových nárazů.
- Vytvořen živý konzistentní operation-level diff 92 724 řádků. Validátor prošel; všech 60 nových teplotních NULL_CLEAR událostí přesně navazuje na audit; 1 497 audit/current-state neshod zůstává označeno k review. Žádná operace není schválena pro produkci.
- Odděleno databázové schema od izolované MariaDB instance. Aktuální test schema je na server_id=1; tento LXC nemá Proxmox přístup. Přidán fail-closed provisioning postup pro Debian 13 / MariaDB 11.8.6 / server_id 99.
- V dostupném WH1080 archive nalezeno 6 659 platných exact-time směrových kandidátů, včetně 526 prioritních; bez aplikace, protože archivní kopie nejsou nezávislým potvrzením. Dlouhé konstantní běhy klasifikovány jako podezřelé, nikoli automaticky opravované.
- Vytvořena komprimovaná konzistentní MariaDB záloha všech 26 tabulek v `/opt/meteo-audit-artifacts/final-database-backups/`; SHA-256 a oprávnění jsou v `FINAL_BACKUP_RECEIPT.json`.
- Produkce zůstala beze změn. Obnova na skutečně izolované instanci, WeeWX přepočet a celo-migrační rollback zůstávají NO-GO, dokud infrastruktura nezpřístupní samostatný test server.

## 2026-11-24 — import tří vrstev historického tlaku

- Ověřen gzip release SHA-256 `2c111a5f…b9122`, index a 6 157 denních SHA balíčků. V `loucka_reconstruction` byly transakčně uloženy tři oddělené tlakové vrstvy (1 697 621 timestampů), provenance, kvalita, stavy schválení a Q1 ochrana.
- Null-safe shoda staging/cíl: 0 rozdílů; `CHECK TABLE` OK; InnoDB rollback ověřen. `archive.pressure`, produkční DB a WeeWX denní statistiky beze změny. Detail: `reports/2026-11-24-pressure-reconstruction-db-import.md`.

## 2026-11-13 — LuhaMet teplotní holdout 2019–2020

- Read-only train 2015–2017 / test 2019–2020 exact-time transferový screen; správné kvartální UTC mapování enumeruje všechny train roky. Celkem 235 135 train a 192 235 test pairů.
- Přímý reference baseline porazil train-only globální i kvartální bias na celkovém MAE/RMSE; výsledky jsou complete-case transfer diagnostics, ne missing-block validace.
- 959 teplých Loučka/0°C LuhaMet konfliktů zůstává QC neuzavřeno (ER-28); nebyly automaticky vyřazeny.
- Přidány report, SQL, suffstats, summary, limited top-case CSV, scorer, validator a manifest run `20261113T024046Z-f5f9c57e`.

## 2026-11-13 — complete schema columns and indexes

- Read-only `information_schema.COLUMNS` / `STATISTICS` snapshot rozšířen na všech 102 tabulek: 1 410 sloupcových definic, 120 indexových částí, 113 indexů.
- Přidány full CSV exporty, shrnující report, reprodukční SQL, deterministic validator a hash lineage run `20261113T023016Z-e44e4b07`.
- Export popisuje DDL/indexy; fyzické jednotky a hodnotovou kvalitu nevyvozuje.

## 2026-11-13 — information_schema table catalog

- Metadata-only katalog vyjmenoval 102 InnoDB BASE TABLE v šesti schématech; všechny GOALem uvedené history/reference/rain auxiliary tabulky byly nalezeny.
- Přidán CSV, report, read-only SQL, lokální validator a manifestovaný validator run `20261113T022746Z-8de014ca`.
- `TABLE_ROWS` je označen jako přibližný; přesné počty ani data tabulek tímto krokem nebyly ověřeny.

## 2026-11-13 — archive column metadata inventory

- Metadata-only `information_schema.COLUMNS` snapshot pro 6 archive tabulek, 515 definic a 155 názvů; reconstruction/production i dva legacy archivy mají úplnou pairwise definici shodnou; GW1000 a starší WeeWX archivy mají očekávané subsety bez definicových konfliktů.
- Přidán plný CSV export, report rozdílů, read-only SQL a deterministický validator; žádné měřicí řádky nebyly skenovány.

## 2026-11-13 — live production tail snapshot 02:15Z

- Aktualizován bounded read-only tail od reconstruction anchoru: 4 162 produkčních tail řádků do 02:15Z; 4 159 přesných pětiminutových kroků a tři dříve známé 10min mezery. Celkový počet řádků archivu nebyl z nového bounded dotazu odvozován.
- Všechny T/RH/rain/rainRate hodnoty tailu jsou non-NULL; žádný import ani návrh nevznikl.
- Přidány snapshot report, CSV, SQL, lokální validator a úspěšný wrapper run `20261113T022038Z-e8193148`; `findings.json` a `source_inventory.json` dostaly aktuální snapshot.

## 2026-11-13 — první manifestovaný validační běh

- Wrapper etapy N použit nad existujícím CHMI LMT validačním skriptem bez DB přístupu; run `20261113T021639Z-99d92a65` uspěl a jeho log/manifest/hash lineage uloženy v `reports/validation-runs/`.
- Výsledek pouze reprodukuje validaci předchozího artefaktu (730 řádků, oba station checks); nepřidává nové meteorologické závěry.

## 2026-11-13 — Etapa N: audit run checkpoint wrapper

- Přidán lokální wrapper pro běhy, se samostatným UTC run ID, logem a JSON manifestem pro scope/config, kód, zdroje, výstupy, hashe a stav procesu.
- Přidán příklad ne-tajné JSON konfigurace, README návod a dva unittesty (úspěch/selhání); testy, syntaxe a whitespace kontrola prošly.
- Wrapper nemá DB konektor a sám nesandboxuje child proces; DB běhy nadále vyžadují existující SELECT/SHOW-only adapter a bezpečnostní kontrolu příkazu.
- Dosavadní auditní data zůstala beze změny; žádný DB dotaz ani zápis, žádné kandidáty ani zásahy do 2021.

## 2026-11-12

- Založeny MASTER_PLAN, STATUS, findings, decisions, source inventory, blockers.
- Provedena aktuální read-only kontrola seznamu databází, rozsahů přístupných archivů a stavů reconstruction_changes přes Weather MCP.
- Žádný databázový zápis ani změna služby.
- Doplněny čtyři unit testy pro `gap_screening`; první běh odhalil a druhý běh ověřil opravu validace nečíselného roku. Celkem 51 testů prošlo.
- Read-only roční přepočet rain/rainRate nad aktuální pracovní DB; uloženo CSV, SQL a revalidation report.
- Zjištěno, že archivní stav se po CSV exportu 2026-10-30 změnil dalšími aplikovanými dávkami; 484 změn rainRate v roce 2026 je přesně spojeno s poklesem rain>0/rainRate=0 z 633 na 149. Starší rok 2021 zůstává pouze diagnostický.
- Přes historii a první staré hodnoty byl zpětně obnoven stav před exportem; shoduje se 16/16 ročních CSV počtů mimo rok 2021. Rok 2026 staré CSV neobsahuje a jeho hodnota 633 byla ověřena proti oddělenému historickému souhrnu; 2021 vynechán.
- Pro neshody rain/rainRate bez chráněného 2021 vytvořen časový screening: 21 465 řádků v 8 032 skupinách, max 20 400 s. SQL/CSV/report jsou uloženy a metodická nejistota zařazena jako ER-04.
- Aktualizován další krok auditu a stav etap tak, aby odrážely dílčí dokončení a proměnlivý stav zdroje.
- Přeshraniční gap screening opraven z pevného 4 500s lookbacku na přesného předchůdce; znovu agregováno 18 UTC roků. Aktualizován detailní CSV (34 kombinací), roční CSV, report, findings a ER-01. Výsledek 24 523 kandidátních párů, z toho 24 519 nad oběma kroky; 2012 obsahuje doloženou 198denní časovou mezeru přes hranici roku. Žádná příčina výpadku ani počet chybějících slotů z toho nevyvozován.
- Etapa F: doplněn UTC kontext epizod PM2.5 >500 v září 2024 (4 skupiny, nejdelší 446 bodů/37 h 05 min), souběžné RH/srážky/vítr a telemetrie. Bez nezávislé PM reference zůstává SUSPECT/REVIEW_REQUIRED; založena ER-05, bez návrhu korekce.
- Etapa F: rozšířen read-only lightning audit. Po poslední `lightning_distance` (2026-03-07 20:10 UTC) zůstává 67 938 archivních řádků, včetně 179 s nenulovým `lightning_strike_count`; před cutoffem distance také často koexistuje s nulovým count. Sémantika polí nejistá, založena ER-06, bez doplnění/korekce.
- Etapa I: pending staging reconciliován proti pozdějším applied událostem. 54 target-variable kandidátů (13 RH, 2 rain, 39 rainRate) mají 55 post-batch applied událostí; RH blok 2022 přesně navazuje na `humidity-202204-dual-station-v1` a current odpovídá její historii. Založen read-only report; staging zůstal beze změny.
- Etapa H: time-blocked LuhaMet teplotní baseline, train 2022–2023 / holdout 2024, bez outTemp change-log cílů. Konstantní offset snížil RMSE, ale zhoršil MAE a oba ukazatele v UTC Q1/Q4; doložena sezónní nestabilita, ER-07. Report + CSV, bez rekonstrukčních návrhů.
- Reprodukovatelnost teplotního blokového pilotu doplněna o dva read-only SELECTy (celý holdout a UTC kvartály) a strojově čitelný CSV; agregace SQL byly aritmeticky překontrolovány přes vážené kvartální metriky.
- Etapa J: živě revalidován dewpoint po RH změnách v UTC dubnu 2022. Všech 1 077 odchylek >2 °C spadá do 2 194 RH-changed porovnatelných cílů; z 4 875 nezměněných RH cílů 0 odchylek >2 °C, maximum 0,026 °C. V dubnu 3 578 applied RH cílů, žádné dewpoint/heatindex/humidex/appTemp změny. Přidán SQL/report/ER-08; bez přepočtu.
- Etapa J: doplněn inventory downstream odvozenin na 3 578 RH změnových cílech dubna 2022. Potenciální stale hodnoty po non-NULL změně / vymazání a NULL odvozeniny po doplnění RH; bez tvrzení algoritmu či plošné opravy. Založena ER-09, read-only SQL/report.
- Etapa B: interval-aware délková pásma za 18 UTC roků; 24 523 kandidátních gap párů, 824 ≥1h (z toho 61 přesně 1h; přísně >1h je 763), 44 >1d, 5 ≥7d a 1 ≥90d. Zachován přesný předchůdce přes rok 2012. CSV, report, reprodukční SQL a ER-01 aktualizovány; příčina/slot counts nevyvozovány.

- Etapa B pokračování: vytvořen sekvenční event-level katalog 763 mezer přísně >1 h (`gap-events-over-1h.csv`) a reprodukční SQL/report. Hraniční kontrola opravila interpretaci: 824 je počet ≥1 h, zahrnující 61 přesně hodinových párů; přísně >1 h je 763. Aktualizovány STATUS, ER-01, MASTER_PLAN, findings a pásmový report.

- Etapa G/H pokračování: ověřena sousední cadence a `MOD 300` fáze LuhaMet a ILOUKA4. PWS reference ILOUKA4 je typicky posunutá o ~8 s; exact-time join není úplná párovací metoda. Přidán agregační report/SQL a ER-10 pro bezpečné 1:1 časové zarovnání; žádné reference ani cílové záznamy nebyly změněny.

- Etapa B: úplný event-level katalog 24 523 kandidátních gap párů z 216 měsíčních bounded SELECT bloků. CSV reconciliováno po letech a délkách, 0 duplicit, 0 timestamp/threshold neshod; bez aplikovaných změn během běhu. ER-01/02 zachovávají nejistotu očekávaných slotů a příčiny.

- Etapa B metodika: agregováno 1 689 889 sousedních delta/interval dvojic pro ověření sousedních kroků. Zjištěno 4 182 změn uloženého intervalu, 3 732 deltas přesně odpovídajících jednomu kroku, 24 519 nad oběma a 79 pod oběma. Přidán report/CSV/SQL, aktualizovány ER-01, STATUS, MASTER_PLAN a inventory.

- Etapa F pokračování: pressure `altimeter-barometer` rozdíly stratifikovány podle UTC roku a outTemp. Všech 273 párů >5 hPa leží při teplotě <0 °C; všechny párové hodnoty pod 0 °C jsou záporné. Přidány agregační reporty/SQL a ER-03 rozšířena o fyzikální validační otázku; žádné tlakové hodnoty nebyly změněny.

- Etapa G/H continuation: ILOUKA4 exact-time pairing returned only 3 temperature pairs; nearest-grid sensitivity and uniqueness diagnostic found 481 616 unique temperature candidates at 10s, with 280 collision cells (254 in 2023). Added report/annual CSV/read-only SQL and ER-10 evidence. No matching method approved; no training/correction performed.

- Etapa B/C/D: bounded exact-time source/reconstruction reconciliation 2009–2020 found ~207k source timestamps per archive absent in reconstruction and source measurements available for current NULLs. Nearest 300s-grid feasibility has ~146k off-grid rows near an archive row but nontrivial collisions, so no missing-slot/recovery claims. Added report/aggregate CSV/repro SQL and ER-01 evidence; no DB data changed.

- Etapa I source availability follow-up: exact-time current-NULL source values reconciled with the latest recorded history. 203 RH, 129 rain, and 129 rainRate distinct targets are latest applied NULL clearings (sensor-failure/counter-artifact batches); 0 outTemp candidates have a change event. This rules out simple source restoration for cleared values. Added report/SQL/findings/inventory; no correction batch created.

- Etapa D/I: přesné kopie `outHumidity` byly porovnány na 30 391 společných zdrojových cílech s NULL/no-history. 30 385 přesných shod a šest konfliktů v roce 2019 (39,10–55,37 p. b.; teploty i intervaly shodné). Přidán problémový CSV/report a ER-11; ponecháno REVIEW_REQUIRED, bez obnovy či DB zápisu.

- Etapa C/I pokračování: read-only exact-time annual source-copy screening pro `outTemp` bez change-history. `old_weewx` a `weewx_WH1080` se shodují přesně na 8 965/8 965 společných cílech; rozpad 2009–2020 a min/max uloženy v CSV/reportu + reprodukční SQL. Závěr je dostupnostní lead, nikoli nezávislá validace/oprava.
- Doplněna unit/cadence kontrola stejných `outTemp` source kandidátů: všech 8 965 párů je `usUnits=17`, `interval=5` v obou zdrojích. Přidán samostatný read-only SQL a závěr do reportu/checkpointů; rozdíl source `usUnits=17` vs rekonstrukční `16` stále vyžaduje historickou WeeWX interpretační kontrolu.

- Etapa C/I: roční source-copy kandidáti `outTemp` rozšířeni o UTC měsíční screening 2013. V červenci 18 záporných hodnot (17× −0,6 °C, 1× −9,6 °C) v 4h45m bloku; kopie se shodují, ale nezávislost neznámá. Vytvořen malý problémový CSV, read-only reprodukční SQL a ER-12; žádná korekce. Opraven scope neighbor souhrnu: původních 30/25 bylo za všech 5 640 ročních kandidátů; pro 18 červencových záporných kandidátů je ±300s check 0/1/0. Bounded ±24h endpointy jsou dostupné pro všech 18 a source−linear baseline residual je −18,93 až −7,60 °C; přidán kontextový CSV a reprodukční SQL.

- Etapa F: nezávisle reconciliovány PM2.5 součty a délka epizody. 2 149 bodů `>500` platí za 2022–2026, z toho 2 126 za 2024; 1 401 bodů `>=999.8` výhradně 2024. Hlavní 446bodová skupina má endpoint span 37h05 (445 kroků) a nominální slot coverage 37h10 (446×5min). Reporty opraveny, SQL přidáno, bez závěru o správnosti senzoru.

- PM2.5 pokračování: reconciliován denní průměr 958,3 vs 980,85 jako lokální `Europe/Prague` den vs UTC den (oba 288 vzorků, všechny >500), epochově validováno `zoneinfo`. Přidán day-basis CSV a rozšířeno reprodukční SQL; předchozí souhrny nyní explicitně označují timezone.
- Etapa C/I follow-up ER-12: nearest endpoints všech 18 červencových bodů porovnány s oběma source archivy a change-history. Všech 36 endpointů se shoduje napříč třemi archive řadami, 0 endpoint history events; source záporné hodnoty jsou o 7,60–18,93 °C pod jednoduchou lineární kontextovou baseline. Důkaz je podpůrný, nikoli nezávislý ground truth. Přidáno reprodukční SQL, report/ER-12 a strukturované findings.

- Etapa G/H/C follow-up: staženy a hashem ověřeny veřejné denní ČHMÚ TMA/TMI soubory pro Vizovice/Kladnou-Žilín k ER-12. Pro 2013-07-01 jsou TMI 4,5/4,4 °C, ale přesné `DT`/`TIMEFUNC` okno, stanovištní metadata a vzdálenost nejsou ověřeny; jde pouze o regionální denní kontext. 10min/hodinový veřejný historický archiv začíná 2018. Přidány zdrojová cache/licence, manifest, bounded subset, skript, reference inventory a ER-12 podklady. Žádné DB změny.

- Etapa G/H ER-12 provenance nuance: ověřena oficiální stránka stanice ČHMÚ Vizovice. Denní data mohou mít historicky ne-kalendářní okna; uvedené 21–07 SEČ je pro minimální přízemní teplotu a nelze je přiřadit TMI vzdušné teplotě. Report, ER-12 a inventáře nyní tuto hranici explicitně uvádějí.

- Etapa G/H follow-up ER-12: oficiální CHMI API metadata potvrdila polohu/výšku Vizovic (49.22297 N, 17.84361 E; 313 m) a Kladné-Žilín (49.08420 N, 17.79250 E; 329 m); raw response SHA-256 jsou v kompaktním metadata JSON. Souřadnice čidla Loučky nalezeny nebyly, proto se vzdálenost nepočítá. Findings, inventář, report, README a ER-12 aktualizovány; žádná DB změna.

- Etapa C/G/H: dokončena kvartální offset validace LuhaMet 2022–23 → 2024. 104 271 exact-time holdout párů; RMSE 1,3799 → 1,3384 °C, ale MAE 1,0825 → 1,0891 °C. Pro 10 414 mrazových párů se MAE/RMSE zhoršila 1,1208/1,3173 → 1,1680/1,3684 °C. První chybný dotaz s hranicemi 2024 použitými pro trénink odmítnut; opravený explicitní UTC epochový SQL reconciliován podle kvartálních počtů. Přidán report/CSV/SQL, ER-02, findings/inventory/checkpoint; žádné korekce ani DB změny.

- Etapa C/D: bounded read-only freeze/plateau screening přes UTC 2019–2020 (přesný 300s cadence, interval=5, ≥144 bodů) našel osm `outHumidity=100%` epizod, nejdelší 64h45 elapsed, a žádnou 12h outTemp plateau. Source archivy končí před všemi epizodami; saturace není diagnóza závady. Přidány report/CSV/SQL, ER-13, findings/inventory/checkpoint. Bez změny DB a bez korekcí; 2021 vynechán.

- Etapa D/G: přesný timestamp join LuhaMet nad 8 RH plateau epizodami 2020 pokryl všech 2 760 řádků. Pět epizod má regionální RH 83–95 % bez nul; ve třech epizodách jsou LuhaMet nulové RH (21/778, 30/485, 89/154). Doplněn referenční CSV/SQL a opravená interpretace v reportu/ER-13: regionální vlhkost podporuje plausibilitu, ale QC nul a lokální shoda zůstávají nejasné. Žádný nearest-time join ani korekce.

- Etapa C/D/I/G: pět historických 12h freeze bloků z 2013 rozšířeno na celé souvislé 5min běhy (T 15h30–24h05; RH 17h10–24h05). Přesné source hodnoty se shodují s rekonstrukcí; třetí epizoda má jeden timestamp pouze v rekonstrukci, chybí v obou source kopiích; 0 change events. Denní ČHMÚ minima/maxima pouze kontextují. Přidán ER-14, report/CSV/4 read-only SQL, checkpoint a inventory; žádné změny DB.

- ER-11 pokračování: stažena a hashována oficiální ČHMÚ 2019 hodinová E (vapor pressure) a 10min T pro dvě blízké stanice. Deterministický skript vytvořil 4 přesné regionální E/T páry a 12 odvozených tlakových kandidátů. Hourly CHMI kontext leží mezi konfliktními RH variantami a není lokální ground truth; LuhaMet má v cílovém okně výpadek. Report/manifest/ER-11/MASTER_PLAN/STATUS aktualizovány; žádná RH obnova ani DB zápis.

- Etapa A/B pokračování: přes `information_schema` read-only cross-schema SELECT byly zpřístupněny tři produkční archivy navzdory odmítání názvů v přímém MCP database targetu. Exact rows/time/unit/intervals a key variable coverage zreconciliovány. Hlavní produkce má 4 100 pětiminutových záznamů po konci rekonstrukce; tři 600s mezery mají přesné absent-grid kandidáty, které nejsou ani v GW1000/reconstruction. Přidán live inventory report/CSV/SQL, findings/inventory/blocked note/checkpoints aktualizovány; žádný import ani write.

- Rozšíření produkčního live inventory: při opakovaném snapshotu 21:11 UTC se archiv posunul na 1 683 903 řádků / max 21:10 UTC a novější interval na 4 101 bodů. Reconciliováno 4 100 sousedních párů (4 097×300s, 3×600s). Hrubý range screening nového úseku: bez zvolených širokých rozsahových/sentinel flagů (PM2.5 max 243); žádná tvrzení o kalibraci nebo správnosti. Přidán range-screen CSV a aktualizované checkpointy; DB zůstává read-only.

- ER-06 source follow-up: read-only cross-archive exact-time join nově zpřístupněného `pocasi-loucka.eu_GW1000` odhalil 5 269 `lightning_distance` hodnot (1–40; 70 distinct, usUnits=16/5min), které jsou na stejných časech NULL v hlavní produkci i rekonstrukci a nemají change event. 4 441 doprovází count=0 a 661 count=NULL. Zdrojový konflikt byl zdokumentován; review required, nic se neobnovuje.
- Live production snapshot se během auditu posunul na 21:15 UTC (1 683 904 řádků; 4 102 po konci rekonstrukce). Re-run reconciliován v reportech/CSV/JSON/STATUS; 4 101 sousedních hran má pořád přesně 3 desetiminutové mezery. Novější řádky mají broad range screen bez flagů; DB zůstává read-only.

- ER-06 metodika: doplněn primární Ecowitt GW1000 protocol v1.6.4, WH57 manual a WeeWX GW1000 driver v0.6.3 source. Dokumentují daily cumulative device count, per-period `lightning_strike_count` delta a `last` distance accumulation; poslední detekční čas není ve čtyřech archive schématech uložen. Interpretace zero-count distance se proto zpřesnila jako kompatibilní s přetrvávající poslední distance, nikoli jako důkaz stale hodnoty. Historická config/provenance zůstává otevřená; bez importu.

- Pokračování etapy B po načtení dodatku GOAL: přidán deterministický výřez 44 gap delt ≥24 h, s review flagy pro ER-01/ER-02 a zvláštním označením 2018 Q1/2021. Pro pět delt ≥7 d read-only timestampový join potvrdil shodné záznamy v obou historických archivech (3 561/5 344/4 812/1/2 263 společných timestampů). Interpretace omezena na source-only lead; žádná obnova, slot extrapolace ani DB zápis. Nový checkpoint v STATUS/MASTER_PLAN, otázka zachována v EXPERT_REVIEW_REQUIRED.
- Source-overlap follow-up nejdelší mezery: agregované exact-time porovnání zjistilo plnou shodu `outTemp`/rain/rainRate/jednotek/intervalu v 3 561 společných záznamech; RH souhlasí ve všech 297 společných non-NULL párech, ale 3 264 RH jsou pouze v old_weewx a NULL ve WH1080. Availability/provenance konflikt přidán do ER-11; zdroj nebyl vybrán a nic se neobnovuje.
- Dlouhé gap source follow-up pro `outTemp`: nalezeny zero-heavy zdrojové bloky ve WH1080 (2016-01/02: 5 343/5 344; 2017-05: 4 810/4 812; mrazový 2017-01: 2 261/2 263; 2011–2012: 3 264/3 561). `old_weewx` má v těchto případech převážně NULL; společné nenulové endpointy souhlasí. Přidány cadence/zero-run agregace, reprodukční SELECTy a ER-01/02/11 expert review; nuly nebyly klasifikovány jako jistý sentinel a žádná data se nemění.
- Rozšířen long-gap `outTemp` source screen o přesné nula-run segmenty, agregovanou source availability a deduplikovaný cross-archive join na `reconstruction_changes`: 15 981 source timestampů, 0 `outTemp` events. Zero-heavy bloky označeny jako podezřelé, nikoli potvrzený sentinel; mrazové okno 2017-01 vyžaduje zvláštní odbornou revizi. Přidány repro SQL/CSV a updates ER-01/02/11; bez DB zápisu.
- Přidán lokální `scripts/validate_long_gap_followup.py` pro reconciliaci 24 523-row katalogu, 44/5/1 gap subsetů, zdrojových timestampů, zero-run agregací a nulové change-history. `findings.json` a `source_inventory.json` obsahují agregovaný source-zero finding; oba JSON jsou ověřovány parserem.
- Zero-heavy gapy doplněny o exact-time LuhaMet regionální kontext: 2017-01 2 254 párů, 1 803 teplot pod nulou (−19,0 až 3,4 °C) souběžně s 2 252 zdrojovými nulami; 2017-05 4 601 párů, všechny reference kladné (5,5 až 25,5 °C) souběžně s 4 599 nulami; 2016 žádné exact pair. Vše `reference_only`; bez tolerancí/ground truth. Přidán report/SQL, rozšířena evidence a lokální verifier.
- Etapa A/B timezone/DST ověření: DB session/global `SYSTEM`, system label `CET`, local snapshot UTC+1; system `FROM_UNIXTIME` round-trip sedí pro letní/zimní epochy a vybrané DST skoky/repetice. `CONVERT_TZ` pro Europe/Prague i SYSTEM vrací NULL; UTC epoch workflow zachovat a lokální agregace dělat přes Python `zoneinfo`. Přidán B-TZ-01 blocker, SQL/report a finding/inventory metadata; žádná data neměněna.
- Validace dnešního pokračování: `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_gap_screening.py'` (4/4 passed), `scripts/validate_long_gap_followup.py`, JSON parsers a `git diff --check` bez chyb.
- Unit/provenance etapa A pokračování: `usUnits` distributions znovu agregovány v šesti archivech; reconstruction/prod jsou jednotně 16, historické source archives jednotně 17. Standardní WeeWX 5.5 mapping určuje možný analýzu-only převod rain/rainRate ×0,1 a speed ×3,6 při 17→16; historický custom config neznámý, data raw a beze změny. Přidán archivní jednotkový report/CSV/SQL a aktualizována inventární dostupnost cross-schema produkčních archive.
- Live produkční inkrement 21:15→22:00Z: devět nových řádků, 8/8 300s cadence, `usUnits=16`, 12 kontrolovaných sloupců non-NULL a široký range screen bez flagů. Snapshot/report/CSV/SQL přidány; bez importu.
- Etapa B pokračování: pro 44 dlouhých delt byla dopočtena endpoint fázová shoda s 300s a čistě podmíněná 5min slotová aritmetika (97 048 mezilehlých slotů při předpokladu nepřerušeného provozu). Výsledek je explicitně označen jako triáž, nikoli missing-slot count; přidány reprodukční skript, report/CSV a agregované finding/inventory checkpointy.
- Etapa A pokračování: read-only přesné počty rekonstrukčních batch/candidate/history a RH/reference/rain backup/QC tabulek; opravené rozlišení přesných COUNT(*) od přibližného `information_schema.TABLE_ROWS`. Přidán aktuální inventory report a reprodukční SQL; 2021 zůstává diagnostický a nebyly provedeny žádné zápisy.
- Etapa I: nová chronologická latest-event kontrola současného archivu (86 256/86 256 NULL-safe shod, 0 chybějících řádků/neshod) pro outTemp, RH, rain a rainRate. Chráněný 2021 explicitně vynechán, Q1 2018 samostatně označeno interim. Přidán reprodukční SELECT/report a finding/inventory; účetní shoda není vydávána za meteorologickou validaci.
- Etapa B: kompletní měsíční UTC epoch LAG inventář 2009-03–2026-10 (212 měsíců) a roční agregace; 1 689 890 rows / 1 689 889 hran reconciliováno; izolováno šest měsíců bez řádků 2011-09–2012-02 s neklasifikovanou příčinou; Q1 2018 interim, 2021 diagnostický. Přidány bounded SQL template, verifier, reporty/CSV a B-EPOCH-01 blocker.
- Etapa B: agregované striktní cadence run segmentation po UTC rocích; 1 661 559 exact-step hran v 7 299 ročních segmentech. 6min metadata nevytvořila stabilní 6min hranu; 5min převažuje, dvě 30min hrany. Výsledek označen jako kandidátní režimy, nikoli provozní epochy; rozšířena ER-01.
- Etapa B pokračování: exact predecessor/successor check všech 2 090 `interval=6` řádků; žádná sousední delta 360 s, 1 703 předchozích a 2 020 následujících 300s delt odpovídá sousednímu řádku. Sémantika zůstává nejasná; ER-01 rozšířena, bez změn dat.
- Etapa D/I: kompletní 3 734-row RH April-2022 decision table NULL-safe reconciliována s current archive a latest changes: 3 493 odhadů, 85 invalidací, 156 unresolved; bez missing archive row. Účetní shoda neznamená nezávislou validitu; derived values nepřepočítány.
- Etapa C/H: nový exact-time temporal confirmation block 2025 (train 2022–24/test 2025) porovnal raw LuhaMet, globální a kvartální offsety na 98 681 holdout párech, včetně 13 510 mrazových; offsety celkově zhoršily MAE/RMSE, bez modelovaných gap hodnot. Report/SQL/aggregate CSV/lokální summarizer; ER-02/07 rozšířeny.
- Etapa I pokračování: read-only reconciliation všech 272 pending kandidátů (20 batchů/9 veličin) proti archive a change-history; 58 kandidátů/59 applied eventů po vlastním batchi, 2 cíle bez archive row, Q1 2018 interim (8) a 2021 bez kandidátů. Doplněny ER-15 (mrazový source-only outTemp, cross-archive aggregate) a ER-16 (rain/counter sémantika); report/CSV/scope/SQL/verifier aktualizovány. Žádné staging, cancel, apply ani zápis.
- Etapa F: úplná read-only konzistenční triáž `windSpeed`/`windGust` mimo Q1 2018 a samostatně diagnostický 2021; z 226 striktních gust<speed případů 197 je jen ≤0,01 km/h, 29 významných (2014/2016/2017), 21 >5 km/h. Všech 226 odpovídá produkčnímu archivu; jen 2/29 významných případů mají source-copy overlap. ER-17, aggregate report/CSV/SQL/verifier přidány; žádné zápisy.
- Etapa B/F: aktualizovaný read-only snapshot odhalil produkční tail 4 123 timestampů po posledním rekonstrukčním řádku (14 d 7 h 50 min), se třemi 600s deltas; radiace/UV screening nalezl 76 drobných nočních radiation hodnot bez UV a čtyři vysoké denní UV cases pro ER-18. Byly opraveny epochové hranice popisu wind reportu; výsledky pokrývají úplný reconstruction archive do 2026-10-29. Přidány tail/solar SQL, reporty, CSV a lokální verifier; bez DB zápisu/synchronizace.
- Etapa F: read-only audit `windDir` dostupnosti při kladné rychlosti (77 988 targetů): 6 652 early source-concordant úhlů, 228 bez zdroje, 11 historických konfliktů nula-vs-poškozený úhel, 71 097 chybějících úhlů 2020–2022 bez běžně dostupné source hodnoty; 2021 diagnosticky. Přidán ER-19, annual/monthly/speed-band/source-group CSV, SQL a deterministic validator; bez obnovy.

## 2026-11-13 — Diagnostika rainRate/rain

Přidán read-only poměrný screening pro Q1 2018 interim a 2021 diagnostic-only, report/SQL a lokální agregátní konzistenční kontrola. Sémantická nejistota zůstává pod ER-04; screening nevytváří opravy ani kandidáty.

## 2026-11-13 — Follow-up sekundárních senzorů

Přidán agregační rozsahový screening indoor/extra/soil kanálů a přesná current-main source reconciliation pro out-of-range případy. Extrémy zůstávají SUSPECT/REVIEW_REQUIRED; ER-20 eviduje chybějící channel map a raw packet lineage.

## 2026-11-13 — technické RSSI/signal/battery kanály

Přidán read-only inventář 17 technických kanálů a časové rozdělení `ws80_sig`; významová změna či mapovací změna zůstává nevyřešena (ER-21). Stavové a bateriové kódy nebyly dekódovány bez dokumentace.

## 2026-11-13 — celohistorická kontrola dewpointu po RH změnách

Rozšířena stale-derivative triáž z dubna 2022 na všechny aplikované RH cíle mimo 2021. Shoda dewpointu s předchozí RH je velmi silná; historický vzorec/provenience ale zůstává expertní otázkou ER-08/09. Bez přepočtu.

## 2026-11-13 — RH dependency cascade napříč historií

Rozšířen dubnový availability check na všech 20 712 aplikovaných RH targetů mimo 2021; changed/cleared/filled typy porovnány s odvozenými kanály. ER-09 rozšířena, bez přepočtu.

## 2026-11-13 — interní dewpoint dependency control

Přidáno 433 955 řádků formula-consistency screen `inDewpoint` vůči aktuálním vnitřním T/RH. Výsledek slouží jako vnitřní konzistence, nikoli nezávislá reference nebo důkaz historického algoritmu.

## 2026-11-13 — odvozeniny po doplnění outTemp

Zmapována přítomnost deseti downstream kanálů na všech 10 127 aplikovaných NULL→non-NULL outTemp targetech mimo 2021. Odvozeniny nebyly doplňovány; historická dependency/provenience je ER-22.

## 2026-11-13 — rain Phase A history revalidation

Reconciliovány tři existující rain backup sady proti původní batch historii, pozdější supersession a current archive. 19 cílů je správně NULL po explicitním review eventu; žádná korekce nebyla opakována.

## 2026-11-13 — chráněný rok 2021: diagnostický snapshot

Přidán SELECT-only roční snapshot kontinuity a dostupnosti primárních/sekundárních veličin. Výsledky jsou diagnostické, explicitně bez korekčních návrhů; mrazy a dlouhé mezery navázány na ER-01/02.

## 2026-11-13 — produkční tail follow-up

Aktualizován read-only snapshot hlavního produkčního archivu do 2026-11-13 00:00 UTC. Oproti předchozímu checkpointu přibylo 12 tail řádků; rekonstrukce zůstává na původním high-water marku.

## 2026-11-13 — Q1 2018 applied history/current reconciliation

Přidán interim status report a cross-tab batch labelů vůči UTC cílovým měsícům. Zjištěný rozdíl proti počtům v GOALu zdokumentován v ER-23; bez jakéhokoli zásahu do DB nebo souběžné aplikace.

## 2026-11-13 — July-2021 rain history vs. reconstruction artifact

Rozšířena diagnostická kontrola 146 targetů s latest applied NULL eventem; current archive nuly souhlasí se samostatným CHMI reconstruction artifactem, ale nemají navazující logged target event. Provenance konflikt zdokumentován v ER-24; bez write nebo opravy chráněného 2021.

## 2026-11-13 — konsolidovaný audit rekonstrukční historie

Znovu agregovány event counts, opakované target-variable pairs, latest-event/current shody a pending-stage overlaps. Nový report výslovně zachycuje rozsah neprošetřených event detailů; July-2021 rain rozšířen na 1 497 targetů a UTC hranice dřívějšího subreportu opravena.

## 2026-11-13 — provenance field coverage v change history

Spočítána vyplněnost source archive/time/value, reason a batch metadat nad celou reconstruction_changes; 1 092 source/target timestamp offsetů a 243 chybějících rainRate source_value jsou zdokumentovány bez závěru o správnosti. Sémantika source timestampů vedena v ER-25.


## 2026-11-13 — source-row provenance follow-up

- Přidán přímý read-only source row report, agregovaný CSV, reprodukční SQL a deterministický validator pro 61 002 externích change events.
- Rozšířen ER-25 o 551 self-source RH eventů bez přesného řádku v aktuálním reconstruction archive.
- Aktualizovány MASTER_PLAN, STATUS, findings a source inventory; žádný zápis databáze ani korekce.


## 2026-11-13 — all-archive screening dlouhé mezery

- Rozšířeno bounded SELECT ověření nejdelšího 198denního gapu na všech šest dostupných archivů. Potvrzeno nulové vnitřní pokrytí hlavních production/GW1000/reconstruction archivů a přesný rozsah historické kopie včetně RH availability asymetrie.
- Přidán agregovaný CSV, metodický report, read-only SQL a deterministický validator; ER-01/02 a inventáře aktualizovány. Žádný DB zápis ani rekonstrukce.


## 2026-11-13 — RH reference availability 2015–2017

- Přidán bounded exact-time LuhaMet RH availability audit podle UTC epoch hranic; 38 582 cílů má reference-only nonzero RH source a žádnou předchozí RH history event.
- Starý report null counts byl reconciliován jako historický snapshot vůči aktuálnímu měsíčnímu coverage souhrnu. Otevřena ER-26 pro validační metodiku; nevznikly návrhy ani fill.


## 2026-11-13 — chronological RH reference transfer test

- Přidán exact-time blocked train/test baseline pro lokální RH proti LuhaMet; měřil direct transfer, global bias a quarter bias. Výsledek ukazuje vysokou přenosovou chybu i po offsetu; ER-26 rozšířena.
- Vytvořen agregovaný report, CSV, reprodukční read-only SQL a lokální validator. Žádné imputace ani DB zápisy.


## 2026-11-13 — RH vapor-pressure/phase holdout

- Rozšířen blokový RH transfer test o WMO pure-phase water/ice saturation vapor-pressure transformation na stejném observed holdoutu. Jednoduchý transfer neobstál; ice/water citlivost zaznamenána v ER-26.
- Přidány report, agregované CSV, read-only SQL a validator včetně zdrojů fyzikálních rovnic. Bez imputace a DB write.

## 2026-11-13 — empirická kontrola denního ČHMÚ SRA

- Z již uložených CHMI JSON pro rok 2018 byla extrahována veličina SRA10M pro Vizovice a Kladnou-Žilín; stažena byla pouze dvě denní CSV SRA a uložen manifest zdrojů s hashi.
- Deterministické porovnání dvou 24hodinových oken silně empiricky podpořilo `(DT, DT+24h]`; oficiální význam DT/TIMEFUNC a přiřazeného dne zůstává nevyřešen. ER-27 eviduje podklady, alternativy, limity a konkrétní otázku pro odborníka.
- Přidány report, párové/agregované CSV, reprodukční skript a validátor, zdrojový inventář a nález. Bez dotazu či zápisu do DB a bez korekcí; 2021 nebyl součástí analýzy.

## 2026-11-13 — historický rain/rainRate range screen

- Opravený časově explicitní UTC-year SELECT shrnul rozsah 17 ročních bloků mimo chráněný 2021: záporné rain/rainRate nenalezeny.
- Deskriptivní horní případy byly omezeny na pět časů a exact-time ověřeny proti starému kumulativnímu counteru, GW1000 i change history. Výsledek nepředstavuje nezávislou meteorologickou validaci ani kandidáty na opravu; ER-04 rozšířena.
- Uloženy dva read-only SQL, agregát a case CSV, report a lokální verifier. Validator prošel; bez databázových zápisů.

## 2026-11-13 — exact-source rain NULL availability

- Bounded annual SELECTs reconciled 2009–2020 NULL targets against both legacy sources and latest rain change history: 11 780 exact targets, 129 documented applied invalidations and 11 651 without rain history.
- Q1 2018 follow-up found 10 091 source-exact NULL targets; ten positive source values are isolated by 300-second zeros, disagree in status with current rainRate, and have no target history. Exact archive copies are not independent; ER-04 records the driver/raw packet question.
- Added source/history annual and monthly aggregates, alternative archive cross-check, ten-case CSV, reusable SQL and validator. No candidates, DB writes, or 2021 scope.

## 2026-11-13 — source-neighbor shape pro rain NULL

- Roční LAG/LEAD agregace oddělila sousední mokré běhy 2013 od jednorázových positive-source hodnot mezi nulami v 2016–2018; souběžně reconciliovala aktuální rainRate status.
- Rozšířena ER-04 o neznámý driver/reset/export význam a požadavek na packet/config evidence. Bez klasifikace jako chyba nebo náhrada.
- Přidán report, CSV, SQL template a rozšířen validator; bez DB write, fill nebo návrhu kandidátů.

## 2026-11-13 — 2013 rain counter epoch follow-up

- Exact-time UTC LAG porovnal consecutive 300-second legacy rain deltas s reconstruction a zachytil prudký posun shody od nulové v Jan–Mar přes 3/34 v dubnu k téměř úplné shodě v květnu–prosinci. Výsledek je metodicky podmíněný a neinterpretuje raw součty jako úhrny.
- ER-04 doplněna o konkrétní epochový konflikt a otázku k historickému WeeWX driver/config/packet evidence. Žádný kandidát, korekce ani DB zápis.
- Přidány agregovaný report, měsíční CSV, read-only SQL a lokální validator; chybné timezone/CASE iterace jsou v reportu označeny jako zahozené.


## 2026-11-13 — 2013 rain reset-aware diagnostic

- Rozpad záporných 300s legacy rain kroků našel 137/177 přesně na UTC půlnoci. Reset-aware hypotéza nepomáhá vysvětlit Jan–Apr neshody (kladné post-reset hodnoty jsou proti current zero/NULL), zatímco May–Dec dřívější delta shody zůstávají.
- ER-04 doplněna o reset cadence, alternativy a požadavek na historical driver/packet evidence. Hypotéza nebyla použita jako hodnota ani pravidlo.
- Uloženy měsíční agregace, read-only SQL a deterministic validator; bez DB zápisu a korekcí.


## 2026-11-13 — ČHMÚ denní SRA podle místního středního slunečního času

- Oficiální zdroje potvrzují 24h odečet v 07:00 LMT přiřazený předchozímu dni; historické CSV schema však přímo nevykládá DT/TIMEFUNC.
- Deterministický longitude-adjusted test na SRA/SRA10M 2018 zlepšil shodu proti DT+24h: 328/328 dnů Vizovice a 333/334 Kladná-Žilín s endpointem 05:50 UTC následujícího dne; všech 260 mokrých denních hodnot souhlasí.
- ER-27 zůstává otevřena pro oficiální export mapping a zákaz lokální pětiminutové imputace trvá. Přidány report, detail, summary, hash manifest, reprodukční skript a validator; DB beze změny.

- Etapa C/H: OLS s reference teplotou a denní/roční harmonikou, train 2015–2017, holdout 2019–2020. Citlivostní model zlepšil RMSE (2,7565 proti 2,8520 °C), ale zhoršil MAE (1,5890 proti 1,4865 °C); bez reference-zero/hot konfliktů zůstává MAE horší (1,4875 proti 1,3737). Pouze agregované sufficient statistics a score; žádná rekonstrukce. ER-07/ER-28.


- Etapa H: bloková holdout diagnostika OLS 2019–2020 po 1/7/30 dnech. 202 723 target slots, 192 235 reference dostupných (94,826 %); 10 488 chybí exact LuhaMet řádek, včetně souvislých 2019 bloků bez coverage. OLS horší v MAE a bodových kvantilech mimo observed-freeze subset; není způsobilá k rekonstrukci. Přesný percentile SQL timeout nahrazen 0,1 °C histogramem. ER-07/28.

- Etapa C/H: synthetic masking pilot interpolation 1/6/24h na nezměněných targetech v týdnu 2019-07-01–08. MAE/RMSE se zhoršuje s horizontem: 0,322/0,475; 1,488/1,872; 5,231/6,744 °C. Jeden letní týden; bez rekonstrukčních návrhů.

- Etapa C/H: masked-block endpoint interpolation across 8 quarters 2019–2020; 1/6/24h. 19,714 blocks. Interpolation beat exact LuhaMet and harmonic OLS in quarterly MAE for 1h/6h; pooled MAE/RMSE 0.225/0.369 and 0.914/1.383 °C. 24h interpolation worsened to 3.036/4.656 °C; P90/P95 8.85/10.95. Conditional complete-window diagnostic; no correction candidates.

- Etapa B/C: source concordance případ 2019 interval=6. Reconstruction/current production/GW1000 sdílejí −2 °C na 04:40Z; starší archivy row nemají. Sousední 5min hodnoty se shodují napříč archivy. Hodnota ponechána, interval semantics ER-01.


## 2026-11-13 — block extrema interpolation follow-up

- Added eight read-only quarterly extrema SQL queries (2019–2020) and 24-row/3-row aggregate outputs for 1h/6h/24h masks.
- Added deterministic validator reconciling counts with the existing 19,714 seasonal blocks.
- Result: interpolation attenuates masked block maxima/minima, most strongly for daily 24h maximum (clean-sample MAE 6.22 °C, worst block 19.57 °C); logged as diagnostic only and added ER-07.
- No DB writes, correction proposals, Q1 2018 reads, or 2021 reads.


## 2026-11-13 — secondary sensor audit consolidation

- Added a partial evidence-based secondary sensor audit report and rebuilt 11 observed-epoch coverage aggregates from the existing monthly snapshot.
- New numerator and denominator exclude protected year 2021; builder and reconciliation validator included.
- Consolidates pressure/wind/solar/PM2.5/soil/lightning findings with explicit evidence limits and open expert review IDs. Stage F remains partial; no new DB access or corrections.


## 2026-11-13 — reference data inventory

- Added a consolidated reference inventory for LuhaMet, ILOUKA4, cached CHMI series, and ERA5/ERA5-Land catalog candidates.
- Refreshed reference station registry via SELECT; recorded unavailable coordinates instead of estimating distances.
- Built manifest-derived CHMI cache catalog: 34 distinct local files, 113,681,963 bytes, SHA-256 verified; two boundary files unavailable (HTTP 404).
- Official ERA products were catalog-checked only; no login, credential use, or download. Stage G remains partial pending Loučka coordinates and matching/source review.

## 2026-11-13 — exact production archive_day inventory

- Read-only aggregate SELECT counted all 78 metric `archive_day_*` tables in the main production schema: exactly 6,104 rows per table, with identical first/last `dateTime` key epochs.
- Added aggregate CSV, reproducible SELECT union, deterministic validator, and consolidated inventory/plan/status checkpoints.
- This verifies row/key coverage only; local-day semantics, summary-field units/validity, `_metadata`, and auxiliary tables remain open. No database writes.

## 2026-11-13 — exact reconstruction auxiliary counts refreshed

- Exact `COUNT(*)` snapshot for all 17 non-archive reconstruction tables; `reference_observations` has 1,652,638 rows, exactly equal to station counts for LuhaMet and ILOUKA4.
- Reconfirmed 24 batches / 365 candidates, 112,772 applied+reverted change events, and 3,734 RH-2022 decision rows with grouped subtotals.
- Added exact-count/status CSVs, SELECT-only SQL and deterministic reconciliation validator; pending Q1 state remains live. No DB writes.

## 2026-11-13 — bridge annual cadence segments

- Indexed bounded read-only samples around 17 UTC year boundaries detected 13 candidate joins among 7,299 year-local exact-cadence fragments; four boundary edges remain irregular (2012, 2014, 2017, 2022).
- Deterministic validator derives 7,286 joined sequences and preserves 2018 as interim, 2021 diagnostic, and 2026 partial.
- This is cadence segmentation only, not operational-epoch or expected-slot classification; ER-01/02 remain open. No DB writes.

## 2026-11-13 — production outTemp daily-summary crosscheck

- Compared 6,103 complete local-day `archive_day_outTemp` summaries with bounded raw production archive aggregates using DST-aware local-day keys and end-of-interval `(start,end]` membership.
- 2009–2025 min/max match; in 2026, 86/316 daily maxima differ by >0.1 °C (max 0.38 °C), with stored extrema times often absent from archive rows, while daily count/sum/sumtime reconcile.
- Added annual/monthly/control CSVs, reproduced SELECT, validator and ER-29 expert-review request. No archive or summary changes/rebuild.


## 2026-11-13 — crosscheck denních extrémů RH/větru/srážek

- Read-only roční a měsíční agregace porovnala 6 103 dnů na veličinu pro outHumidity, rain, windSpeed a windGust.
- Historické min/max 2009–2025 přesně souhlasí; v 2026 od března vznikají konfliktní minima RH/větru, rain odchylka je ojedinělá 0,02.
- Přidán reproducible SQL, CSV, report a validator; ER-30/B-DAILY-SUMMARY-02 vedou k procesní/source review. Bez DB zápisů či rebuildů.


## 2026-11-13 — souhrnný audit časové kontinuity

- Z předchozích read-only snapshots sestaven `reports/TIME_CONTINUITY_AUDIT.md`; nevznikl nový DB scan.
- Nový validator reconciliuje měsíční/roční edges, 24 523 gap kandidátů, intervalové vztahy, cadence run fragments, 17 cross-year hranic a 44 dlouhých delt.
- Explicitně zachováno, že hypotetické pětiminutové sloty nejsou missing-record count a dlouhé zimní mezery vyžadují ER-01/02 review.


## 2026-11-13 — konsolidované teplotní a modelové reporty

- Přidán `reports/TEMPERATURE_AUDIT.md` s source/freeze/plateau/model/daily-summary důkazy a přesnými omezeními; neprohlašuje všechny temperature-like senzory za auditované.
- Přidán `reports/MODEL_VALIDATION_REPORT.md` s chronologickými transfery, reference-zero citlivostí, syntetickými missing blocks a extrémovým tlumením.
- Konsolidační i existující specializované lokální validátory PASS; žádný nový database access ani rekonstrukční návrh.


## 2026-11-13 — konsolidovaný RH audit a RH modelové výsledky

- Přidán `reports/HUMIDITY_AUDIT.md` pro rozsah, zdrojové konflikty, exact-time reference coverage, applied history, plateau a RH/dewpoint cascade.
- `reports/MODEL_VALIDATION_REPORT.md` rozšířen o chronologické RH holdouty a vapor-pressure voda/led citlivost.
- Nový bundle validator a existující RH availability/transfer/cascade/dewpoint validátory PASS; žádný nový database query ani correction proposal.

## 2026-11-13 — pokračování po RH checkpointu

- Ověřeny existující lokální balíčky validátorů pro směr větru, sekundární senzory, RH a teplotní/modelové souhrny; JSON inventory soubory parsují a `git diff --check` je čistý.
- `STATUS.md` zaznamenává návaznost bez nového DB snapshotu. Rozpracovaná epochová identifikace sekundárních kanálů a odborné source/provenance otázky zůstávají otevřené.

## 2026-11-13 — kontrola rekonstrukčního tailu

- Read-only SELECT potvrdil, že `loucka_reconstruction.archive` nemá záznamy po 2026-10-29 15:10 UTC, zatímco produkční tail je doložen do 2026-11-13 00:00 UTC.
- Uloženy report, reprodukční SELECT a aktualizované source/findings inventáře; bez synchronizace či databázových změn.

## 2026-11-13 — produkční tail k 05:00 UTC

- Ověřeno 60 nových produkčních řádků od půlnoci do 05:00Z přes bounded read-only aggregate; základní cadence/unit a dostupnost vybraných polí zapsány.
- Přidán SQL/report checkpoint a aktualizovány source/findings inventáře. Rekonstrukce se nesynchronizovala.

## 2026-11-13 — návrh append-only postupu pro produkční tail

- Cross-schema read-only agregát porovnal 4 195 produkčních řádků po reconstruction anchoru; žádný timestamp se nepřekrývá s reconstruction archive, tři interní 600s delty zůstávají nevyplněné.
- Zdokumentován podmíněný append-only postup pro případné budoucí samostatné schválení. Nevznikly kandidáti, synchronizace ani write.

## 2026-11-13 — konsolidovaný audit srážek

- Přidán `reports/RAIN_AUDIT.md` se syntézou rozsahů, NULL/source availability, counter epochy 2013, historie Phase A a diagnostiky chráněného 2021.
- Přidán deterministický `scripts/validate_rain_audit_bundle.py`; konsolidace i specializované kontroly prošly. Bez nového DB query, kandidátů či zápisů.
- Hashovaný běh konsolidace uložen v `runs/20261113T050901Z-2c8c16a9/manifest.json` (14 inputs, 3 outputs, succeeded).

## 2026-11-13 — mapa odvozených veličin

- Přidán `reports/DERIVED_VARIABLE_AUDIT.md` a deterministická CSV mapa schema coverage pro všech 21 požadovaných derived fields.
- Bundle validator kontroluje šest schémat i RH/outTemp/inDewpoint aggregate evidence; formule/producers zůstávají neprokázány, bez lokálního WeeWX configu/runtime.
- Etapa J byla zabalena do hashovaného běhu `runs/20261113T051428Z-699180d2/manifest.json` (7 vstupů, 4 výstupy, succeeded); historické formule zůstávají neověřené.

## 2026-11-13 — kvalita dat a odborná review fronta

- Přidán `reports/QUALITY_CLASSIFICATION_AUDIT.md`, sidecar JSON schema a strojový registr 31 ER skupin s rizikovými tagy pro dlouhé výpadky, mrazy, inverze, modelovou nejistotu a source conflicts.
- Validator ověřuje kompletní coverage ER headingů i ochranu Q1 2018/2021. Neprovádí plošnou row-level klasifikaci a nemění databázi.
- Strojový review register a quality sidecar návrh ověřeny hashovaným během `runs/20261113T051940Z-d2d744d3/manifest.json` (succeeded).

## 2026-11-13 — offline simulátor korekcí

- Přidán `src/meteo_audit/simulation.py`, lokální JSON CLI a 12 synthetic tests pro concurrency conflicts, NULL/insert/update, preserve invariants, duplicate/idempotency/dependencies a injected failure.
- `reports/LOCAL_CORRECTION_SIMULATION.md` jasně odděluje lokální rollback od skutečného DB dry-run; žádný Weather MCP dry-run, staging ani write se neprovedl.
- Hashovaný synthetic test run: `runs/20261113T052721Z-7ded254d/manifest.json` (12 passed, 5 source inputs, 3 outputs).
- Celá offline unit test suite prošla: 65 testů / 9 souborů; hashovaný běh `runs/20261113T052813Z-117938da/manifest.json`.

## 2026-11-13 — konsolidovaný inventář historických návrhů

- Reconciliovány známé Phase A aplikace/supersession, July 2021 externí SQL evidence a pending staging 2026-11-12.
- 360 rain targetů má current/latest-event účetní shodu; 19 později změněno z nuly na NULL. July 2021 zůstává nereprodukovaný externí zásah.
- 58/272 pending cílů má pozdější applied historii; 8 Q1 2018 interim; 0 roku 2021; 2 source-only bez archive row.
- Přidány `reports/PROPOSAL_INVENTORY.md` a CSV. Žádný DB write, staging ani nové correction payloads.

## 2026-11-13 — secondary `extraTemp2` cross-archive census

- Bounded SELECT porovnal 790 `extraTemp2>80` targetů v pěti archive schématech. Exact matches má pouze production copy (790/790; 260 distinct); GW1000/older archive nemají nenulové hodnoty v cílech, staré sensor archives nemají rows.
- ER-20 a secondary follow-up report doplněny jako source-lineage uncertainty, bez tvrzení o fyzické neplatnosti a bez korekcí.
- Validator PASS; hashovaný checkpoint `runs/20261113T053312Z-a2539854/manifest.json`.

## 2026-11-13 — soil temperature source-lineage follow-up

- Jediný `soilTemp1<-40` cíl má hodnotu jen v production archive; dva další cílové rows jsou NULL a dva staré archives nemají row. Starší schémata nemají `soilTemp5/6`.
- ER-20, sekundární report a agregovaný soubor aktualizovány; bez quality decision či změn DB.
- Validator PASS, hash checkpoint `runs/20261113T053439Z-b27b1d21/manifest.json`.

## 2026-11-13 — offline audit CLI

- Přidán `scripts/meteo_audit.py`: allowlisted validator execution through the hash checkpoint wrapper and SHA-256 comparison for same-scope runs; README documents safe use and current limits.
- 3 CLI unit tests PASS. Two repeated secondary-channel validation runs succeeded; digest comparison stored in `reports/2026-11-13-cli-repeatability-comparison.json`.
- No DB access or writes; Stage N remains partial.

## 2026-11-13 — předběžná readiness matrix

- Z monthly temporal/null snapshots postavena matice 198 rok/kanál buněk (2009–2026 × 11 kanálů) s row denominatorem, NULL coverage, observed-month coverage a známými issue tags.
- Výsledek je explicitně předběžný: 138 review-required, 60 not-available-in-archive snapshot, 0 ready; 2021 chráněný a 2018 interim. Bez falešného expected-slot jmenovatele či odhadovaných correction counts.
- Builder/validator PASS; hash checkpoint `runs/20261113T054113Z-6fef5655/manifest.json`. Úplná readiness pro všechny veličiny zůstává otevřená.

## 2026-11-13 — povinný report bundle a master synthesis

- Ověřeno všech 18 požadovaných reportových názvů; vytvořeny transparentní aliases pro precipitation, derived, quality a simulation, plus master audit, consolidated corrections a next steps.
- Přidán machine-readable `reports/required-report-inventory.json`; deterministický bundle validator PASS.
- Hashovaný CLI běh `runs/20261113T054445Z-fa03f924/manifest.json`; final ZIP zůstává odložen kvůli neuzavřenému auditu.

## 2026-11-13 — bounded secondary sensor snapshot 2026

- Read-only annual-range aggregate: 86,877 rows through 2026-10-29, 42 sensor/diagnostic fields with NULL/non-NULL/min/max; stored CSV/JSON and reproduction SQL.
- ER-06 strengthened: 47,599/47,599 `lightning_disturber_count` values fall in 2026 Unix epoch range; `lightning_noise_count` exactly equals strike count at 179/179 available rows; `lightning_energy` all NULL. Interpretation remains mapping-review only.
- Local aggregate validators PASS; DB unchanged.

- Revalidován povinný report inventory po přidání lightning evidence; všech 18 požadovaných reportů zůstává přítomných.
- Lightning/secondary evidence hash-checkpoint `runs/20261113T054916Z-1d7fb3af/manifest.json` (8 output hashes verified).

## 2026-11-13 — lightning field cross-archive validation

- Cross-schema SELECT reconcilioval všech 47,599 epoch-like disturber targets s main production copy; GW1000 source fields jsou NULL ve 46,745 available rows a dvě starší archives nemají rows.
- Přidány tři bounded examples, SQL a validators; ER-06 nyní obsahuje explicitní alternatives/question. Nebyla provedena oprava ani přejmenování.
- Hashovaný CLI checkpoint lightning evidence: `runs/20261113T055222Z-7a40db36/manifest.json`; všech 6 output hashes ověřeno.

## 2026-11-13 — 2026 soil temperature outlier context

- Lokálně agregováno 31 bounded soilTemp5/6 extreme targetů: 10/21, žádné sousední pětiminutové případy, 31/31 shoda s main production copy; kontextové soil channels shrnuty.
- ER-20, secondary sensor report a master synthesis aktualizovány, hodnoty zůstávají `REVIEW_REQUIRED`.
- Validator a hash checkpoint `runs/20261113T055512Z-6fe4054e/manifest.json` PASS.

## 2026-11-13 — cross-year secondary sensor coverage

- Srovnáno 42 polí v 102,946 archive rows za 2025 a 86,877 partial 2026 rows. Deset polí je 2025 all-NULL a v 2026 přítomných; first-non-NULL onsets jsou v březnu a květnu.
- ER-06/20/21 rozšířeny; observed onsets výslovně nejsou vydávány za fyzická data instalace. Bez korekcí.
- Deterministické 2025/2026 aggregate validators PASS.
- Přidán bounded read-only SQL pro first/last non-NULL epoch 10 fields; annual 2025/2026 comparison hash checkpoint `runs/20261113T060026Z-806eeade/manifest.json`.

## 2026-11-13 — závazný dodatek GOALu a coverage 2024–2026

- Načten `/opt/meteo-audit/GOAL_ADDENDUM.md` a jeho závazné požadavky začleněny do `MASTER_PLAN.md`; původní omezení zachována.
- Navázáno na existující cross-year práci, bez opakování již hotových analýz; roční availability rozšířena o 2024 pro stejných 42 polí.
- Agregované počty: 104 935 řádků (2024), 102 946 (2025), 86 877 partial (2026). Coverage bundle PASS.
- Checkpoint `runs/20261113T060353Z-b6c9f8cd/manifest.json` succeeded; žádné chybějící výstupy. STATUS potvrzuje začlenění a pokračování.
## 2026-11-13 — roční dostupnost všech číselných archive polí

- Dokončeno 18 sekvenčních UTC year-range SELECT agregátů pro 77 numerických polí, 2009–2026; 1 386 field-year záznamů.
- Ověřena aritmetika NULL/non-NULL/archive rows a shoda 42 polí s existujícími 2024–2026 snapshots.
- SQL/builder/validator, CSV/JSON/MD availability a 77řádkový observed-year span přehled uloženy; validátor PASS.
- Hashovaný checkpoint `runs/20261113T061456Z-b0d5f74f/manifest.json`; bez databázových změn a bez correction candidates pro 2021.
## 2026-11-13 — exact secondary archive concordance

- 42 polí, exact timestamp join production/reconstruction: 104 935 rows (2024), 102 946 (2025), 86 877 (partial shared 2026 window).
- 0 row/interval/unit mismatches, 0 unequal non-NULL values, 0 one-sided values. Interpretace zůstává shared copy, nikoli nezávislá validace.
- Report, aggregate data, SQL, builder a validator uloženy; ER-06/20/21 aktualizovány.

Hashovaný cross-archive checkpoint: `runs/20261113T061927Z-5b2c588d/manifest.json` (succeeded, 7 výstupů, SHA-256 ověřeno).
## 2026-11-13 — měsíční NULL coverage 77 archive fields

- Dokončeno měsíční faktické pokrytí 77 numeric polí v 216 UTC měsících; 16 632 field-month řádků.
- Všechna měsíční row/NULL/non-NULL totals se shodují s 1 386 ročními souhrny; no-row měsíce odlišeny od all-NULL.
- Readiness report zůstává výslovně předběžný; availability matrix sama nevytváří `READY` status.
## 2026-11-13 — RH long-gap triage 2022

- Daily audit našel 30denní all-NULL `outHumidity` run 2022-01-30 až 2022-02-28; 8 632 z 8 634 target rows mají přesný LuhaMet RH source timestamp.
- Únorových 8 058 NULL cílů nemá reconstruction RH history event. Q1 RH je non-NULL jen 1 715/25 238 rows.
- Otevřena odborná revize ER-31; ref data zůstávají `reference_only`, žádný model/candidate/write nebyl vytvořen.



## 2026-11-13 — P3 short-gap ESTIMATED proposals

- Vytvořeno 107 interpolovaných návrhů pro 56 skutečných 10–60min gap epizod v 2019–2020 po read-only filtru na cadence, units, history, endpoint meteorologii.
- Přidány endpoint/context metadata, non-additive exclusions, 3 MCP-compatible proposal batches (50/50/7), selection SQL a lokální simulation s before/after scope counts.
- Deterministický package validator PASS; 4 jiné priority zůstávají blocked with zero candidates. Žádný databázový zápis, staging, MCP apply ani publikace.

- 2026-11-13: Added row-level reviews for 20 residual strict-copy source-only records (2013/2016/2017/2020); all REVIEW_REQUIRED pending source/sensor provenance. Corrected UTC year attribution in 207,182 source-only aggregate. Added official-source license/provenance applicability review; no publication, ERA downloads, or database writes.
- 2026-11-13: Completed 103 read-only chunks comparing all 44,406 WH1080 source rows inside conditional gap slots against old_weewx by primary variable; added zero/RH conflict stratification, exclusion gates, validators, progress and expert evidence requests. No correction promoted.
- 2026-11-13: Added episode-level run-length analysis for the 42,298 zero outTemp rows in gap overlay candidates; 2,247 zero runs across 2,085 gap events, with longest nonprotected windows individually documented. No RESTORED/ESTIMATED promotion; Q1 2018 diagnostic-only.

- 2026-11-13: Closed stage A4 with exact row/time/all-nullable-field/audit-time/state aggregates across 17 auxiliary reconstruction tables. Added exact 2021 snapshot timestamp-delta evidence (seven reconstruction-only zero rows; 0 reverse delta) and Phase A backup date-scope anomaly; 2021 remains diagnostic-only. Added deterministic validator and run checkpoint; no archive tail refresh or DB writes.
- 2026-11-13: Resolved provenance of seven auxiliary 2021 rain-snapshot-only timestamps by exact current-archive and change-history SELECTs; found seven rain-only rows and 21 applied rain events (bootstrap→unknown→CHMI estimate). Diagnostic reporting only; no write.


## 2026-11-13 — owner-attested lineage and historical edits

- Added `SOURCE_LINEAGE_OWNER_STATEMENT.md` and separate `OWNER_ATTESTED` entries in `source_inventory.json` and `findings.json`; facts are not presented as independently verified.
- Updated source-first policy/code for historical transformations, possible pre-audit removal, timestamp duplicates, and multi-channel stuck-sensor evidence. Restored eligibility now requires explicit historical-transformation resolution and removal screening.
- Updated HUMAN_INPUT_REQUIRED so unidentified historical backups are not the sole clearance route; appended targeted 2012 and renumbered 2018 source-only evidence requests.
- Row-screened 8,424 2012 off-grid source-only timestamps: 4 offsets, 8,424 occupied nearest targets, 8,421 projected slots, 3 double-source collision slots, 50 source-zero temperatures, and 6 focused copy anomaly rows. All held; no operations created.

## 2026-11-13 — větrné epochy a source-only evidence

Doplněny roční exact-timestamp windSpeed/windGust/windrun poměry z read-only dotazů 2009–2020, cílené hranice 2013, interval mismatch counts, strojová data a SQL reprodukce. Rozšířena etapová evidence; bez DB zápisů.

## 2026-11-13 — 2013 source-only RESTORED pilot

Vytvořen balíček pro tři chybějící T/RH řádky a jeden NULL outTemp field 2013-07-08; 7 operací, tři fyzické partial rows, jedna update. Deterministická lokální simulace a manifestní validace PASS. Záměrné historické odstranění bylo zváženo; provenance MODERATE s jasným limitem neznámého merge/cleaning původu. Bez DB přístupu/zápisu.

- 2026-11-13: Hardened the synthesized report builder to preserve verified checkpoint addenda; isolated clean-workspace rebuild retained the latest ER-37 scope in all three summary reports. No database access or writes.

- 2026-11-13: Mapped specific period/field publication impacts and evidence requirements for five BLOCKS_FINAL_PUBLICATION expert groups; strengthened the register validator. Remaining K4 mapping stays open.

- 2026-11-13: Corrected ER-32 and P3 independent-review language so the superseded v2 count 24/83 cannot be mistaken for active; current v2.1 status remains 21 ESTIMATED / 86 REVIEW_REQUIRED.

- 2026-11-13: Added deterministic global active-package deduplication; 29 active operations, 29 unique timestamp/variable targets, no duplicates, batches <=50 and protected periods excluded.

- 2026-11-13: Built validated archive readiness availability baseline for 1,386 field/year cells (77 fields × 18 years); no availability-only READY labels, 2018/2021 safeguards retained.

- 2026-11-13: Added qualified read-only six-archive annual availability for 11 core fields, 2009–2020 (792 cells). Found equal newer-gateway yearly row counts but 37 non-NULL availability differences; no value-quality claim.

- 2026-11-13: Sliced saved exact-pair GW1000/GW3000 aggregates for 2009–2020; confirmed shared rowset but major pressure/altimeter value divergence. No new DB query.
## 2026-11-13 — A26 availability checkpoint

Added all-numeric-field annual availability for the three newer merged archives, UTC years 2009–2020. The 3,220,903 archive-row/year records (overlapping across databases) and 3,012 field-year cells are summarized in JSON/CSV/MD; 84 bounded read-only SQL files plus builder and validator are included. No quality or restoration status is inferred. Year 2021 was not queried; Q1 2018 remains protected.

## 2026-11-13T17:50:35Z — v3 independent review and v4 checkpoint

- Corrected active P3/2013 validator commands, per-archive 2020 evidence, two explicit 2020 review holds, package reasons, cadence and uncertainty metadata.
- Active counts: 63 operations (42 RESTORED, 21 ESTIMATED), 54 timestamps, 52 insert rows, 11 update operations.
- v4 clean extraction PASS. v3 preserved immutable. No approval, dry-run, staging, DB write or application.
- Added bounded read-only extraction CLI for stage N4 after v4; no live query and validation pending.

## 2026-11-13T17:58:42Z — 2014 source-only episode evidence

- Reviewed 120 timestamps and 12 fields in a 600-second off-grid June episode. Outdoor fields are constant zero/null; surrounding temperatures are 15.6 and 21.7 C; merged archive omits the block.
- Recorded suspected sensor-stuck/historical-removal classifications; no correction proposal created.

## 2026-11-13T18:01:54Z — stage N4

- Added bounded SELECT-only archive extraction CLI and docs; three offline unittest checks passed. Actual database execution was not attempted because local protected connection configuration and MariaDB client are unavailable. Stage N set COMPLETED_WITH_LIMITATIONS.

## 2026-11-13T18:06:01Z — full 2014 source-only outTemp cohort

- Expanded review from 120 shared rows to all 1,071 source-only timestamps. All source outTemp values are zero; one current target conflicts at 16.2 C, 1,070 targets are absent. No proposals created.

## 2026-11-13T18:11:31Z — stage O availability matrix

- Built an 1,386-cell annual readiness baseline for all 77 numeric fields across 18 years. 673 cells remain REVIEW_REQUIRED, 713 are NOT_AVAILABLE in the archive-year snapshot; no READY certification.


## 2026-11-13T21:21:58Z — O4 availability/readiness closeout

- Synchronizována 77polová × 18letá readiness matice s ročním zdrojovým snapshotem a aktivním registrem; celkem 1 386 buněk a 64 aktivních návrhů.
- 673 buněk zůstává REVIEW_REQUIRED, 713 NOT_AVAILABLE a nula READY. NOT_AVAILABLE není interpretováno jako důkaz odstávky senzoru.
- Přidán O4 closure report a deterministický validator; O4 uzavřeno COMPLETED_WITH_LIMITATIONS, O5 zůstává otevřené.
- Databáze nebyla dotazována ani změněna; bez stagingu, dry-runu a publikace.


## 2026-11-13T22:33:03Z — D5 2014 RH midpoint pilot

Added one RESTORED/MODERATE outHumidity update proposal at 1401550800 after read-only source/neighbor/history review across six archives. Added package-local frozen evidence, batch contract, validator, simulator, and exclusion disposition; active registry updated to 65 operations. No database write, staging, MCP dry-run, approval or application.
# 2026-11-24 — Finální databázový audit a migrace

- Přidány `FINAL_DATABASE_AUDIT.md`, `WIND_QUALITY_REPORT.md`, `FINAL_MIGRATION_MANIFEST.json`, `FINAL_BACKUP_RECEIPT.json`, `FINAL_MIGRATION_TEST_REPORT.md` a `FINAL_GO_NO_GO.md`.
