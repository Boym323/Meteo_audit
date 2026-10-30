# Evidence manifest pro SQL provedené mimo aplikaci

Tento manifest je doplňkový souborový záznam pro DBA operaci provedenou například přes Navicat. Nenahrazuje `reconstruction_changes`, kandidáty ani batch stav a nemění je. Každá operace dostane vlastní JSON soubor s neměnným `operation_id`; opravy záznamu se zapisují jako nový superseding záznam, původní se neupravuje.

## Povinné položky

- `operation_id`, `status`, aktér a UTC časy přípravy/provedení/ověření.
- Repository commit, relativní cesta původního SQL a SHA-256 přesných bajtů tohoto skriptu. Pokud původní soubor chybí, pole zůstávají `null` a stav zůstane `reported_not_independently_reproduced`.
- Přesné cílové schéma/tabulka/sloupce, databázové časové hranice UTC a sémantika WeeWX `(start,end]`.
- Počet zamýšlených a skutečně dotčených řádků, počet řádků před/po, explicitní počty NULL a nulových hodnot.
- Backup tabulka nebo export, čas vytvoření a SHA-256 nezměněného kanonického exportu.
- SHA-256 kanonického exportu dotčených řádků po operaci. Export řadit podle primárního klíče, používat UTF-8, LF a jednoznačnou reprezentaci NULL (`\\N`). Manifest ani export nesmí obsahovat přihlašovací údaje.
- Přesné read-only validační SELECTy, jejich výsledky, případné rollback/kompenzační kroky a odkaz na související batch/candidate řádky.

Příklad neúplného retrospektivního záznamu července 2021 je pouze dokumentace toho, co je dnes doloženo a co zůstává neznámé. Jeho null hodnoty se nesmějí doplnit odhadem.
