# Metodika auditu srážek

## Co představují zdroje

- `pocasi-loucka.eu.archive`: původní produkční archiv; čte se pouze pro srovnání.
- `loucka_reconstruction.archive`: pracovní archiv, který už obsahuje externě aplikované rekonstrukce a historii změn; nejde o kopii produkčních měření.
- `pocasi-loucka.eu_GW1000.archive`: archiv dalšího WeeWX/Ecowitt zdroje. Podobnost hodnot s produkcí sama nedokazuje nezávislé měření.
- `pocasi-loucka.eu_old.archive`, `old_weewx.archive`, `weewx_WH1080.archive`: historické databáze s odlišným časovým pokrytím a možnou sémantikou čítače. Nezaměňovat jejich `rain` za intervalový déšť bez potvrzení driveru a konfigurace.
- LuhaMet, ILOUKA4 a ČHMÚ: nezávislé srovnávací zdroje s různou vzdáleností, časovým rozlišením, agregací a kvalitou. Nejsou náhradou místního čidla bez vyhodnocení.

## Jednotky a význam

WeeWX označuje hodnotou `0x10` systém METRIC, kde je srážka v cm a intenzita v cm/h; `0x11` METRICWX používá mm a mm/h. Viz [oficiální tabulka jednotek WeeWX 5.4](https://www.weewx.com/docs/5.4/reference/units/). Proto lze `usUnits=16` převést na mm násobením 10, pokud všechny řádky daného souhrnu používají právě tento systém. To ověřuje kód systému jednotek, nikoliv historickou konfiguraci driveru pro konkrétní sloupec. Před produkční rekonstrukcí je nutné ověřit WeeWX `weewx.conf`, ovladač a historické přechody. V tomto checkoutu WeeWX konfigurace nalezena nebyla.

`rain` je analyzován jako uložený intervalový přírůstek, `rainRate` je vykázán odděleně jako uložená hodnota. Není předpokládáno `rainRate = rain × 12`; stejný rozměrový vztah navíc předpokládá pět minut, konzistentní jednotky a konkrétní definici průměrné intenzity. Historická intenzita může být přímo měřená, odvozená driverem, nebo rekonstruovaná.

`NULL` znamená chybějící hodnotu. `0` je uložená nulová hodnota. Chybějící řádek znamená chybějící archivní záznam; žádná z těchto kategorií se automaticky nepřevádí na jinou.

## Měsíční audit

CLI používá hranice lokálního kalendáře Europe/Prague a WeeWX intervaly `(start, end]`. Měsíční a roční úhrny se skládají ze stejných nepřekrývajících se období. Denní extrémy jsou podle občanského místního dne, nikoliv meteorologického dne s posunutou uzávěrkou. Srážky z neúplného prvního a posledního měsíce se označí jako částečné.

Výstup obsahuje uložený součet, počet NULL, nulových a kladných řádků, histogram `interval`, odhad chybějících timestampů a nezávisle od něj počet řádků s deštěm. Odhad pokrytí je kadence záznamů, nikoliv procento ověřených měření.

## Prověřený rozdíl rainRate (30. 10. 2026)

Šest databází a roční časové řezy lze zopakovat příkazem `PYTHONPATH=src python3 -m meteo_audit.rainrate --start-year 2009 --end-year 2025`. CLI zapisuje každé schéma do vlastního adresáře a u CSV ukládá JSON s rozsahem, jednotkami, počtem řádků a verzí kódu.

Read-only kontrola zjistila v celém archivu (včetně částečného roku 2026) 38 244 případů `rain>0 AND rainRate=0` v produkci a 2 476 v pracovní DB. V místních letech 2009–2025 jsou přesné počty 37 611 a 1 843; zbylých 633 případů leží v obou schématech v roce 2026. Podrobné počty po zdroji a místním roce jsou v `reports/2026-10-30-rainrate-2009-2025-by-source.csv`. Produkce měla v období 2009–2025 nula řádků `rainRate>0 AND rain=0`; v pracovní DB jich bylo 21 586. Historické sloupce v databázích `old_weewx` a `weewx_WH1080` mají mnohem vyšší počet `rain>0 AND rainRate=0` (přes 122 tisíc), což je další důvod nepovažovat jejich `rain` automaticky za stejnou intervalovou veličinu.

Příčina rozdílu v uložených hodnotách je nyní z velké části doložena. Join produkce a rekonstrukce podle stejného `dateTime` pro 2009–2025 našel 1 592 913 společných timestampů. V 34 596 případech měla produkce `rain>0, rainRate=0`, zatímco rekonstrukce měla `rain>0, rainRate>0`. Pracovní archiv má evidováno 58 936 aplikovaných změn v batchi `rainrate-restore-2009-2025-v1`; záznamy uvádějí zdroj `pocasi-loucka.eu_GW1000` a pravidlo shody timestampu, jednotek a úhrnu `rain`. Tento batch tedy vysvětluje obnovenou kladnou intenzitu v tisících sdílených záznamů, ale samo zdrojové pravidlo neprokazuje, že `rainRate` GW1000 mělo stejnou historickou sémantiku jako produkční měření.

Dalších 1 172 produkčních případů `rain>0, rainRate=0` má v rekonstrukci `rain=0/NULL` a odpovídá časům, kde červencová rekonstrukce 2021 nahradila původní kladný `rain` nulou. Tím se počet rekonstruovaných `rain>0, rainRate=0` snížil z 37 611 na 1 843: 34 596 změn intenzity a 1 172 změn srážky; v joinu nebyl nalezen opačný případ, který by tuto anomální kombinaci nově vytvořil. Údaj 2 476 pro celý archiv přidává 633 případů z roku 2026 v obou databázích a nemění rozdíl 35 768.

Rozdíl databází je tedy vysvětlen operacemi v rekonstrukční kopii; správnost obnovených hodnot `rainRate` zůstává neověřená. `old_weewx` a `weewx_WH1080` mají jiné pokrytí a vysoké počty kladného `rain` při nulovém `rainRate`; bez konfigurace driveru je nelze považovat za nezávislé přímé intenzity.

**Závěr:** neprovádět automatickou opravu `rainRate`. Potřebné důkazy jsou konfigurace WeeWX/driverů po historických obdobích, původní zdrojové pakety/logy a mapování každé změny v rekonstrukční historii.
