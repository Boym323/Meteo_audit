# Rekonstrukce tlaku Loučky po PR #96 — samostatný read-only follow-up

**Datum snapshotu:** 2026-11-24 UTC · **rozsah nového modelového testu:** 2022-01 až 2022-07 · **stav:** všechny návrhy `ESTIMATED / UNAPPROVED`; 0 schválených a 0 kalibrovaných náhrad.

Žádný příkaz tohoto běhu nezapisoval do SQL. Použil se existující účet `loucka_web_ro` v jediné `START TRANSACTION READ ONLY` transakci na ověřeném serveru `lo-infra-db-mariadb01`, server_id 1. Nebyla dotčena původní data, produkční DB, SQL práva ani WeeWX. Q1 2018 je vyloučeno z návrhů. Všechny nové odhady zůstávají oddělené od archivu a neschválené.

## Uchování výstupu PR #96

Původní `evidence.json` a CSV byly zkopírovány z `/tmp/loucka-pressure-shadow-2022-v1` do trvalého lokálního adresáře `/opt/meteo-audit-artifacts/pressure-shadow-2022-v1` a do tohoto repozitáře. SHA-256 původních souborů:

- `evidence.json`: `50f33ebb3883e865d06234938ce33049c6c7596e76823ac178231c32ecfec8f7`
- `pressure-shadow-unapproved.csv`: `d4ac993dae6a640e01049e733e0ff23f61900f129347359ca1c694b1a42e5179`

Podrobné hashe všech verzovaných souborů jsou v [SHA256SUMS.txt](data/pressure-shadow-2022-v1/SHA256SUMS.txt). Originální artefakty nebyly upraveny; obohacený návrhový CSV je samostatný soubor.

## Přesná měsíční brána a důvody odmítnutí

Zachována nezměněná brána zmrazeného modelu: nejméně 100 společných hodin s oběma stanicemi, pokrytí alespoň 80 % způsobilých přesných UTC hodin, na **každé** stanici MAE ≤2 hPa, absolutní mediánový bias ≤1.5 hPa a P95 absolutní chyby ≤4 hPa. Jednotlivé referenční metriky jsou vůči ČHMÚ `P` po transportu výšky z 425 m na výšku stanice. Bias níže je podepsaný medián rezidua.

| Měsíc | Společné / způsobilé hodiny | Pokrytí | Holešov MAE / bias / P95 (hPa) | Mošnov MAE / bias / P95 (hPa) | Rozhodnutí a přesná příčina |
|---|---:|---:|---:|---:|---|
| 2022-01 | 686 / 687 | 99.85 % | 1.000 / +0.484 / 2.893 | 2.128 / +1.917 / 4.520 | Fail: Mošnov porušuje MAE, bias i P95 |
| 2022-02 | 648 / 650 | 99.69 % | 1.635 / +1.586 / 3.422 | 2.991 / +2.988 / 5.687 | Fail: Holešov bias; Mošnov MAE, bias i P95 |
| 2022-03 | 567 / 569 | 99.65 % | 0.902 / +0.487 / 2.729 | 1.147 / +0.712 / 3.213 | Pass diagnostic only |
| 2022-04 | 119 / 119 | 100 % | 2.043 / −2.092 / 2.998 | 2.003 / −1.991 / 3.185 | Fail: obě MAE a bias; počet/pokrytí dostačují |
| 2022-05 | 694 / 694 | 100 % | 0.953 / −0.851 / 2.029 | 0.956 / −0.457 / 2.072 | Pass diagnostic only |
| 2022-06 | 641 / 645 | 99.38 % | 2.302 / +2.480 / 5.015 | 2.517 / +2.996 / 5.548 | Fail: obě stanice porušují MAE, bias i P95 |
| 2022-07 | 79 / 80 | 98.75 % | 3.473 / +3.530 / 4.925 | 3.652 / +3.578 / 5.273 | Fail: jen 79 hodin (<100) a obě stanice porušují MAE, bias i P95 |

Korekce dřívějšího předběžného popisu: gate v modelu PR #96 je MAE 2, P95 4, |median bias| 1.5, nikoli 1.5/3/1. Pro úplnou reprodukci hodnot viz [originální evidence](data/pressure-shadow-2022-v1/evidence.json).

## Fyzikální alternativy, oddělení bloků a drift

Na stejných missing exact-hour timestamp blocích 2022 byly bez přeučení porovnány tři předem jednoznačné varianty: (1) čistá hypsometrická inverze barometer→station pressure, (2) fyzikální výsledek + zmrazený konstantní offset z tréninku 2020 a (3) původní zmrazená teplotní korekce, trénovaná v 2020 a vybraná na samostatné validaci 2021. Všechny používají stejný, nezměněný dual-station gate. Nebyly odhadovány měsíční korekce z validačního měsíce. Kompletní stanice×model×měsíc MAE, bias, P95 a coverage jsou v [alternative-models.json](data/pressure-shadow-2022-v1/alternative-models.json); graf je [monthly-model-mae.svg](data/pressure-shadow-2022-v1/monthly-model-mae.svg).

Výsledek: fyzikální varianta sama gate splňuje v lednu, březnu a květnu; konstantní a teplotní modely pouze v březnu a květnu. Žádná z variant neodstraní chybu února, dubna, června ani července. V lednu se fyzikální varianta vůči Mošnovu blíží limitům (MAE 1.717, bias +1.311, P95 3.988), ale starší zmrazený teplotní model zde selže. Nepoužil jsem únorová/červnová data k dopočtu nové měsíční korekce, protože by se tím validační blok stal i tréninkem.

Pro období 2016–2018 nebyla tato regionální hodinová metoda rozšířena do kandidátní řady. Již doložený přesný test 2018 WH1080 proti oběma ČHMÚ stanicím vykazuje pro chybějící cílový tlak MAE 22.97/22.45 hPa, median bias −23.06/−22.81 hPa a P95 25.63/25.43 hPa; WH1080 a `old_weewx` jsou jedna kopírovaná linie. To je doložený tlakový drift/bias, ne vhodný korekční koeficient pro imputaci. Pro 2016–2017 zůstává dostupný podklad denní ČHMÚ kontext, který nevaliduje hodinové ani pětiminutové hodnoty. Q1 2018 zůstává výslovně chráněné. Bez nezávislých bloků v každé době senzoru nelze věrohodně převést pozdější fyzikální model do starší epochy.

## Kontrola 15 166 odhadů

Všech 15 166 původních preview řádků odpovídá existujícím NULL `pressure` timestampům ve stejné read-only extrakci; duplikátů není. Hodnoty spadají do 953.5508–991.3134 hPa a všechny jsou v širokém fyzikálním rozsahu 900–1050 hPa. To není nezávislé potvrzení.

| Měsíc | Počet | Rozsah hPa | Odhady v pětiminutových párech | Nejdelší mezera mezi kandidáty | Největší pětiminutový skok |
|---|---:|---:|---:|---:|---:|
| březen | 6 880 | 953.5508–991.3134 | 6 786 | 21 h 30 min | 5.2482 hPa |
| květen | 8 286 | 956.4849–977.8390 | 8 203 | 4 h 50 min | 1.5255 hPa |

Pro porovnání s naměřeným tlakem v okně ±1 hodina existuje jen 54 březnových a 38 květnových sousedů. Rozdíl predikce od nejbližší takové hodnoty má median/P95/max 0.572/1.008/1.162 hPa v březnu a 0.672/1.152/1.307 hPa v květnu. Málo sousedních měření a výběr podle dostupnosti nedovolují tvrdit plošnou pětiminutovou přesnost. Velký březnový skok a dlouhé časové mezery proto zůstávají v kandidátním CSV explicitně zachované.

Každý řádek samostatného [pressure-series-proposed-unapproved.csv](data/pressure-shadow-2022-v1/pressure-series-proposed-unapproved.csv) uvádí timestamp UTC, původní NULL, odhad, zdrojové vstupy, hash modelu a referencí, třídu `ESTIMATED`, `UNAPPROVED` a empirickou nejistotu z maxima měsíčního regionálního P95 a lokálního holdout P95. Tato nejistota je diagnostická empirická chyba, **není** interval spolehlivosti ani mez chyby konkrétního řádku.

## Jednotný stav řady a zbývající mezery

Aktuální read-only inventura obsahuje 1 697 588 archivních řádků za roky 2009–2026. [annual-status-inventory.json](data/pressure-shadow-2022-v1/annual-status-inventory.json) rozlišuje existující `MEASURED`, `CALIBRATED=0`, samostatné `ESTIMATED=UNAPPROVED` a zbylé NULL `UNRESOLVED`. V roce 2022 má aktuální snapshot 46 315 NULL tlaků, z toho 42 484 má `barometer+outTemp`; 15 166 řádků je pouze preview z března a května, 31 149 zůstává unresolved. Celkem mají roky 2016–2018 90 567 NULL tlaků; současný důkazní stav nepodporuje automatické převzetí WH hodnot ani modelové náhrady.

Počty podle statusu a roku v JSON jsou snapshotové; nová měření mohou změnit stav archivu. `MEASURED` zde znamená pouze původní neprázdný archive pressure a není tvrzením o univerzální kalibraci. `CALIBRATED` je nula. `UNRESOLVED` znamená NULL bez vložené návrhové hodnoty, nikoli nulu nebo potvrzenou meteorologickou absenci.

## Rozhodnutí a další krok

- Zachovat 15 166 řádků jako oddělené diagnostické `ESTIMATED / UNAPPROVED`; nevkládat do DB ani do apply manifestu.
- Žádné další měsíce neprošly stejnou bránou napříč oběma referencemi. Zamítnuté měsíce zůstávají `UNRESOLVED`.
- `CALIBRATED` hodnoty: 0. Doporučení ke schválení/produkční aplikaci: **žádné**. Březen/květen mohou být případně předloženy k odbornému individuálnímu posouzení jen jako modelové odhady, nikoli obnovená měření; pětiminutový holdout a chyby v místech skoků chybí.
- Historické 2016–2018 dál neobnovovat, dokud nebude k dispozici epochově nezávislá reference, která vysvětlí drift WH1080; zachovat ochranu Q1 2018.
