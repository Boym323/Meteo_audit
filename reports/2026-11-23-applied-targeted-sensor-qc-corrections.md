# Skutečně aplikované kusové QC opravy v `loucka_reconstruction` — 23. 11. 2026

**Stav:** `APPLIED`, **60 záznamových změn** (ve dvou transakčních auditních dávkách), nikoliv plán, odhad ani teprve PR. Původní produkční databáze `pocasi-loucka.eu.archive` zůstala nezměněna. Tyto změny byly zapsány přes `Weather_MCP.reconstruction_apply_corrections`, který povoluje pouze pracovní rekonstrukci, provádí expected-old-value (CAS) a vede neměnnou auditní stopu. Žádný nový `RESTORED` zdroj nebyl vymyšlen; cílové hodnoty jsou `NULL`.

## Výsledek

| Auditní batch | Proměnná | Počet | Původní extrémy | Náhrada |
|---|---|---:|---|---|
| `qc-extra-temp-outliers-20261123-v1` | `extraTemp1` | 2 | 114,72; 190,41 °C v časech 2024-02-17 | `NULL` |
| stejný batch | `extraTemp2` | 14 | cca **822,4 °C**, 2024-02-17 14:25–15:30 UTC | `NULL` |
| `qc-soil-negative-outliers-20261123-v1` | `soilTemp1` | 13 | 2 v roce 2022, 11 v roce 2026 pod −20 °C | `NULL` |
| stejný batch | `soilTemp5` | 10 | 2026 pod −40 °C | `NULL` |
| stejný batch | `soilTemp6` | 21 | 2026 pod −40 °C | `NULL` |
| **CELKEM** | | **60** | | **60× NULL** |

Obě dávky nejprve úspěšně prošly `dry_run=true` s kontrolou `expected_old_value`; teprve potom `dry_run=false`. Nástroj potvrdil:

- Extra teploty: **applied=16, verified=16, unchanged=0, replayed=false**.
- Půdní teploty: **applied=44, verified=44, unchanged=0, replayed=false**.
- SQL post-check: `reconstruction_changes` má přesně 2+14+13+10+21 aplikovaných auditních událostí, všechny `new_value IS NULL`.
- Ve **správné rekonstrukci**: nyní **0** řádků 2024 s `extraTemp1>80 OR extraTemp2>100` a **0** řádků 2022–2026 s `soilTemp1<-20 OR soilTemp5<-40 OR soilTemp6<-40` v kontrolovaném řezu.
- Produkce nadále drží **14** původních problémových časových řádků s extra teplotami a **44** časových řádků s půdními odlehlostmi — doloženo, že nebyla přepsána.

### Reprodukovatelný read-only receipt

```sql
SELECT batch_key,variable,COUNT(*) n,
       SUM(new_value IS NULL) num_set_to_null,
       MIN(target_time) first_utc,MAX(target_time) last_utc
FROM loucka_reconstruction.reconstruction_changes
WHERE batch_key IN (
 'qc-extra-temp-outliers-20261123-v1',
 'qc-soil-negative-outliers-20261123-v1'
) AND state='applied'
GROUP BY batch_key,variable ORDER BY batch_key,variable;

SELECT
 (SELECT COUNT(*) FROM loucka_reconstruction.archive
  WHERE dateTime>=1704067200 AND dateTime<1735689600
  AND (extraTemp1>80 OR extraTemp2>100)) extra_still_bad,
 (SELECT COUNT(*) FROM loucka_reconstruction.archive
  WHERE dateTime>=1640995200 AND dateTime<=1795415700
  AND (soilTemp1<-20 OR soilTemp5<-40 OR soilTemp6<-40)) soil_still_bad,
 (SELECT COUNT(*) FROM `pocasi-loucka.eu`.archive
  WHERE dateTime>=1704067200 AND dateTime<1735689600
  AND (extraTemp1>80 OR extraTemp2>100)) production_extra_rows_unchanged,
 (SELECT COUNT(*) FROM `pocasi-loucka.eu`.archive
  WHERE dateTime>=1640995200 AND dateTime<=1795415700
  AND (soilTemp1<-20 OR soilTemp5<-40 OR soilTemp6<-40))
  production_soil_rows_unchanged;
```

Pro rozhodnutí o validitě původních čísel a jejich povolené náhradě viz [hloubkový audit](2026-11-23-deep-sensor-pm25-soil-mapping-followup.md) a [read-only zdrojové SELECT](../sql/readonly/production_sensor_mapping_pm25_followup_20261123.sql).

## PM2.5 a další měření, která **nebyla fyzicky přepsána**

- PM2.5 2024: 2 128 intervalů s `pm25_1>=500`, z toho 1 401 `~999.9`. Jsou totožné s GW kopií, **nemají nezávisle doložené náhradní hodnoty**, nelze je změnit na nulu ani vymazat jako jistě chybné. Zůstávají v obou DB. Webové API implementuje **časově omezený publikovací HOLD** a nepropustí staré kontaminované `archive_day_*` do certifikovaných statistik; viz webový PR #173.
- Půdní `soilTemp5/6` 2026 mezi −10 a −40 °C: dalších přes 2 900 podezřelých původních hodnot, často při ostatních sondách nad 0 °C. **Nebyly přepsány**; původní fyzický/kalibrační důkaz chybí. Ve webové publikační vrstvě přidán `UNVERIFIED` HOLD pro toto pásmo.
- Září 2022 `extraTemp2`: 1 765 čísel 27,57–99, není prokázána identita teplotního senzoru a může jít o jiný kanál; **0 přepisů**. Veřejná publikace jako teplotní rekord zadržena, historický originál dostupný pro forenzní kontrolu.

## Vlastnictví a omezení

Tato opravná etapa **není** přepnutím produkce na rekonstrukci. Nezakládá neprokázané `MEASURED` a nemění `archive_day_*`. Zůstává potřeba konzistentní **backup + izolovaný restore celé rekonstrukce** před hromadnou migrací / masovým přepisem dalších tisíců hodnot. 60 jednotlivě ověřených změn je vratných z archivních originálů a `reconstruction_changes.old_value`, ale neznamená to, že celá MariaDB má prokázaný restore checkpoint.

**Pravidlo:** analytika či frontend musí používat QC masks nad původními daty nebo explicitně připravený schválený rekonstruovaný dataset; nesmí automaticky přepočítávat rekordy z původních denních agregací.
