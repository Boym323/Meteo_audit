# Časové intervaly WeeWX a agregace

## Význam času archivu

`archive.dateTime` je Unix čas v sekundách UTC na **konci** archivního intervalu. Záznam s koncem `t` a délkou `archive.interval` minut reprezentuje `(t - interval, t]`. Stejnou konvenci popisuje [dokumentace WeeWX pro vývojáře](https://www.weewx.com/docs/5.4/devnotes/) a [návod k importu WeeWX](https://www.weewx.com/docs/latest/utilities/weectl-import-common-opt/).

Dotaz pro místní období s hranicemi `start` a `end` proto používá `dateTime > start_epoch AND dateTime <= end_epoch`. Sousední období `(A,B]` a `(B,C]` mají průnik prázdný: záznam v `B` náleží právě období, které v `B` končí. Záznam o půlnoci patří předchozímu občanskému dni/měsíci/roku. Toto pravidlo nepředpokládá pětiminutovou kadenci.

## Časová pásma a denní součty

Hranice kalendáře se nejprve vytvářejí jako půlnoc `Europe/Prague` a až poté převádějí na Unix UTC. Délka dne tedy může být 23 nebo 25 hodin. Opakovaná místní hodina je jednoznačně rozlišena epochou a UTC offsetem (`+0200` / `+0100`); neexistující jarní hodina se nevytváří.

Denní maximum v `monthly.py` používá občanský den od místní půlnoci do další půlnoci. Meteorologický srážkoměrný den s jiným časem uzávěrky je jiná definice a tento výstup jej nepředstírá. Pro něj musí být hranice zadána explicitně jako místní čas a převedena zvlášť.

Intervalový déšť se přiřazuje do bucketu podle konce záznamu. Pokud neobvykle dlouhý interval překročí hranici bucketu, hodnota se nedělí poměrem ani nepřipisuje nule; zůstává celá u okamžiku konce a situace je určena k samostatnému posouzení.

## Pokrytí a chybějící data

Výstup odděluje počet archivních řádků, `rain=NULL`, skutečnou `rain=0` a kladný déšť. Chybějící celý řádek se odhaduje z mezer mezi časovými značkami a z intervalu předchozího záznamu; nesoulad s násobkem intervalu se eviduje jako nepravidelný krok. Samostatně se označují timestampy mimo pětiminutovou UTC mřížku.

`expected_grid_rows_estimated` a `row_coverage_pct_estimated` jsou pouze odhadem příležitostí k archivaci na nejčastějším intervalu v měsíci (u prázdného měsíce na globálním nejčastějším intervalu). Neříkají, zda měření ověřil senzor ani zda jeho hodnota byla správná. První/poslední částečné období a celé měsíce bez řádku se nesmějí zaměnit s měřenou nulovou srážkou.

V rozsahu reportu z 30. 10. 2026 bylo vygenerováno 214 kalendářních měsíců 2009-01 až 2026-10. V dřívějším výstupu mělo řádky 206 měsíců; zbývajících 8 tvořily dva měsíce před první historií a šest prázdných měsíců během výpadku 2011-09 až 2012-02. Jde o rozdílné a souběžně správné počty.
