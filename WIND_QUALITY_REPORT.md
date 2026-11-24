# Audit kvality větru — finální revize 2026-11-24

## Rozsah zdrojů

Read-only inventory na MariaDB `lo-infra-db-mariadb01` potvrdil, že účet této relace může číst schémata `pocasi-loucka.eu`, `loucka_reconstruction` a `weewx_WH1080`. Další historicky známá schémata `old_weewx`, `pocasi-loucka.eu_old` a `pocasi-loucka.eu_GW1000` nejsou pod tímto účtem viditelná. Lokální inventura `.sql`, `.sql.gz`, `.dump`, SQLite a archivních balíků nenašla původní raw archive backupy. Dostupné ZIPy obsahují reporty/analytické exporty, nikoli další původní databázi. `data/historical_value_concordance.sqlite` je analytický concordance dataset, ne obnovitelný původní archive backup.

Historická metadata (`HISTORICAL_SOURCE_CATALOG.md`) uvádějí starší `weewx_WH1080` v `usUnits=17`, zatímco reconstruction používá 16. METRIC 16 má wind km/h a rain cm; METRICWX 17 má ve standardním WeeWX kontraktu wind m/s a rain mm. Projektové cross-archive důkazy však popisují před-2013 raw shodu a 2013 epochové přechody, takže jednotkový kód sám o sobě neopravňuje k převodu. Směr je úhlová veličina, ale jeho zdrojovou validitu je stále třeba ověřit.

## Fyzikální a časové screeningy

Read-only dotazy nad `loucka_reconstruction.archive` při řezu `dateTime <= 1795541700` potvrdily:

- 318 případů `windGust < windSpeed`; 29 má rozdíl přes 1 km/h. Původní report rozděluje těchto 29 na 6 v roce 2014, 18 v 2016 a 5 v 2017. Dalších 92 porušení je v diagnostickém roce 2021 a novější malé rozdíly mohou být desetinné zaokrouhlení.
- 77 988 řádků s nenulovou rychlostí a chybějícím `windDir`.
- 6 řádků s nenulovou rychlostí a nulovým `windGust`.
- `1456856400` i `1456856700`: `windSpeed=78.48 km/h`, `windGust=0`, `windDir=270`. V dostupném WH1080 archivu pro tyto přesné timestampy není žádný řádek.

Kruhové a roční výsledky musí být čteny jako diagnostika epoch, ne automatický trend stanice. Předchozí roční porovnání identifikovalo stored-value transformaci mezi archive copies: 2009–2012 většinou raw ratio 1, smíšený režim 2013 a 2014–2019 převážně ratio 3,6 vůči `usUnits=17` kopii. V 2020 jsou lokální výjimky. Aktuální jednoduché průměry `windSpeed` z reconstruction jsou 10.17 km/h (2009), 10.06 (2012), 6.88 (2013), 7.79 (2014), 5.16 (2015), 5.36 (2016), 6.24 (2017), 7.19 (2021), 10.58 (2022); nejedná se o intervalově normalizované ani nezávislé stanice. Pokles 2014–2016 a nárůst 2022 je třeba interpretovat v kontextu změny senzorů, coverage, 2013–14 jednotkových transformací a známých dlouhých zmrazených úseků.

Úplný existující audit transformací a omezení: `HISTORICAL_WIND_TRANSFORMATION_REPORT.md`, `data/historical_wind_transformation_annual.json`, `reports/2026-11-12-wind-speed-gust-screening.md`, `reports/2026-11-12-wind-speed-gust-annual.csv` a `reports/2026-11-13-wind-direction-availability.md`.

## Dlouhé identické úseky

Všechny archive řádky v řezu byly zkontrolovány po UTC `dateTime`; úplná trojice `(windSpeed, windGust, windDir)` byla považována za identickou při přesných raw hodnotách na souvislé 5min mřížce. Screen našel 944 běhů trvajících alespoň hodinu (12 řádků), spolu 88 824 řádků. Většina nejdelších běhů jsou opakované nuly/nully, nikoli měřený konstantní vítr. Přesto byly nalezeny dlouhé nenulové plateaus:

| UTC interval | Délka | Uložená trojice | Source cross-check |
|---|---:|---|---|
| 2013-01-24 19:20 – 2013-01-27 09:10 | 743 řádků / 61 h 50 min | 17.3, 17.3, 1° | WH1080 má všech 743 řádků a přesně shodné raw hodnoty; source není nezávislé potvrzení |
| 2013-01-31 01:50 – 2013-02-01 13:10 | 425 řádků / 35 h 20 min | 51.5, 51.5, NULL | WH1080 má všech 425 řádků, raw rychlosti/nárazy shodné; source `usUnits=17`, target 16 |
| 2013-03-14 08:55 – 17:15 | 101 řádků / 8 h 20 min | 30.6, 30.6, NULL | WH1080 má všech 101 řádků, raw rychlosti/nárazy shodné; `outTemp` je v obou kopiích −4.7 °C po celý běh |
| 2020-01-29 20:25 – 2020-02-08 10:20 | 2 760 řádků / 9 d 13 h 55 min | 0, 0, NULL | WH1080 má všech 2 760 řádků a stejné nuly; `outTemp` v reconstruction během běhu kolísá −4 až 11.9 °C |

Poslední případ může znamenat období bez větru, chybějící/anulovaný kanál nebo zkopírovaný sentinel; z archive dat samotných nelze rozhodnout. První tři vypadají jako podezřelé zamrznutí či starý shared-copy artefakt, ale existující kopie opakují tentýž stav. Jiné veličiny v některých blocích také zamrzají. Nejsou k dispozici raw packet logy ani původní WeeWX konfigurace, které by určily skutečnou fyzikální hodnotu.

## Přímá obnovitelnost vs. nerozhodnuté případy

- **Zdrojově dohledatelné kandidáty směru:** z 77 988 missing-direction řádků má dostupná WH1080 archive přesný timestamp pro 6 681; u 6 671 je ve WH1080 `windDir` vyplněn a 6 659 z nich je v platném rozsahu `[0,360)`. Dvanáct hodnot je mimo rozsah a vyloučeno z kandidátů. Z těchto přesných řádků je 6 648 raw rychlostí a 6 645 raw nárazů shodných s reconstruction. To dokládá uložené hodnoty v historické kopii, ne nezávislý originál ani validitu stejného senzoru. Kandidáty lze identifikovat a případně po původu/schema review navrhnout jako `RESTORED`; v tomto běhu nebyly přidány do diffu ani aplikovány.
- **Prioritní interval 1359597000–1359724200:** 425 exact-time WH1080 směrů je k dispozici, reconstruction směr chybí u všech 425; rychlost i náraz se raw shodují ve všech 425. Jde o kandidáty pouze pro směrový kanál, s nevyřešenou proveniencí kopie.
- **Prioritní interval 1363251300–1363281300:** 101 exact-time WH1080 směrů je k dispozici, reconstruction směr chybí u všech 101; raw rychlost a náraz se shodují ve všech 101. Opět pouze zdrojové kandidáty.
- **Prioritní intervaly 1359055200–1359277800 a 1362171600–1362247200:** dostupný zdroj má směrové hodnoty; v overlapu jsou již shodné se reconstruction. V těchto oknech nebyl zjištěn `windGust < windSpeed`.
- **Prioritní 2022 interval 1670341200–1670372400:** WH1080 nemá záznamy; v aktuálním přístupu není vhodný originální archive row k obnově.
- **318 gust/speed rozporů:** WH1080 přesně překrývá jen 3 případy; ve všech třech má stejnou poruchu. Pro 2016 anomálii 78.48 km/h a 0 gust není přesný řádek v dostupném WH1080. Žádný alternativní zdrojový gust/speed nebyl doložen.
- **77 988 missing direction:** pro 71 329 případů není dostupná přesná WH1080 hodnota směru v platném rozsahu; jde o neobnovitelné z výhradně dostupné kopie, nikoli důkaz, že nikdy neexistoval jiný původní zdroj. Většina 2020–2022 směrů chybí i ve starších exportech podle předchozích auditů.

Jednotkové označení WH1080 je 17 a reconstruction 16; dřívější epochová analýza ukazuje, že raw shodu v některých letech nelze vysvětlit standardním převodem. Proto se zde neprovádí m/s↔km/h transformace. Žádná rychlost, náraz ani směr nebyly odhadnuty, interpolovány či zapsány. Neschválené `windDir` kandidáty zůstávají evidencí k review; desetinné/suspicious rychlosti a gust zůstávají diagnostickými případy.

## Shrnutí disposition

- **Obnovitelné jako doložené archive payload kandidáty:** 6 659 přesných `windDir` hodnot v platném rozsahu v dostupné WH1080 kopii (včetně 526 ve dvou prioritních oknech); bez produkčního schválení a bez tvrzení o nezávislém měření.
- **Podezřelá/zmrazená data:** 29 velkých gust<speed konfliktů, 6 nulových gust při nenulové rychlosti, dva body 78.48 km/h/0 gust a nenulové dlouhé plateaus z tabulky.
- **Nedostupné k obnově z nyní přístupných zdrojů:** většina missing direction po roce 2020, prioritní 2022 řada a šest nulových gust případů. Ponechat tak, jak jsou, dokud se neobjeví originální data.
- **Žádné opravy:** bez nezávislého původního zdroje, jednotkového kontraktu a schválené migrační metodiky se nesmějí vytvářet náhradní hodnoty.
