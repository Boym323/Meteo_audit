# WH1080 — rebaseline kandidátů a nestageovaných časů

**Snapshot:** 2026-11-22, MariaDB / Weather MCP read-only SELECT. Issues #20, #18, #19.

## Proč je nový baseline nutný

Audit 2026-10-30 popisoval **49 796** WH1080 staging kandidátů bez cíle a **20 950** řádků mimo staging bez zarovnaného cíle. Od té doby se `loucka_reconstruction.archive` změnil. Tabulka stagingu nezaručuje, že je timestamp stále volný. Opakované full-row INSERT bez kontroly aktuálního cíle je nepřípustné.

## Přímý join stagingu proti aktuálnímu archive

| Staging status | Celkem v tabulce | Cíl už existuje | Cíl dosud chybí |
|---|---:|---:|---:|
| `pressure_only_review` | 47 737 | **10 080** | 37 657 |
| `needs_validation` | 758 | **31** | 727 |
| `frozen_sensor_review` | 1 301 | 0 | 1 301 |
| **Celkem** | **49 796** | **10 111** | **39 685** |

Zdrojový WH1080 záznam existuje u všech 49 796 staging řádků. Mezi 10 080 nově obsazenými `pressure_only_review` cíli se `outTemp` shoduje s tím, co je ve stagingu, jen v **112** případech a `pressure` v **0** případech. To potvrzuje, že **obsazený cíl není důvodem přepsat ho zdrojem WH1080**. U `needs_validation` je 31 obsazených cílů, z nichž 31 má shodné `outTemp` a 30 shodný `pressure`; shoda však nepotvrzuje nezávislost ani správnost.

## WH1080 zdroje mimo staging bez zarovnaného cíle

**20 942** současných zdrojových řádků má `FLOOR((dateTime+150)/300)*300` mimo rekonstrukční archiv a zároveň nemá `source_time` v tabulce stagingu. To je o **8 méně** než historický počet 20 950; jde o časově závislý stav dostupnosti, nikoliv automaticky ověřených 8 meteorologických obnov.

| Interval zdroje | Zdrojová epocha na 5min UTC mřížce | Počet |
|---|---|---:|
| 5 minut | Ne | **16 094** |
| 5 minut | Ano | **4 670** |
| 6 minut | Ne | **162** |
| 6 minut | Ano | **16** |
| **Celkem** | | **20 942** |

20 937 z těchto 20 942 WH1080 zdrojových timestampů se také vyskytuje v `old_weewx`. To jsou možné kopie téhož zdroje, **nikoli dvě nezávislá senzorová potvrzení**.

UTC rozdělení 20 942: 2011 **3 267**, 2013 **1**, 2014 **1 065**, 2015 **2 136**, 2016 **10 564**, 2017 **3 485**, 2018 **1**, 2019 **99**, 2020 **324**; ostatní roky bez položek.

## Reprodukce a bezpečnost

Soubor [`sql/readonly/wh1080_staging_current_disposition.sql`](../sql/readonly/wh1080_staging_current_disposition.sql) obsahuje tři ověřené SELECT dotazy. Každý se přes single-statement MCP spouští samostatně. Snap je **jen screening časové příležitosti**, není schváleným časovým ani hodnotovým převodem. `interval=6`, off-grid epocha, DST a kolize vyžadují individuální fyzickou validaci.

**Žádný INSERT, UPDATE ani DELETE nebyl spuštěn.** Neexistuje žádné schválení full-row WH1080 importu ani přepsání 10 111 obsazených cílových timestampů.

## Nevyřešeno pro uzavření #20

- Plný per-source, per-field fingerprint a intervalový překryv 20 942 aktuálně nestageovaných zdrojových řádků, s klasifikací časového posunu a kolize po malých časových dávkách.
- Nezávislost kopií, fyzický senzor/driver a jednotkové epochy (#21), bez nichž nelze přidělit status MEASURED.
- Případné schválení jednotlivých navržených hodnot až po ochranném CAS preflightu (#26), ne plošný import.
