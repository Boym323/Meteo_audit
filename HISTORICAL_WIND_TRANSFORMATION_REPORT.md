# Historické transformace větru

**Rozsah:** přesné timestampové překryvy `weewx_WH1080` (většinou `usUnits=17`, METRICWX) vs `pocasi-loucka.eu_old` (`usUnits=16`, METRIC), UTC roky 2009–2020. Je to porovnání uložených archivů, nikoli potvrzení původních správných hodnot.

## Standardní jednotkový kontrakt

Oficiální WeeWX kontrakt uvádí pro METRICWX rychlost větru v m/s a déšť v mm; METRIC používá km/h a cm. Pro `windSpeed`/`windGust` je očekávaný převod METRICWX→METRIC násobení 3,6. `windrun` je vzdálenostní veličina a dokumentované jednotky jsou km v obou systémech; automatický faktor 3,6 pro windrun z toho neplyne. Viz [WeeWX unit systems](https://www.weewx.com/docs/latest/reference/units/) a [StdConvert](https://www.weewx.com/docs/latest/reference/weewx-options/stdconvert/).

## Pozorované faktory

| UTC epocha | Přesné páry (přibližně) | WindSpeed / Gust | Windrun | Interpretace |
|---|---:|---|---|---|
| 2009–2012 | 78k–104k ročně | raw shoda prakticky u všech; hodnoty WH×3,6 se obvykle neshodují s `site_old` | poměr `site_old/WH` zhruba 1/3,6, s přechodovými/nevýraznými hodnotami | raw vítr neodpovídá standardnímu kontraktu kódů jednotek; nelze určit, který archiv byl již přepočten |
| 2013 do 6. 4. | podmnožina ročních párů | převážně poměr 1 | windrun poměr zhruba 1/3,6 | starší režim |
| 2013 od 12. 4. | podmnožina ročních párů | převážně faktor 3,6 | převážně faktor 1 | pozorovaná změna režimu; přesný přechod je intervalově ohraničen mezerou v párových datech |
| 2014–2019 | 76k–105k ročně | poměr odpovídá standardnímu faktoru 3,6 u převážné většiny nenulových párů | převážně poměr 1 | silný systematický vzor; stále neprokazuje konkrétní úmysl migrace |
| 2020 | 68 935 exact timestamp pairs; 61 095 nonzero paired speed values | poměr ±0,001: 58 324 odpovídá 3,6 a 2 771 je mimo; přísná přesná konverzní tolerance zvýrazňuje lokalizovanou skupinu 20. 8.–1. 9. | 58 290/61 095 odpovídá poměru 1; 2 805 mimo | anomální lokální epocha; možné úpravy/senzorové chování, nikoliv prokázaná příčina |

Párové počty ukazují dlouhodobý rozsah: 2009 78 248, 2010 104 115, 2011 62 861, 2012 75 372, 2013 95 491, 2014 96 157, 2015 101 916, 2016 88 455, 2017 76 858, 2018 87 653, 2019 104 717, 2020 68 935 exact timestamp pairs, z nichž 61 095 mají obě nenulové rychlosti. U 2013 je poměr 1 pozorován do 6. dubna a faktor 3,6 od 12. dubna (pro gust se přesné poslední/nejstarší body mírně liší). Bez dat mezi těmito skupinami nelze určit přesnou hranici.

## Annual exact-timestamp ratio distribution

Ratio categories are counted only where both values are non-NULL and nonzero; ratio tolerance is ±0.001. “Other” is the remaining nonzero pairs after the two named ratio classes. Unit flags differ in every pair (`17` vs `16`); interval flags differ in five 2019 pairs and 37 in 2020.

| Year UTC | Exact pairs | unit mismatches | interval mismatches | speed ratio 1 | speed ratio 3.6 | speed other | gust ratio 1 | gust ratio 3.6 | windrun other | windrun ratio 1 | windrun ratio 1/3.6 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2009 | 78,248 | 78248 | 0 | 77,534/77,534 | 0/77,534 | 0 | 77,965/77,965 | 0/77,965 | 0 | 0/77,534 | 77,534/77,534 |
| 2010 | 104,115 | 104115 | 0 | 99,033/99,033 | 0/99,033 | 0 | 99,825/99,825 | 0/99,825 | 0 | 0/99,033 | 99,033/99,033 |
| 2011 | 62,861 | 62861 | 0 | 61,394/61,394 | 0/61,394 | 0 | 61,836/61,836 | 0/61,836 | 0 | 0/61,394 | 61,394/61,394 |
| 2012 | 75,372 | 75372 | 0 | 73,749/73,749 | 0/73,749 | 0 | 74,197/74,197 | 0/74,197 | 0 | 0/73,749 | 73,749/73,749 |
| 2013 | 95,491 | 95491 | 0 | 15,135/63,337 | 48,202/63,337 | 0 | 16,169/67,483 | 51,314/67,483 | 0 | 48,202/63,337 | 15,135/63,337 |
| 2014 | 96,157 | 96157 | 0 | 0/91,261 | 91,261/91,261 | 0 | 0/94,420 | 94,420/94,420 | 0 | 91,261/91,261 | 0/91,261 |
| 2015 | 101,916 | 101916 | 0 | 0/79,847 | 79,847/79,847 | 0 | 0/84,876 | 84,876/84,876 | 0 | 79,847/79,847 | 0/79,847 |
| 2016 | 88,455 | 88455 | 0 | 0/73,798 | 73,798/73,798 | 0 | 0/78,914 | 78,914/78,914 | 0 | 73,798/73,798 | 0/73,798 |
| 2017 | 76,858 | 76858 | 0 | 0/70,192 | 70,192/70,192 | 0 | 0/73,817 | 73,817/73,817 | 0 | 70,192/70,192 | 0/70,192 |
| 2018 | 87,653 | 87653 | 0 | 0/84,442 | 84,442/84,442 | 0 | 0/86,419 | 86,419/86,419 | 0 | 84,442/84,442 | 0/84,442 |
| 2019 | 104,717 | 104717 | 5 | 0/99,900 | 99,900/99,900 | 0 | 0/102,159 | 102,159/102,159 | 5 | 99,895/99,900 | 0/99,900 |
| 2020 | 68,935 | 68935 | 37 | 0/61,095 | 58,324/61,095 | 2,771 | 0/62,203 | 60,555/62,203 | 2,805 | 58,290/61,095 | 0/61,095 |

The year-level rows show the field-specific transition directly: speed/gust ratios are 1 throughout nonzero 2009–2012 pairs, mixed in 2013, then 3.6 throughout 2014–2019. In 2020 there are 2,771 speed and 1,648 gust nonzero pairs outside the 3.6 ratio class; the localized Aug 20–Sep 1 window contains the observed mismatch cluster. Windrun is inverse to speed early on: 2009–2012 is approximately 1/3.6, the 2013 ratio changes between April 6 and April 12, and 2014–2019 is ratio 1. The 2020 windrun has 2,805 nonzero pairs outside ratio 1. For 2020 this ±0.001 ratio classification yields 2,771 speed and 1,648 gust nonzero cases outside the nominal 3.6 class; the stored exact-factor test is stricter and its event subset may include near-factor rounding differences. The annual maximum absolute residual against `WH×3.6` is 7.62 m/s for speed and 21.96 for gust. These ratios describe stored values, not approved transforms.

A focused 2013 query found the last windSpeed ratio-1 point at **2013-04-06 15:10 UTC** and first ratio-3.6 point at **2013-04-12 17:55 UTC**; windGust last ratio-1 at **2013-04-06 14:55 UTC** and first ratio-3.6 at the same April 12 point. Windrun ratio-1/3.6 ends at 2013-04-06 15:10 UTC and ratio 1 begins 2013-04-12 17:55 UTC. Intermediate nonzero pair cases and null/zero pairs are separately counted in `data/historical_wind_transformation_annual.json`; there is no evidence to interpolate a precise regime boundary across that interval.

## Omezení a rozhodnutí

Vlastník nezávisle attests, že rychlost větru historicky přepočítával, ale přesná pravidla nezná. Pozorované faktory jsou proto `TECHNICALLY_OBSERVED`; jejich vazba na vlastníkovo konkrétní přepočítání je `WORKING_HYPOTHESIS`. Jednotková metadata v archivech nejsou sama o sobě dostačující, protože raw hodnoty v letech 2009–2012 jim neodpovídají. `windrun` musí být analyzován samostatně. Reprodukční bounded SQL template (spustit zvlášť pro každý UTC rok): `sql/readonly/historical_wind_transformation_single_utc_year.sql`; výsledky a 2013 boundary probe: `data/historical_wind_transformation_annual.json`; focused boundary SQL: `sql/readonly/historical_wind_2013_ratio_epoch_bounds.sql`. Nevydávat korekční návrhy na základě samotného poměru; vyžadovat field/epoch kontrakt, nulové a extrémní výjimky, okolní kontinuitu a případnou zdrojovou historii. V roce 2021 nebyla provedena žádná analýza ani návrh.

## Triangulace proti merged archivu `pocasi-loucka.eu_old` — 2026-11-13

Nová přesná source-copy concordance porovnala 1 146 308 union timestamp keys v letech 2009–2020 a odděleně klasifikovala poměr `pocasi-loucka.eu_old / old_weewx` pro shodné nenulové kopie. Na společných timestampových řádcích mají staré archivy `usUnits=17`, merged archive `usUnits=16`; dominantní interval je 5 minut. Pro každý faktor je požadována tolerance ±0,001.

- `windSpeed`: 2009–2012 poměr 1 u 311 710 nenulových párů; v roce 2013 je 48 202/63 337 v pásmu 3,6 a 15 135/63 337 v pásmu 1; 2014–2020 je poměr 3,6 u 553 259 párů a žádná z 553 259 spadá do poměru 1.
- `windGust`: 2009–2012 poměr 1 u 313 823 párů; 2013 51 314/67 483 v pásmu 3,6 a 16 169/67 483 v pásmu 1; 2014–2020 poměr 3,6 u 575 382 párů.
- 2013 obsahuje smíšenou epochu v souladu s dřívějším časovým ohraničením 6.–12. dubna. V roce 2014–2020 přesný faktor 3,6 souhlasí s převodem METRICWX→METRIC, což silně podporuje jednotkovou transformaci uložených hodnot. To samo neprokazuje, zda byl stejný převod zamýšlen při merge ani zda jsou zdrojová měření správná.
- Před rokem 2013 identické raw hodnoty navzdory 17→16 unit kódům ukazují, že jednotková metadata a raw payload spolu v této epoše netvoří konzistentní jednoduchý kontrakt. Nelze zpětně aplikovat faktor 3,6 plošně.
- `rain` se často neshoduje s očekávaným poměrem 0,1; `rainRate` jej většinou sleduje, ale má lokalizované výjimky. Bez intervalového kontraktu a counter/aggregation semantics to není schválená konverzní politika.

Annual detail, source aggregates, 12 fixed-year SELECTs and validator are in `reports/2026-11-13-historical-migration-conversion-factor-2009-2020.md`, `data/historical_migration_conversion_factor_2009_2020.json`, and `sql/readonly/historical_migration_conversion_factor_<year>.sql`. Výsledek klasifikuje transformaci jako silně podpořenou pro `windSpeed`/`windGust` od 2014, nikoli jako opravu jednotlivých řádků. Rok 2021 nebyl dotazován.


## Long-gap boundary cross-check — 2015–2017 exact source keys

Five `pocasi-loucka.eu_old` rows near 2015–2017 long-gap boundaries share exact timestamp keys with `old_weewx`/`weewx_WH1080` and are 59–120 seconds from an existing reconstruction endpoint. At these exact keys, each nonzero windSpeed and windGust value is 3.6× the old archive value (zero remains zero), with `usUnits=16` at eu_old/reconstruction and `usUnits=17` in old/WH1080. The transformed wind fields also exactly match the nearest existing reconstruction row. This is a small direct example consistent with METRICWX m/s → METRIC km/h conversion and corroborates, but does not extend beyond, the 2014–2020 aggregate factor already reported above. Four earlier boundary rows have the metadata transition without a numeric wind change, so no factor should be applied before the observed epoch. The nine rows are boundary-adjacent duplicates, not missing gap measurements; one has a separate 1.1 °C temperature conflict. No correction is proposed. Details: `reports/2026-11-13-long-gap-eu_old-boundary-rows.md`.


## Cílená revize anomální epochy 2020-08-20 až 2020-09-01

Read-only exact-key agregace `weewx_WH1080` proti `pocasi-loucka.eu_old` zjistila v polootevřeném UTC okně 3 454 WH1080 řádků, 3 446 společných klíčů a 8 chybějících `eu_old` řádků. `old_weewx` v celém okně řádek nemá. Faktor METRICWX→METRIC 3,6 odpovídá 801/3 421 nenulových `windSpeed` a 1 906/3 443 nenulových `windGust` párů; ostatní jsou mimo faktory 3,6 i 1. U všech společných klíčů jsou větrné hodnoty v `pocasi-loucka.eu`, `pocasi-loucka.eu_GW1000` a `loucka_reconstruction` shodné s `pocasi-loucka.eu_old`, tedy sdílejí jeho uložený výsledek a nepředstavují nezávislé potvrzení. Epizoda zůstává `REVIEW_REQUIRED`; žádná korekce ani plošná konverze není navržena. Detailní denní agregáty, reprodukční SQL a validator jsou uvedeny v `reports/2026-11-14-historical-wind-2020-anomaly-review.md` a `data/historical_wind_2020_aug20_sep1_review.json`.
