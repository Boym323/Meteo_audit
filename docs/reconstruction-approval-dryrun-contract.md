# Fáze #26: immutable dry-run, owner approval a rollback — pouze simulace

**Záměrná hranice:** Nový modul `meteo_audit.approval_dryrun` neobsahuje SQL adapter, žádný `INSERT/UPDATE/DELETE`, žádné připojení k DB, žádný automaticky aplikovatelný skript. Je to bezpečnostní jádro a syntetické testy. Skutečný MariaDB apply či rollback **není hotový** a vyžaduje samostatné schválení konkrétního manifestu.

## Manifest / preflight

- `CandidateBatch`: striktní cílové schéma `loucka_reconstruction.archive`, neměnná posloupnost unikátních `(target_time_utc,variable)` a kanonický SHA-256 všech přesných operací. Hodnoty mohou být skutečné 0 i `NULL`, ale prázdný návrh a nečíselné sentinelové hodnoty jsou zamítnuty.
- `FieldCorrection`: `expected_old`, `proposed_new`, `source_ref`, `unit_epoch_ref`, `rule_version`, `diagnosis_confidence`, `replacement_confidence`. Tyto důkazní odkazy musí pro budoucí produkční proces projít nezávislou verifikací, ne pouze validací neprázdného řetězce.
- `preflight` bezpečně odmítá chybějící target, již aplikovanou historii, neshodný expected-old (model SQL `<=>`), duplicitu a chráněné období. Vypíše counts, payload hash, immutable before-image a jeho SHA-256. Stav je pouze `READY_FOR_EXPLICIT_APPROVAL_NOT_APPLIED`.
- Ochranná brzda blokuje jakékoliv operace v Q1 2018 a `rain`/`rainRate` během 2021; samostatná změna těchto pravidel by vyžadovala zvláštní doložení, nikoliv nepozorovanou automatickou výjimku.

## Simulace transakce a rollbacku

- `BatchApproval` musí obsahovat konkrétní `batch_id`, SHA-256 přesného manifestu a neprázdnou approver referenci. Jde o simulaci, nikoliv ověřený digitální podpis či owner autorizaci.
- `simulate_atomic_apply` používá kopii snapshotu a až po všech předběžných kontrolách vrací nový stav + receipt; původní stav nedotkne. Opakované nebo konkurenční apply při změně expected-old bezpečně selže.
- `simulate_atomic_rollback` vynucuje shodu receipt, before-image hash a **post-image CAS**. Při následné změně hodnot či pozměněném předobrazu odmítne operaci.
- CI testy pokrývají nulové hodnoty vs NULL, chybějící cíl, stale CAS, kolize historii, duplicitu, změněný hash, replay, konkurující manifest, úspěšný rollback, chybné before-image, chráněné epochy a více změn v jedné kopírovací simulaci.

## Co zbývá pro skutečné dokončení #26

1. Získat per-variable verifikované návrhy (většina z 92 664 operací zůstává QUARANTINE) s originálními raw referencemi a ověřenými jednotkami.
2. Transakční implementaci s `SELECT ... FOR UPDATE`, DB advisory lockem, NULL-safe CAS, immutable before-image storage, append-only audit a idempotency guardem testovat na syntetických databázích v CI; žádný další trvalý server MariaDB se pro tento projekt nezřizuje. Provozní aplikace na stávající `loucka_reconstruction` musí mít nezávislé konkrétní schválení vlastníka.
3. Jako model disaster recovery používat **stávající Proxmox Backup Server** podle [provozní PBS politiky](issue26-pbs-backup-recovery-policy.md): doložit snapshot pro správný DB host a zahrnutí všech disků/datadir, úspěšný backup job a PBS Verify, případně bezpečnou file-level kontrolu; oddělená MariaDB není podmínkou dokončení. PBS integrita není totéž jako reálně otestovaný start obnovené DB. Zvlášť kontrolovat historickou invariantu července 2021 cca 42,567 mm, Fázi A a všechny dřívější override události.
4. Vyžádat explicitní souhlas vlastníka pro **konkrétní batch+SHA**, nikoliv pro celé issue, PR nebo algoritmus. Teprve potom provést testovací apply; produkční DB zůstává nedotknutá.
