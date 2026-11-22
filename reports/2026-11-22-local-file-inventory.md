# Lokální inventář `/opt/meteo-audit` — 22. 11. 2026

Tento inventář byl znovu vytvořen 22. 11. 2026 z aktuálních souborů v pracovním stromu. CSV obsahuje relativní cestu, velikost, SHA-256, konzervativní kategorii A/B/C, informaci o sledování v checkoutu a důvod zacházení. Neobsahuje obsah meteorologických databází ani hodnotové řádky.

## Rozsah a srovnání

| Metrika | Nové zjištění |
| --- | ---: |
| Cesty zahrnuté do inventáře | 5 282 |
| A — zdroj, SQL, testy a metodiky k publikaci po běžné revizi | 1 786 |
| B — výsledky/evidence vyžadující bezpečnou redakci nebo agregaci | 2 784 |
| C — lokální, binární, provozní či potenciálně hodnotové artefakty | 712 |
| Sledované cesty v původním checkoutu | 58 |

Původní čísla 4 817 souborů a 3 213 cest nepřítomných na GitHubu nelze reprodukovat ani porovnat přesně: odkazy na `reports/2026-11-22-local-file-inventory.md`, `reports/data/2026-11-22-local-file-inventory.csv` a dřívější manifest v pracovním stromu chyběly. Aktuální kontrola zahrnula běžné soubory mimo `.git`, virtuální prostředí, cache, `node_modules`, `build` a `dist`; na rozdíl od dřívějšího údaje reportuje cesty a neodvozuje počet unikátních obsahů. Starší rozsah mohl používat jiné filtry či počítat artefakty před změnami pracovního stromu. CSV uvádí klasifikaci po jednotlivých cestách.

Klasifikace A je kandidát k publikaci, nikoli automatické schválení: zdrojový soubor se musí před zařazením do PR ještě zkontrolovat na oprávněnost, duplicitní implementaci, tajemství a závislost na lokálních datech. Kategorie B se nesmí publikovat bez kontroly řádkových hodnot, infrastruktury a identifikátorů. Kategorie C se nezahrnuje do běžného Git repozitáře.

## Bezpečné uchování kategorie C

Lokální soubory nemažte. Před externí zálohou ověřte, že cílové úložiště má šifrování, řízení přístupů, retenční politiku a test obnovy. Přenášejte pouze schválené artefakty a k záloze uložte manifest SHA-256, vlastníka, účel, závislosti, datum a umístění. Obnovu proveďte do izolovaného adresáře, znovu ověřte hashe a následně validujte SQLite (`PRAGMA integrity_check`) nebo ZIP (`unzip -t`). GitHub není úplnou zálohou LXC.

Příklady lokálních C artefaktů (podrobné cesty, velikosti a hashe jsou v přiloženém CSV):

- `data/historical_value_concordance.sqlite` — 1 663 004 672 bajtů; obsahuje hodnotovou konkordanci a musí zůstat v omezeném úložišti.
- 114 ZIP archivů — 3 403 538 773 bajtů podle dosavadního lokálního package manifestu; obsah některých archivů může zahrnovat původní data či migrační payloady.
- `FINAL_MIGRATION_MANIFEST_20261117.jsonl` — 128 967 733 bajtů; obsahuje časové a hodnotové návrhy, publikovatelný není.
- `final_migration_package/MIGRATION_DIFF.csv` — 83 067 783 bajtů; obsahuje řádkové migrační hodnoty.
- `.env` a další autentizační konfigurace, pokud jsou přítomné, nepatří do inventáře veřejného repozitáře ani do nešifrované zálohy.

Historický package manifest uváděl 114 ZIPů a součet 3 403 538 773 bajtů. Aktuální inventář se týká cest přítomných právě v tomto běhu; před obnovou použijte SHA-256 z aktuálního CSV, ne pouze starý součet.

## Omezení

Inventář ověřuje existenci, velikost a hash souborů. Neověřuje, že každý report je věcně správný, že jsou data legálně publikovatelná, ani že lokální DB odpovídá živému serveru. Změny proti minulému inventáři nelze přesně vysvětlit bez původního CSV. Před publikací zůstává nutná lidská kontrola kategorie A/B.
