# Kalibrace historického tlaku Loučky: skutečný časový holdout po epochách

**Provedeno:** 23. 11. 2026. **Stav:** diagnostický výpočet na **existujících měsíčních statistikách PR #89**, bez SQL zápisů a bez jakýchkoli schválených náhrad. [Zdrojový model](../../scripts/backtest_pressure_epoch_monthly.mjs) · [Strojově čitelné úplné výsledky](pressure-epoch-monthly-holdout-20261123.json).

## Stručný závěr

Výpočet porovnal **10 historických kalibračních epoch**, z nichž 4 mají před rokem 2018 pouze hrubý měsíční kontext, 1 krátká přechodová epocha má jen jeden měsíc a 5 má přímo časově párované hodinové referenční údaje **agregované do měsíčních mediánů**.

**Jediná epocha, která prošla oběma směry nezávislého měsíčního testu, je H5 (2024-08 až 2026-01).** V letech 2018–2019 je výrazný signál správně modelovatelného driftu, ale výsledek po trénování na Mošnovu je horší než předběžná podmínka. V letech 2019–2024 není zlepšení stabilní; po březnu 2026 máme jen 2 testovací měsíce a původní tlak je již blízko ČHMÚ.

**Ani úspěšný měsíční backtest není validací jednotlivých hodin nebo pětiminutových hodnot.** Tato fáze se vztahuje ke **`barometer` vůči ČHMÚ `P_hm`**. Nevytváří lokálně změřený ani opravený staniční `pressure`, žádná data se nesmí aplikovat. Před 2018 jde o modelovaný staniční `pressure` porovnávaný s denním `P` **bez přesného časového párování**; výsledky slouží pouze k průzkumu.

## Metodika bez úniku dat

- Srovnávané varianty: **bez korekce** (nulový bias), **konstantní korekce** (medián na tréninku), **časový trend** (Theil–Sen robustní medián párových sklonů + medián interceptu).
- Každá epocha má chronologické bloky trénink (~60 % starších měsíců), validace (~20 % následujících) a **holdout (zbývající poslední měsíce)**. Všechny koeficienty vznikají výhradně z tréninku, výběr varianty výhradně na validaci. Holdout nemůže ovlivnit ani parametry, ani výběr.
- Model se trénuje a vybírá zvlášť na **Holešovu** a na **Mošnovu**. Každý výsledek se na pozdějším holdoutu vyhodnocuje **pro obě stanice**, včetně opačné stanice nikdy nepoužité k jeho kalibraci. Vyhodnocení je nevyvážený průměr přes měsíce (každý měsíc má stejnou váhu, nikoli počet SYNOP hodin).
- Rozlišují se kvality: pro hourly podklad jen ČHMÚ `QUALITY=0`, přesné UTC páry, minimálně 48 párů na stanici/měsíc. Pro starší denní kontext min. 15 denních `P` referencí a 2 000 lokálních archivních záznamů na měsíc. **Jiné časové podpory se nikdy nepovažují za ekvivalent.**
- Přechodové měsíce `2013-08`, `2019-04`, `2022-08`, `2024-05`, `2024-07`, `2026-02`, `2026-03` jsou vyloučené nebo izolované kvůli doloženým či podezřelým zlomům. **Rozdělení H3–H6 je předběžné podle GW1000 pojmenované kopie, která není totožná s rekonstrukcí; nemá se vydávat za důkaz fyzické výměny senzoru.**
- Závazné bezpečnostní pravidlo: **žádné SQL UPDATE/INSERT/DELETE, žádné APPLY, žádné kopírování WH1080 ani automatický výpočet station `pressure` z `barometer`**.

## Test na měsících, které model neviděl (MAE v hPa)

H = Holešov 11774; M = Mošnov 11782. `H→M` znamená model **trénovaný na Holešově**, ale testovaný na **Mošnovu** v budoucích měsících. Všechny uvedené MAE jsou **průměrná absolutní chyba měsíčních mediánů**, **nikoli MAE jednotlivých hodin nebo archivních intervalů**.

| Epocha | Časový úsek | Dostupné měsíce | Zvolený model H / M | H→H MAE | H→M MAE | M→M MAE | M→H MAE | Diagnostický stav |
|---|---|---:|---|---:|---:|---:|---:|---|
| D1 | 2009–2011 před výpadkem | 29 | Konstantní offset / Theil–Sen drift | 1,13 | 1,20 | 1,15 | 1,25 | Pouze orientační souhrny |
| D2 | 2012 až před skokem 2013 | 17 | Theil–Sen drift / Theil–Sen drift | 2,16 | 1,88 | 1,66 | 1,94 | Pouze orientační souhrny |
| D3 | po skoku 2013 až 2015 | 28 | Theil–Sen drift / Theil–Sen drift | 0,55 | 0,71 | 0,80 | 0,62 | Pouze orientační souhrny |
| D4 | 2016–2017 | 24 | Theil–Sen drift / Theil–Sen drift | 0,67 | 0,77 | 2,58 | 3,39 | Pouze orientační souhrny |
| H1 | 2018 až před přepnutím 2019 | 15 | Theil–Sen drift / Theil–Sen drift | 0,34 | 0,95 | 1,91 | 1,31 | Neprošel diagnostickou podmínkou |
| H2 | 2019 po přepnutí až před GW1000 | 39 | Konstantní offset / Bez korekce | 2,22 | 2,56 | 1,54 | 1,36 | Neprošel diagnostickou podmínkou |
| H3 | GW1000 před změnou kopie 2024 | 20 | Konstantní offset / Konstantní offset | 1,97 | 2,32 | 2,09 | 1,85 | Neprošel diagnostickou podmínkou |
| H4 | přechod mezi změnami 2024 | 1 | — | — | — | — | Nedostatečná data |
| H5 | 2024 změněná kopie až 2026 | 18 | Theil–Sen drift / Theil–Sen drift | 1,02 | 0,94 | 1,07 | 1,24 | Prošel pouze měsíční test |
| H6 | 2026 po březnovém rozchodu | 8 | Konstantní offset / Bez korekce | 0,07 | 0,35 | 0,08 | 0,31 | Neprošel diagnostickou podmínkou |

Předběžná, **nikoliv schvalovací** podmínka „měsíční test prošel“ je: alespoň 3 měsíce na holdoutu a v obou směrech stanice MAE nejvýše 1,5 hPa a 95. percentil absolutních **měsíčních mediánových** chyb nejvýše 3,0 hPa. Krátká H4 ji nemůže vyhodnotit; D1–D4 nejsou časově přímá hodinová měření. Tento práh **nijak nedokazuje bezpečnost rekonstrukce nebo shodu v konkrétní hodině**.

### Důležité srovnání s nulovou korekcí

- **H1 (2018-01 až 2019-03), holdout 2019-01 až 2019-03:** model trénovaný na Holešově `Theil–Sen` má MAE **0,34** na Holešově a **0,95** na nezávislém Mošnovu; bez korekce **27,20** a **26,59** hPa. Při tréninku na Mošnovu vychází na Mošnovu MAE **1,91** hPa, proto výsledek není oboustranně přesvědčivý podle stanoveného pilotního prahu.
- **H2 (2019-05 až 2022-07), holdout 2021-11 až 2022-07:** konstantní offset z Holešova **zhoršil** jeho chybu z **1,36 hPa bez korekce** na **2,22 hPa**. Pro toto období model nesmíme předpokládat lepší než raw; nezávislý Mošnov na validaci dokonce vybral **raw**.
- **H3 (2022-09 až 2024-04):** konstantní offset dosáhl na Holešovu MAE **1,97** a na Mošnovu při opačném tréninku **2,09** hPa. Zlepšení není dostatečně spolehlivé.
- **H5 (2024-08 až 2026-01), holdout 2025-09 až 2026-01:** trend naučený na Holešovu dává MAE **1,02** na Holešově a **0,94** na Mošnovu. Trend z Mošnova má **1,07** na Mošnovu a **1,24** na Holešovu. Bez kalibrace by byly vlastní chyby **4,16** a **4,64** hPa. **Prošel pouze měsíčním diagnostickým testem**, nikoliv skutečnou hodinovou kalibrací.
- **H6 (2026-04 až 2026-11):** Mošnov na validaci vybral původní **raw**; holdout zahrnuje pouze 2 měsíce a nelze z něj odvozovat dlouhodobou platnost kalibrace.

## Další nezbytná validace před vůbec uvažovaným APPLY

1. **Hodinové backtesty na originálních SHA-256 referencích ČHMÚ:** na LXC, kde jsou raw CSV z PR #89, přesně v UTC připojit hodinové P_hm k pětiminutovému `barometer`, a zvlášť P k diagnostickému výškově převedenému `pressure`. Hodnotit po jednotlivých hodinách: MAE, bias, MAD, p95 absolutní chyby, pokrytí, extrémy, změnové body a časové holdouty, nikoli jen měsíční mediány. Nesmí se měnit tréninkový model na základě holdoutu.
2. **Kalibrační epistemika:** přímo měřené WH1080 z let 2016–18 nesou významný tlakový drift; modelově korigovaná hodnota není čisté `MEASURED` pozorování. Je třeba explicitní provenance, nejistota a `ESTIMATED/CALIBRATED` status.
3. **Roky 2009–2017:** testovat historicky platné výšky, jednotky, pětiminutové úseky a plnohodnotné časové agregace (CHMI denní `TIMEFUNC`); současný měsíční kontext bez synchronizace nedává konkrétní obnovitelnou hodnotu. Zvláště chránit 2018 Q1.
4. **Rok 2022:** pro 45 069 chybějících primárních hodnot bez přímého zdroje **nelze** použít regionální ČHMÚ referenci jako původní místní měření. Případný odhad musí mít samostatnou validaci (chybějící vstupy, odlišná meteorologická podporovaná doba, confidence intervals).
5. **Explicitní rozhodnutí:** než bude existovat hodinový a pětiminutový test i schválený individuální manifest `batch_id + SHA256 + before-images + old/new + source`, zůstává **NO-GO**. Neměnit produkci ani WeeWX v jiném LXC.

## Reprodukce

Požaduje pouze Node.js 20+ a dva již verzované agregované CSV soubory PR #89. Z kořene čistého worktree:

```sh
node scripts/backtest_pressure_epoch_monthly.mjs --out /tmp/pressure-epoch-monthly.json
node --test tests/test_backtest_pressure_epoch_monthly.mjs
```

Zdroj: [`hourly_monthly_stats.csv`](pressure-chmi-numeric-2009-2026/hourly_monthly_stats.csv), [`daily_chmi_monthly_context.csv`](pressure-chmi-numeric-2009-2026/daily_chmi_monthly_context.csv); přesné blob identifikátory a plné parametry jsou v JSON výstupu. **Model byl skutečně numericky vyhodnocen na těchto CSV v aktuálním nástroji a základní kontrolní aserce i test nulového úniku z holdoutu prošly.** Samostatné spuštění Node test runneru a **živé hodinové/pětiminutové** testy na LXC zatím nebyly provedeny a nesmějí být vykazovány jako PASS.

**Verdikt:** `NO_GO_PRESSURE_APPLY`. Pouze jedna moderní epocha uspěla v měsíční diagnostice; žádná jednotlivá hodnotová náhrada nebyla schválena.
