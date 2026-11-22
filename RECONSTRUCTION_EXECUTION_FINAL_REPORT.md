# Rekonstrukce archivu Loučka – závěrečná zpráva aplikační fáze

Stav: **COMPLETED_WITH_DEFERRED_RAIN_OPERATIONS**
Dokončeno (UTC): 2026-11-14T17:29:15Z

Tato zpráva uzavírá pouze aplikaci schválených návrhů finálního auditu v1.1 v uvedeném rozsahu. Celý historický archiv není označen za kompletně rekonstruovaný ani certifikovaný. Analytický GOAL zůstává uzavřený.

## Výsledek

- Zbývajících schválených 314 nesrážkových field operations bylo aplikováno v deseti samostatných dávkách.
- Spolu s dříve aplikovanými osmi událostmi je ověřeno **322 field operations: 301 RESTORED a 21 ESTIMATED**.
- V celé aplikační fázi vzniklo **311 fyzických řádků**. Nová fáze vytvořila 310; dřívější událost 135133 vytvořila jeden řádek. Tři řádky z pilotu 2013 každý obsahují outTemp i outHumidity; tyto skupinové INSERT hodnoty nejsou šest samostatných řádků.
- Z 322 operací je 314 INSERT field operations a osm UPDATE field operations. Fyzický počet řádků není počtem field operations.
- Všechny nové fyzické záznamy mají `usUnits=16`, `interval=5`. U INSERT řádků byly nezadané meteorologické veličiny NULL.
- Auditní ID všech 322 operací tvoří souvislý jedinečný rozsah **135126–135447**, všechny `state=applied`. Každý klíč timestamp + variable i jeho hodnota, old/new value, source database/time/value a MCP-normalizovaný důvod byly porovnány s payloadem. Jednoznačný seznam událostí je v exekučním registru a evidence souborech.

## Deset nově aplikovaných dávek

| Dávka | Klasifikace | Operace | Nové fyzické řádky | Auditní ID | SHA-256 payloadu | Dry-run a výsledek |
|---|---:|---:|---:|---|---|---|
| `p3-v2-1-estimated-01-exec-v12` | ESTIMATED | 21 | 21 | 135427–135447 | `db8e7fbae165c452346c829d36eee392f802d64bfb84b8413a0847a741f6851e` | Fresh MCP dry-run | `applied=21`, `unchanged=0`, `verified=21`, `replayed=false` |
| `restored-source-only-2013-jul8-01-v1-exec-v12` | RESTORED | 7 | 3 | 135134–135140 | `8519da6071cd51a5ba20d8e28d991e7d28628b874e6e8ccfcd99c9c628b6ad32` | Prior MCP dry-run; current state rechecked | `applied=7`, `unchanged=0`, `verified=7`, `replayed=false` |
| `restored-source-only-2020-isolated-outtemp-01-v1-exec-v12` | RESTORED | 27 | 27 | 135141–135167 | `5a0cfd32dc1a38b4b38ba0f6798aae201269eeb1f970d22492fb1e14bec1feac` | Prior MCP dry-run; current state rechecked | `applied=27`, `unchanged=0`, `verified=27`, `replayed=false` |
| `restored-2020-march-outtemp-v2-001-exec-v12` | RESTORED | 4 | 4 | 135168–135171 | `3239f25f958c01c1422f8065fce7ec9cc3efd8d74db5dc75cb0ac003f712d889` | Prior MCP dry-run; current state rechecked | `applied=4`, `unchanged=0`, `verified=4`, `replayed=false` |
| `restored-2022-august-outtemp-01-v1-exec-v12` | RESTORED | 50 | 50 | 135172–135221 | `81cb95bb2a22bde562ff5618df5c472c9e738405994a868ace1d0f251e797684` | Fresh MCP dry-run | `applied=50`, `unchanged=0`, `verified=50`, `replayed=false` |
| `restored-2022-august-outtemp-02-v1-exec-v12` | RESTORED | 15 | 15 | 135222–135236 | `c98e511d241c1fc411c9dcec7c209d12fec4ab56e726fb1f7eb45993fa99fa7f` | Fresh MCP dry-run | `applied=15`, `unchanged=0`, `verified=15`, `replayed=false` |
| `restored-2023-may-outtemp-01-v1-exec-v12` | RESTORED | 50 | 50 | 135237–135286 | `f27759b3ed0ec1b0f49a849abc6fce10641b7f1e654dd7773bed3b4c2bcc39da` | Fresh MCP dry-run | `applied=50`, `unchanged=0`, `verified=50`, `replayed=false` |
| `restored-2023-may-outtemp-02-v1-exec-v12` | RESTORED | 50 | 50 | 135287–135336 | `e4f13f875976d15c2d4d526845ddbefdf75ea89ce676862a29b544ab6cdea5a9` | Fresh MCP dry-run | `applied=50`, `unchanged=0`, `verified=50`, `replayed=false` |
| `restored-2023-may-outtemp-03-v1-exec-v12` | RESTORED | 50 | 50 | 135337–135386 | `a6e4d74b9f791e1a7020906884f6c303ad9f9fc69c329e9548bac89c7b842ac9` | Fresh MCP dry-run | `applied=50`, `unchanged=0`, `verified=50`, `replayed=false` |
| `restored-2023-may-outtemp-04-v1-exec-v12` | RESTORED | 40 | 40 | 135387–135426 | `664e5d0a2b39d3b673990bfdf64e95ed668bf7762a116004a02bd3d50ea8032d` | Fresh MCP dry-run | `applied=40`, `unchanged=0`, `verified=40`, `replayed=false` |

Před každým skutečným zápisem byly ověřeny hashe, cílová historie, očekávaná přítomnost/nepřítomnost řádku a zdrojové předpoklady. U července 2013, obou dávek 2020 byly aktuální čitelné zdroje a cíle porovnány s úspěšnými dřívějšími dry-run výsledky; u srpna 2022, května 2023 a P3 byl před aplikací proveden nový skutečný MCP dry-run. Každá z deseti dávek byla samostatná atomická transakce. Po každé následovaly nezávislé SELECT kontroly a checkpoint.

## Závěrečné SELECT a auditní kontroly

- Živý archiv potvrdil všech 322 schválených klíčů timestamp + variable a správné cílové hodnoty.
- Auditní dotaz `id BETWEEN 135126 AND 135447` vrátil přesně 322 unikátních řádků bez mezery v ID; všechny mají `state=applied`. Provenience a důvody odpovídají payloadům včetně známého prefixu `insert:` / `update:` přidaného MCP.
- Úplný `SELECT *` postimage byl uložen a ověřen pro všech 311 nových řádků. Všechny hodnoty, metadatové sloupce i NULL u ostatních meteorologických veličin prošly. Deterministické SHA-256 úplných řádků jsou v `reports/v1_2/application_evidence/POSTIMAGE_SHA256_MANIFEST.json`.
- U UPDATE bylo ověřeno zachování ostatních veličin; zejména po operaci 2013 zůstalo na timestampu 1373320800 `outHumidity=60`. Zdrojové hodnoty 27 operací izolované teploty 2020 byly znovu přečteny po aplikaci a zůstaly stejné.
- U P3 bylo bezprostředně před aplikací znovu ověřeno 26 krajních měření včetně hodnot a absence odpovídajících auditních změn, všech 21 čistých cílových timestampů, absence původních hodnot na cílech a neměnnost vstupů. Po commitu se všech 26 krajních hodnot znovu ověřilo beze změny. Použitý v2.1 odhad nebyl přepočítán. Předchozí kontextové filtry zůstaly podmínkou validace.
- Staging zůstal beze změny: 4 cancelled batches, 20 pending batches a 272 candidates; žádný staging vytvořen ani změněn.
- Nebyla použita produkční ani zdrojová databáze k zápisu. Weather MCP zapisoval pouze do `loucka_reconstruction.archive`; implementace MCP nebyla změněna.
- Timestamp 1661591400 nemá v cílovém archivu žádný řádek, nebyl doplněn.

## Rozsah, klasifikace a omezení

Kanonický ZIP [loucka_complete_historical_data_audit_v1.1.zip](loucka_complete_historical_data_audit_v1.1.zip) zůstal beze změny; závěrečný SHA-256 je `71b40577715de0a95459acbe60d342099467dc9dae1f6332cf01b861c10f721e`. V1.2 exekuční manifest má SHA-256 `854303e4d3de4800efb8031c63e51365a23f5fb521e0f7bf77ac2499abfb6276`. Všech deset schválených payloadů odpovídá manifestu, pokrývá 314 unikátních klíčů a neobsahuje rain/rainRate, Q1 2018 ani rok 2021. Meteorologické hodnoty odpovídají kanonickému návrhu; technické úpravy se omezily na doloženou kompatibilitu batch ID a důvodů, odstranění insert-only polí z UPDATE objektů a prefixy důvodů přidané MCP.

Lokální validátor `scripts/validate_execution_payloads_v1_2.py` skončil PASS. Reprodukuje doložený kompatibilitní kontrakt, **neimportuje přímo produkční Weather MCP modul**, protože jeho zdroj není v pracovním prostředí. Očekávaný ověřený SHA-256 zdrojového souboru MCP je `95d87c09608347aa50c21cf30befa4465f9bcddd34ad2b578804a49e55c465eb`; soubor nebyl dostupný. Samotný Git HEAD nebyl použit jako důkaz přesné verze MCP. Runtime kontrakt se opírá o skutečné MCP dry-run výsledky a aplikační odpovědi.

Známé limity datové evidence zůstávají:

- U července 2013 byla zachována nejistota desetiminutové pozorované kadence při deklarovaném pětiminutovém intervalu.
- U dvanácti případů srpna 2022 označených `neighbor_plausibility` zůstává samostatná revize.
- Květen 2023 zachovává zdroj `pocasi-loucka.eu_old` a doloženou nejistotu jeho původu. Read-only SQL nástroj odmítá tento název databáze, proto zde MCP dry-run ověřil pouze cílový stav a formální správnost operací; skutečné hodnoty zdroje byly následně nezávisle ověřeny SELECTem přes information_schema a kvalifikované názvy tabulek, spojením auditních ID 135172–135426 přes source_time se zdrojovým archivem. Pro srpen 2022 bylo ověřeno 65/65 řádků a pro květen 2023 190/190 řádků: žádný chybějící zdroj, rozdíl outTemp/source_value ani nesoulad usUnits=16 či interval=5. Původ historického zdrojového archivu zůstává nejistý.
- Dvě srážkové korekce ze Silvestra 2018 (`rain` a `rainRate`, timestamp 1546297200) zůstaly odloženy kvůli E4; nebyly v payloadu této fáze.
- Q1 2018 zůstává chráněno; rok 2021 byl pouze diagnostický a nebyl změněn.
- Vlastník potvrdil existenci snapshotu databázového serveru a samostatné Navicat zálohy `loucka_reconstruction`. Obnovitelnost ani praktický rollback nebyly testovány; vlastník rozhodl, že toto ověření nebude blokovat schválenou aplikaci.

## Rollback evidence

Rollback nebyl proveden. Návrhy auditované kompenzace pro osm UPDATE obsahují zachycené původní řádky a jejich hashe v `ROLLBACK_EVIDENCE_322.json`. Tyto návrhy nebyly provedeny ani testovány. MCP neumí bezpečně DELETE pro 311 INSERT řádků. Případné odstranění vyžaduje samostatný administrátorský postup s kontrolou úplného postimage hashe, pozdější auditní historie a nepřítomnosti dalších doplněných veličin.

## Další postup

Dokončení tohoto schváleného rozsahu neuzavírá celý historický archiv. Další rozhodnutí se týká oddělené E4 revize dvou odložených srážkových operací. Poté lze samostatně rozhodnout o případných dalších návrzích a jejich certifikaci. Tento balíček ani provedené zápisy takové rozšíření neschvalují.


Opravená v1.1 evidence odděluje neměnný předaplikační `EXECUTION_MANIFEST.json` od `EXECUTION_FINAL_MANIFEST.json`, který zachycuje všech 14 aplikovaných dávek a jejich skutečná auditní ID.


## Oprava evidence v1.1

Původní ZIP v1 zůstává neměnnou historií. Oprava v1.1 opravuje odkaz rollback návrhu pro 1373320800/outTemp na auditní událost 135140, doplňuje kontrolu všech osmi rollback odkazů a samostatný finální manifest. Všechny 322 auditní události, 311 úplných postimages a osm rollback návrhů byly konzistenčně ověřeny. Pro tento evidenční krok nebyla provedena aplikace, staging ani MCP dry-run.
