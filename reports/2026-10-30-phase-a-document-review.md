# Revize metodiky a dokumentace fáze A — 30. 10. 2026

## Rozsah a bezpečnost

Jde o **revizi souborů GitHub repozitáře**, nikoli nový běh živé MariaDB. V této práci nebyl proveden SQL dotaz proti databázi ani změněn původní/rekonstrukční archiv, evidence kandidátů, granty nebo historická CSV. Údaje původní diagnostiky jsou zachovány jako historické pozorování; sporné interpretace byly přímo označeny.

## Opraveno

- Zavedena metodika pro denní `SRA` ČHMÚ: 24hodinový úhrn měřený ráno, připisovaný předchozímu dni, **není automaticky totožný** s intervalem `(DT−24 h, DT]`. Význam historických CSV polí `DT` a `TIMEFUNC` je do ověření označen jako neznámý.
- Opraveno dřívější časové přisouzení ČHMÚ jako přímého důkazu pětiminutového impulzu v červnu 2010, březnu 2011 a únoru 2025; původní naměřené hodnoty jsou nedotčené.
- Odlišena jistota diagnózy anomálie od jistoty navržené náhrady. Všech 16 kandidátů za červen 2010 i případy z let 2011 a 2025 zůstávají **neschválenými historickými návrhy**; bez dalšího důkazu se nesmí dosadit ani `0`, ani `NULL`.
- Opravena zavádějící hlavička tabulky (převod uloženého `rain` na mm, nikoli „Předloha CHMI“) a rozbitá tabulka dvou `rainRate` review případů. Původní identifikátory batchů se v DB nemění.
- Doplněny instrukce pro Codex v `AGENTS.md`, `README.md` a metodikách; opraven duplicitní zápis tabulky `archive`.
- Verzovaný hook `.githooks/post-commit` nově **nepushuje automaticky na main**. Jestli je aktivní starý lokální hook v LXC, musí se ověřit jeho skutečný obsah a aktivace `core.hooksPath`; samotná změna souboru na GitHubu jej nemusí ihned nahradit.

## Otevřené blokátory

1. Zjistit a doložit skutečnou interpretaci `DT`/`TIMEFUNC` v historických CSV ČHMÚ. Vyplnit jednoznačné časové hranice UTC pro každý referenční řádek; do té doby `REFERENCE_WINDOW_UNVERIFIED`.
2. Samostatně ověřit místní impulsy přes časově rozlišené nezávislé zdroje, raw čítače a konfigurace přístrojů.
3. Dokončit provenienci externí rekonstrukce července 2021 (zdrojový SQL skript, záloha, záznam batch a skutečná aplikace) podle [manifestu](../proposals/external-sql-manifest.md). Staré pracovní hodnoty automaticky nepřepisovat.
4. Zprovoznit a ověřit dedikovaný `meteo_audit_ro`; následné čtení DB teprve pod tímto účtem a neprivilegovaným OS uživatelem.
5. Opravit nebo nahradit starý poškozený měsíční export pomocí **nové verzované cesty**, původní CSV nepřepisovat.

## Reprodukce a omezení

Základní [metodika časových hranic WeeWX](../docs/time-intervals.md) platí pro WeeWX archiv `(start,end]`, nikoli bez dalšího pro ČHMÚ. Nový postup časového přiřazení ČHMÚ je v [docs/chmi-daily-sra.md](../docs/chmi-daily-sra.md). Tento PR sám nepotvrzuje žádnou konkrétní náhradní meteorologickou hodnotu a neopravňuje k zápisu. Před budoucím zápisem je nutný samostatný důkaz, schválení, přesné porovnání staré hodnoty, záloha, transakce, post-kontrola a rollback.
