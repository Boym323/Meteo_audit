# WH1080 vs ČHMÚ pilot — 2018

**Provedeno:** 2026-11-23 19:35 UTC na zl-dev-frontendPocasi, čistý worktree z main po merge PR #91 (`0b38cc9`). Reprodukovatelný runner: [`scripts/validate_wh1080_chmi_pressure.py`](../../../scripts/validate_wh1080_chmi_pressure.py).

## Rozsah a reprodukce

Runner provedl pouze SELECT uvnitř `START TRANSACTION READ ONLY` pod existujícím `loucka_web_ro@192.168.0.131` (`lo-infra-db-mariadb01`, `server_id=1`). Dotaz pároval `loucka_reconstruction.archive` a `weewx_WH1080.archive` na přesných celých UTC hodinách v roce 2018; zahrnul pouze nenulové WH `pressure`. Žádné hodnoty SQL nebyly zapisovány.

ČHMÚ vstupy jsou hodinové P a P_hm pro Holešov 11774 a Mošnov 11782; všechny čtyři stanice/prvek sady obsahují 12 měsíčních souborů a SHA-256 souhlasí s lokálním manifestem. SHA-256 manifestu je `3c935d0a134a6cd351fe1915cb0a720cf47bed4dc8fc18c0e7d88ece4b72409e`. Ze 17 520 očekávaných hodnot každého prvku/stanice mělo 17 409 quality=0 a 111 quality=4 (missing); do statistik se používá pouze quality=0.

Příkaz použitý pro běh:

```sh
python3 scripts/validate_wh1080_chmi_pressure.py \
  --cnf /root/meteo-loucka-ro.cnf \
  --chmi-cache /opt/meteo-pressure-chmi/data/chmi-pressure-2009-2026 \
  --out-dir reports/parallel-audit/pressure-wh1080-chmi-pilot-2018
```

## Výsledek

SQL našel **8 055** celých hodin s nenulovým WH1080 zdrojem: **3 835** hodin, kdy cílový `pressure` chybí, a **4 220** kontrolních hodin, kdy cílový `pressure` existuje. U těchto hodin byly zjištěny následující robustní statistiky:

| Porovnání | Počet / skupina | Holešov 11774: medián (MAD), hPa | Mošnov 11782: medián (MAD), hPa |
|---|---:|---:|---:|
| WH pressure transportovaný z 425 m na výšku stanice − ČHMÚ P, cílový pressure NULL | 3 817 / 3 816 párů | −23,064 (1,437) | −22,809 (1,333) |
| WH pressure transportovaný na výšku stanice − ČHMÚ P, cílový pressure present | 4 187 / 4 185 párů | −23,636 (1,312) | −23,053 (1,118) |
| Platný cílový pressure transportovaný na výšku stanice − ČHMÚ P, kontrolní skupina | 4 187 / 4 185 párů | −22,873 (1,570) | −22,374 (1,299) |
| Cílový barometer − ČHMÚ P_hm, cílový pressure NULL | 2 986 / 2 985 párů | −24,314 (1,106) | −24,642 (0,990) |
| WH pressure − existující cílový pressure | 4 220 zdroj/target párů celkem | — | — |

Měsíční medián výškově upraveného `WH pressure − ČHMÚ P` v cílových mezerách se pohyboval od −25,48 hPa (Holešov, prosinec) do −20,48 hPa (Holešov, leden); Mošnov −24,77 až −19,23 hPa. Podrobné měsíční n, median, MAD, mean, p05 a p95 jsou v `wh_chmi_monthly_groups.csv`.

## Interpretace a kandidáti

WH1080 série v této 2018 pilotní podmnožině po výškovém přepočtu vykazuje vůči oběma ČHMÚ staničním tlakům mediánový deficit přibližně 23 hPa. Prakticky stejný deficit má kontrolní skupina již vyplněných cílových hodnot. WH1080 tedy v těchto datech nekoriguje pozorovaný epochový posun; jeho rozdíl vůči existujícímu cíli má medián −0,517 hPa (MAD 0,345), měsíční mediány sahají od −1,01 do −0,29 hPa. Tato shoda je slučitelná s již popsanou společnou proveniencí WH1080/old_weewx a není nezávislým potvrzením fyzikální správnosti.

**Závěr:** žádná z 3 835 přesných hodinových mezer 2018 není v tomto pilotu povýšena na bezpečný kandidát obnovy. WH hodnoty nejsou označeny za chybné jako senzorová měření; prokazují však výrazný systematický nesoulad s nezávislými staničními referencemi při dané výškové metodě. Tento výsledek se vztahuje pouze na přesné celé hodiny roku 2018, nikoli na všechny 75 074 pětiminutové hodnoty 2016–2018 z PR #88. Pro ně je stále nutná rozšířená, časově zarovnaná nezávislá kontrola.

Transport ze 425 m na výšku stanic používá suchou hypsometrickou rovnici a současnou Loučkovu `outTemp`; je to diagnostický model, nikoli ground truth. Hodinový SYNOP záznam a bodový WeeWX archiv nemají totožnou časovou podporu. Nevytvářely se imputované/modelované hodnoty, manifesty UPDATE ani opravy. Cílové Q1 2018, produkční archive a denní tabulky nebyly měněny.

## Výstupy

- `evidence.json` — identita DB, pokrytí a quality kódy ČHMÚ, počty, manifest SHA a limity.
- `wh_chmi_annual_groups.csv` — robustní roční výsledky podle stanice, cílového stavu a metriky.
- `wh_chmi_monthly_groups.csv` — měsíční robustní výsledky pro obě stanice ČHMÚ, s rozdělením target NULL/present.

CSV obsahují pouze agregace; jednotlivé měřicí hodnoty ani přihlašovací údaje nejsou součástí tohoto výstupu.
