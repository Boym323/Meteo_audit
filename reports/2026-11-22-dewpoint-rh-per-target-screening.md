# Dewpoint / RH 2022-04 — kandidáti po aplikované rekonstrukci

**Stav:** read-only živé ověření dne 22. 11. 2026 přes Weather MCP, bez změny DB. Odkaz: issue #15.

## Co přesně lze nyní doložit

- V pracovní DB je **3 734** rozhodovacích řádků `reconstruction_humidity_202204`; **3 493** `estimate_ready`, **156** `missing_unresolved`, **85** `invalidate_frozen`.
- U **2 194** porovnatelných řádků s aplikovanou změnou RH je aktuální RH shodná s naposledy aplikovanou hodnotou (`<=>`).
- **1 077 / 2 194** má uložený `dewpoint` vzdálený od diagnostické Magnusovy aproximace z **aktuální** RH o více než **2 °C**.
- U **všech 1 077** zjištěných případů uložený `dewpoint` odpovídá diagnostickému výpočtu ze **staré** RH s odchylkou nejvýše 0,1 °C.
- Největší absolutní odchylka vůči screeningovému vzorci z aktuální RH činí **13,5068 °C**.

## Nový reprodukovatelný per-target export

[`sql/readonly/dewpoint_rh_202204_candidate_targets.sql`](../sql/readonly/dewpoint_rh_202204_candidate_targets.sql) vrací **1 077 jednotlivých timestampů**, nikoliv pouhý agregát. U každé položky obsahuje starou/aktuální RH, teplotu, uložený rosný bod, oba diagnostické výpočty, rozdíly, RH history event ID, navazující `heatindex`/`appTemp`/`humidex` a existenci jiné dewpoint historie.

Dotaz **nenavrhuje žádnou náhradní hodnotu** (`proposed_value = NULL`, `qc_state = UNRESOLVED_HISTORICAL_WEEWX_FORMULA`). Výsledný hodnotový CSV/JSON manifest zůstává mimo veřejný GitHub a pro samostatnou revizi se musí opatřit časem snapshotu, hashem a kontrolou neměnnosti.

## Důležitá metodická hranice

Použitá Magnusova formule (`a=17.625`, `b=243.04`) je pouze **diagnostický screening**. Z těchto shod nelze dokázat konkrétní historickou verzi WeeWX/driveru ani přesný čas výpočtu odvozených veličin. Ani 1 077 shod se starou RH tedy automaticky neautorizuje přepis `dewpoint`, `appTemp`, `humidex`, `heatindex` nebo denních extrémů.

## Zbývající acceptance blokace #15

- Dohledat dobové `weewx.conf`, verzi WeeWX a mechanismus uložení odvozenin v dubnu 2022.
- Verifikovat formuli a vazby dalších derivátů; provést samostatný validovaný dopad na denní extrémy, včetně ošetření `RH=0/NULL`, `T=0` a UTC/CET/CEST.
- Až potom připravit nezávisle schvalovaný per-value manifest a vratný návrh; **žádný DB apply nebyl proveden**.
