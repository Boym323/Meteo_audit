# Závěrečná inventura lokálních souborů `/opt/meteo-audit`

**Datum:** 2026-11-22

**Porovnávaný GitHub `main`:** `d93b386365d64c1729a642aa0cc6b0368083940c` (po PR #39, #40, #41 a #42)
**Detailní metadata:** [`reports/data/2026-11-22-local-file-inventory.csv`](data/2026-11-22-local-file-inventory.csv)

## Souhrn

Inventura porovnává cesty v `/opt/meteo-audit` s rekurzivním stromem aktuálního `main`. Z počtů jsou vynechány `.git`, všechny procházené adresářové části začínající `.venv` a Python/test/lint cache (`__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`). Obsah původního projektu se neměnil.

| Výsledek | Souborů | Rozhodnutí |
|---|---:|---|
| Lokální soubory ve vymezeném inventáři | 4 817 | Zahrnují shodné, odlišné i nové cesty |
| Cesta i obsah shodné s `main` | 1 591 | Již publikované kopie |
| Cesta existuje na `main`, obsah se liší | 13 | Všechny rozdíly jsou starší lokální verze nebo formátovací změny; nic nepřepisovat |
| Cesta na `main` chybí | 3 213 | Rozděleno níže a v CSV; bezpečné metodiky/reporty byly publikovány PR #41 a #42 |

Počet nových cest je o 25 vyšší než dříve uváděných 3 188. Při této inventuře je počítáno 4 817 procházených souborů a 1 604 existujících cest na `main` (1 591 shodných + 13 rozdílných), takže zbývá 3 213 nových cest. Dřívější 3 188 se současným stavem a vymezením nelze reprodukovat; CSV zachycuje aktuální inventář podle výše popsaných pravidel a nahrazuje předchozí odhad.

CSV obsahuje všech 3 213 nových cest a všech 13 rozdílných kopií: relativní cestu, počet bajtů, vztah k `main`, klasifikaci, důvod a případné označení skupiny přesné duplicity. Neobsahuje obsah souborů ani jejich kontrolní součty.

## Rozdělení nových cest podle umístění a obsahu

| Umístění | Počet | Klasifikace a důvod ponechání lokálně |
|---|---:|---|
| `reports/` | 1 142 | Generované reporty, CSV/JSON, kandidáti a postimages; jde o výsledkové důkazy s detailními hodnotami a neprošly jednotlivou redakcí. |
| `data/` | 943 | Zdrojová, srovnávací a odvozená data. Obsahují například `data/historical_value_concordance.sqlite` (1 663 004 672 B) a zmrazené synchronizační payloady; nepublikovat. |
| `proposals/` | 253 | Konkrétní návrhy a hodnotové payloady rekonstrukcí; nejsou zdrojovým kódem ani veřejným souhrnem. |
| `runs/` | 139 | Dočasné logy a manifesty jednotlivých běhů; obsahují opakované/stavové výstupy. |
| `scripts/` | 89 | 87 `scripts/build_vN_checkpoint.py` souborů pro N=3–65 a 73–96 a dva lokální MariaDB integrační spouštěče. Checkpoint skripty jsou generované iterace závislé na lokálních výstupech, ne udržované samostatné moduly. |
| `final_migration_package/` | 52 | Migrační balík, manifesty a data potřebná pro lokální reprodukci; neveřejné hodnotové artefakty. |
| `production-existing-account-v1.2/` | 49 | Provozní balík se schvalovacími, integračními a datovými artefakty. |
| `loucka_review_build/` | 43 | Lokální sestava reportů a reprodukčních dat; obsahově se překrývá s dalšími balíky. |
| `archives/` | 33 | Historické pracovní verze a předchozí výstupy; zastaralé vůči aktuálním reportům. |
| `config/` | 30 | Konkrétní lokální validační/produkční konfigurace, nikoli obecná veřejná konfigurace. |
| `release-v1.2/` | 30 | Kopie release balíku; stejné soubory jsou také v `production-existing-account-v1.2/` a `production-run-20261115/`. |
| `production-run-20261115/` | 29 | Výsledky a kopie balíku z provozního běhu. |
| `tests/` | 25 | 19 nových unit-test modulů, 2 MariaDB integrační testy a 4 fixture/evidence soubory. Unit testy v izolaci očekávají lokální vygenerované evidence; integrační testy jsou navázané na DB a provozní payloady. |
| `execution_payloads/` | 18 | Vykonávací payloady a manifesty; neveřejné. |
| `recovered-insert-batches-20261117/` | 17 | Konkrétní návrhy vložení historických hodnot; neveřejné. |
| `sql/` | 4 | Návrhy migrací a změn oprávnění/struktury/zápisu; ponechat lokálně a nikdy nespouštět v rámci synchronizace. |
| `[kořen projektu]` | 311 | Směs reportů, manifestů, šablon, write-capable skriptů a 114 verzovaných ZIP balíků (3 403 538 773 B celkem). ZIPy jsou souhrnné/historické balíky, ne zdrojové soubory. |
| `deploy/` | 2 | Service/timer šablony pro provozní nasazení; mimo publikaci auditního zdrojového kódu. |
| `approvals/`, `approval_payloads/`, `stream_copy_receipts/` | 3 | Schválení, provozní payload nebo potvrzení provedení; lokální řízení a auditní důkazy. |
| `atlas_preview/` | 1 | Lokální HTML náhled navázaný na datový kontrakt. |

Uvedené počty podle umístění dávají 3 213. Kromě toho jsou v kořeni konkrétní write-capable soubory `apply_recovered_source_batch.py`, `apply_recovered_source_inserts.py`, `apply_verified_rain_nullfills.py`, `run_three_repairs.py`, `production-cutover-approved-candidates-20261117.sql` a `production-cutover-rollback-20261117.sql`; zůstávají lokální. Všechny čtyři návrhy pod `sql/migrations/` také zůstávají lokální.

## Publikovatelné soubory a důkazní omezení

Publikovatelné jádro v `src/meteo_audit/` i existující metodiky v `docs/` jsou na `main` již obsahově shodné. Z lokálních nových dokumentů prošly obsahovou a bezpečnostní revizí a byly publikovány:

- [PR #41](https://github.com/Boym323/Meteo_audit/pull/41): `HISTORICAL_PROVENANCE_POLICY.md`, `ARCHIVE_QUALITY_AND_PROVENANCE_MODEL.md` — metodiky klasifikace bez řádkových měření.
- [PR #42](https://github.com/Boym323/Meteo_audit/pull/42): `HISTORICAL_WIND_TRANSFORMATION_REPORT.md`, `ARCHIVE_UNIT_TIME_PHYSICAL_QUALITY_REVIEW.md` — agregované souhrnné výsledky, bez surových výpisů.

Další přesné zdrojové kandidáty byly prověřeny podle účelu a závislostí. `scripts/build_vN_checkpoint.py` je sada verzovaných checkpoint builderů navázaná na lokální snapshoty; nový `src/` modul není. Nové testy odkazují na chybějící soubory jako `MONTHLY_VALIDATION_EVIDENCE.json`, `CURRENT_GW3000_E4_VALIDATION.json`, `MASTER_FINALIZATION_CHECKPOINT_20261117.json` a lokální preview artefakty. Při spuštění 19 nových unit-test modulů nad současným `main` byly chyby z chybějících lokálních důkazů; úplný běh se všemi přidanými moduly skončil 60 chybami. Dvě integrační sady vyžadují MariaDB/provozní snapshot. Těchto testů ani fixture dat se proto PR neobsahuje.

Automatická kontrola citlivých vzorů označila credential-like konstrukce v pěti kopiích integračních testů. Konkrétně `tests/integration/test_gw3000_full_frozen_runner.py` a jeho kopie v `release-v1.2/`, `production-existing-account-v1.2/` a `production-run-20261115/`, plus `release-v1.2/loucka-gw3000-v1.2/tests/integration/test_archive_sync_mariadb.py`. Nejsou součástí PR. Hodnoty ani tajemství v tomto reportu neuvádím. Jména `.env.example`, `.env.source.example` a `.env.target.example` jsou jen šablony; dvě lokální šablony navíc nejsou potřeba pro obecný workflow v mainu.

Z metodik a reportů ponechaných lokálně jsou zvlášť relevantní `ARCHIVE_CONTINUOUS_SYNC_DESIGN.md` (obsahuje přesný živý watermark/snapshot) a `STATISTICAL_PUBLICATION_POLICY_V2.md` (obsahuje konkrétní pilotní výsledky). Detailní reporty pod `reports/` nebyly publikovány hromadně, protože mnoho CSV/JSON obsahuje row-level důkazy, soukromé hodnotové exporty nebo manifesty postimages. Agregovaný větrný report a souhrn jednotek/intervalů jsou na main z PR #42.

## Duplicitní a zastaralé soubory

SHA-256 byl použit pouze pro identifikaci shodného obsahu, neukládá se do reportu ani CSV. Z 3 213 nových cest bylo 3 098 souborů do 10 MB takto porovnáno; bylo nalezeno **226 skupin přesně stejných souborů**, celkem 657 cest. Zbývajících 115 souborů nad 10 MB nebylo hashováno kvůli jejich velikosti; zůstávají lokální podle datového/provozního umístění.

Mezi duplicitami jsou opakované identické výsledky v `data/p1p2_source_gap_overlay_results_*.json` a `data/short_gap_source_detail_results_*.json`, stejné běhové logy pod `runs/` a opakované kopie release souborů mezi `release-v1.2/`, `production-existing-account-v1.2/` a `production-run-20261115/`. Konkrétní duplicitní skupiny jsou v CSV označené `DUP-001` až `DUP-226`; samotné soubory jsem nemazal ani nepřesouval. Historické ZIP iterace v kořeni se liší obsahem/velikostí a zůstávají jako archivní balíky; nebyly označeny jako byte-identical duplicates.

## 13 odlišných kopií vůči `main`

Všechny cesty byly porovnány vůči aktuálním blobům na `main`; nic nebylo automaticky přepsáno. Lokální kopie nemají dosud nezveřejněnou obsahovou změnu:

| Cesta | Rozdíl a rozhodnutí |
|---|---|
| `.github/workflows/ci.yml` | Lokální verze používá `self-hosted` a nemá setup Python 3.13. Je starší; zachovat novější GitHub-hosted CI na `main`. |
| `.gitignore` | Lokální verze postrádá novější pravidla main pro ZIP/SQLite a hodnotové manifesty. Je starší; nepřepsat. |
| `RECONSTRUCTION_EXECUTION_FINAL_REPORT.md` | Pouze dodatečné koncové mezery Markdown; obsahově shodné. |
| `reports/2026-11-22-reconstruction-finalization-status.md` | Lokální kopie neobsahuje synchronizační sekci přidanou do `main`; starší report. |
| `scripts/simulate_estimated_short_temperature_proposals.py` | Pouze koncový newline. |
| `sql/readonly/archive_column_metadata.sql` | Pouze koncový newline. |
| `sql/readonly/database_schema_metadata.sql` | Pouze koncový newline. |
| `sql/readonly/database_table_catalog.sql` | Pouze koncový newline. |
| `sql/readonly/gw3000_insert_only_backfill_snapshot.sql` | Pouze koncový newline. |
| `sql/readonly/p3_short_temperature_gap_candidates_2019_2020.sql` | Pouze koncový newline. |
| `sql/readonly/production_archive_day_outtemp_consistency_2026.sql` | Pouze koncový newline. |
| `sql/readonly/temperature_transfer_2019_2020_holdout.sql` | Pouze koncový newline. |
| `src/meteo_audit/archive_sync_frozen.py` | Pouze koncový newline. |

## Ověření a zachování hranic

- PR #41 a #42 mají úspěšné GitHub Actions CI včetně syntaxe, celé současné unit/mocked integration sady a secret scanneru.
- Aktuální main sada prošla lokálně: 173 testů OK. `python3 -m compileall -q src tests scripts`, `python3 scripts/check_repo_secrets.py` a `git diff --check` prošly.
- Žádná SQL, migrace ani integrační test nebyly spuštěny proti databázi. Nebyly změněny databáze, WeeWX, produkční web ani původní soubory v `/opt/meteo-audit`.
- CSV je metadata-only inventář; neobsahuje obsah, surové hodnoty ani kontrolní součty lokálních dat.

Po PR #41–#43 jsou všechny zjištěné cesty buď už publikované, nebo zařazené jako neveřejný důkaz, lokální report, provozní/pomocný výstup, zastaralá kopie či zdroj/test vyžadující neveřejné artefakty. Nezveřejněné záznamy zůstávají záměrně v `/opt/meteo-audit`; nic nebylo odstraněno.

## Kontrola lokálních větví

Na větvi `chore/finalize-sync-20261122` zůstal lokální commit `9400f3a11efe3cd048567ab5431fa53dcbe84922`, který není ancestor aktuálního `main`. Porovnání stromů vůči `main` neukázalo žádnou cestu ani změnu obsahu jedinečnou pro tuto větev: její soubory jsou buď stejné, nebo starší než zveřejněné verze. Mezi stromy je 6 nových cest na současném `main` a 7 novějších verzí souborů na `main`; lokální commit tedy nepředstavuje chybějící publikovatelnou práci a nebyl znovu pushnut. Ostatní lokální pracovní větve nemají commit navíc oproti svým vzdáleným upstreamům. Větve nebyly přepisovány ani mazány.
