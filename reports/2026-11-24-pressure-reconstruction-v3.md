# Tlaková rekonstrukce V3: 10min ČHMÚ, validační oprava a stav

**Datum běhu:** 2026-11-24 · **stav:** neprodukční diagnostika · všechny případné odhady `ESTIMATED / UNAPPROVED`.

## ČHMÚ 10min reference

Zdroj: [ČHMÚ Open Data – historical 10min air pressure](https://opendata.chmi.cz/meteorology/climate/historical_csv/data/10min/air_pressure/). Staženo 2018–2025 pro Holešov `0-20000-0-11774` a Mošnov `0-20000-0-11782`, 12 měsíčních CSV na stanici a rok (192 souborů). Metadata ČHMÚ `meta2.csv` deklarují `P` jako „Tlak vzduchu“, jednotku hPa a přesnost/nejistotu zdroje podle epochy; `meta1.csv` potvrzuje polohy Holešov 49.320556 N, 17.5700 E, 222.25 m a Mošnov 49.698333 N, 18.119167 E, 250.4 m.

Bylo ověřeno 841 536 řádků a SHA-256 každého souboru (manifest: `fe21d23d8123ecf153d7e43fd6c1495eaacfa896dbbb22b8fc8b5d5669c4caca`). Všechny časy mají explicitní UTC suffix `Z`; časová podpora je nominální desetiminutový tlakový záznam. `QUALITY=0.0`: 840 589 řádků; `QUALITY=3.0`: 947 (vyloučeno z fitu); ostatní quality: 0. Záznamy mimo široký rozsah 850–1100 hPa: 0. Minuty s úplnou dvojitou staniční řadou dávají 419 838 společných quality‑0 časů. Jejich přímý rozdíl Holešov minus Mošnov má medián +4.2 hPa (MAE 4.261 hPa; p95 absolutního rozdílu 5.7 hPa). Stanice proto nelze zprůměrovat bez převodu výšky/regionální korekce.

Veřejná evidenční kopie měsíčních SHA a souhrnný QC jsou v `reports/data/pressure-reanalysis-v3/`; plná raw data zůstávají mimo Git v `/opt/meteo-audit-artifacts/pressure-reanalysis-v3/chmi-10min/raw/`. Soubory pro další blízké tlakové stanice byly v indexech katalogu dohledány, ale jejich vzdálenost a representativnost pro Loučku nebyly v tomto běhu vyhodnoceny. Do kombinovaného modelu proto vstupují pouze dvě referenční stanice známé z validace V2.

## Oprava validační logiky po PR #98

Předchozí kód odvozoval coverage všech metod ze společného ERA5 + obou stanic denominatoru a u modelu s chybějícím lokálním prediktorem tak nevykazoval jeho vlastní počet/coverage. Upravený `model_scores` nyní pro každou variantu samostatně zaznamená počet způsobilých predikcí, počet společných staničních referencí, coverage, UTC timestamps a skóre. Navíc publikuje skóre všech modelů na průniku totožných timestampů. Pevné prahy gate z PR #98 jsou zachovány.

Přidán unit test, v němž místní vstup záměrně chybí na jednom čase; ověřuje samostatné N modelů, coverage i párovanou množinu. Test prošel. `py_compile` obou nových/upravených skriptů prošel.

## Model a časová podpora

V3 má rozlišovat čtyři původy: `MEASURED` (původní Loučka), `MEASURED_REFERENCE` (surový ČHMÚ 10min), `ESTIMATED` (jakýkoli odhad/interpolace, vždy `UNAPPROVED`) a `UNRESOLVED`. Navržený kombinovaný kandidát používá quality‑0 ČHMÚ bodové hodnoty s jejich přesným UTC časem, regionální převod mezi stanicemi podle ERA5 teploty/výšky a ERA5 surface pressure jen jako záložní prostorový prediktor. V1 lokální model vstupuje pouze při splnění vstupního QC. Před jakýmkoli použitím musí být rodina vybrána na validační bloku a porovnána na stejných timestamp vzorcích; raw desetiminutový tlak se nesmí označit za tlak Loučky bez převodu.

Desetiminutový odhad mezi referencemi je interpolovaný modelový odhad, nikoli měření. Hodinové ERA5 interpolované na 5min jsou rovněž odhad, s nižší časovou podporou; oba zdroje musí mít oddělené `method` a uncertainty evidenci. Q1 2018 je z kandidátní vrstvy vyloučeno.

## Zbývající blokace a přesnost

V tomto checkoutu chybí surová důvěryhodná pětiminutová Loučka řada a aktivní lokální SELECT export pro DB. Lokální PR #98 artifacts `/opt/meteo-audit-artifacts/pressure-reanalysis-v2/final-v3` obsahují pouze odvozenou V2 unified řadu a V2 candidates, nikoli raw pětiminutový target/validation sample. Repo archive CSV jsou denní agregace. Proto nebyl vypočten přesný artificial-gap backtest (trénink/výběr/holdout, délky mezer/sezóny/rychlé změny), numerické 5min porovnání 10min interpolace vs hodinové ERA5, ani nová celořádková V3 řada či přesné V1/V2/V3 coverage metriky. Nevydávám měsíční/týdenní souhrny za náhradu pětiminutových řádků.

Pro roky 2009–2017 lze zachovat V2 stavy a využít ERA5 plus denní ČHMÚ pouze jako nízkou časovou podporu; nesmí se tvrdit minutová validační přesnost. Chybějící 5min lokální snapshot brání i rozdělenému historickému holdoutu. Q1 2018 zůstává chráněné. Žádné SQL zápisy, APPLY, změny produkce, WeeWX ani oprávnění neproběhly.

## Ověření

- CHMI fetch/parser: 192/192 souborů, 841 536 řádků; 840 589 quality‑0, 947 quality‑3.
- SHA-256 všech raw souborů ověřen proti manifestu.
- `python3 -m unittest tests.test_pressure_reconstruction_v3 -v`: PASS.
- `python3 -m py_compile scripts/compare_pressure_reanalysis_v2.py scripts/validate_chmi_10min_pressure.py`: PASS.
- Hodnoty zůstávají pouze evidenční; žádná rekonstrukční hodnota nebyla schválena.
