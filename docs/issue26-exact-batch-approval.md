# Issue #26 — schválení konkrétní opravné dávky (bez záloh)

## Rozsah

Na výslovné rozhodnutí vlastníka se v tomto projektu od 23. 11. 2026
**ignoruje kontrola záloh/PBS**. Viz
[rozhodnutí o rozsahu](issue26-owner-decision-ignore-backups.md).
To neznamená, že jsou zálohy ověřené; **riziko ztráty celého serveru je
přijaté, nikoli technicky odstraněné**. Zálohování se už nemá objevovat
jako podmínka issue #26.

Zachováváme bezpečnost **jednotlivých změn** (neřeší katastrofické
poškození celého serveru): přesný manifest, výslovné schválení, CAS,
before-image, audit a podmíněný rollback.

## Přidaný modul

- `meteo_audit.approval_gate`: přesný text schválení obsahující
  `batch_id`, `payload_sha256` a `before_image_sha256`.
- Schvalovací receipt je časově omezená, HMAC-SHA256 ověřitelná
  struktura pro jedinou dávku; změna původních hodnot, veličiny,
  navrhované hodnoty nebo pravidla znamená nové schválení.
- `verify_fresh_snapshot()` znovu prověřuje CAS a kolizi s již
  aplikovanou historií před případnou budoucí SQL transakcí.
- `scripts/issue26_approval_review.py` nabízí offline
  `challenge`, `sign`, `verify`, bez jakéhokoli SQL připojení
  nebo úpravy meteorologických hodnot.

**Bezpečnostní hranice:** HMAC potvrzuje držení privátního klíče,
nikoliv nezávisle ověřenou identitu člověka. Vlastní evidenci
schvalovatele, ochranu klíče a rozdělení oprávnění musí zajistit
provozní postup. Review snapshot je pouze vstup; **není možné
považovat jej za pravdivý bez samostatného read-only SQL exportu**.
Až případný reálný SQL writer musí pod transakčním zamykáním znovu
ověřit aktuální hodnoty, historii a souhlas. PR ani CI dávku
automaticky nepovoluje.

## Použití na syntetickém příkladu

Připravit JSON manifest přesně se schématem
`loucka-field-correction-review-v1` a cílem
`loucka_reconstruction.archive`, unikátními operacemi
`FieldCorrection` a odpovídajícím seznamem předobrazů
`[{target_time_utc, variable, old}]`.
Tyto soubory musí mít skutečnou, zkoumanou provenienci,
nikoliv automaticky generovanou náhradu.

Jednorázový tajný HMAC klíč vytvořit mimo repozitář:
`umask 077; openssl rand 32 > /root/meteo-issue26-approval.key`.
Přístup ke klíči není veřejný a soubor nemá být v Gitu.

```bash
PYTHONPATH=src python3 scripts/issue26_approval_review.py challenge \
  --manifest /private/batch.json --before-image /private/before.json

PYTHONPATH=src python3 scripts/issue26_approval_review.py sign \
  --manifest /private/batch.json --before-image /private/before.json \
  --operator owner:local-reviewed \
  --key-file /root/meteo-issue26-approval.key \
  --receipt-file /private/batch-approval.json
# Program interaktivně vyžádá přesný challenge z předchozího příkazu.

PYTHONPATH=src python3 scripts/issue26_approval_review.py verify \
  --manifest /private/batch.json --before-image /private/before.json \
  --key-file /root/meteo-issue26-approval.key \
  --receipt-file /private/batch-approval.json
```

Úspěch znamená `VALID_SIGNED_APPROVAL_NOT_APPLIED`, **nikoli**
provedenou opravu. Receipt je nutné uchovat s předobrazem a
auditovat; nikdy necommitovat klíč.

## Zbývá do uzavření #26

- Implementovat a integrovat **transakční SQL writer** pouze proti
  `loucka_reconstruction.archive` s nezměnitelnou auditní historií
  a per-field NULL-safe CAS pod SQL lockem.
- Jeho předpoklady zahrnují načtení skutečných read-only SQL
  hodnot před schválením a **nové porovnání pod transakcí** po schválení.
- S rollbackem obnovovat staré hodnoty pouze pokud aktuální stav
  stále odpovídá přesnému schválenému post-image.
- Provést CI syntetické regresní testy dvou konkurenčních transakcí,
  opakovaného apply, NULL vs 0 a Fáze A/2021 guard.
- Teprve po výslovném schválení konkrétní dávky je možné
  použít opravený runner. Toto rozhodnutí o zálohách **není**
  souhlasem k zápisu do DB.

Denní extrémy necháváme WeeWX na pozdější přepočet podle PR #71.
