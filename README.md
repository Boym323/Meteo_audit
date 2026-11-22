# Počasí Loučka — projekt auditu meteorologické databáze

## Cíl
Prověřit historická měření přibližně od roku 2009 do roku 2026, odlišit chyby senzorů, změny hardwaru, jednotek a časového posunu od skutečných extrémních jevů a připravit doložené, vratné návrhy rekonstrukce.

## Infrastrukturа a připojení
- Auditní prostředí: Debian LXC `zl-dev-AuditMeteo`, projekt `/opt/meteo-audit`.
- Zdroj: MariaDB, předchozí známá verze 11.8.6 (aktuální ověřit).
- Připojení bylo ověřeno 2026-10-30 na MariaDB 11.8.6; aktuální host a port jsou pouze v lokálním `.env` a do dokumentace se nekopírují.
- Analytické CLI znovu používá stávající účet `loucka_audit` z `.env` (`DB_USER`, `DB_PASSWORD`). **Podle provozního nastavení uživatele má do všech původních/produkčních databází pouze SELECT a zápisová oprávnění jen do `loucka_reconstruction`.** V rekonstrukční DB zůstává auditní CLI softwarově read-only (validace SELECT/SHOW a transakce READ ONLY); žádná oprávnění se nemění.
- Tajné údaje jsou výhradně v lokálním `.env` s oprávněním 600; nikdy v dokumentaci ani Gitu.
- **DB:** názvy databází obsahují tečku a pomlčku — v SQL je uzavírej do zpětných apostrofů, např. `` `pocasi-loucka.eu`.`archive` ``.

### Vzor lokálního `.env` (bez skutečných tajných údajů)
```dotenv
DB_HOST=VYPLNIT
DB_PORT=3306
DB_USER=loucka_audit
DB_PASSWORD=SET_OUT_OF_BAND
TZ=Europe/Prague
```
Použij `.gitignore` obsahující `.env` a `.env.*` kromě `.env.example`; nastav `chmod 600 .env`. S existujícím `DB_USER=loucka_audit` a správným `DB_PASSWORD` v lokálním `.env` není potřeba zakládat další účet ani měnit granty.

## Ověřené databáze (Weather MCP, 30. 10. 2026)
`pocasi-loucka.eu`, `loucka_reconstruction`, `old_weewx`, `pocasi-loucka.eu_GW1000`, `pocasi-loucka.eu_old`, `weewx_WH1080`. Přítomna je také systémová `information_schema`.

### Historická data
Hlavní tabulka: `pocasi-loucka.eu`.`archive`.
Známé základní sloupce: `dateTime` (Unix čas v UTC, sekundy; primární klíč), `usUnits`, `interval` (minuty). Historický počet řádků k 28. 10. 2026: cca 1 679 574; nikoli aktuálně ověřený počet.

Známé veličiny zahrnují: `outTemp`, `inTemp`, `appTemp`, `dewpoint`, `windchill`, `heatindex`, `humidex`, `outHumidity`, `inHumidity`, `inDewpoint`, `barometer`, `pressure`, `altimeter`, `windSpeed`, `windGust`, `windDir`, `rain`, `rainRate`, `radiation`, `maxSolarRad`, `UV`, `ET`, `cloudbase`, `luminosity`, `pm25_1`, `soilMoisture1`–`soilMoisture4`, `soilTemp1`–`soilTemp4`, `extraTemp1`–`extraTemp2`, `extraHumid1`–`extraHumid2`, `lightning_*` a stavové hodnoty baterií. **Úplný seznam, typy a jednotky ověřit vůči skutečnému schématu a WeeWX konfiguraci**; jednotky závisí na `usUnits`.

### Rekonstrukční databáze
`loucka_reconstruction` obsahuje aktuálně zjištěné tabulky:
- `archive` pro pracovní rekonstrukce — **nepředpokládej identický obsah s produkční tabulkou**.
- Srážky červenec 2021: `rain_archive_original_202107`, `rain_audit_202107`, `rain_backup_202107_before_chmi_v1`, `rain_qc_202107`, `rain_qc_daily_202107`, `rain_reconstruction_202107_chmi_v1`.
- Vlhkost duben 2022: `reconstruction_humidity_202204`.
- Evidence změn/návrhů: `reconstruction_batches`, `reconstruction_candidates`, `reconstruction_changes`.
- Reference: `reference_stations`, `reference_observations`, `reference_daily`.

Pouze existence těchto tabulek je ověřena. Jejich obsah, aktuální kvalita a to, které změny již byly aplikovány, je nutné zvlášť zjistit.

## Externí referenční zdroje
- LuhaMet: https://www.luhamet.cz/archiv/
- Weather Underground — ILOUKA4: https://www.wunderground.com/dashboard/pws/ILOUKA4
- ČHMÚ: oficiální staniční záznamy a případně archiv radarových odhadů, s rozlišením pozorování od modelovaného odhadu. Denní `SRA` nelze bez ověření přiřazení dne a časového okna použít jako přímý důkaz pětiminutového impulsu; viz [metodika denních srážek ČHMÚ](docs/chmi-daily-sra.md).

## Pravidla vyhodnocování
- Všechna data páruj primárně podle UTC. Pro denní úhrny používej výslovně uvedený místní meteorologický nebo občanský den a ošetři změnu času.
- U srážek zkoumej vazbu `rain` (inkrement archivního intervalu), `rainRate` (intenzita), délky intervalu, resetů a zdrojových jednotek; neodvozuj význam jen z názvu.
- Ani velká odchylka od okolní stanice není automaticky chyba: srážky bývají prostorově proměnlivé.
- Nulovou hodnotu nezaměňuj s chybějícím měřením. Rekonstrukce musí zachovat údaj o nejistotě.
- Historické senzory půdní teploty (`soilTemp`) a externí teploty (`extraTemp`) byly přeznačovány. Původní názvy mezi obdobími nesrovnávej bez mapování konfigurací.

## První bezpečné SQL kontroly
```sql
SELECT COUNT(*) AS n, FROM_UNIXTIME(MIN(dateTime)) AS start_time,
       FROM_UNIXTIME(MAX(dateTime)) AS end_time
FROM `pocasi-loucka.eu`.`archive`;

SELECT usUnits, `interval`, COUNT(*) AS n
FROM `pocasi-loucka.eu`.`archive`
GROUP BY usUnits, `interval` ORDER BY n DESC;

SELECT TABLE_NAME, TABLE_ROWS
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'loucka_reconstruction'
ORDER BY TABLE_NAME;
```
Pozor: `FROM_UNIXTIME` používá časovou zónu připojení; pro přesné časové porovnání nastav relaci na UTC nebo pracuj s číselným `dateTime`.

## Provoz a použití CLI

Měsíční audit čte archiv po jednom místním měsíci, používá allowlist šesti známých databází a ukládá výstup do adresáře daného schématu. Pro rekonstrukční dataset:

```bash
PYTHONPATH=src python3 -m meteo_audit.monthly \
  --database loucka_reconstruction \
  --start-year 2009 \
  --end-year 2026
```

Produkční zdroj vyber explicitně:

```bash
PYTHONPATH=src python3 -m meteo_audit.monthly \
  --database pocasi-loucka.eu \
  --start-year 2009 \
  --end-year 2026
```

Výstupy budou v reports/loucka_reconstruction/ a reports/pocasi-loucka.eu/; každá databáze má vlastní měsíční CSV, roční CSV a metadata JSON. Metadata uvádějí schéma, UTC čas vytvoření, období, časovou zónu, jednotky, počet řádků a commit analytického kódu.

Read-only srovnání uložených hodnot rain a rainRate po místních rocích pro všech šest archivních zdrojů:

```bash
PYTHONPATH=src python3 -m meteo_audit.rainrate \
  --start-year 2009 \
  --end-year 2025
```

Každý zdroj dostane vlastní adresář pod reports/rainrate/; report uvádí NULL, nulu i kladnou hodnotu zvlášť a nepřepočítává intenzitu ze srážky.

WeeWX ukládá čas na konci archivního intervalu. Pro místní hranice je proto filtr dateTime > start AND dateTime <= end. Místní půlnoc patří právě skončenému občanskému dni a měsíci. Časy vytvářej v Europe/Prague, aby se správně promítl CET/CEST. Podrobná pravidla jsou v [časové metodice](docs/time-intervals.md) a [metodice auditu srážek](docs/rain-audit-methodology.md).

Přístup k DB je chráněn single-statement SELECT/SHOW kontrolou, allowlistem schémat, read-only transakcí, timeoutem a souborem přihlašovacích voleb 0600. Transakce nejsou náhradou za SELECT-only grant. CLI používá aktuální účet `loucka_audit`; samostatný SELECT-only účet podle [volitelného runbooku](sql/admin/create_meteo_audit_ro.sql) není podmínkou. Upozornění: do původních zdrojových databází je účet dle provozního nastavení pouze SELECT, ale v `loucka_reconstruction` je zápis povolen. Analytický klient v této pracovní DB nadále vynucuje read-only dotazy; opravy vyžadují samostatné schválení. Úplná pravidla jsou v [bezpečnostní dokumentaci](docs/security.md).

## Testy a CI

Bez MariaDB spusť deterministickou sadu unit a mockovaných integračních testů:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests scripts
python3 scripts/check_repo_secrets.py
```

GitHub Actions používá Python 3.13, provádí syntaktickou kontrolu, testy a kontrolu sledovaných souborů na tajemství. Nepřipojuje se k databázi a nevytváří artefakty.

Dodržuj AGENTS.md. Žádné automatické UPDATE, DELETE, DROP, TRUNCATE ani zápisy do původních archivů nebo auditních tabulek. Výstupy ukládej pod reports/ a návrhy oprav pod proposals/.

## Auditní výstup

První aktuální diagnostika a Fáze A jsou zaznamenány v [reports/2026-10-30-diagnostic-phase-a.md](reports/2026-10-30-diagnostic-phase-a.md). Kandidátní opravy jsou pouze návrhy, viz [proposals/phase-a-review-20261030.md](proposals/phase-a-review-20261030.md). Produkční data nebyla změněna.

## Projektové adresáře

- `src/meteo_audit/` — lehké standard-library komponenty pro screening.
- `tests/` — deterministické unit a mockované integrační testy; běží bez DB.
- `sql/readonly/` — kontrolní SELECTy; žádné zápisové příkazy.
- `reports/` — běhy auditů a důkazy.
- `proposals/` — návrhy bez automatické aplikace.

## Checkpoint běhu auditu

Pro lokální reprodukovatelný běh lze příkaz obalit `scripts/run_audit_checkpoint.py`.
Obal sám databázi neotevírá a child proces nesandboxuje; databázové běhy musí použít
projektový SELECT/SHOW-only adapter `src/meteo_audit/db.py` a příkaz je třeba předem
zkontrolovat. Wrapper spustí předaný příkaz bez shellu, uloží průběžný log
a zapíše `manifest.json` s run ID, rozsahem z JSON konfigurace, exit stavem a SHA-256
skriptu, vstupů, vytvořených výstupů a logu. Konfigurace nesmí obsahovat tajné údaje.
Příklad (výstupní cesta musí odpovídat skriptu, který se spouští):

```bash
python3 scripts/run_audit_checkpoint.py \\
  --config config/audit-run.example.json \\
  --source sql/readonly/long_gap_source_cadence.sql \\
  --output reports/<generated-output>.csv \\
  -- python3 <audit-script.py> <its-arguments>
```

Každý běh dostane samostatný adresář v `runs/`. Před předáním běhu je třeba
zkontrolovat, že uvedený scope/config odpovídá skutečně spuštěnému příkazu a že
výstupy existují; hash identifikuje soubor, sám o sobě nepotvrzuje věcnou správnost.

## GitHub a pravidelná synchronizace

Repozitář `https://github.com/Boym323/Meteo_audit` je připojen jako `origin`; změny vznikají na pracovní větvi a předávají se pull requestem do `main`. Před commitem zkontroluj staged diff a spusť tajemství scanner. `.env` zůstává ignorovaný; nikdy se nepublikují tajné údaje.

### Automatické publikování commitů

Verzovaný soubor `.githooks/post-commit` je součástí repozitáře, ale běží jen pokud jej checkout aktivoval (např. přes `core.hooksPath`). Výchozí hook nyní **nic automaticky nepushuje** a pouze upozorní na commit na `main`. Před commitem ověř `git branch --show-current` a `git config --get core.hooksPath`; změny publikuj přes pracovní větev a PR. Staré lokální hooky v LXC mohou mít jiný obsah a mohou stále automaticky pushovat — ověř je samostatně.

Aktuální diagnostika a Fáze A: [report](reports/2026-10-30-diagnostic-phase-a.md). Výsledky stabilizace a metodiky: [report](reports/2026-10-30-code-review-stabilization.md). Přehledová CSV a evidence ČHMÚ jsou v `reports/`. Tato data představují auditní souhrny a zdokumentované reference; kompletní produkční `archive` není v tomto pracovním stromu exportován.

## Offline audit CLI (Stage N, partial)

`scripts/meteo_audit.py` is a local entry point over the existing deterministic validators. It has no database client and does not perform database writes. Database snapshots must continue to come from the approved bounded read-only Weather MCP workflow.

Run a validator with hashed inputs and evidence outputs:

```bash
python3 scripts/meteo_audit.py run-validator \
  --script scripts/validate_secondary_channel_followup.py \
  --name secondary-channel-followup \
  --scope snapshot=2026-11-13 --scope database_access=none \
  --source reports/2026-11-13-secondary-channel-followup.csv \
  --output reports/2026-11-13-secondary-channel-followup.csv
```

The run wrapper creates a unique ID, UTC timestamps, JSON configuration, command log, exit status, and SHA-256 records under `runs/`. Use `--source` and `--output` repeatedly to capture the full evidence set. `compare` accepts two successful manifests only when their scopes are identical and writes a JSON digest comparison; hash changes do not imply scientific changes. Arbitrary shell commands and non-validator scripts are rejected.

This is an incremental Stage N interface: it standardizes offline validation and run comparison. It does not yet provide one command for live year/variable SQL audits, source extraction, correction-package construction, or readiness generation; those stages remain tied to their reviewed, bounded SQL and analysis scripts.


## Stav synchronizace a finální validační rozhodnutí (22. 11. 2026)

- Aktivní LXC je ověřen jako `zl-dev-frontendPocasi`, pracovní strom `/opt/meteo-audit`; odstraněný `zl-dev-AuditMeteo` se nepoužívá.
- Lokální checkpoint a rozhodovací artefakty ověřují 92 664 operací: 92 366 `QUARANTINE`, 298 `ALREADY_APPLIED`, žádné další `APPLY` ani `KEEP`. To není certifikace ani souhlas s produkčním cutoverem.
- Publikace zůstává blokována: Q1 2018 je chráněné, rok 2021 diagnostický a 462 GW3000 E4 řádků `rain`/`rainRate` blokovaných.
- SHA a počty reprodukuje `scripts/verify_finalization_integrity.py`. Velké hodnotové manifesty, konkordance SQLite a ZIP balíčky zůstávají mimo Git; soupis jejich hashů je v `reports/data/2026-11-22-local-package-integrity.json`.
- Žádný produkční zápis, WeeWX rebuild ani webový deploy nebyl proveden. Aktuální synchronizační PR a CI: doplnit po dokončení.
- Podrobnosti: [ověřený report finalizace](reports/2026-11-22-reconstruction-finalization-status.md).
