# Konsolidace Meteo_audit a vypořádání issues — 22. 11. 2026

## Stav synchronizace

- GitHub `main` při zahájení i v aktuálním fetchi: `747a654dd8b2269b3878211337118d8b894eef72`.
- Aktuální souborová inventura LXC je v [CSV](reports/data/2026-11-22-local-file-inventory.csv) a [metodice](reports/2026-11-22-local-file-inventory.md). Po odfiltrování `.git`, virtuálních prostředí, cache, `node_modules`, `build` a `dist` bylo zkontrolováno 5 282 cest: A 1 786, B 2 784, C 712. To jsou počty inventarizovaných cest, nikoli počty bezpečně publikovatelných souborů.
- Původní údaje 4 817 souborů a 3 213 chybějících cest nejsou reprodukovatelné, protože odkazovaný CSV inventář v LXC chyběl a jeho filtry nejsou známy. Aktuální vstupní pracovní strom je od `main` velmi odlišný; nebyly na něj aplikovány reset ani hromadné stage.
- Důležité historické výsledky, které už jsou v `main`, nebyly kopírovány znovu: registry provenance, politiky statistické publikace, checkpointy a synchronizační dokumentace. Nové bezpečné přehledy: inventář a [stav finalizace](reports/2026-11-22-reconstruction-finalization-status.md).
- Veřejné repo není úplnou zálohou LXC. Lokální soubory C zůstávají na místě; připravte šifrovanou externí zálohu s přístupovými a retenčními omezeními, SHA-256 manifestem, evidencí účelu/závislostí a periodicky ověřovanou obnovou. Detailní lokální manifest obsahuje cesty, velikosti a hashe. Zejména SQLite 1 663 004 672 B, 114 ZIP archivů (dříve celkem 3 403 538 773 B), hodnotový JSONL manifest (~129 MB) a migrační CSV (~83 MB) zůstávají neveřejné. Nešifrované `.env`, klíče a přihlašovací údaje se nezálohují jako běžné projektové artefakty.

## Issues #14–#27

Živý seznam při kontrole obsahoval 14 otevřených issues #14–#27. Popisy a závislosti byly načteny. Nezavíral jsem žádné issue: pro většinu akceptace vyžaduje nové read-only databázové důkazy, dobovou konfiguraci nebo fyzikální sémantiku, které v této práci nebyly znovu ověřeny. Dokončené části a blokace:

| Issue | Před → po | Provedená práce / důvod otevřenosti |
|---|---|---|
| #14 | open → open | Historický PR #28 je sloučen; aktuální fáze A spustila lokální integrity checker, ale akceptace vyžaduje read-only CLI běh nad aktuální DB a kontrolní součty. Nové DB ověření nebylo provedeno. |
| #15 | open → open | Potřebuje dobovou WeeWX formuli, kompletní hodnotový manifest 1 077 odchylek a dopad na denní/odvozené veličiny. Bez nového výpočtu a DB vstupů. |
| #16 | open → open | Potřebuje per-epoch déšť/rychlost, nezávislé intervalové reference a RainRater sémantiku; žádné nové měření ani veřejný hodnotový export zde nebyl proveden. |
| #17 | open → open | Mapper/firmware a raw GW3000 payload nebyly doloženy. Nezaměňovat historické pole se správným kódováním ani nevymýšlet reálné payload fixture. |
| #18 | open → open | Tlakový význam, jednotky WH1080, srovnávací zdroj a 28 hraničních konfliktů potřebují DB/reference evidence. |
| #19 | open → open | 758 kandidátů a 1 301 frozen záznamů potřebují per-variable review; shoda kopií není nezávislá reference. |
| #20 | open → open | 71 391 slotů je jen časová příležitost; úplná klasifikace 20 950 mimo-staging řádků nebyla nově provedena. |
| #21 | open → open | Epochy jednotek a čítačů vyžadují dobovou konfiguraci WeeWX/hardware; bez DB/referenčních artefaktů nelze potvrdit přesné hranice. |
| #22 | open → open | Divergence GW1000, tlak a 2026 meteorologické/senzorové řady potřebují párová data a konfigurační metadata. |
| #23 | open → open | Auditní dokumentace existuje, ale issues žádá kompletní roční/měsíční QC mapu a dobová senzorová metadata; aktualitu databázových důkazů nelze potvrdit. |
| #24 | open → open | Dokumentované anomálie vyžadují sensor_epoch, instalaci/RSSI/raw payload a testy signal vs zero; nedoloženo. |
| #25 | open → open | V repozitáři už existuje quality/provenance model a API plán, ale ERD, vývojová migrace, více QC na řádek a UI akceptace splněny nejsou. |
| #26 | open → open | Jsou návrhy preflightu/rollbacku, ale issue požaduje testy konkurenční aplikace na izolované DB a obnovu zálohy. V tomto běhu neproběhly. |
| #27 | open → open | Zastřešující plán na `main` má stále všech 14 dílčích úloh nezaškrtnutých; aktualizace jednotlivých stavů není doložena, proto se nepřepisuje na hotovo. |

Odkazy: [issues](https://github.com/Boym323/Meteo_audit/issues?q=is%3Aissue+is%3Aopen).

## Pull requests

| PR | Stav | Zjištění a rozhodnutí |
|---|---|---|
| #32 | open draft → open draft | Veřejné referenční workflow prošlo. Python job byl po 24 h zrušen před kroky (nešlo o neúspěšný test). Diff je jen retrieval workflow. Licence/podmínky ČHMÚ a chybějící rerun brání merge. |
| #33 | open draft → open draft | Stejný stav CI: public-reference prošel, Python job zrušen před kroky. Užitečný nezávislý retrieval pilot; reprodukovatelné načtení a licence/atribuce je třeba doložit před merge. |

Ostatní starší PR byly již uzavřeny/sloučeny; jejich obsah se neimportoval opakovaně. CI pro oba otevřené PR nebylo možné v této fázi znovu vyvolat bez upravení jejich větví; merge by byl v rozporu s požadavkem na skutečný výsledek CI. Review komentáře u #32/#33 nebyly vráceny žádné.

## Stav historické rekonstrukce

- **Dokončeno v rámci dostupných důkazů:** konsolidovaný checkpoint 17. 11. má 92 664 operací; lokální ověřovač 22. 11. potvrdil SHA a součty: 92 366 `QUARANTINE`, 298 `ALREADY_APPLIED`, další `APPLY`/`KEEP` = 0. Výsledek `ALREADY_APPLIED` se týká testovací/pracovní rekonstrukce, nikoli produkce.
- **Neověřeno znovu:** aktuální počty `loucka_reconstruction.archive`, produkční lag, 231 GW1000 řádků mimo rekonstrukci/produkci a konkrétní neprázdné dodatečné historické sloupce. Tyto dříve hlášené údaje jsou časově závislé snapshoty.
- **Otevřené odborné brány:** Q1 2018 chráněno a dříve zamítnutý SELECT na referenční schéma; 2021 diagnostic-only; srážky a GW3000 E4 nerozhodnuty; nezávislá přenositelnost RH mezi stanicemi omezená; časové posuny 2015–2017 vyžadují časovou osu; 80sloupcové schéma neobsahuje všechny historické veličiny.
- **Připravená cesta:** (1) nové read-only snapshoty a watermarky pro cílový archiv, produkci a GW1000; (2) field-level manifest obnovitelných měření s UTC, původem, jednotkami, confidence a explicitními unresolved položkami; (3) schválené schéma zachování dodatečných veličin; (4) izolovaný test s ověřenou zálohou, CAS, audit append-only a rollback; (5) průběžný insert-only sync s watermarkem/monitoringem; (6) opakované integrity a aplikační ověření před vyřazením starých DB. Produkční migrace vyžaduje samostatné výslovné schválení, které nebylo dáno.
- **Vyřazení starých databází:** blokuje chybějící úplné field-level konkordance, nevyřešené jednotky/srážky, neověřená obnova záloh, chybějící historické sloupce a nedoložená kontinuita synchronizace.

## Bezpečnost a testy

- Lokální finalizační integritní skript: PASS, porovnává manifest/checkpoint/diff/summary; DB přístup `false`, hodnotové řádky nevypisuje.
- GitHub `main` CI při zahájení: poslední běh na `747a654` úspěšný.
- PR #32/#33: jeden veřejný referenční job úspěšný, Python joby zrušené po 24 h před zahájením kroků; žádný merge.
- Secret scanner se v tomto konsolidačním PR zatím nespouštěl. Před merge je vyžadováno CI na přiloženém CSV (cesty/hash/velikosti pouze), nikoli na neveřejných payload datech.
- Nebyl proveden DB zápis, DDL, produkční deploy, změna živého sběru ani mazání archivů.

## Závěrečná kontrola

GitHub snapshot byl načten přes API/CLI: `main` `747a654…`, 14 otevřených issues #14–#27 a 2 otevřené Draft PR #32–#33. Finální znovunačtení po tomto PR a CI doplní jeho merge SHA a aktuální počty; do té doby jde o report stavu před merge. Lokální pracovní větev má 4 731 záznamů změněného/necommitnutého stavu a 1 568 odlišných cest oproti vzdálenému `main`; žádné významné změny z tohoto stromu nebyly hromadně publikovány, protože ještě neprošly obsahovou a bezpečnostní kontrolou. Inventář poskytuje cestu po cestě vysvětlení A/B/C.
