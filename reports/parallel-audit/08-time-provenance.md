# 08 — Forenzní audit časové struktury a provenance (2009–2026)

**Datum kontroly:** 2026-10-30. **Režim:** výhradně SQL `SELECT`, bez importu a bez změny databází. **Zdroj:** Weather MCP / MariaDB, šest schémat. Časy událostí ukládat jako epoch UTC; měsíční součty jsou zde po občanských měsících `Europe/Prague`, konvence WeeWX `(start,end]`.

## Metodika měsíční úplnosti

- Každý rok byl čten samostatným časově ohraničeným `SELECT` pro každou ze šesti tabulek `archive`; v SQL lze reprodukovat pomocí indexovaného predikátu `dateTime > start_epoch AND dateTime <= end_epoch` a `GROUP BY DATE_FORMAT(FROM_UNIXTIME(dateTime-1),'%Y-%m')`.
- `dateTime-1` přiřazuje interval končící přesně o půlnoci předchozímu měsíci. Číselné hranice místních měsíců byly vypočteny zvlášť v UTC (CET nebo CEST), nikoli prostým přidáním 24 hodin. MariaDB má `@@session.time_zone='SYSTEM'`, `@@system_time_zone='CET'`; test pro přechod říjen 2020 ukázal obě lokální `02:30` pro odlišné UTC epochy. `CONVERT_TZ(...,'UTC','Europe/Prague')` vrací `NULL` — nepoužívat bez naplněných timezone tabulek.
- Hodnota v buňce: **skutečné řádky (orientační procento pětiminutových slotů)**. Jmenovatel je počet pětiminutových kroků v měsíci, zkrácený první/poslední zaznamenanou epochou daného zdroje; prázdné měsíce uvnitř aktivního časového rozsahu se považují za 0 %. `—` je období mimo rozsah daného zdroje, nikoli výpadek. Pozor: překrývající se a nepravidelné archivní intervaly mohou způsobit **více než 100 %**; nejde o validovaný uptime, pouze o inventář řádků.
- Měsíční kontrola nesmí zaměňovat počet řádků za počet unikátních intervalů/senzorových měření; senzorová dostupnost vyžaduje vlastní masku přítomnosti po období.

## Úplnost po měsících (214 měsíců, 2009-01 až 2026-10)

| Měsíc | RECON | PROD | GW | OLD | WEEWX | WH1080 |
|---|---:|---:|---:|---:|---:|---:|
| 2009-01 | — | — | — | — | — | — |
| 2009-02 | — | — | — | — | — | — |
| 2009-03 | 619 (96.7 %) | 619 (96.7 %) | 619 (96.7 %) | 619 (96.7 %) | 619 (96.7 %) | 619 (96.7 %) |
| 2009-04 | 8 514 (98.5 %) | 8 514 (98.5 %) | 8 514 (98.5 %) | 8 535 (98.8 %) | 8 535 (98.8 %) | 8 535 (98.8 %) |
| 2009-05 | 8 927 (100.0 %) | 8 927 (100.0 %) | 8 927 (100.0 %) | 8 928 (100.0 %) | 8 928 (100.0 %) | 8 928 (100.0 %) |
| 2009-06 | 8 515 (98.6 %) | 8 515 (98.6 %) | 8 515 (98.6 %) | 8 517 (98.6 %) | 8 517 (98.6 %) | 8 517 (98.6 %) |
| 2009-07 | 7 951 (89.1 %) | 7 951 (89.1 %) | 7 951 (89.1 %) | 7 960 (89.2 %) | 7 960 (89.2 %) | 7 960 (89.2 %) |
| 2009-08 | 8 762 (98.1 %) | 8 762 (98.1 %) | 8 762 (98.1 %) | 8 851 (99.1 %) | 8 851 (99.1 %) | 8 851 (99.1 %) |
| 2009-09 | 8 613 (99.7 %) | 8 613 (99.7 %) | 8 613 (99.7 %) | 8 614 (99.7 %) | 8 614 (99.7 %) | 8 614 (99.7 %) |
| 2009-10 | 8 791 (98.3 %) | 8 791 (98.3 %) | 8 791 (98.3 %) | 8 799 (98.4 %) | 8 799 (98.4 %) | 8 799 (98.4 %) |
| 2009-11 | 8 607 (99.6 %) | 8 607 (99.6 %) | 8 607 (99.6 %) | 8 614 (99.7 %) | 8 614 (99.7 %) | 8 614 (99.7 %) |
| 2009-12 | 8 795 (98.5 %) | 8 795 (98.5 %) | 8 795 (98.5 %) | 8 800 (98.6 %) | 8 800 (98.6 %) | 8 800 (98.6 %) |
| 2010-01 | 8 901 (99.7 %) | 8 901 (99.7 %) | 8 901 (99.7 %) | 8 905 (99.7 %) | 8 905 (99.7 %) | 8 905 (99.7 %) |
| 2010-02 | 7 985 (99.0 %) | 7 985 (99.0 %) | 7 985 (99.0 %) | 7 989 (99.1 %) | 7 989 (99.1 %) | 7 989 (99.1 %) |
| 2010-03 | 8 792 (98.6 %) | 8 792 (98.6 %) | 8 792 (98.6 %) | 8 794 (98.6 %) | 8 794 (98.6 %) | 8 794 (98.6 %) |
| 2010-04 | 8 614 (99.7 %) | 8 614 (99.7 %) | 8 614 (99.7 %) | 8 616 (99.7 %) | 8 616 (99.7 %) | 8 616 (99.7 %) |
| 2010-05 | 8 900 (99.7 %) | 8 900 (99.7 %) | 8 900 (99.7 %) | 8 902 (99.7 %) | 8 903 (99.7 %) | 8 903 (99.7 %) |
| 2010-06 | 8 506 (98.4 %) | 8 506 (98.4 %) | 8 506 (98.4 %) | 8 506 (98.4 %) | 8 506 (98.4 %) | 8 506 (98.4 %) |
| 2010-07 | 8 716 (97.6 %) | 8 716 (97.6 %) | 8 716 (97.6 %) | 8 716 (97.6 %) | 8 716 (97.6 %) | 8 716 (97.6 %) |
| 2010-08 | 8 744 (97.9 %) | 8 744 (97.9 %) | 8 744 (97.9 %) | 8 753 (98.0 %) | 8 753 (98.0 %) | 8 753 (98.0 %) |
| 2010-09 | 8 566 (99.1 %) | 8 566 (99.1 %) | 8 566 (99.1 %) | 8 566 (99.1 %) | 8 566 (99.1 %) | 8 566 (99.1 %) |
| 2010-10 | 8 841 (98.9 %) | 8 841 (98.9 %) | 8 841 (98.9 %) | 8 843 (98.9 %) | 8 843 (98.9 %) | 8 843 (98.9 %) |
| 2010-11 | 8 619 (99.8 %) | 8 619 (99.8 %) | 8 619 (99.8 %) | 8 619 (99.8 %) | 8 619 (99.8 %) | 8 619 (99.8 %) |
| 2010-12 | 8 906 (99.8 %) | 8 906 (99.8 %) | 8 906 (99.8 %) | 8 906 (99.8 %) | 8 906 (99.8 %) | 8 906 (99.8 %) |
| 2011-01 | 8 927 (100.0 %) | 8 927 (100.0 %) | 8 927 (100.0 %) | 8 928 (100.0 %) | 8 928 (100.0 %) | 8 928 (100.0 %) |
| 2011-02 | 8 038 (99.7 %) | 8 038 (99.7 %) | 8 038 (99.7 %) | 8 042 (99.7 %) | 8 042 (99.7 %) | 8 042 (99.7 %) |
| 2011-03 | 8 830 (99.0 %) | 8 830 (99.0 %) | 8 830 (99.0 %) | 8 830 (99.0 %) | 8 830 (99.0 %) | 8 830 (99.0 %) |
| 2011-04 | 8 355 (96.7 %) | 8 355 (96.7 %) | 8 355 (96.7 %) | 8 357 (96.7 %) | 8 357 (96.7 %) | 8 357 (96.7 %) |
| 2011-05 | 8 098 (90.7 %) | 8 098 (90.7 %) | 8 098 (90.7 %) | 8 100 (90.7 %) | 8 100 (90.7 %) | 8 100 (90.7 %) |
| 2011-06 | 8 358 (96.7 %) | 8 358 (96.7 %) | 8 358 (96.7 %) | 8 363 (96.8 %) | 8 363 (96.8 %) | 8 363 (96.8 %) |
| 2011-07 | 8 464 (94.8 %) | 8 464 (94.8 %) | 8 464 (94.8 %) | 8 467 (94.8 %) | 8 887 (99.5 %) | 8 887 (99.5 %) |
| 2011-08 | 3 784 (42.4 %) | 3 784 (42.4 %) | 3 784 (42.4 %) | 3 785 (42.4 %) | 7 833 (87.7 %) | 7 833 (87.7 %) |
| 2011-09 | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| 2011-10 | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| 2011-11 | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| 2011-12 | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| 2012-01 | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| 2012-02 | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| 2012-03 | 4 384 (49.2 %) | 4 384 (49.2 %) | 4 384 (49.2 %) | 4 387 (49.2 %) | 4 387 (49.2 %) | 4 387 (49.2 %) |
| 2012-04 | 8 470 (98.0 %) | 8 470 (98.0 %) | 8 470 (98.0 %) | 8 473 (98.1 %) | 8 473 (98.1 %) | 8 473 (98.1 %) |
| 2012-05 | 8 816 (98.7 %) | 8 816 (98.7 %) | 8 816 (98.7 %) | 8 822 (98.8 %) | 8 822 (98.8 %) | 8 822 (98.8 %) |
| 2012-06 | 8 215 (95.1 %) | 8 215 (95.1 %) | 8 215 (95.1 %) | 8 216 (95.1 %) | 8 216 (95.1 %) | 8 216 (95.1 %) |
| 2012-07 | 8 845 (99.1 %) | 8 845 (99.1 %) | 8 845 (99.1 %) | 8 847 (99.1 %) | 8 847 (99.1 %) | 8 847 (99.1 %) |
| 2012-08 | 8 244 (92.3 %) | 8 244 (92.3 %) | 8 244 (92.3 %) | 8 247 (92.4 %) | 8 247 (92.4 %) | 8 247 (92.4 %) |
| 2012-09 | 6 501 (75.2 %) | 6 501 (75.2 %) | 6 501 (75.2 %) | 6 503 (75.3 %) | 6 503 (75.3 %) | 6 503 (75.3 %) |
| 2012-10 | 8 136 (91.0 %) | 8 136 (91.0 %) | 8 136 (91.0 %) | 8 140 (91.1 %) | 8 140 (91.1 %) | 8 140 (91.1 %) |
| 2012-11 | 8 563 (99.1 %) | 8 563 (99.1 %) | 8 563 (99.1 %) | 8 563 (99.1 %) | 8 563 (99.1 %) | 8 563 (99.1 %) |
| 2012-12 | 5 161 (57.8 %) | 5 161 (57.8 %) | 5 161 (57.8 %) | 5 163 (57.8 %) | 5 163 (57.8 %) | 5 163 (57.8 %) |
| 2013-01 | 8 526 (95.5 %) | 8 526 (95.5 %) | 8 526 (95.5 %) | 8 528 (95.5 %) | 8 528 (95.5 %) | 8 528 (95.5 %) |
| 2013-02 | 5 547 (68.8 %) | 5 547 (68.8 %) | 5 547 (68.8 %) | 5 548 (68.8 %) | 5 549 (68.8 %) | 5 549 (68.8 %) |
| 2013-03 | 7 699 (86.4 %) | 7 699 (86.4 %) | 7 699 (86.4 %) | 7 701 (86.4 %) | 7 701 (86.4 %) | 7 701 (86.4 %) |
| 2013-04 | 6 501 (75.2 %) | 6 501 (75.2 %) | 6 501 (75.2 %) | 6 501 (75.2 %) | 6 501 (75.2 %) | 6 501 (75.2 %) |
| 2013-05 | 8 768 (98.2 %) | 8 768 (98.2 %) | 8 768 (98.2 %) | 8 768 (98.2 %) | 8 768 (98.2 %) | 8 768 (98.2 %) |
| 2013-06 | 8 123 (94.0 %) | 8 123 (94.0 %) | 8 123 (94.0 %) | 8 123 (94.0 %) | 8 123 (94.0 %) | 8 123 (94.0 %) |
| 2013-07 | 7 757 (86.9 %) | 7 757 (86.9 %) | 7 757 (86.9 %) | 7 757 (86.9 %) | 7 760 (86.9 %) | 7 760 (86.9 %) |
| 2013-08 | 8 818 (98.8 %) | 8 818 (98.8 %) | 8 818 (98.8 %) | 8 818 (98.8 %) | 8 818 (98.8 %) | 8 818 (98.8 %) |
| 2013-09 | 8 637 (100.0 %) | 8 637 (100.0 %) | 8 637 (100.0 %) | 8 637 (100.0 %) | 8 637 (100.0 %) | 8 637 (100.0 %) |
| 2013-10 | 8 830 (98.8 %) | 8 830 (98.8 %) | 8 830 (98.8 %) | 8 830 (98.8 %) | 8 830 (98.8 %) | 8 830 (98.8 %) |
| 2013-11 | 8 638 (100.0 %) | 8 638 (100.0 %) | 8 638 (100.0 %) | 8 638 (100.0 %) | 8 638 (100.0 %) | 8 638 (100.0 %) |
| 2013-12 | 7 647 (85.7 %) | 7 647 (85.7 %) | 7 647 (85.7 %) | 7 647 (85.7 %) | 7 647 (85.7 %) | 7 647 (85.7 %) |
| 2014-01 | 7 472 (83.7 %) | 7 472 (83.7 %) | 7 472 (83.7 %) | 7 472 (83.7 %) | 7 472 (83.7 %) | 7 472 (83.7 %) |
| 2014-02 | 8 037 (99.7 %) | 8 037 (99.7 %) | 8 037 (99.7 %) | 8 037 (99.7 %) | 8 037 (99.7 %) | 8 037 (99.7 %) |
| 2014-03 | 8 641 (96.9 %) | 8 641 (96.9 %) | 8 641 (96.9 %) | 8 641 (96.9 %) | 8 641 (96.9 %) | 8 641 (96.9 %) |
| 2014-04 | 8 248 (95.5 %) | 8 248 (95.5 %) | 8 248 (95.5 %) | 8 248 (95.5 %) | 8 248 (95.5 %) | 8 248 (95.5 %) |
| 2014-05 | 8 924 (100.0 %) | 8 924 (100.0 %) | 8 924 (100.0 %) | 8 925 (100.0 %) | 8 925 (100.0 %) | 8 925 (100.0 %) |
| 2014-06 | 3 350 (38.8 %) | 3 350 (38.8 %) | 3 350 (38.8 %) | 3 350 (38.8 %) | 3 470 (40.2 %) | 3 470 (40.2 %) |
| 2014-07 | 7 242 (81.1 %) | 7 242 (81.1 %) | 7 242 (81.1 %) | 7 585 (85.0 %) | 8 382 (93.9 %) | 8 382 (93.9 %) |
| 2014-08 | 8 865 (99.3 %) | 8 865 (99.3 %) | 8 865 (99.3 %) | 8 897 (99.7 %) | 8 900 (99.7 %) | 8 900 (99.7 %) |
| 2014-09 | 8 489 (98.3 %) | 8 489 (98.3 %) | 8 489 (98.3 %) | 8 489 (98.3 %) | 8 640 (100.0 %) | 8 640 (100.0 %) |
| 2014-10 | 8 940 (100.0 %) | 8 940 (100.0 %) | 8 940 (100.0 %) | 8 940 (100.0 %) | 8 940 (100.0 %) | 8 940 (100.0 %) |
| 2014-11 | 8 640 (100.0 %) | 8 640 (100.0 %) | 8 640 (100.0 %) | 8 642 (100.0 %) | 8 642 (100.0 %) | 8 642 (100.0 %) |
| 2014-12 | 8 926 (100.0 %) | 8 926 (100.0 %) | 8 926 (100.0 %) | 8 926 (100.0 %) | 8 926 (100.0 %) | 8 926 (100.0 %) |
| 2015-01 | 8 904 (99.7 %) | 8 904 (99.7 %) | 8 904 (99.7 %) | 8 906 (99.8 %) | 8 930 (100.0 %) | 8 930 (100.0 %) |
| 2015-02 | 8 037 (99.7 %) | 8 037 (99.7 %) | 8 037 (99.7 %) | 8 037 (99.7 %) | 8 064 (100.0 %) | 8 064 (100.0 %) |
| 2015-03 | 8 914 (100.0 %) | 8 914 (100.0 %) | 8 914 (100.0 %) | 8 914 (100.0 %) | 8 914 (100.0 %) | 8 914 (100.0 %) |
| 2015-04 | 8 195 (94.8 %) | 8 195 (94.8 %) | 8 195 (94.8 %) | 8 195 (94.8 %) | 8 640 (100.0 %) | 8 640 (100.0 %) |
| 2015-05 | 7 986 (89.4 %) | 7 986 (89.4 %) | 7 986 (89.4 %) | 7 987 (89.5 %) | 8 027 (89.9 %) | 8 027 (89.9 %) |
| 2015-06 | 8 600 (99.5 %) | 8 600 (99.5 %) | 8 600 (99.5 %) | 8 603 (99.6 %) | 8 643 (100.0 %) | 8 643 (100.0 %) |
| 2015-07 | 8 417 (94.3 %) | 8 417 (94.3 %) | 8 417 (94.3 %) | 8 418 (94.3 %) | 8 921 (99.9 %) | 8 921 (99.9 %) |
| 2015-08 | 8 241 (92.3 %) | 8 241 (92.3 %) | 8 241 (92.3 %) | 8 439 (94.5 %) | 8 893 (99.6 %) | 8 893 (99.6 %) |
| 2015-09 | 8 408 (97.3 %) | 8 408 (97.3 %) | 8 408 (97.3 %) | 8 560 (99.1 %) | 8 610 (99.7 %) | 8 610 (99.7 %) |
| 2015-10 | 8 879 (99.3 %) | 8 879 (99.3 %) | 8 879 (99.3 %) | 8 907 (99.6 %) | 8 907 (99.6 %) | 8 907 (99.6 %) |
| 2015-11 | 8 403 (97.3 %) | 8 403 (97.3 %) | 8 403 (97.3 %) | 8 584 (99.4 %) | 8 617 (99.7 %) | 8 617 (99.7 %) |
| 2015-12 | 8 277 (92.7 %) | 8 277 (92.7 %) | 8 277 (92.7 %) | 8 365 (93.7 %) | 8 896 (99.6 %) | 8 896 (99.6 %) |
| 2016-01 | 5 151 (57.7 %) | 5 151 (57.7 %) | 5 151 (57.7 %) | 5 152 (57.7 %) | 8 910 (99.8 %) | 8 910 (99.8 %) |
| 2016-02 | 6 284 (75.2 %) | 6 284 (75.2 %) | 6 284 (75.2 %) | 6 328 (75.8 %) | 8 316 (99.6 %) | 8 316 (99.6 %) |
| 2016-03 | 8 200 (92.0 %) | 8 200 (92.0 %) | 8 200 (92.0 %) | 8 303 (93.1 %) | 8 880 (99.6 %) | 8 880 (99.6 %) |
| 2016-04 | 8 569 (99.2 %) | 8 569 (99.2 %) | 8 569 (99.2 %) | 8 603 (99.6 %) | 8 603 (99.6 %) | 8 603 (99.6 %) |
| 2016-05 | 8 892 (99.6 %) | 8 892 (99.6 %) | 8 892 (99.6 %) | 8 891 (99.6 %) | 8 894 (99.6 %) | 8 894 (99.6 %) |
| 2016-06 | 8 036 (93.0 %) | 8 036 (93.0 %) | 8 036 (93.0 %) | 8 039 (93.0 %) | 8 609 (99.6 %) | 8 609 (99.6 %) |
| 2016-07 | 6 930 (77.6 %) | 6 930 (77.6 %) | 6 930 (77.6 %) | 7 133 (79.9 %) | 8 897 (99.7 %) | 8 897 (99.7 %) |
| 2016-08 | 7 585 (85.0 %) | 7 585 (85.0 %) | 7 585 (85.0 %) | 7 744 (86.7 %) | 8 663 (97.0 %) | 8 663 (97.0 %) |
| 2016-09 | 5 183 (60.0 %) | 5 183 (60.0 %) | 5 183 (60.0 %) | 5 183 (60.0 %) | 8 494 (98.3 %) | 8 494 (98.3 %) |
| 2016-10 | 8 812 (98.6 %) | 8 812 (98.6 %) | 8 812 (98.6 %) | 8 812 (98.6 %) | 8 940 (100.0 %) | 8 940 (100.0 %) |
| 2016-11 | 6 967 (80.6 %) | 6 967 (80.6 %) | 6 967 (80.6 %) | 6 968 (80.6 %) | 8 644 (100.0 %) | 8 644 (100.0 %) |
| 2016-12 | 7 304 (81.8 %) | 7 304 (81.8 %) | 7 304 (81.8 %) | 7 311 (81.9 %) | 8 936 (100.1 %) | 8 936 (100.1 %) |
| 2017-01 | 3 130 (35.1 %) | 3 130 (35.1 %) | 3 130 (35.1 %) | 3 132 (35.1 %) | 8 930 (100.0 %) | 8 930 (100.0 %) |
| 2017-02 | 7 044 (87.4 %) | 7 044 (87.4 %) | 7 044 (87.4 %) | 7 047 (87.4 %) | 8 066 (100.0 %) | 8 066 (100.0 %) |
| 2017-03 | 8 390 (94.1 %) | 8 390 (94.1 %) | 8 390 (94.1 %) | 8 399 (94.2 %) | 8 917 (100.0 %) | 8 917 (100.0 %) |
| 2017-04 | 7 266 (84.1 %) | 7 266 (84.1 %) | 7 266 (84.1 %) | 7 270 (84.1 %) | 8 642 (100.0 %) | 8 642 (100.0 %) |
| 2017-05 | 2 280 (25.5 %) | 2 280 (25.5 %) | 2 280 (25.5 %) | 2 283 (25.6 %) | 8 931 (100.0 %) | 8 931 (100.0 %) |
| 2017-06 | 3 810 (44.1 %) | 3 810 (44.1 %) | 3 810 (44.1 %) | 3 811 (44.1 %) | 8 634 (99.9 %) | 8 634 (99.9 %) |
| 2017-07 | 6 502 (72.8 %) | 6 502 (72.8 %) | 6 502 (72.8 %) | 6 502 (72.8 %) | 8 918 (99.9 %) | 8 918 (99.9 %) |
| 2017-08 | 7 945 (89.0 %) | 7 945 (89.0 %) | 7 945 (89.0 %) | 7 946 (89.0 %) | 8 926 (100.0 %) | 8 926 (100.0 %) |
| 2017-09 | 8 097 (93.7 %) | 8 097 (93.7 %) | 8 097 (93.7 %) | 8 097 (93.7 %) | 8 639 (100.0 %) | 8 639 (100.0 %) |
| 2017-10 | 8 336 (93.2 %) | 8 336 (93.2 %) | 8 336 (93.2 %) | 8 336 (93.2 %) | 8 928 (99.9 %) | 8 928 (99.9 %) |
| 2017-11 | 7 510 (86.9 %) | 7 510 (86.9 %) | 7 510 (86.9 %) | 7 513 (87.0 %) | 8 645 (100.1 %) | 8 645 (100.1 %) |
| 2017-12 | 6 510 (72.9 %) | 6 510 (72.9 %) | 6 510 (72.9 %) | 6 511 (72.9 %) | 8 697 (97.4 %) | 8 697 (97.4 %) |
| 2018-01 | 5 735 (64.2 %) | 5 735 (64.2 %) | 5 735 (64.2 %) | 5 736 (64.2 %) | 8 929 (100.0 %) | 8 929 (100.0 %) |
| 2018-02 | 614 (7.6 %) | 614 (7.6 %) | 614 (7.6 %) | 614 (7.6 %) | 8 065 (100.0 %) | 8 065 (100.0 %) |
| 2018-03 | 2 082 (23.4 %) | 2 082 (23.4 %) | 2 082 (23.4 %) | 2 082 (23.4 %) | 8 906 (99.9 %) | 8 906 (99.9 %) |
| 2018-04 | 8 639 (100.0 %) | 8 639 (100.0 %) | 8 639 (100.0 %) | 8 639 (100.0 %) | 8 639 (100.0 %) | 8 639 (100.0 %) |
| 2018-05 | 8 928 (100.0 %) | 8 928 (100.0 %) | 8 928 (100.0 %) | 8 931 (100.0 %) | 8 931 (100.0 %) | 8 931 (100.0 %) |
| 2018-06 | 8 636 (100.0 %) | 8 636 (100.0 %) | 8 636 (100.0 %) | 8 642 (100.0 %) | 8 642 (100.0 %) | 8 642 (100.0 %) |
| 2018-07 | 8 925 (100.0 %) | 8 925 (100.0 %) | 8 925 (100.0 %) | 8 926 (100.0 %) | 8 926 (100.0 %) | 8 926 (100.0 %) |
| 2018-08 | 8 928 (100.0 %) | 8 928 (100.0 %) | 8 928 (100.0 %) | 8 929 (100.0 %) | 8 929 (100.0 %) | 8 929 (100.0 %) |
| 2018-09 | 8 632 (99.9 %) | 8 632 (99.9 %) | 8 632 (99.9 %) | 8 634 (99.9 %) | 8 634 (99.9 %) | 8 634 (99.9 %) |
| 2018-10 | 8 937 (100.0 %) | 8 937 (100.0 %) | 8 937 (100.0 %) | 8 943 (100.0 %) | 8 943 (100.0 %) | 8 943 (100.0 %) |
| 2018-11 | 8 640 (100.0 %) | 8 640 (100.0 %) | 8 640 (100.0 %) | 8 641 (100.0 %) | 8 641 (100.0 %) | 8 641 (100.0 %) |
| 2018-12 | 8 927 (100.0 %) | 8 927 (100.0 %) | 8 927 (100.0 %) | 8 936 (100.1 %) | 8 937 (100.1 %) | 8 937 (100.1 %) |
| 2019-01 | 8 927 (100.0 %) | 8 927 (100.0 %) | 8 927 (100.0 %) | 8 929 (100.0 %) | 8 929 (100.0 %) | 8 929 (100.0 %) |
| 2019-02 | 8 064 (100.0 %) | 8 064 (100.0 %) | 8 064 (100.0 %) | 8 066 (100.0 %) | 8 066 (100.0 %) | 8 066 (100.0 %) |
| 2019-03 | 8 916 (100.0 %) | 8 916 (100.0 %) | 8 916 (100.0 %) | 8 922 (100.1 %) | 8 922 (100.1 %) | 8 922 (100.1 %) |
| 2019-04 | 8 637 (100.0 %) | 8 637 (100.0 %) | 8 637 (100.0 %) | 8 637 (100.0 %) | 8 637 (100.0 %) | 8 637 (100.0 %) |
| 2019-05 | 8 590 (96.2 %) | 8 590 (96.2 %) | 8 590 (96.2 %) | 8 590 (96.2 %) | 8 931 (100.0 %) | 8 931 (100.0 %) |
| 2019-06 | 8 628 (99.9 %) | 8 628 (99.9 %) | 8 628 (99.9 %) | 8 628 (99.9 %) | 8 648 (100.1 %) | 8 648 (100.1 %) |
| 2019-07 | 8 926 (100.0 %) | 8 926 (100.0 %) | 8 926 (100.0 %) | 8 926 (100.0 %) | 8 929 (100.0 %) | 8 929 (100.0 %) |
| 2019-08 | 8 927 (100.0 %) | 8 927 (100.0 %) | 8 927 (100.0 %) | 8 927 (100.0 %) | 8 928 (100.0 %) | 8 928 (100.0 %) |
| 2019-09 | 8 639 (100.0 %) | 8 639 (100.0 %) | 8 639 (100.0 %) | 8 639 (100.0 %) | 8 640 (100.0 %) | 8 640 (100.0 %) |
| 2019-10 | 8 928 (99.9 %) | 8 928 (99.9 %) | 8 928 (99.9 %) | 8 928 (99.9 %) | 8 940 (100.0 %) | 8 940 (100.0 %) |
| 2019-11 | 8 640 (100.0 %) | 8 640 (100.0 %) | 8 640 (100.0 %) | 8 640 (100.0 %) | 8 640 (100.0 %) | 8 640 (100.0 %) |
| 2019-12 | 8 928 (100.0 %) | 8 928 (100.0 %) | 8 928 (100.0 %) | 8 928 (100.0 %) | 8 927 (100.0 %) | 8 927 (100.0 %) |
| 2020-01 | 8 927 (100.0 %) | 8 927 (100.0 %) | 8 927 (100.0 %) | 8 927 (100.0 %) | 8 928 (100.0 %) | 8 928 (100.0 %) |
| 2020-02 | 8 129 (97.3 %) | 8 129 (97.3 %) | 8 129 (97.3 %) | 8 129 (97.3 %) | 8 347 (99.9 %) | 8 347 (99.9 %) |
| 2020-03 | 8 585 (96.3 %) | 8 585 (96.3 %) | 8 585 (96.3 %) | 8 585 (96.3 %) | 8 892 (99.7 %) | 8 892 (99.7 %) |
| 2020-04 | 8 640 (100.0 %) | 8 640 (100.0 %) | 8 640 (100.0 %) | 8 640 (100.0 %) | 8 640 (100.0 %) | 8 640 (100.0 %) |
| 2020-05 | 8 715 (97.6 %) | 8 715 (97.6 %) | 8 715 (97.6 %) | 8 715 (97.6 %) | 8 860 (99.2 %) | 8 860 (99.2 %) |
| 2020-06 | 8 473 (98.1 %) | 8 473 (98.1 %) | 8 473 (98.1 %) | 8 473 (98.1 %) | 8 563 (99.1 %) | 8 563 (99.1 %) |
| 2020-07 | 8 889 (99.6 %) | 8 889 (99.6 %) | 8 889 (99.6 %) | 8 889 (99.6 %) | 8 836 (99.0 %) | 8 834 (98.9 %) |
| 2020-08 | 8 912 (99.8 %) | 8 912 (99.8 %) | 8 912 (99.8 %) | 8 912 (99.8 %) | 1 599 (99.2 %) | 8 899 (99.7 %) |
| 2020-09 | 7 930 (91.8 %) | 7 930 (91.8 %) | 7 930 (91.8 %) | 7 930 (91.8 %) | — | 481 (99.8 %) |
| 2020-10 | 8 593 (96.1 %) | 8 593 (96.1 %) | 8 593 (96.1 %) | 8 593 (96.1 %) | — | — |
| 2020-11 | 8 297 (96.0 %) | 8 297 (96.0 %) | 8 297 (96.0 %) | 8 297 (96.0 %) | — | — |
| 2020-12 | 8 905 (99.7 %) | 8 905 (99.7 %) | 8 905 (99.7 %) | 8 905 (99.7 %) | — | — |
| 2021-01 | 8 370 (93.8 %) | 8 370 (93.8 %) | 8 370 (93.8 %) | 8 370 (93.8 %) | — | — |
| 2021-02 | 8 049 (99.8 %) | 8 049 (99.8 %) | 8 049 (99.8 %) | 8 049 (99.8 %) | — | — |
| 2021-03 | 8 910 (99.9 %) | 8 910 (99.9 %) | 8 910 (99.9 %) | 8 910 (99.9 %) | — | — |
| 2021-04 | 8 636 (100.0 %) | 8 636 (100.0 %) | 8 636 (100.0 %) | 8 636 (100.0 %) | — | — |
| 2021-05 | 8 895 (99.6 %) | 8 895 (99.6 %) | 8 895 (99.6 %) | 8 895 (99.6 %) | — | — |
| 2021-06 | 8 492 (98.3 %) | 8 492 (98.3 %) | 8 492 (98.3 %) | 8 492 (98.3 %) | — | — |
| 2021-07 | 8 921 (99.9 %) | 8 921 (99.9 %) | 8 921 (99.9 %) | 8 921 (99.9 %) | — | — |
| 2021-08 | 8 879 (99.5 %) | 8 879 (99.5 %) | 8 879 (99.5 %) | 8 879 (99.5 %) | — | — |
| 2021-09 | 8 545 (98.9 %) | 8 545 (98.9 %) | 8 545 (98.9 %) | 8 545 (98.9 %) | — | — |
| 2021-10 | 8 725 (97.6 %) | 8 725 (97.6 %) | 8 725 (97.6 %) | 8 725 (97.6 %) | — | — |
| 2021-11 | 8 619 (99.8 %) | 8 619 (99.8 %) | 8 619 (99.8 %) | 8 619 (99.8 %) | — | — |
| 2021-12 | 8 418 (94.3 %) | 8 418 (94.3 %) | 8 418 (94.3 %) | 8 418 (94.3 %) | — | — |
| 2022-01 | 8 497 (95.2 %) | 8 497 (95.2 %) | 8 497 (95.2 %) | 8 497 (95.2 %) | — | — |
| 2022-02 | 8 058 (99.9 %) | 8 058 (99.9 %) | 8 058 (99.9 %) | 8 058 (99.9 %) | — | — |
| 2022-03 | 8 669 (97.2 %) | 8 669 (97.2 %) | 8 669 (97.2 %) | 8 669 (97.2 %) | — | — |
| 2022-04 | 8 633 (99.9 %) | 8 633 (99.9 %) | 8 633 (99.9 %) | 8 633 (99.9 %) | — | — |
| 2022-05 | 8 902 (99.7 %) | 8 902 (99.7 %) | 8 902 (99.7 %) | 8 902 (99.7 %) | — | — |
| 2022-06 | 8 577 (99.3 %) | 8 577 (99.3 %) | 8 577 (99.3 %) | 8 577 (99.3 %) | — | — |
| 2022-07 | 8 893 (99.6 %) | 8 893 (99.6 %) | 8 893 (99.6 %) | 8 893 (99.6 %) | — | — |
| 2022-08 | 8 840 (99.0 %) | 8 840 (99.0 %) | 8 840 (99.0 %) | 8 909 (99.8 %) | — | — |
| 2022-09 | 8 614 (99.7 %) | 8 614 (99.7 %) | 8 614 (99.7 %) | 8 623 (99.8 %) | — | — |
| 2022-10 | 8 904 (99.6 %) | 8 904 (99.6 %) | 8 904 (99.6 %) | 8 937 (100.0 %) | — | — |
| 2022-11 | 8 634 (99.9 %) | 8 634 (99.9 %) | 8 634 (99.9 %) | 8 634 (99.9 %) | — | — |
| 2022-12 | 8 919 (99.9 %) | 8 919 (99.9 %) | 8 919 (99.9 %) | 8 918 (99.9 %) | — | — |
| 2023-01 | 8 920 (99.9 %) | 8 920 (99.9 %) | 8 920 (99.9 %) | 8 920 (99.9 %) | — | — |
| 2023-02 | 8 051 (99.8 %) | 8 051 (99.8 %) | 8 051 (99.8 %) | 7 995 (99.1 %) | — | — |
| 2023-03 | 8 875 (99.5 %) | 8 875 (99.5 %) | 8 875 (99.5 %) | 8 909 (99.9 %) | — | — |
| 2023-04 | 8 603 (99.6 %) | 8 603 (99.6 %) | 8 603 (99.6 %) | 8 624 (99.8 %) | — | — |
| 2023-05 | 8 709 (97.5 %) | 8 709 (97.5 %) | 8 709 (97.5 %) | 7 203 (80.7 %) | — | — |
| 2023-06 | 8 602 (99.6 %) | 8 602 (99.6 %) | 8 602 (99.6 %) | 5 833 (67.5 %) | — | — |
| 2023-07 | 8 891 (99.6 %) | 8 891 (99.6 %) | 8 891 (99.6 %) | 2 223 (24.9 %) | — | — |
| 2023-08 | 8 879 (99.5 %) | 8 879 (99.5 %) | 8 879 (99.5 %) | 3 909 (100.0 %) | — | — |
| 2023-09 | 8 626 (99.8 %) | 8 626 (99.8 %) | 8 626 (99.8 %) | — | — | — |
| 2023-10 | 8 904 (99.6 %) | 8 904 (99.6 %) | 8 904 (99.6 %) | — | — | — |
| 2023-11 | 8 451 (97.8 %) | 8 451 (97.8 %) | 8 451 (97.8 %) | — | — | — |
| 2023-12 | 8 923 (99.9 %) | 8 923 (99.9 %) | 8 923 (99.9 %) | — | — | — |
| 2024-01 | 8 726 (97.7 %) | 8 726 (97.7 %) | 8 726 (97.7 %) | — | — | — |
| 2024-02 | 8 329 (99.7 %) | 8 329 (99.7 %) | 8 329 (99.7 %) | — | — | — |
| 2024-03 | 8 887 (99.7 %) | 8 887 (99.7 %) | 8 887 (99.7 %) | — | — | — |
| 2024-04 | 8 618 (99.7 %) | 8 618 (99.7 %) | 8 618 (99.7 %) | — | — | — |
| 2024-05 | 8 888 (99.6 %) | 8 888 (99.6 %) | 8 888 (99.6 %) | — | — | — |
| 2024-06 | 8 635 (99.9 %) | 8 635 (99.9 %) | 8 635 (99.9 %) | — | — | — |
| 2024-07 | 8 919 (99.9 %) | 8 919 (99.9 %) | 8 919 (99.9 %) | — | — | — |
| 2024-08 | 8 922 (99.9 %) | 8 922 (99.9 %) | 8 922 (99.9 %) | — | — | — |
| 2024-09 | 8 534 (98.8 %) | 8 534 (98.8 %) | 8 534 (98.8 %) | — | — | — |
| 2024-10 | 8 934 (99.9 %) | 8 934 (99.9 %) | 8 934 (99.9 %) | — | — | — |
| 2024-11 | 8 620 (99.8 %) | 8 620 (99.8 %) | 8 620 (99.8 %) | — | — | — |
| 2024-12 | 8 923 (99.9 %) | 8 923 (99.9 %) | 8 923 (99.9 %) | — | — | — |
| 2025-01 | 8 832 (98.9 %) | 8 832 (98.9 %) | 8 832 (98.9 %) | — | — | — |
| 2025-02 | 8 058 (99.9 %) | 8 058 (99.9 %) | 8 058 (99.9 %) | — | — | — |
| 2025-03 | 8 910 (99.9 %) | 8 910 (99.9 %) | 8 910 (99.9 %) | — | — | — |
| 2025-04 | 8 639 (100.0 %) | 8 639 (100.0 %) | 8 639 (100.0 %) | — | — | — |
| 2025-05 | 8 926 (100.0 %) | 8 926 (100.0 %) | 8 926 (100.0 %) | — | — | — |
| 2025-06 | 8 617 (99.7 %) | 8 617 (99.7 %) | 8 617 (99.7 %) | — | — | — |
| 2025-07 | 8 895 (99.6 %) | 8 895 (99.6 %) | 8 895 (99.6 %) | — | — | — |
| 2025-08 | 8 578 (96.1 %) | 8 578 (96.1 %) | 8 578 (96.1 %) | — | — | — |
| 2025-09 | 8 611 (99.7 %) | 8 611 (99.7 %) | 8 611 (99.7 %) | — | — | — |
| 2025-10 | 8 882 (99.4 %) | 8 882 (99.4 %) | 8 882 (99.4 %) | — | — | — |
| 2025-11 | 7 560 (87.5 %) | 7 560 (87.5 %) | 7 560 (87.5 %) | — | — | — |
| 2025-12 | 8 438 (94.5 %) | 8 438 (94.5 %) | 8 438 (94.5 %) | — | — | — |
| 2026-01 | 8 925 (100.0 %) | 8 925 (100.0 %) | 8 925 (100.0 %) | — | — | — |
| 2026-02 | 8 044 (99.8 %) | 8 044 (99.8 %) | 8 044 (99.8 %) | — | — | — |
| 2026-03 | 8 917 (100.0 %) | 8 917 (100.0 %) | 8 594 (96.4 %) | — | — | — |
| 2026-04 | 8 641 (100.0 %) | 8 641 (100.0 %) | 5 546 (64.2 %) | — | — | — |
| 2026-05 | 8 927 (100.0 %) | 8 927 (100.0 %) | 7 489 (83.9 %) | — | — | — |
| 2026-06 | 8 642 (100.0 %) | 8 642 (100.0 %) | 8 631 (99.9 %) | — | — | — |
| 2026-07 | 8 946 (100.2 %) | 8 946 (100.2 %) | 8 891 (99.6 %) | — | — | — |
| 2026-08 | 8 932 (100.0 %) | 8 932 (100.0 %) | 8 924 (100.0 %) | — | — | — |
| 2026-09 | 8 645 (100.1 %) | 8 645 (100.1 %) | 8 640 (100.0 %) | — | — | — |
| 2026-10 | 8 269 (100.0 %) | 8 549 (100.0 %) | 8 167 (99.5 %) | — | — | — |

### Kontroly pokrytí

**Vnitřní měsíce s nulou řádků:** 2011-09:RECON, 2011-09:PROD, 2011-09:GW, 2011-09:OLD, 2011-09:WEEWX, 2011-09:WH1080, 2011-10:RECON, 2011-10:PROD, 2011-10:GW, 2011-10:OLD, 2011-10:WEEWX, 2011-10:WH1080, 2011-11:RECON, 2011-11:PROD, 2011-11:GW, 2011-11:OLD, 2011-11:WEEWX, 2011-11:WH1080, 2011-12:RECON, 2011-12:PROD, 2011-12:GW, 2011-12:OLD, 2011-12:WEEWX, 2011-12:WH1080, 2012-01:RECON, 2012-01:PROD, 2012-01:GW, 2012-01:OLD, 2012-01:WEEWX, 2012-01:WH1080, 2012-02:RECON, 2012-02:PROD, 2012-02:GW, 2012-02:OLD, 2012-02:WEEWX, 2012-02:WH1080.

**Měsíce s vyšším počtem řádků než odhadnutými 5min sloty (prvních 45):** 2015-06 WEEWX 8643/8640; 2015-06 WH1080 8643/8640; 2016-11 WEEWX 8644/8640; 2016-11 WH1080 8644/8640; 2016-12 WEEWX 8936/8928; 2016-12 WH1080 8936/8928; 2017-05 WEEWX 8931/8928; 2017-05 WH1080 8931/8928; 2017-11 WEEWX 8645/8640; 2017-11 WH1080 8645/8640; 2018-05 OLD 8931/8928; 2018-05 WEEWX 8931/8928; 2018-05 WH1080 8931/8928; 2018-10 OLD 8943/8940; 2018-10 WEEWX 8943/8940; 2018-10 WH1080 8943/8940; 2018-12 OLD 8936/8928; 2018-12 WEEWX 8937/8928; 2018-12 WH1080 8937/8928; 2019-03 OLD 8922/8916; 2019-03 WEEWX 8922/8916; 2019-03 WH1080 8922/8916; 2019-05 WEEWX 8931/8928; 2019-05 WH1080 8931/8928; 2019-06 WEEWX 8648/8640; 2019-06 WH1080 8648/8640; 2026-07 RECON 8946/8928; 2026-07 PROD 8946/8928; 2026-08 RECON 8932/8928; 2026-08 PROD 8932/8928; 2026-09 RECON 8645/8640; 2026-09 PROD 8645/8640.

## Auditní výchozí informace z přímých SELECT

| Zdroj | Počet řádků archive | MIN UTC epoch | MAX UTC epoch | Unikátnost uvnitř zdroje |
|---|---:|---:|---:|---|
| `loucka_reconstruction` | 1 679 802 | 1238345100 | 1793286600 | `dateTime` je primární klíč |
| `pocasi-loucka.eu` | 1 680 081 | 1238345100 | 1793370600 | `dateTime` je primární klíč |
| `pocasi-loucka.eu_GW1000` | 1 674 765 | 1238345100 | 1793268600 | `dateTime` je primární klíč |
| `pocasi-loucka.eu_old` | 1 336 195 | 1238345160 | 1692013500 | `dateTime` je primární klíč |
| `old_weewx` | 1 104 422 | 1238345160 | 1596716400 | `dateTime` je primární klíč |
| `weewx_WH1080` | 1 112 201 | 1238345160 | 1599055800 | `dateTime` je primární klíč |

## Zjištění k přítomným WH1080 kandidátům

Přípravná tabulka `loucka_reconstruction.wh1080_missing_5min_candidates_20261030` má přesně **49 796** řádků: 758 `needs_validation` (2019–2020), 1 301 `frozen_sensor_review` (2009/2011) a 47 737 `pressure_only_review` (2016–2018). Všechny mají `time_offset_sec = 0`; přímým `LEFT/INNER JOIN` bylo zjištěno **0** přesných shod `candidate.target_time=archive.dateTime` s pracovním archivem. Neprokazuje to nezávislost ani kvalitu senzoru. **Import zakázán**.

## Časová konvence a pravidla předběžné identifikace

1. Záznam WeeWX s koncem `dateTime=t` a `interval=i` minut reprezentuje `(t-60*i,t]`; přiřazení do dne/měsíce podle konce. Nedělit dlouhé intervaly ani nevytvářet syntetické nuly.
2. Klíč fyzického měření není jen `dateTime`, ale `(source, interval_start_utc, interval_end_utc, variable, source_observation_id)`. `dateTime` je klíčem archivního **řádku**, ne nezávislosti měření mezi zdroji.
3. Časové zarovnání 5min mřížky je **odvozená kandidátní transformace**, nikoli důkaz shody. Párovat nejprve přesnou epochu a délku `interval`; poté tolerantně posuzovat blízké konce (+/- 60 až 150 sekund) a překryv intervalů, bez automatického přepsání času.
4. Přechody CET/CEST: vždy nejprve převést lokální datum na dvě explicitní UTC epochy při podzimním opakování hodiny; jarní neexistující lokální minuty nikdy nevytvářet.
5. Zdroje s `usUnits=17` nemají automaticky shodnou numerickou sémantiku s `usUnits=16`; přesné kopie dat vyžadují validovaný převod jednotek, nezávislost a kontrolu hodnot, nikoli jen shodu epoch.

## Celkové sjednocení časových značek (skutečně změřené souhrny)

Z **18 samostatných ročních, indexovanými hranicemi omezených SELECTů** (šest `archive` v každém roce; časové přesahy 150 sekund kolem hranic) je výsledkem následující tabulka. Výpočet odděluje identitu původní epochy od hypotetického 5min *kanonického slotu*. Použitá funkce zarovnání: `FLOOR((dateTime+150)/300)*300` (zaokrouhlení na nejbližších 300 sekund, při vazbě uprostřed směrem nahoru). **Nejde o fyzikální rekonstrukci data ani o důkaz pravosti**.

| Rok | Všechny řádky ze 6 zdrojů | Různé původní UTC značky | Různé zarovnané sloty | Časově redundantní řádky |
|---|---:|---:|---:|---:|
| 2009 | 468 993 | 81 905 | 78 194 | 390 799 |
| 2010 | 624 617 | 106 079 | 104 090 | 520 527 |
| 2011 | 386 114 | 67 870 | 67 318 | 318 796 |
| 2012 | 452 088 | 83 759 | 75 335 | 376 753 |
| 2013 | 572 969 | 97 510 | 95 495 | 477 474 |
| 2014 | 577 920 | 107 478 | 96 801 | 481 119 |
| 2015 | 613 825 | 150 028 | 103 383 | 510 442 |
| 2016 | 561 775 | 163 460 | 103 995 | 457 780 |
| 2017 | 517 053 | 115 913 | 104 845 | 412 208 |
| 2018 | 560 766 | 106 198 | 105 091 | 455 675 |
| 2019 | 629 284 | 105 568 | 105 114 | 524 170 |
| 2020 | 545 089 | 104 495 | 103 814 | 441 275 |
| 2021 | 413 836 | 103 459 | 103 459 | 310 377 |
| 2022 | 416 670 | 104 263 | 104 263 | 312 407 |
| 2023 | 366 918 | 104 714 | 104 714 | 262 204 |
| 2024 | 314 805 | 104 935 | 104 935 | 209 870 |
| 2025 | 308 838 | 102 946 | 102 946 | 205 892 |
| 2026 | 255 909 | 87 401 | 87 138 | 168 771 |
| **Celkem** | **8 587 469** | **1 897 981** | **1 750 930** | **6 836 539** |

- Po zarovnání se 8 587 469 archivních řádků promítá do **1 750 930 různých pětiminutových časových slotů**. Číslo **6 836 539** jsou *opakované výskyty slotů*, **nikoli potvrzené kopie meteorologických hodnot**. Zároveň různé hodnoty v témže slotu nesmějí být bez důkazu sloučeny.
- Samotná pracovní rekonstrukce má **1 679 802 řádků**, ale po zarovnání jen **1 679 539 různých slotů**: v roce 2026 se 263 řádků časově slévá do jiných slotů. Rozdíl **71 391** slotů tvoří nové časové příležitosti z ostatních pěti databází; jiné jednotky, chyba nebo zamrzlá čidla mohou i tak znemožnit rekonstrukci hodnot.
- Před výše uvedeným sjednocením bylo mezi zdroji mimo pracovní archiv identifikováno **142 494 řádků**, z nichž je **71 391** rozdílných slotů. Zbývající výskyty tvoří **70 832 opakování přesně stejné zdrojové epochy** a **271 kolizí odlišných epoch po zaokrouhlení**. Z 71 391 slotů se **70 460** vyskytuje ve více zdrojových řádcích.
- Nejméně u dvojice WH1080 ↔ old_weewx se přesné časové značky 2009–2018 shodují **936 620 / 936 620**. Pětice hodnot `outTemp,outHumidity,windSpeed,windDir,barometer` je v **780 132** z těchto řádků přesně shodná při NULL-safe porovnání. Silný indikátor společného původu, nikoli automatický důkaz, který archiv byl původní nebo že zbývající řádky jsou nezávislá pozorování.
- Live produkční `archive` mezi SELECTy roste. Součet početních inventářů a sjednocovací běh mohou vykázat jednotkové rozdíly u října 2026; tento audit není transakčně konzistentní historický snapshot.

### Metoda SQL pro opakování sjednocení

Každý rok zvlášť. Pro každý zdroj připojit `SELECT dateTime AS ts, FLOOR((dateTime+150)/300)*300 AS canonical FROM \`db\`.\`archive\` WHERE dateTime > :local_year_start_utc_minus_150 AND dateTime <= :next_local_year_start_utc_plus_150`; dílčí výsledky spojit přes `UNION ALL`; ve vnějších dotazech filtrovat `canonical > :local_year_start_utc AND canonical <= :next_local_year_start_utc` a agregovat `COUNT(*)`, `COUNT(DISTINCT ts)`, `COUNT(DISTINCT canonical)`. Parametry jsou číselné epochy UTC; jejich místní hranice vypočítat mimo DB podle pravidel Europe/Prague, přičemž samotné sloty zůstávají UTC. V DB nyní `CONVERT_TZ` pro pojmenovanou zónu nefunguje. Hlavní dotaz nikdy nespouštět jako nenaindexovanou agregaci 17 let naráz.

## Meziarchivní párování a chronologie časových anomálií

| Zdroj proti `loucka_reconstruction` | Přesná shoda epochy | Shoda až po přepočtu na 5min slot | Bez shody i po zarovnání |
|---|---:|---:|---:|
| `pocasi-loucka.eu` | 1 679 802 | 0 | 280 |
| `pocasi-loucka.eu_GW1000` | 1 674 534 | 0 | 231 |
| `pocasi-loucka.eu_old` | 1 189 955 | 145 736 | 504 |
| `old_weewx` | 887 193 | 146 498 | 70 731 |
| `weewx_WH1080` | 894 942 | 146 513 | **70 746** |

Párování zahrnuje i různé délky `interval`, protože jde nejdříve o *časový screening*. Fyzikální identitu intervalů teprve potvrzuje druhá fáze podle startu, konce, zdrojového payloadu, časového offsetu a jednotek. U negridového timestampu může zaokrouhlení překrýt dva různé intervaly; z toho nikdy neplyne automatický import.

**Chronologie:**

1. **Březen 2009:** pracovní/produkční záznamy začínají na UTC epochě `1238345100`, archiv WH1080 a old_weewx na `1238345160` (o minutu později); nelze z toho vyvozovat fixní +60s posun celé historie.
2. **15. 8. 2011 – 1. 3. 2012:** zásadní chybějící období; šest úplně prázdných občanských měsíců 2011-09 až 2012-02. Podrobnosti níže. Staré zdroje pokračují téměř o dva týdny déle než produkční/rekonstrukční archiv.
3. **Duben 2013:** v pracovním archivu je doložena velká časová mezera v období 7.–12. 4. 2013 (viz tabulka mezer). Jednotková či srážkoměrná změna kolem 14.–19. 4. 2013 je kontext jiného auditu a nesmí se ztotožňovat s prokázanou chybou hodin; samotné `usUnits` neurčuje skutečný fyzikální převod.
4. **2014–2019:** `interval=6` je v rekonstrukci **2 090×**, převážně 2015–2017 (736, 1 128, 137); tyto značky přesto leží na 5min mřížce. Ve WH1080 je 6min interval **2 338×** a značky jsou často o sekundy/minuty posunuté. Je nutné individuálně ověřit fyzickou šířku intervalu, ne předpokládat, že šest minut znamená obyčejnou 5min vzorkovací periodu.
5. **2015–2018:** dramaticky roste počet historických syrových značek mimo 5min mřížku; například v roce 2016 má WH1080 módy `dateTime % 300` rovné 0 (34 970 řádků), 181 (13 065), 1 (11 065), 241 (9 585). Jde o více různých reziduí, tedy **ne o jediný konstantní hodinový/minutový posun**. Toto a velký počet shod po snapu jsou indicie přepočtu či importního zaokrouhlování, ale zdrojový algoritmus zatím nebyl dohledán.
6. **2016–2018:** největší oblast chybějícího časového pokrytí i problémů s vlhkostí. WH1080 má bez zarovnané shody 16 293 (2016), 28 027 (2017) a 17 469 (2018) řádků. Není oprávněné označit je plošně za kompletní meteorologické měření.
7. **Srpen–září 2020:** `old_weewx` končí na `1596716400` (2020-08-06), WH1080 na `1599055800` (2020-09-02). Tyto konce přesně vymezují rozsah původních zdrojů. Přechod zařízení je historický kontext, ale název databáze `_GW1000` **neznamená**, že veškeré její řádky od roku 2009 vznikly na GW1000; tento archiv obsahuje i starou historii.
8. **Srpen 2022:** v pracovním archivu se poprvé objevují `radiation`, `UV`, `pm25_1`, blesky a další senzory; NULL před tímto datem není výpadkem těchto veličin.
9. **Březen–říjen 2026:** produkce má 390 timestampů mimo 5min mřížku, především s rezidui 240 s (277 řádků), 60 s (43), 180 s (39), 120 s (31). Pouze **43** z 390 má i kanonickou 5min epochu jako další řádek stejné produkční tabulky, z toho jen **4** mají shodnou teplotu i vlhkost. Nejde tedy o 390 prokázaných kopií, ale o kandidáty k individuálnímu ověření zpoždění, přesunů intervalů a kolizí.

### Změna přiřazení dne/měsíce při zarovnání

Proti čistě uloženému `dateTime` mění hypotetické zaokrouhlení na pět minut občanský den u **270** řádků `pocasi-loucka.eu_old`, **299** `old_weewx` a **299** WH1080; pro každou z těchto tří DB mění občanský měsíc u **8** řádků. V pracovní rekonstrukci, produkci a GW1000 bylo takových překlasifikací **0**. Např. původní epoch `1451602860` v WH1080 spadá do ledna 2016, zatímco 5min zarovnání do prosince 2015. Pro audit kalendářních úhrnů je to přímý důvod zachovávat vedle původní epochy také transformovanou epochu, delta-sekundy a identifikátor pravidla. Změna bucketu je **dokázaná**, původní chyba hodin/migrace však **není dokázaná**. Původní měsíční tabulka v tomto dokumentu pracuje se zdrojovým `dateTime` bez snapu.

## Mezery a detekce archivních výpadků

Následující největší mezery pracovní rekonstrukce byly zjištěny čtecím `LEAD(dateTime) OVER (ORDER BY dateTime)` na indexovanými hranicemi omezených úsecích, s oddělenou kontrolou přes hranici roků. Jde o rozdíly koncových časových značek; vlastní počet chybějících 5min slotů se odvozuje teprve ze skutečné délky sousedních intervalů.

| Období | Poslední konec před mezerou (UTC) | První konec po mezeře (UTC) | Rozdíl dní |
|---|---|---|---:|
| Mezi srpnem 2011 a březnem 2012 | 2011-08-15 20:05:00Z | 2012-03-01 09:25:00Z | 198.56 |
| 2018 | 2018-02-21 13:45:00Z | 2018-03-24 16:00:00Z | 31.09 |
| 2016 | 2016-01-18 22:35:00Z | 2016-02-06 13:10:00Z | 18.61 |
| 2017 | 2017-05-12 04:50:00Z | 2017-05-28 21:45:00Z | 16.70 |
| 2014 | 2014-06-20 22:50:00Z | 2014-07-03 17:00:00Z | 12.76 |
| 2013 | 2013-04-06 22:20:00Z | 2013-04-12 17:45:00Z | 5.81 |
| 2009 | 2009-07-21 15:15:00Z | 2009-07-24 12:00:00Z | 2.86 |

- Ve zdrojích WH1080 a old_weewx pokračují záznamy až do **2011-08-28 21:15 UTC** a obnovují se **2012-03-01 09:23 UTC**. Jejich vlastní mezera činí cca **185,51 dne**, oproti cca **198,56 dne** v rekonstrukci. Rozdílný konec starých zdrojů potvrzuje, že část mezery v cílovém archivu neznamená fyzickou absenci měření.
- U ostatních dlouhých mezer nejde bez dalšího zkoumání o prokázanou poruchu stanice: je nutné rozlišit výpadek přenosu, neimportovanou historii, chybné UTC při migraci a chybějící aktivní senzor.

## Archivní časové intervaly a CET/CEST

- `dateTime` je číselná UTC epocha; `interval` udává nominální **minuty reprezentovaného úseku**, nikoli záruku délky mezery od předchozího řádku. V pracovní rekonstrukci je 1 677 705 záznamů s `interval=5`, 2 090 se `interval=6`, tři `interval=30`, po jednom `interval=10,40,55,75`. Všechny pracovní záznamy mají `usUnits=16`; WH1080 je `usUnits=17`.
- Časové hranice WeeWX jsou `(t-interval*60,t]`; pro lokální občanský den se kalendářní interval nejprve vytvoří v Europe/Prague, teprve poté převede na UTC. Půlnoc je vždy koncem **předchozího** občanského dne.
- Správný jarní přechod má **276** pětiminutových časových slotů, podzimní **300**. V RECON je 2020-03-29 přesně 276 a 2020-10-25 přesně 300 řádků; v roce 2026 je 2026-03-29 rovněž 276 a 2026-10-25 300. Dny s menším počtem (např. 2013-10-27 212/300) jsou skutečné nedostatky archivních řádků, ne automaticky „hodina DST“.
- Dvě podzimní lokální hodiny 02:00–02:59 jsou odlišné UTC epochy a **nesmějí se deduplikovat podle lokálního řetězce**. V MariaDB test `FROM_UNIXTIME` zobrazil obě lokální 02:30; `CONVERT_TZ` s `Europe/Prague` však při běhu vrací NULL, proto musí aplikace pracovat s číselnou epochou a explicitní časovou zónou (nikoli s převodem na SQL serveru bez ověření tz tabulek).
- V přechodech se nenašel důkaz **plošné systémové chyby jedné hodiny**. Lokální podezření vyžadují primární logger timestamp a nezávislý fyzikální fingerprint, nikoli jen počet shod při posunu +3600 s (pravidelná mřížka dává spoustu falešných shod).

## Historická aktivita senzorů: omezení denominatoru

V `loucka_reconstruction.archive` byly po jednotlivých rocích spočítány nenulové (tj. `NOT NULL`, nikoli nenulová numerická hodnota) hodnoty vybraných veličin. Důkazní příklady:

| Rok | Řádků celkem | outTemp přítomna | outHumidity přítomna | radiation přítomna | pm25_1 přítomna |
|---|---:|---:|---:|---:|---:|
| 2016 | 87 913 | 87 725 | 74 486 | 0 | 0 |
| 2017 | 76 820 | 76 553 | 51 884 | 0 | 0 |
| 2018 | 87 623 | 87 577 | 51 731 | 0 | 0 |
| 2021 | 103 459 | 102 512 | 102 441 | 0 | 0 |
| 2022 | 104 140 | 101 305 | 60 829 | 36 090 | 36 159 |
| 2023 | 104 434 | 104 279 | 104 292 | 104 251 | 101 509 |
| 2026 (část) | 86 888 | 86 887 | 86 886 | 86 368 | 86 868 |

**První zaznamenaná nenulová přítomnost (UTC, nikoli prokázané datum montáže):**

| Senzor / pole | První neprázdná UTC epocha |
|---|---|
| soilTemp1 a soilTemp2 | 2019-04-26 14:45:00Z |
| radiation / UV / PM2.5 / lightning / soilMoist1 | 2022-08-27 09:40:00Z |
| extraTemp1 | 2022-09-02 08:45:00Z |
| wh26_rssi | 2026-03-08 12:25:00Z |
| vpd | 2026-03-08 12:15:00Z |
| sunshineDur | 2026-03-12 18:00:00Z |

Před první zdokumentovanou aktivitou senzoru se v reportech používá stav **NOT_OBSERVED_BEFORE_FIRST_SEEN** (instalace bez konfigurace nesmí být vyloučena). Teprve instalační deník/config interval povýší na **NOT_INSTALLED**. Po prokázaném spuštění lze rozlišit **SENSOR_DATA_MISSING** (`NULL` v existujícím archivu), **ARCHIVE_RECORD_MISSING** (neexistuje řádek), **TRANSPORT_GAP**, **SENSOR_OFFLINE** (pokud potvrzeno diagnostikou). U `soilTemp*` a `extraTemp*` dodatečně nutná časově verzovaná mapa fyzických čidel; přeznačení se nesmí vyhodnotit jako ztráta senzoru.

## Kandidáti WH1080 — forenzní kontrola, bez importu

Kandidátová tabulka obsahuje 49 796 řádků: 1 301 `frozen_sensor_review` (100 v roce 2009, 1 201 v roce 2011), 47 737 `pressure_only_review` (5 729 v roce 2016, 24 542 v roce 2017, 17 466 v roce 2018) a 758 `needs_validation` (1 v roce 2018, 266 v roce 2019, 491 v roce 2020). Všech **49 796** má skutečný zdrojový řádek v `weewx_WH1080.archive` a postrádá záznam na kanonickém cílovém slotu v pracovní rekonstrukci. `time_offset_sec` je pro všechny 0 a původní `source_time` leží na 5min UTC mřížce. Tato množina je podmnožinou **70 746** WH1080 nezarovnatelných časů; **20 950** dalších časů není v přípravné kandidátní tabulce. **Nedoplňovat automaticky**, zejména 2016–2018 bez běžných senzorů.

## Návrh normalizované evidence kvality a původu pro budoucí frontend

Model eviduje *řádky zdrojů*, *fyzické intervaly*, *jednotlivé veličiny*, *jejich revize* a *kvalitu* odděleně. Jde o návrh schématu, **ne provedenou DDL/migraci**:

| Entita | Podstatná pole | Účel |
|---|---|---|
| `source_registry` | `source_id`, schéma/tabulka, generace zařízení, archivní role, timezone konfigurace, časová platnost | Zdroj a lineage (GW1000 DB může obsahovat staré importy) |
| `raw_archive_ref` | `source_id`, původní `dateTime`, `interval`, `usUnits`, digest raw payloadu, původní kolony, import/export run | Neměnný auditní odkaz, neklonovat řádky bez zdroje |
| `canonical_interval` | `canonical_id`, `start_utc`, `end_utc`, `source_end_utc`, `alignment_delta_sec`, `rule_version`, `time_confidence` | Výslovné oddělení zdrojové a normalizované epochy |
| `field_lineage` | `canonical_id`, veličina, `raw_archive_ref`, raw value/unit, normalized value/unit, metoda převodu, fingerprint, `independence_group` | Nevydávat převzatou hodnotu za nové měření |
| `sensor_lifecycle` | fyzický senzor, veličina, platnost od/do, konfigurace/driver, evidence aktivace/deaktivace, mapování labelů | Jmenovatel úplnosti pouze během prokázané dostupnosti |
| `quality_assessment` | `field_lineage`, flags, evidence IDs, `diagnosis_confidence`, `replacement_confidence`, revize, reviewer, rule version | Oddělit podezření od jistoty náhradní hodnoty |

Doporučené stavové příznaky: `RAW_OBSERVED`, `TIME_ALIGNED_CANDIDATE`, `SOURCE_COPY_SUSPECTED`, `VALUE_CONFLICT`, `INTERVAL_NON_5MIN`, `DST_AMBIGUITY`, `SENSOR_FROZEN_SUSPECTED`, `SENSOR_DATA_MISSING`, `ARCHIVE_RECORD_MISSING`, `NOT_OBSERVED_BEFORE_FIRST_SEEN`, `NOT_INSTALLED_CONFIRMED`, `RECONSTRUCTED_VERIFIED` a `RECONSTRUCTED_UNCERTAIN`. Pro každé pole povinně vyznačit způsob měření (raw / přepočtené / importované / rekonstruované), zdroj a dvojici jistot. Frontend má zvlášť kreslit **časovou úplnost řádků**, **dostupnost konkrétního senzoru** a **důvěryhodnost hodnot**. Neznámou hodnotu či nedostupný senzor nikdy nevykreslovat jako nulu nebo zelených 100 %.

### Doporučená pravidla deterministického párování intervalů

1. **P0 – přesné:** shoda `(start_utc,end_utc,interval,variable)` a validovaných jednotek. Porovnat payload a nezávislost zdrojů.
2. **P1 – přesná epocha, odlišná délka:** shodný konec `dateTime` ještě není shodný fyzický interval; jen *candidate*, rozhoduje míra překryvu a reprezentované období.
3. **P2 – jemný drift:** pro původní `interval=5` navrhnout nearest-5min zarovnání pouze při `abs(delta)<=150 s`, zamezit kolizím v témže zdroji a měřit výskyt posunu v časově souvislých blocích. Hodnota ani epoch nesmí být přepsána bez důkazu.
4. **P3 – jiná archivní perioda:** u `interval=6/10/30/40/55/75` chápat řádek jako interval s vlastní délkou a určit časový překryv. Bez legitimního agregátoru nepřevádět na 5min záznam či samostatně nepřerozdělovat srážky.
5. **P4 – konflikt:** při dvou různých hodnotách ve stejném kanonickém slotu uložit obě reference, nezávislost a kvalitu; rozhodovat jednotlivou veličinu, ne celé řádky; auditní stopa je neměnná.
6. **P5 – TZ/DST:** nápadný posun 3600/7200 s pouze jako hypotéza, ověřit jej na neperiodickém fyzikálním signálu nebo primárním logu. U podzimního opakování lokálního času preferovat explicitní UTC epochu a offset; u jarního skoku nevkládat imaginární hodiny.
7. **P6 – aktivita senzoru:** hodnotit `NULL` jen v intervalech, kde existuje validovaná evidence aktivního senzoru; před ní zůstat `UNKNOWN_NOT_OBSERVED` nebo `CONFIRMED_NOT_INSTALLED`, nikdy automatický výpadek.

## Ověřitelnost a omezení závěrů

- Všechny číslice vycházejí z čtecích SELECT dotazů. Velké archivy byly rozděleny na **18 ročních úseků**, případně kratší rozsahy; žádný INSERT/UPDATE/DELETE/DDL ani import WH kandidátů.
- Pracovní `loucka_reconstruction.archive` může mít změněné měřené hodnoty proti produkci; počet přesných epoch **není důkaz identických hodnot**. Neexistuje spolehlivá evidence fyzicky nezávislých senzorových snímků bez autentických logger ID/datalogů a verzovaných konfigurací.
- Číslo **1 750 930** je unikátnost hypotetických **5min UTC slotů**, nikoli počet nezávislých fyzických měření. `8 587 469-1 750 930` označuje redundantní *přítomnosti* slotu, ne definitivně označené kopie. 5min zaokrouhlení není pro dlouhé intervaly věcně ekvivalentní a nepoužívat je k importu.
- Původní měsíc v tabulce pokrytí je přiřazen podle `dateTime`, bez časového snapu; 8 hraničních přerozdělení v každém starém zdroji změní měsíc až při analytickém zarovnání.
- U přítomnosti senzorů `NOT NULL` nevypovídá samo o správnosti fyzikálních hodnot ani o datu instalace. Instalační dokumentace, generace senzoru a WeeWX konfigurace jsou nutné pro definitivní klasifikaci.
- Příští krok: vytvořit nezapisující diagnostický test fingerprintů a intervalového překryvu pro 70 746 WH časů po malých měsících, vyřešit 20 950 nepřipravených časů, dokumentovat schéma původu a uložit verifikované kalendářní přechody do samostatných regresních testů.
