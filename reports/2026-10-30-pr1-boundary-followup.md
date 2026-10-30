# Doplnění review PR #1: sjednocení ročních časových hranic

Toto doplnění dokumentuje opravy po review commitu `9d1e8b8`.

- `rainrate.py` dříve používal `[start,end)`, zatímco `monthly.py` již `(start,end]`. Nově oba sestavují SQL predikát pomocí `time_bounds.archive_period_predicate()`.
- Roční `rainRate` agregace správně zahrnuje interval končící 1. ledna do předchozího roku a nezahrne jej do následujícího. Metadata a přehled časových hranic jsou přejmenovány na `start_utc_epoch_exclusive` a `stop_utc_epoch_inclusive`.
- Odhad `expected_grid_rows_estimated` v `monthly.py` se nyní omezuje skutečným prvním a posledním timestampem v archivu; především neoznačuje dosud neexistující budoucí intervaly aktuálního měsíce jako chybějící.
- Přidány regresní testy hranice roku, správného jednostranného zahrnutí, prvního a posledního archivního intervalu a odmítání chybných parametrů.
- Historická CSV z předchozího běhu zůstávají beze změny a jejich staré časové filtry se **nesmí** vydávat za nový přepočet. Roční `rainRate` statistiky se mají znovu vygenerovat až po zřízení a ověření samostatného read-only MariaDB účtu `meteo_audit_ro`.

Žádná meteorologická hodnota, historie rekonstrukcí ani databázová oprávnění se touto úpravou nemění.
