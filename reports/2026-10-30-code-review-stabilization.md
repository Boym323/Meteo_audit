# Opravný audit a stabilizace projektu — 30. 10. 2026

## Rozsah a bezpečnost

- Pracovní větev: `fix/audit-time-boundaries-and-data-provenance`, výchozí commit před změnami `94e8616`.
- Zdrojové databáze ověřeny pouze čtecími dotazy v MariaDB read-only transakcích. Nebyla provedena změna meteorologické hodnoty, účtu, oprávnění, auditní tabulky ani rekonstrukce.
- Live MariaDB transakční test použil již existující lokální připojení; tento účet má podle předchozí diagnostiky v rekonstrukční DB také zápisová oprávnění. Pro trvalé použití nového CLI kód vyžaduje samostatný `meteo_audit_ro`; účet nebyl vytvořen. Dokud správce účet nezaloží a neověří jeho granty, nové CLI správně odmítne DB spojení.
- Provedl jsem procesní chybu: první hromadné read-only SELECTy a exporty jsem spustil ze shellu `root`, přestože projekt vyžaduje OS účet `meteo-audit`. `.env` zůstal s režimem 0600, heslo nebylo vypsáno a všechny SQL běhy začaly `START TRANSACTION READ ONLY`; hlavní počty produkce, rekonstrukce a července 2021 jsem následně ověřil znovu jako `meteo-audit`. Metadata obou exportů tuto odchylku uvádějí. Další databázovou práci provádět výhradně pod `meteo-audit` a po založení účtu `meteo_audit_ro`.
- MariaDB klient/server verze nebyla znovu nezávisle ověřena v tomto úkolu. Předchozí inventář uvádí 11.8.6.

## Prokázaná chyba časových hranic

WeeWX archivní timestamp označuje konec intervalu. Primární dokumentace WeeWX definuje interval jako `(start, end]`; viz [developer notes WeeWX 5.4](https://www.weewx.com/docs/5.4/devnotes/) a [pravidla importu WeeWX](https://www.weewx.com/docs/latest/utilities/weectl-import-common-opt/). Dosavadní filtr `[start, end)` proto zařazoval interval končící přesně na hranici do následujícího měsíce/dne. Dřívější denní maximum navíc bucketingem podle místního data timestampu připsalo půlnoční interval následujícímu dni.

Nový filtr je `dateTime > start_epoch AND dateTime <= end_epoch`, kde lokální hranice vytváří `Europe/Prague` a převádí na Unix UTC. Sousední období nepřekrývají záznam na společné hranici. Místní půlnoc patří právě skončenému občanskému dni/měsíci/roku. Měsíční a roční sumy používají stejnou definici. Pětiminutový ani jiný jednotný interval není předpokládán.

### Stejná data: stará a nová podmínka

Čtené období: místní kalendář 2009-01 až 2026-10 (214 měsíčních období). Každé schéma bylo čteno v samostatné transakci `START TRANSACTION READ ONLY`; obě varianty podmínky byly porovnány ve stejném snapshotu dané databáze.

| Databáze | Řádky stará / nová | Součet rain uloženě stará / nová | Měsíce s rozdílem | Měsíce s počtem řádků jiným | Měsíce se změnou součtu | Nejvyšší změna měsíčního součtu |
|---|---:|---:|---:|---:|---:|---:|
| `pocasi-loucka.eu` | 1 680 020 / 1 680 020 | 1 158,502619899 / 1 158,502619899 | 33 | 26 | 8 | 0,2 mm |
| `loucka_reconstruction` | 1 679 802 / 1 679 802 | 1 092,657886479 / 1 092,657886479 | 33 | 26 | 8 | 0,2 mm |

Celkové součty při přechodu mezi podmínkami zůstaly stejné. Roční součty byly stejné pro každý místní rok; u roků 2009, 2011, 2012, 2016, 2017, 2018, 2019 a částečného 2026 se změnil počet hraničních řádků přiřazených do roku, nikoli jejich celkový rain součet. Změněné měsíční součty jsou přesunem intervalu přes hranu měsíce, nikoli změnou hodnoty. Nová agregace produkce dává 1 158,502619899 uložených jednotek; při `usUnits=16` je to 11 585,026199 mm. Dřívější report uváděl 11 585,028 mm a 1 680 012 načtených řádků; proti tomuto běhu rozdíl je −0,001801 mm a +8 řádků. Databáze se během živého čtení doplňovala, proto se tento rozdíl nepřipisuje samotné metodě hranic. Původní CSV zůstalo zachováno.

Podrobná reprodukce po každém měsíci a obou metodách je `2026-10-30-monthly-boundary-comparison.csv` s metadaty JSON. Filtry v porovnání byly přesně:

```sql
-- Dosavadní chybná hranice
WHERE dateTime >= :start_epoch AND dateTime < :end_epoch

-- Nová WeeWX hranice
WHERE dateTime > :start_epoch AND dateTime <= :end_epoch
```

`214` znamená počet vygenerovaných kalendářních měsíců; dřívější výstup `206` znamenal měsíce s alespoň jedním řádkem. Osm prázdných měsíců tvoří leden–únor 2009 před prvním záznamem a září 2011–únor 2012 bez dat. Odhad řádkového pokrytí není ověřené měření. Nový kód zvlášť hlásí existující řádek s `rain=NULL`, uloženou nulovou srážku, kladný déšť, vnitřní časové mezery, nepravidelný krok, odchylku od 5minutové UTC mřížky a intervaly zjištěné z `archive.interval`.

## Historické `rainRate`

V živém archivu k datu kontroly bylo `rain>0 AND rainRate=0` v produkci 38 244krát a v rekonstrukční DB 2 476krát. Za místní období 2009-01-01 až 2026-01-01 jsou přesné počty 37 611 a 1 843; zbývajících 633 případů v obou schématech je v roce 2026. Rozdíl 35 768 případů za 2009–2025 je tak přesně rozložen:

- 34 596 sdílených timestampů mají v produkci `rain>0, rainRate=0`, ale v rekonstrukci `rain>0, rainRate>0`.
- 1 172 sdílených timestampů mají kladný `rain` v produkci a `rain=0` v rekonstrukci; tyto záznamy odpovídají již zdokumentovanému červenci 2021.
- Rekonstrukční databáze v tomto rozsahu nepřidala opačný případ `rain>0, rainRate=0`, který by produkce neměla.

`reconstruction_changes` dokládá 58 936 aplikovaných změn `rainRate` v batchi `rainrate-restore-2009-2025-v1`, zdroj `pocasi-loucka.eu_GW1000`; evidované pravidlo uvádí shodu timestampu, jednotek a rain a zdrojovou intenzitu do 5 cm/h. To vysvětluje obnovené kladné hodnoty ve pracovní DB, ale neprokazuje historickou sémantiku GW1000 `rainRate` ani její ekvivalenci s produkčním senzorem. 1 172 změn srážky odpovídá červencové rekonstrukci, nikoli změně `rainRate`. Nic nebylo upraveno.

Auditní CSV počítá pro všech šest zdrojů po místním roce 2009–2025: `pocasi-loucka.eu`, `loucka_reconstruction`, `pocasi-loucka.eu_GW1000`, `pocasi-loucka.eu_old`, `old_weewx`, `weewx_WH1080`. Výsledek je v uložených hodnotách; žádný odhad jednotek ani `rainRate = rain × 12` nebyl aplikován. `old_weewx` a `weewx_WH1080` vykazují přes 122 tisíc `rain>0 & rainRate=0` a odlišné pokrytí; bez historického WeeWX nastavení nelze jejich rain považovat za stejné intervalové měření.

**Závěr:** hodnoty `rainRate` se neopravují. Rozdíl mezi hlavní produkcí a pracovní rekonstrukcí má doložené příčiny ve změnách pracovní databáze; fyzikální správnost obnovených intenzit zůstává neověřená.

## Provenience července 2021

Místní interval `2021-07-01 00:00 CEST` až `2021-08-01 00:00 CEST` má epoch hranice 1 625 090 400 a 1 627 768 800. Stav ověřený přes read-only SQL:

- Produkční archiv a `rain_archive_original_202107`: ve starém rozsahu `[start,end)` 8 921 řádků a 70,10146 cm = 701,0146 mm.
- `rain_reconstruction_202107_chmi_v1`: 8 928 plánovaných timestampů, součet 4,25672658 cm = 42,5672658 mm. Z toho dle tabulky 8 905 bodů `chmi10m_idw2` a 23 počátečních bodů `initial_archive_zero_no_june_csv`.
- Pracovní archiv ve starém rozsahu `[start,end)`: 8 921 řádků; všech 8 921 timestampů přesně odpovídá rekonstrukční tabulce a nemá rozdíl hodnot `rain`. Sedm plánovaných timestampů chybí v archivu.
- Při novém správném rozsahu `(start,end]` je v archivu stále 8 921 řádků a stejný součet, protože se vymění interval timestampu na 1. července za timestamp 1. srpna. 8 920 řádků se shoduje s plánovací tabulkou; další koncový záznam `2021-08-01 00:00 CEST` má `rain=0` a není v ní. Jeho nula je skutečně uložená hodnota, ne imputace provedená tímto auditem.
- `rain_backup_202107_before_chmi_v1`: 8 921 řádků, součet 58,64606 cm, 146 `rain=NULL` a 243 `rainRate=NULL`. Ve srovnání s `rain_archive_original_202107` se přesně 146 hodnot rain a 243 hodnot rainRate liší na NULL; ostatní hodnoty jsou shodné. Tabulka proto není nepozměněný originální snapshot: její obsah odpovídá stavu po dřívějším vynulování/kvůli karanténě 146 rain a 243 rainRate hodnot, ale přesný čas a SQL vytvoření backupu nejsou v repozitáři doloženy.
- Historie `reconstruction_changes` ukazuje 8 921 `reverted` položek pro rain a 8 921 pro rainRate v `rain-jul2021-quarantine-v1`, plus 146 `applied` rain a 243 `applied` rainRate položek v `rain-jul2021-dryday-22-24-v1`. Dva související candidate batch zůstávají `pending`: 71 kandidátů `loucka-rain-jul2021-chmi-dualrh-20261029-v1` a 3 `loucka-july2021-rain-divergence-review-v1`; celkem 74 kandidátů.

Stav archivu skutečně odpovídá rekonstrukční tabulce v původním okně, ale změna nebyla plně evidována přechodem batch/candidate životního cyklu. Původní přesný SQL skript z Navicatu a jeho hash nebyly nalezeny; přesné provedené příkazy, účet a časy operace tedy nejsou prokázány. Historické stavy `reverted` a `pending` nevysvětlují externí aplikaci rekonstrukce. Rekonstrukce nebyla znovu spuštěna.

Pro další operace je navržen nový append-only manifest v `proposals/external-sql-manifest.md`. Záznam má obsahovat UTC čas, aktéra, commit, SQL skriptu SHA-256, schéma/tabulku, přesné UTC rozsahy a WeeWX hranice, počty, identifikaci backupu, SHA-256 kanonického exportu před/po, ověřovací SELECTy a odkaz na existující auditní batch. Neúplný historický případ je v `proposals/external-sql-manifest-july-2021.json` označen `reported_not_independently_reproduced`; neznámé údaje jsou null. Žádná databázová evidence se nepřepisuje.

## Testy, CI a zbývající blokátory

- Unit a mockované integrační testy pokrývají půlnoc, přechod měsíce/roku, CET→CEST, CEST→CET, opakovanou hodinu, NULL/0, chybějící a nepravidelné intervaly, cm→mm, rozdílné rainRate, whitelist, SQL guard, izolaci výstupů DB a jednorázové započtení hraničního záznamu.
- GitHub Actions je připraveno pro Python 3.13, syntaxi, unittest a scan sledovaných souborů na tajemství. CI nepoužívá DB.
- Staré a nové sumy byly porovnány v live read-only transakcích; vlastní nové CLI nelze v tomto úkolu připojit, protože dedikovaný DB účet dosud neexistuje a oprávnění měnit bylo výslovně zakázáno. Tento účet musí vytvořit správce podle `sql/admin/create_meteo_audit_ro.sql`; do té doby je live běh nové implementace blokován.

## Stav předchozího měsíčního CSV

Původní reports/monthly_rain_coverage.csv jsem zachoval beze změny, ale jeho obsah není spolehlivý: má 48 fyzických řádků, poslední čitelný měsíc 2012-11 a od bajtu 8 187 obsahuje netextové/ne-UTF-8 bajty. Nelze ho použít jako důkaz pro předchozí denní a hodinová maxima. Celkové staré/nové měsíční a roční součty jsem proto porovnal z čerstvých read-only SQL dotazů. Denní/hodinová pravidla ověřují deterministické testy, nikoliv tento poškozený export.
