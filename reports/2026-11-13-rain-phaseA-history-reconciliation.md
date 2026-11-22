# Revalidace aplikovaných historických korekcí deště Fáze A

**Snapshot:** 2026-11-13. Read-only přesná reconciliation záložních řádků → původní dávka → poslední event → current archive. Rozsah: tři stávající zálohy 2009–2011/2010/2011; 360 unikátních cílů. Nejde o nové návrhy.

| Záloha / rozsah | Backup rows | Přesně 1 původní applied event | old_value = backup | Původní event new=0 | Current zero | Current NULL po pozdějším review | Current = latest event |
|---|---:|---:|---:|---:|---:|---:|---:|
| Půlnoční reset 2009–2011 | 328 | 328 | 328 | 328 | 328 | 0 | 328 |
| June 2010 Phase A | 30 | 30 | 30 | 30 | 12 | 18 | 30 |
| Ostatní Phase A | 2 | 2 | 2 | 2 | 1 | 1 | 2 |

Všechny tři backup sady mají přesně jednu původní applied událost na každý target; její old_value přesně souhlasí s rain_before, žádná událost nechybí ani není duplicitní. Všech 360 původních událostí nastavilo rain=0. U všech 360 current hodnoty odpovídají poslední archivované události.

Důležitá chronologie: po původním vynulování bylo 19 targetů později supersedováno dávkou rain-2010-2011-phaseA-unknown-null-review-v1: 18/30 cílů z června 2010 a 1/2 z malé Phase A sady. U všech 19 je pokračování řetězce konzistentní: původní backup hodnota → první applied new=0 → následný event old_value=0, new_value=NULL → current archive NULL. Důvod v historii označuje přehodnocení ne-půlnoční counter corruption a zachování NULL, protože skutečný lokální rain/rate zůstává neznámý. Těchto 19 proto nyní správně není vedeno jako nula; tento audit je nevrací.

Původní odborná diagnóza resetů/artefaktů a upozornění, že nulová náhrada není absolutní meteorologická pravda, zůstávají v reports/parallel-audit/01-historic-rain.md a CONFIRMED_CANDIDATES.md. Tato nová reconciliation potvrzuje účetní provenienci a aktuální stav, nikoli nezávisle meteorologickou správnost každého původního rozhodnutí. Jednotkový/režimový problém rain před/po dubnu 2013 a dostupnost raw packetů zůstávají ER-04.

Reprodukční SQL: sql/readonly/rain_phaseA_backup_history_reconciliation.sql; agregovaný CSV: reports/2026-11-13-rain-phaseA-history-reconciliation.csv; lokální kontrola: scripts/validate_rain_phaseA_history_reconciliation.py. Databáze byla dotázána pouze přes SELECT.
