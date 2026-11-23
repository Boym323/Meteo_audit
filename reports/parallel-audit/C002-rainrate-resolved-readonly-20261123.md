# C002 — rainRate 2023–2024: divergence v pracovním archivu již odstraněna

**Datum live read-only ověření:** 23. 11. 2026
**Databáze:** loucka_reconstruction, lo-infra-db-mariadb01
**Rozsah:** C002, 13 intervalů 2023 + 15 intervalů 2024
**Režim:** pouze SELECT; bez nových INSERT/UPDATE/DELETE, SQL účtů nebo instancí

## Ověřené fakty

Report z 30. 10. 2026 uváděl 28 intervalů, kde GW1000 měl
rainRate > 5 cm/h a pracovní archiv měl rainRate = 0.
Aktuální live kontrola stejného časového rozsahu zjistila:

- Párové GW1000 × reconstruction řádky v UTC 2023–2024: 209 369.
- Zdrojové hodnoty rainRate > 5 cm/h: 28.
- Z toho reconstruction rainRate = 0: **0**.
- Z toho reconstruction rainRate NULL: **0**.
- Shodné zdrojové a pracovní rainRate: **28/28**.
- Rok 2023: 13/13 shodných; rok 2024: 15/15 shodných.
- Všech 28 časů má auditní záznam applied pro batch
  rainrate-2023-2024-wet-source-review-v1.
- Všech 28 auditních old_value bylo 0 a všech 28 auditních
  new_value odpovídá current reconstruction i zdrojovému GW1000.
- Auditní source_database: pocasi-loucka.eu_GW1000.
- V této etapě nebyly provedeny žádné nové změny dat.

## Reprodukovatelná read-only SQL kontrola

    SELECT
      CASE WHEN g.dateTime<1704067200 THEN '2023'
           ELSE '2024' END AS year_utc,
      COUNT(*) AS high_rate_pairs,
      SUM(g.rainRate <=> r.rainRate) AS exact_equal,
      SUM(r.rainRate=0) AS target_zero
    FROM `pocasi-loucka.eu_GW1000`.archive g
    JOIN loucka_reconstruction.archive r ON r.dateTime=g.dateTime
    WHERE g.dateTime >= 1672531200 AND g.dateTime < 1735689600
      AND g.rainRate > 5
    GROUP BY CASE WHEN g.dateTime<1704067200 THEN '2023'
                  ELSE '2024' END;

    SELECT c.batch_key,c.state,COUNT(*) AS events
    FROM loucka_reconstruction.reconstruction_changes c
    JOIN `pocasi-loucka.eu_GW1000`.archive g
      ON g.dateTime=c.target_time
    WHERE c.target_time >= 1672531200 AND c.target_time < 1735689600
      AND g.rainRate > 5 AND c.variable='rainRate'
    GROUP BY c.batch_key,c.state;

## Důležité omezení závěru

**Databázový rozdíl GW1000>5 / reconstruction=0 z C002 je odstraněn
před touto etapou a nesmí se aplikovat podruhé.**

Stále není nezávisle potvrzeno, že samotné špičky GW1000 jsou
skutečně správnými meteorologickými hodnotami. Ověření driveru,
instalace a nezávislé meteorologické reference zůstává otevřené.
Datová shoda a audit jsou dokladem aplikace, ne fyzikální validace.

Není to autorizace nové dávky. Žádná produkční nebo pracovní
data nebyla touto kontrolou upravena; nezřizujeme další účty,
MariaDB instance ani nepodmiňujeme pokračování kontrolou PBS.
Denní extrémy časem přepočítá WeeWX.
