# Audit kvality větru — 2026-11-24

## Přímé SQL kontroly

Dotazy byly read-only nad `loucka_reconstruction.archive` s pevným řezem `dateTime <= 1795541700`.

- 318 případů `windGust < windSpeed`; 29 překračuje rozdíl 1 km/h (v databázových jednotkách m/s kontrolováno jako `> 1/3.6`).
- 77 988 případů nenulové rychlosti bez směru.
- 6 případů nenulové rychlosti s nulovým nárazem.
- `1456856400` a `1456856700`: `windSpeed=78.4799999907`, `windGust=0`, `windDir=270` u obou.
- 77 988 není důkaz chybného měření: směr mohl být chybějící, mimo dostupný kanál nebo přijatý mimo validní interval. Každý případ vyžaduje epochové posouzení.

## Prioritní intervaly

Následující intervaly zůstávají kandidáty na zdrojový read-back: `1359055200–1359277800`, `1359597000–1359724200`, `1362171600–1362247200`, `1670341200–1670372400`, `1363251300–1363281300`. V této relaci nebyl k dispozici důkaz původního řádkového payloadu pro každý bod. Nejsou tedy označeny jako obnovitelné.

## Dispozice

- **Obnovitelné:** zatím žádná nová hodnota nebyla prohlášena za obnovitelnou; vyžaduje původní archiv/zálohu s ověřeným časem, jednotkami, intervalem i celým řádkem.
- **Podezřelá měření:** 318 porušení gust/speed, včetně dvou extrémních bodů; jde o diagnostické případy, nikoliv automatický důkaz správné náhrady.
- **Podezřelé/nevysvětlené výpadky:** 77 988 rychlostí bez směru, šest nulových nárazů. Rozlišit podle konfigurace senzoru, epochy, sousedních polí a zdrojů.
- **Neobnovitelné výpadky:** nelze určit jen z cílové tabulky; pokud žádný zdrojový záznam ani nezávislý měřicí důkaz neexistuje, ponechat NULL.
- **Dlouhé identické série, změny kruhového průměru směru a roční průměry:** vyžadují kontrolu původních archivů, časových pásem, jednotek/konverzních faktorů a epoch senzoru. Starší podklady: `HISTORICAL_WIND_TRANSFORMATION_REPORT.md`, `data/historical_wind_transformation_annual.json`, `STATION_SENSOR_EPOCH_REGISTRY.json`.

Žádná umělá nebo interpolovaná rychlost/směr/náraz nebyla navržena jako oprava. Neschválené změny zůstávají kandidáty.
