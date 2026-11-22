# Finální rozsah a analytické rozhodnutí

Rozsah hlavního GOALu je uzavřen na definovaných etapách A–O. Stav je analyticky dokončen s omezeními, nikoli potvrzení všech historických hodnot a nikoli dokončení skutečné databázové rekonstrukce.

- B5: COMPLETED_WITH_LIMITATIONS — časové/cadence kohorty deterministicky rozděleny; příčiny neznámých mezer zachovány jako review, žádné automatické posuny.
- K3: COMPLETED_WITH_LIMITATIONS — deterministická value/group klasifikace a 324 záznamový návrhový sidecar; historické hodnoty bez podkladů nejsou přeznačeny za ověřené.
- L3: COMPLETED_WITH_LIMITATIONS — 10 aktivních balíčků, 324 field operations (303 RESTORED,21 ESTIMATED), 315 timestampů, 311 unikátních insertů, 13 updates; globální kontrola a lokální package validators/simulace PASS. Všechny návrhy stále čekají na samostatné schválení; některé vyžadují nezávislou revizi.
- O5: COMPLETED_WITH_LIMITATIONS — 77×18 matici doplňují použitelnostní rozhodnutí pro zobrazení, grafy, statistiky, extrémy, trendy a atlas. Bezpodmínečné READY nebylo přiděleno.
- E4: BLOCKED — srážková sémantika zůstává nedoložena; přesný externí důkaz a dopad jsou v `reports/E4_RAIN_SEMANTICS_BLOCKER_FINAL.md`.

Omezení: Q1 2018 chráněno; 2021 diagnostický; historické zálohy/konfigurace nejsou k dispozici dle vlastníka; historické cleaning/migration a fyzická senzorová správnost nejsou plošně prokázány. Pro schvalovanou aplikaci platí `PRE_APPLICATION_CHECKLIST.md` a `FUTURE_RECONSTRUCTION_PLAN.md`. Žádný DB zápis, dry-run, staging ani publikace nebyly provedeny.
