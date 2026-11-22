# Rekonstrukce historických dat Počasí Loučka — stav finalizace k 22. 11. 2026

**Charakter dokumentu:** dodatečný stavový zápis do verzovaného projektu. Nejde o nový běh SQL, export databáze, nahrání lokálního pracovního stromu ani potvrzení publikace. Čísla pocházejí z dříve oznámených výsledků finalizačního běhu 17. 11. 2026; při tomto zápisu nebyl k dispozici lokální checkpoint ani přímý přístup k databázi. Výsledky je před jakýmkoli použitím jako podklad pro cutover nutné ověřit proti originálním artefaktům.

## Rozhodující finalizační výsledek (17. 11. 2026)

| Metrika | Dříve oznámený stav |
| --- | ---: |
| Operací v rozhodovacím manifestu | 92 664 |
| `QUARANTINE` | 92 366 |
| `ALREADY_APPLIED` | 298 |
| Z toho již přítomných řádků / oprav polí | 291 / 7 |
| Další `APPLY` / `KEEP` v tomto finalizačním rozhodnutí | 0 |
| Zásahy finalizace do produkčního archivu | 0 |

- **SHA-256 rozhodovacího manifestu:** `a6ed14c902b9bec4e746c00aeb71aed225b9672363592cf5add3d57a3a242ef6`.
- **Lokální checkpoint:** `MASTER_FINALIZATION_CHECKPOINT_20261117.json` (existence a obsah nelze ověřit z GitHubu; **není** zde předstírán ani kopírován).
- `ALREADY_APPLIED` znamená stav **v pracovní rekonstrukci**, nikoli 298 nových zápisů provedených tímto finalizačním krokem ani publikaci opravených měření.
- `QUARANTINE` znamená, že návrh nebyl přijat pro automatické použití; nepřekládat na počet unikátních chybných či opravených měření.
- Počet operací se nesmí zaměňovat za počet původních archivních záznamů.

## Dřívější dílčí práce (historický kontext, nikoli součet schválených oprav)

Po 2. 11. 2026 probíhaly iterativní analýzy a rekonstrukce srážek, teploty a relativní vlhkosti v pracovní databázi `loucka_reconstruction`. Mezi dříve hlášené dílčí výsledky patří:

- Srážkové historické dávky: jedna ze závěrečných rekapitulací uváděla 496 intervalů a 506 změn (včetně 10 historických poruch a 486 obnov `rainRate`). Přesnou návaznost těchto dávek na finální manifest je třeba ověřit; **nepřičítat k 298**.
- Rok 2018, teplota: 35 doložených zásahů z historického zdroje; následovaly lednové pilotní a odhadové dávky včetně 2 725 návrhů/úprav v jedné iteraci a dalšího doplnění. Tyto průběžné počty nejsou potvrzeným finálním certifikovaným stavem.
- Rok 2018, vlhkost: lednová etapa vykazovala 3 850 RH návrhů/rekonstrukcí; další práce se věnovaly únoru a březnu.
- Únor/březen 2018: dřívější rekapitulace winter review uváděla 7 200 korekcí/operací v návrhovém procesu. Rozhodující je finální klasifikace v manifestu, nikoli průběžný součet.
- Srovnávací zdroje ČHMÚ, LuhaMet, ILOUKA4 a WH1080 mají odlišnou důkazní sílu; modelované/regionální hodnoty nejsou místní naměřená data.

**Pozor:** starší `reconstruction_changes` log obsahuje aplikované i vrácené události. Součty historických transakcí, pilotů a kandidátů se s finálními výsledky nepřekrývají triviálně a nesmějí být používány jako míra úspěšnosti rekonstrukce.

## Web a publikace

Podle stavu oznámeného 17. 11. 2026:

- API/web prošly kontrolami `READY`, `history`, `daily`, `monthly`, `yearly` = `PASS` po úpravě kontroly oprávnění; šlo o test preview, nikoli certifikaci samotných historických hodnot.
- Frontend vykazoval kvalitu a původ hodnot. Preview commit byl hlášen jako `821ad21d675019c14a040add377f5a3ad99049eb`; **tento hash není potvrzen jako commit v tomto repozitáři** (související webový projekt se spravuje samostatně).
- **Nebyl proveden** produkční cutover rekonstrukce ani `weectl`/WeeWX rebuild denních souhrnů.
- Historické rekordy se nesmějí označovat za certifikované, dokud nejsou splněny brány z [reportu 2. 11.](2026-11-02-publication-readiness.md).
- Aktuální API a živý stav webu nebyly 22. 11. nezávisle otestovány při vytváření tohoto zápisu.

## Co se zatím nepodařilo synchronizovat do GitHubu

**Repozitář `main` měl při kontrole 22. 11. 2026 HEAD `25548d38d51c70c09dd66f5eeb42f05333d308ec` z 2. 11.** Novější lokální práce proto nejsou součástí `main`.

- Lokální commit `b0b5750` byl 17. 11. hlášen jako neodeslaný kvůli chybějícímu Git přihlášení. Přes GitHub se jeho obsah nedá načíst, dokud není skutečně pushnut z LXC. Nepředstírat reprodukci commitu ze slovního popisu.
- Existují vzdálené, avšak nezačleněné větve/PR: [#32 — ČHMÚ měsíční srážky](https://github.com/Boym323/Meteo_audit/pull/32), [#33 — ČHMÚ RH/teplota pilot](https://github.com/Boym323/Meteo_audit/pull/33), [#34 — downloader referencí ČHMÚ 2018](https://github.com/Boym323/Meteo_audit/pull/34). Tyto větve nenahrazují kompletní obsah lokálního `/opt/meteo-audit`.
- Otevřené byly také [#30](https://github.com/Boym323/Meteo_audit/pull/30), [#29](https://github.com/Boym323/Meteo_audit/pull/29) a [#28](https://github.com/Boym323/Meteo_audit/pull/28). Před sloučením prověřit návaznost a duplicity.
- Samotný rozhodovací manifest, lokální finální checkpoint, důkazní sady, aktuální skripty/testy a případné necommitnuté soubory **nebyly tímto stavovým zápisem fyzicky nahrány do repozitáře**.

## Další bezpečný postup

1. V původním LXC **`/opt/meteo-audit`** ověřit `git status --short`, `git branch -vv`, `git log --all --oneline --decorate -20`, `git remote -v` a diff proti `origin/main`. Neměnit DB.
2. Zkontrolovat staged soubory, vyloučit `.env`, přístupové údaje, dumpy a velké neanonymizované exporty; ověřit `scripts/check_repo_secrets.py` a testy.
3. Odeslat dosud nepushnuté lokální commity a příslušné malé reprodukovatelné skripty, metodiky, metadatové manifesty a reporty do **pracovní větve**. Neodesílat produkční data ani tajemství.
4. Porovnat checkpoint a manifest s logem `loucka_reconstruction` read-only, ověřit identitu a počty operací, časové hranice, provenance a možnost rollbacku; přidat důkazní hash a validační výstupy.
5. Otevřít PR do `main`, spustit CI; před publikací řešit samostatné schválení, bezpečnostní zálohu, neměnný cutoff a přepočet WeeWX agregací.

**Bezpečnostní limit:** Tento dokument nemění `archive` ani jediný řádek produkce; není příkazem spustit SQL zápisy nebo automaticky pustit karanténu. Původní zdroje zůstávají read-only. Konkrétní hodnoty finálního manifestu se musí prokazovat originálním artefaktem, nikoli tímto sekundárním zápisem.
