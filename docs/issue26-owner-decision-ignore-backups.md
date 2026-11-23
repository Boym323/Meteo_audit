# Rozhodnutí 2026-11-23: zálohy mimo rozsah auditu #26

**Závazné rozhodnutí vlastníka:** v rámci Meteo_audit dále
**nekontrolujeme, nevyžadujeme ani nevyhodnocujeme zálohy MariaDB ani
Proxmox Backup Server (PBS)**. Nepřipravujeme novou MariaDB instanci,
PBS Verify/restore a nevážeme na tyto činnosti uzavření issue #26.

Tím se nahrazuje backup/restore podmínka v dřívějších PR #72 a #73,
v runboocích a v původní akceptaci issue. Staré technické nástroje
zůstávají pouze jako **nepovinný historický artefakt**; nespouštět je
automaticky ani je nenavrhovat jako další povinný krok.

**Toto rozhodnutí není důkazem** úspěšné, konzistentní či obnovitelné
zálohy. Stav ochrany celého SQL serveru je **NEOVĚŘENÝ, RIZIKO PŘIJATO
VLASTNÍKEM**. Nemáme důkaz, že lze obnovit katastrofické poškození
serveru; oprava hodnot v archivu nemá automaticky celoserverový
rollback. Neslibovat obnovitelnost přes PBS.

## Nadále povinné uvnitř každé opravné dávky

- **Jen pracovní** `loucka_reconstruction.archive`, žádná změna
  produkčního `pocasi-loucka.eu.archive` ani zdrojových historických DB.
- Dry-run jako výchozí režim; přesný per-variable manifest old/new,
  UTC timestamp, původ a jednotková epocha, verze pravidla,
  confidence a kanonický SHA-256.
- **Výslovný souhlas pro jediný konkrétní batch ID + SHA-256** před
  jakýmkoli zápisem. Schválení issue, PR, algoritmu ani této
  výjimky **není** schválením konkrétní dávky.
- NULL-safe compare-and-swap, transakční atomičnost, paralelní
  konflikt/replay guard, neměnný before-image a append-only audit.
- Možnost **per-batch post-image CAS rollbacku** z původních hodnot;
  bez závislosti na záloze. Rollback nesmí přepsat následné odlišné změny.
- Zachovat chráněné Fáze A / Q1 2018 a srážky 2021, včetně invarianty
  července 2021 přibližně 42,567 mm; nevydávat 92 366 QUARANTINE
  položek za schválené.
- Denní extrémy `archive_day_*` ručně neopravovat: po konečném
  schválení archivu je přepočítá WeeWX (PR #71).

## Co řešíme dál

Zbývající #26 je **transakční aplikační/schvalovací a rollback mechanismus**
na stávající MariaDB, bez řešení záloh. Nový PR může přidávat a
testovat kód v CI na syntetických datech; žádný nepodmíněný reálný
`INSERT/UPDATE/DELETE` a žádné automatické nasazení.
