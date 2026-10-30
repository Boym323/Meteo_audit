# Počasí Loučka — projekt auditu meteorologické databáze

## Cíl
Prověřit historická měření přibližně od roku 2009 do roku 2026, odlišit chyby senzorů, změny hardwaru, jednotek a časového posunu od skutečných extrémních jevů a připravit doložené, vratné návrhy rekonstrukce.

## Infrastrukturа a připojení
- Auditní prostředí: Debian LXC `zl-dev-AuditMeteo`, projekt `/opt/meteo-audit`.
- Zdroj: MariaDB, předchozí známá verze 11.8.6 (aktuální ověřit).
- Připojení bylo ověřeno 2026-10-30 na MariaDB 11.8.6; aktuální host a port jsou pouze v lokálním `.env` a do dokumentace se nekopírují.
- Používaný účet `loucka_audit` má SELECT na produkční databázi, ale také zápisová oprávnění v `loucka_reconstruction`. Analytické nástroje v tomto projektu používají read-only transakce; pro další automatizaci se doporučuje samostatný účet pouze pro SELECT.
- Tajné údaje jsou výhradně v lokálním `.env` s oprávněním 600; nikdy v dokumentaci ani Gitu.
- **DB:** názvy databází obsahují tečku a pomlčku — v SQL je uzavírej do zpětných apostrofů, např. `` `pocasi-loucka.eu`.`archive` ``.

### Vzor lokálního `.env` (bez skutečných tajných údajů)
```dotenv
DB_HOST=VYPLNIT
DB_PORT=3306
DB_USER=loucka_audit
DB_PASSWORD=VYPLNIT
DB_SOURCE=pocasi-loucka.eu
DB_RECONSTRUCTION=loucka_reconstruction
TZ=Europe/Prague
```
Použij `.gitignore` obsahující `.env`, `.env.*` kromě bezpečných vzorů (`!.env.example`); nastav `chmod 600 .env`.

## Ověřené databáze (Weather MCP, 30. 10. 2026)
`pocasi-loucka.eu`, `loucka_reconstruction`, `old_weewx`, `pocasi-loucka.eu_GW1000`, `pocasi-loucka.eu_old`, `weewx_WH1080`. Přítomna je také systémová `information_schema`.

### Historická data
Hlavní tabulka: `pocasi-loucka.eu`.`archive`.
Známé základní sloupce: `dateTime` (Unix čas v UTC, sekundy; primární klíč), `usUnits`, `interval` (minuty). Historický počet řádků k 28. 10. 2026: cca 1 679 574; nikoli aktuálně ověřený počet.

Známé veličiny zahrnují: `outTemp`, `inTemp`, `appTemp`, `dewpoint`, `windchill`, `heatindex`, `humidex`, `outHumidity`, `inHumidity`, `inDewpoint`, `barometer`, `pressure`, `altimeter`, `windSpeed`, `windGust`, `windDir`, `rain`, `rainRate`, `radiation`, `maxSolarRad`, `UV`, `ET`, `cloudbase`, `luminosity`, `pm25_1`, `soilMoisture1`–`soilMoisture4`, `soilTemp1`–`soilTemp4`, `extraTemp1`–`extraTemp2`, `extraHumid1`–`extraHumid2`, `lightning_*` a stavové hodnoty baterií. **Úplný seznam, typy a jednotky ověřit vůči skutečnému schématu a WeeWX konfiguraci**; jednotky závisí na `usUnits`.

### Rekonstrukční databáze
`loucka_reconstruction` obsahuje aktuálně zjištěné tabulky:
- `archive`, `archive` pro pracovní rekonstrukce — **nepředpokládej identický obsah s produkční tabulkou**.
- Srážky červenec 2021: `rain_archive_original_202107`, `rain_audit_202107`, `rain_backup_202107_before_chmi_v1`, `rain_qc_202107`, `rain_qc_daily_202107`, `rain_reconstruction_202107_chmi_v1`.
- Vlhkost duben 2022: `reconstruction_humidity_202204`.
- Evidence změn/návrhů: `reconstruction_batches`, `reconstruction_candidates`, `reconstruction_changes`.
- Reference: `reference_stations`, `reference_observations`, `reference_daily`.

Pouze existence těchto tabulek je ověřena. Jejich obsah, aktuální kvalita a to, které změny již byly aplikovány, je nutné zvlášť zjistit.

## Externí referenční zdroje
- LuhaMet: https://www.luhamet.cz/archiv/
- Weather Underground — ILOUKA4: https://www.wunderground.com/dashboard/pws/ILOUKA4
- ČHMÚ: oficiální staniční záznamy a případně archiv radarových odhadů, s rozlišením pozorování od modelovaného odhadu.

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

## Provoz
Dodržuj `AGENTS.md`. Žádné automatické UPDATE, DELETE, DROP, TRUNCATE ani zápisy do původních archivů. SQL dotazy limituj a pro větší analýzy postupuj po měsících/letech; odhadni dopad na produkční databázi. Výstupy ukládej pod `reports/` a návrhy oprav pod `proposals/`.

## Auditní výstup

První aktuální diagnostika a Fáze A jsou zaznamenány v [reports/2026-10-30-diagnostic-phase-a.md](reports/2026-10-30-diagnostic-phase-a.md). Kandidátní opravy jsou pouze návrhy, viz [proposals/phase-a-review-20261030.md](proposals/phase-a-review-20261030.md). Produkční data nebyla změněna.

## Projektové adresáře

- `src/meteo_audit/` — lehké standard-library komponenty pro screening.
- `tests/` — testy klasifikace; běží bez DB.
- `sql/readonly/` — kontrolní SELECTy; žádné zápisové příkazy.
- `reports/` — běhy auditů a důkazy.
- `proposals/` — návrhy bez automatické aplikace.

## GitHub a pravidelná synchronizace

Repozitář `https://github.com/Boym323/Meteo_audit` je připojen jako `origin`; pracovní větev je `main`. Po každém dokončeném úkolu se aktualizují relevantní Markdown reporty a strojově čitelné CSV/JSON výstupy, zkontrolují staged změny a publikují commitem na GitHub. `.env` zůstává ignorovaný; nikdy se nepublikují tajné údaje.

### Automatické publikování commitů

V tomto checkoutu je zapnutý Git hook `post-commit`: po každém commitu vytvořeném na větvi `main` provede `git push origin HEAD:main`. Na jiných větvích nic neposílá. Změny je stále nutné nejdříve výslovně commitnout; hook sám nic nestageuje ani nevytváří commit. Push vyžaduje funkční GitHub přístupové údaje v prostředí. Pokud push selže (například kvůli odlišné historii nebo chybějícím oprávněním), commit zůstane lokálně a Git zobrazí chybu.

Aktuální běh diagnostiky a Fáze A: [report](reports/2026-10-30-diagnostic-phase-a.md). Přehledová CSV a evidence ČHMÚ jsou v `reports/`. Tato data představují auditní souhrny a zdokumentované reference; kompletní produkční `archive` není v tomto pracovním stromu exportován.
