# GO / NO-GO — revize 2026-11-24

## GO

- Review aktuálního operation-level diffu `FINAL_MIGRATION_OPERATIONS.jsonl.gz` při řezu `1795541700`.
- Read-only source audit a independent validator: PASS.
- Všech 60 nových teplotních NULL_CLEAR událostí přesně odpovídá poslednímu aplikovanému rekonstrukčnímu eventu a produkční before-value.

## NO-GO

- Produkční migrace: žádná operace nemá produkční schválení; 1 497 audit/current-state rozdílů navíc vyžaduje review.
- Obnova/test migration/WeeWX/whole rollback: zatím nelze provést na schválené izolované instanci.
- Starší `loucka_migration_test` schema běží na stejném MariaDB serveru `server_id=1` a nesplňuje požadavek izolované instance.
- Tlakové odhady: nikdy nezapisovat do `archive.pressure` ani oficiálních statistik bez nového samostatného schválení; nynější politika je výslovné NO-GO.

## Aktuální počty

- Archive rows při `dateTime <= 1795541700`: produkce 1 687 316; rekonstrukce 1 697 715.
- 10 399 řádkových INSERT a 82 325 field operations; spolu 92 724 operací.
- 80 237 upravených existujících timestampů; 0 produkčních timestampů chybí v rekonstrukci.
- 895 NULL_CLEAR v novém diffu: 835 starších invalidací plus 60 nových teplotních NULL_CLEAR.
- Všechny field operations mají auditní vazbu; 10 399 INSERTů mají related timestamp audit events a source claim. Source claim není automaticky přímé requery ani approval.
- Všech 92 724 operací má `production_approval_status=NOT_APPROVED`.

Proxmox node access/privilege/capacity nebylo možné z aktuálního LXC potvrdit; připravený provisioning postup s fail-closed capacity checks je `ISOLATED_TEST_PROVISIONING_2026-11-24.md`. Produkce zůstala beze změny.
