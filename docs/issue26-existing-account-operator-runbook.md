> **Dodatek 23. 11. 2026: čtecí přístup bez přihlašovacích údajů loucka_audit v LXC**
>
> Codex ověřil, že na zl-dev-frontendPocasi existují bezpečně uložené
> údaje k **již existujícímu** loucka_web_ro a připojení na
> lo-infra-db-mariadb01 funguje. Aktuálně však tento účet nemá žádné
> SELECT oprávnění k loucka_reconstruction (SQL chyba 1142 a při pokusu
> o výběr databáze chyba 1044).
>
> Po rozhodnutí vlastníka lze ručně spustit v Navicatu
> soubor sql/issue26_grant_existing_webro_select_only.sql:
> přidává SELECT **pouze čtyřem pracovním tabulkám** účtu
> loucka_web_ro@192.168.0.131; nezřizuje účet ani jiné objekty.
> Tím se mění oprávnění již existujícího webového účtu,
> takže je nutné zohlednit přístup webové aplikace k těmto datům.
>
> Nový runner připouští pro **status/inspect** buď
> loucka_audit@%, nebo loucka_web_ro@192.168.0.131;
> **apply/rollback stále vyžaduje výhradně loucka_audit@%**
> a nezávislé přesné podepsání dávky.
>
> Spuštění bez zapisovacího účtu z kořene worktree na LXC:
>
>     PYTHONPATH=src .venv/bin/python scripts/issue26_operator.py status \
>       --client-file /root/<EXISTUJICI_PRIVATNI_WEB_RO_KONFIGURACE>
>
> Konkrétní cestu musí určit Codex z dříve nalezeného bezpečného
> souboru, bez výpisu hesla. Pokud CNF soubor neexistuje, lze jej
> bezpečně připravit pouze z již dostupných soukromých credentials,
> bez změny hesla nebo založení účtu.
>
> Před aplikací GRANT se STATUS má nadále odmítnout jako NO-GO,
> žádný oprávněný účet ani SQL právo není vhodné předstírat.
>
# Issue #26: existing account operator workflow (2026-11-23)

Binding owner decisions: no new SQL users, no new persistent MariaDB, no
PBS/backup checks, no manual edits to daily archive_day tables. Reuse
the existing loucka_audit account.

## Verified live conditions (read-only SQL)

The MariaDB host is lo-infra-db-mariadb01, server_id=1, schema
loucka_reconstruction. Both issue26 audit tables exist and were empty
when last checked. Column names/types/collation, indexes and composite
foreign key match the reviewed DDL, with no unexpected triggers.

Information_schema.USER_PRIVILEGES shows that loucka_audit@% has
global SELECT, INSERT, UPDATE and many more powerful privileges,
including CREATE USER and DROP (grantable). This confirms the existing
account is broadly privileged; its rights are NOT being changed. The
operator application must enforce its own restrictions.

## Ready on the existing LXC 192.168.0.131

The new script is scripts/issue26_operator.py. It has four modes:

- status (default): SQL SELECT only. Confirms exact server/ID,
  CURRENT_USER() = loucka_audit@%, all audit DDL/engine/index/FK checks,
  event counts and July 2021 rainfall = 42.567 mm.
- inspect: SQL SELECT only. Validates original read-only review evidence,
  checks the current manifest, hashes, old-value CAS and change history.
- apply --execute: a valid time-limited owner-signed receipt and
  human-entered full phrase APLIKUJI-DAVKU:<batch_id>:<SHA>:<BEFORE_SHA>
  are mandatory. The engine then uses row locks and NULL-safe CAS
  in one atomic transaction, with append-only audit events.
- rollback --execute: NEW owner-signed receipt, different from the
  previous APPLY signature, plus a human-entered separate phrase
  VRATIT-DAVKU:<batch_id>:<SHA>:<BEFORE_SHA>. Checks current post-image
  for exact match and does not remove previous audit events.

The script does not create any accounts, grant privileges, create tables,
modify the production archive or sign on the owner's behalf. Execute
modes require an interactive terminal, a reviewed manifest and previously
created source evidence.

### MariaDB client credentials

Reuse the existing credential for loucka_audit (do not rotate or create
accounts). Put it, without exposing the password, in an operator-owned
absolute non-symlink CNF file mode 0600, for example:

    [client]
    host=192.168.1.52
    port=3306
    user=loucka_audit
    database=loucka_reconstruction
    password=<PLACEHOLDER>

This CNF must never be committed to Git.

### First: inspect existing DB read-only

    PYTHONPATH=src python3 scripts/issue26_operator.py status \
      --client-file /root/meteo-loucka-audit.cnf

Expected: ISSUE26_EXISTING_ACCOUNT_READY_NO_DATA_WRITES, DDL_VERIFIED,
new_sql_users=0 and db_writes=0. Refuse any batch if this fails.

### Next: only when a genuinely evidenced candidate exists

Prepare an exact FieldCorrection manifest, individually corroborated
by the raw source, unit epoch, source time and methodology. Use the
existing read-only SQL export script:

    PYTHONPATH=src python3 scripts/issue26_db_readonly_review.py \
      --manifest /private/issue26-batch.json \
      --client-file /root/meteo-loucka-audit.cnf \
      --expect-host lo-infra-db-mariadb01 \
      --expect-server-id 1 \
      --output-dir /var/lib/meteo-audit/reviews/issue26-batch-unique

Output includes review-evidence.json, before-image.json and completion
receipt. These are NOT owner approval or source validation by themselves.

    PYTHONPATH=src python3 scripts/issue26_operator.py inspect \
      --client-file /root/meteo-loucka-audit.cnf \
      --manifest /private/issue26-batch.json \
      --review-evidence /var/lib/meteo-audit/reviews/issue26-batch-unique/review-evidence.json

After independent source review, the existing issue26_approval_review.py
challenge and sign commands can produce a private operator receipt
bound to the exact batch ID, payload SHA and before-image SHA.
No PR merge or issue state constitutes approval.

### Apply only with distinct exact owner authorization

    PYTHONPATH=src python3 scripts/issue26_operator.py apply \
      --client-file /root/meteo-loucka-audit.cnf \
      --manifest /private/issue26-batch.json \
      --review-evidence /var/lib/meteo-audit/reviews/issue26-batch-unique/review-evidence.json \
      --receipt-file /private/issue26-apply-receipt.json \
      --key-file /root/meteo-issue26-approval.key \
      --execute

This cannot run non-interactively. It requires an unexpired signed
approval and exact second entered APPLY phrase; all CAS checks are
repeated inside a transaction. The user has NOT authorized any specific
real batch in this session; do not invoke APPLY automatically.

### Rollback only with another signed authorization

Issue a NEW HMAC approval receipt via issue26_approval_review.py sign.
Using the original APPLY receipt for ROLLBACK is rejected.

    PYTHONPATH=src python3 scripts/issue26_operator.py rollback \
      --client-file /root/meteo-loucka-audit.cnf \
      --manifest /private/issue26-batch.json \
      --review-evidence /var/lib/meteo-audit/reviews/issue26-batch-unique/review-evidence.json \
      --receipt-file /private/issue26-rollback-receipt.json \
      --key-file /root/meteo-issue26-approval.key \
      --execute

Requires full manual ROLLBACK phrase, same manifest and prior image,
original immutable audit and post-image CAS.

## Remaining tasks

- Verify the actual operator LXC can authenticate as the existing
  loucka_audit@%; read-only connector access is not proof of an
  existing private credentials file on LXC.
- Obtain a sourced, independently reviewed candidate manifest and
  SQL before-image; no real new correction applied here.
- Complete independent read-only Phase A and historical override audit.
- Never create more accounts, DB instances or manual daily extremes.
