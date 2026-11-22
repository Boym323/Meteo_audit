# Rekonstrukce historických dat Počasí Loučka — stav ověřený 22. 11. 2026

Tento dokument odděluje ověřené místní souborové kontroly od starších databázových snapshotů. V tomto běhu nebylo provedeno nové SQL připojení; produkční DB, historické zdroje, živý GW3000 sběr a web nebyly změněny.

## Rozhodnutí migračního běhu 17. 11. 2026

Lokální skript `scripts/verify_finalization_integrity.py` byl spuštěn 22. 11. 2026. Výsledek `PASS` potvrzuje shodu hashů a součtů manifestu, checkpointu, rozhodovacího shrnutí a CSV diffu:

| Stav | Počet operací |
| --- | ---: |
| Celkem | 92 664 |
| `QUARANTINE` | 92 366 |
| `ALREADY_APPLIED` | 298 |
| Další `APPLY` / `KEEP` | 0 / 0 |

298 znamená dříve ověřené operace v pracovní/testovací rekonstrukci, nikoli produkční zápisy. Integrity check nepřistupuje k DB a nevypisuje jednotlivé hodnotové řádky. Podrobné souhrnné ověření je v `reports/data/2026-11-22-finalization-integrity-verification.json`.

## Zbývající blokace rekonstrukce

- Q1 2018 zůstává chráněné. Dříve zaznamenaný přístup k nezávislému referenčnímu schématu byl zamítnut; není doloženo nové oprávnění.
- Rok 2021 je diagnostický; samotná diagnostika neopravňuje k publikaci.
- Historické srážky a GW3000 E4 zůstávají nevyřešené. Starší stav evidoval 462 hodnot `rain`/`rainRate` jako blokované; aktuální číselný stav nebyl znovu načten z DB.
- WeeWX denní souhrny nebyly znovu sestaveny ani nezávisle ověřeny. Produkční cutover ani web deploy neproběhl.
- Předchozí 298 kandidátů vyžadovalo samostatné schválení pro produkční cutover; zde se o zápis nežádalo a žádný nebyl proveden.

Starší snapshot z 15.–17. 11. 2026 uváděl přibližně 1,695 milionu řádků v cílovém archivu a rozdíl vůči produkci od 17. 11. Tyto časově citlivé počty zde nejsou vydávány za aktuální stav.

## Lokální neveřejná data

Dřívější lokální inventář uváděl SQLite `data/historical_value_concordance.sqlite` (1 663 004 672 bajtů) a 114 ZIP balíků (3 403 538 773 bajtů). Hodnotový JSONL manifest a migrační CSV mají přibližně 129 MB a 83 MB. Zůstávají mimo GitHub. Jejich současné hashe a další cesty jsou v `reports/data/2026-11-22-local-file-inventory.csv`; předchozí ZIP manifest je `reports/data/2026-11-22-local-package-integrity.json`.

Při obnově je nutné ověřit SHA-256, obnovit do izolovaného umístění a provést integritní test podle typu artefaktu. GitHub není úplnou zálohou LXC. Viz zásady v `reports/2026-11-22-local-file-inventory.md`.

## Ověřovací omezení

Místní integrity checker prošel. Databázové počty, schema, synchronizaci od 17. 11. a živé PR/issues nelze odvodit z tohoto souborového testu. PR #32 a #33 mají public-reference CI úspěšné; Python joby byly po 24 hodinách zrušeny před spuštěním kroků. Zůstávají otevřené do skutečného CI běhu a kontroly použitých referenčních dat.
