# Issue #14 — read-only ochrana již provedených rekonstrukcí

Aktuální stav ke **30. 10. 2026**. Tento dokument je návrh bezpečnostního kontraktu a inventář uložených výsledků, **není to příkaz k opětovnému zpracování dat**.

## Sledované zdroje

- Produkční a všechny historické archivy jsou výhradně read-only.
- Pracovní schéma `loucka_reconstruction` má u používaného účtu zapisovací práva, ale **tento CLI modul neobsahuje zapisovací SQL ani přepínač `apply`**.
- `reconstruction_changes` je skutečná evidence aplikovaných změn. `reconstruction_batches` a `reconstruction_candidates` slouží jako *návrhové staging tabulky*; `cancelled` a `pending` nejsou indikací již aplikované náhrady.
- `payload_hash` z `reconstruction_batches` je otisk návrhového payloadu, **nikoli hash surového měření ani originálního SQL**.
- Červenec 2021 byl historicky použit mimo tuto aplikaci přes Navicat. V `proposals/external-sql-manifest-july-2021.json` jsou `original_sql_sha256`, `before_export_sha256` a `after_export_sha256` nadále **null**, protože historické bajty neexistují jako doložený soubor. Nikdy nedoplňovat odhadem.

## Čtecí inventář

```bash
PYTHONPATH=src python3 -m meteo_audit.reconstruction_guard
```

CLI používá existující `.env` a `meteo_audit.db.query()` s jedním `SELECT` v transakci `READ ONLY` na dotaz, se souborovými přihlašovacími údaji chráněnými módem 0600. Ověřuje:

1. Přesně pět očekávaných `(batch_key, variable)` skupin v auditní tabulce a jejich stav `applied`, počty, historické rozdíly `rain`.
2. Oba původní návrhové balíčky jsou `cancelled`, mají očekávané počty a původně uložené `payload_hash`.
3. Tři záložní tabulky mají **328 / 30 / 2** řádků a všechny odpovídající pracovní `archive.rain` a `rainRate` jsou dnes nulové.
4. Místní červenec 2021 v konvenci WeeWX `(start,end]` má **42,5673 mm** s hranicemi `dateTime > 1625090400 AND dateTime <= 1627768800`.
5. Počet řádků `archive` je reportován, ale **není pevnou invariantou** — živý archiv může růst.

Výstup je JSON. `baseline.verified=false` a ukončovací kód 2 značí problém, který **blokuje další preflight**. Použitý účet musí mít jen čtecí přístup přes tento CLI, i když databázová identita drží v pracovním schématu více grantů.

## Čtecí předkontrola jednoho návrhu

Struktura **ilustrativního** lokálního JSON (není schválený kandidát):

```json
{
  "batch_id": "example-review-20261030-v1",
  "candidates": [
    {
      "target_time": 1700000000,
      "variable": "rain",
      "expected_old_value": 0.0,
      "proposed_value": 0.03,
      "source_database": "pocasi-loucka.eu",
      "source_time": 1700000000,
      "reason": "Hypoteticka demonstrace datoveho kontraktu, bez aplikace",
      "diagnosis_confidence": "UNRESOLVED",
      "replacement_confidence": "UNRESOLVED"
    }
  ]
}
```

```bash
PYTHONPATH=src python3 -m meteo_audit.reconstruction_guard --proposal /secure/path/candidate.json
```

Konkrétní čísla v ukázce **nepředstavují doloženou opravu**.

Předkontrola **fail-closed** odmítne dávku, pokud:
- není ověřen aktuální baseline, dávka již existuje mezi návrhy nebo změnami, nebo se pokouší znovu použít Fázi A;
- některá dvojice `(target_time, variable)` již existuje v `reconstruction_changes` v **libovolném stavu**, i pod jiným batch ID;
- manifest obsahuje duplicitní cíl, nepovolenou veličinu, neznámé schéma, neplatný UTC timestamp nebo chybí původ, důvod, obě úrovně jistoty a `expected_old_value`;
- aktuální `archive` nemá konkrétní čas nebo má jinou původní hodnotu (včetně rozdílu `NULL` vs `0`);
- je navržen neúčinný přepis identické hodnoty.

První verze výslovně podporuje jen `rain` a `rainRate` a nejvýše 100 kandidátů, aby nebyl umožněn nový zápis ostatních veličin bez vlastní validace. Úspěšný výstup `preflight_clean=true` obsahuje `authorized_to_apply=false`; JSON digest je otisk **návrhu**, nikoli původního senzoru.

**Poznámka:** Bezpečná předkontrola neodstraňuje soutěž dvou transakcí mezi kontrolou a budoucím zápisem. Samotné nasazení oprav **je mimo rozsah tohoto issue**; budoucí pipeline dle [#26](https://github.com/Boym323/Meteo_audit/issues/26) musí provést stejné podmínky znovu atomicky v transakci s očekávanými hodnotami.

## Neměnná historie a rollback kontrakt

1. Uchovávat raw záznam jako `(source_db,source_table,source_time,interval,variable,raw_value,raw_unit,source_hash)`. Nezaměňovat shodné kopie za dvě nezávislá měření.
2. U náhrady vést odděleně **jistotu diagnózy** a **jistotu navrhované náhradní hodnoty**. Staré aplikované `rain=0` jsou auditovaný fakt stavu DB, nikoli nezpochybnitelná meteorologická pravda.
3. Před jakýmkoliv budoucím `apply` zálohovat původní `NULL`/číselné hodnoty jako neměnné before-image, uvést `sha256` souboru původního SQL a exportu; neexistující historické hashe ponechat `null`.
4. Nespouštět dva writery na stejný `(dateTime,variable)`. V transakci zamknout cílový záznam, ověřit očekávanou hodnotu s NULL-safe `<=>`, počty a konflikt s auditem; aplikovat jen do `loucka_reconstruction.archive` po explicitním schválení uživatelem.
5. Auditovat změny append-only bez přepisování historie; kompenzační rollback vyžaduje identifikovanou původní zálohu, očekávanou aktuální hodnotu, transakci, kontrolu a další auditní událost. **Nepoužívat automatický rollback Fáze A**.
6. Každá skupina musí mít nezávislé testy, které zahrnují duben 2013, hranice CET/CEST a zachování července 2021 a historických nulových oprav.

## Testy

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests scripts
python3 scripts/check_repo_secrets.py
```

CI používá mockované dotazy a nepotřebuje ani nesmí mít databázová tajemství. Testy pokrývají již aplikovanou i zrušenou dávku, re-staging pod jiným ID, duplikáty, staré/změněné hodnoty, `NULL`, neplatný zdroj a nepovolenou veličinu.

## Ověřená aktuální evidence (live read-only)

| Balíček | Veličina | Záznamy | Rozdíl `rain` |
|---|---|---:|---:|
| `rain-2009-2011-utc-midnight-reset-v1` | rain | 328 applied | 175,14 mm |
| `rain-phaseA-june2010-corrected-20261030-v1` | rain | 30 applied | 161,76 mm |
| `rain-phaseA-apply-20261030-v1` | rain + rainRate | 2 + 1 applied | 61,22 mm |
| `rainrate-restore-2009-2025-v1` | rainRate | 58 936 applied | nesčítat jako úhrn |

**Výsledek základní kontrolní relace:** `archive=1679802`, zálohy 328/30/2, červenec 2021 42,5673 mm. Tyto počty odpovídají aktuálně vráceným SELECTům dne 2026-10-30, nikoli garanci stavu v budoucnu.
