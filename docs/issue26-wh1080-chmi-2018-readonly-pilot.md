# Issue #26: pilotní porovnání WH1080 ↔ ČHMÚ v roce 2018

**Stav 23. 11. 2026:** nový čtecí grant byl nezávisle potvrzen přes `information_schema.TABLE_PRIVILEGES`: stávající `loucka_web_ro@192.168.0.131` má `SELECT` na `weewx_WH1080.archive`. Žádný nový účet.

**Rozsah:** 3 835 chybějících hodnot tlaku roku 2018, které mají původní WH1080 hodnotu v přesnou UTC celou hodinu.

## Náplň pilotu

Skript `scripts/validate_wh1080_chmi_pressure.py`:

- používá výhradně `START TRANSACTION READ ONLY`, pouze existující účet web_ro a ověřuje identitu serveru;
- čte `loucka_reconstruction.archive` a `weewx_WH1080.archive` v roce 2018, nikoliv živý WeeWX;
- používá soubory ČHMÚ uložené v LXC při PR #89; vyžaduje všech 48 měsíčních P/P_hm CSV obou stanic, kontroluje SHA-256 vůči manifestu;
- bere pouze ČHMÚ QUALITY=0 a přesné UTC celé hodiny;
- odděluje historické `pressure NULL` kandidáty od kontrolních období s nenulovým tlakem;
- porovná WH1080 pressure po **diagnostickém** výškovém přepočtu (425 m → 222,25/252,8 m) proti staničnímu ČHMÚ P, a pracovní barometer proti ČHMÚ P_hm;
- zapíše pouze souhrnné CSV a JSON lokálně, **nikdy žádný SQL zápis nebo per-field nahrazení**.

## Bezpečné spuštění na internetově připojeném LXC

Nejdřív zkontrolovat čistý worktree. Nikdy nepřepsat uživatelské necommitnuté soubory v `/opt/meteo-audit` či `/root/meteo-audit`.

```sh
cd /opt/meteo-audit-issue26
git status --short
git fetch origin main
# Pokud čistý worktree, aktualizovat na nový main bez zahazování změn.

# Použít Python v existujícím projektovém venv s PyMySQL.
python3 scripts/validate_wh1080_chmi_pressure.py \
  --cnf /root/meteo-loucka-ro.cnf \
  --chmi-cache /opt/meteo-pressure-chmi/data/chmi-pressure-2009-2026 \
  --out-dir reports/parallel-audit/pressure-wh1080-chmi-pilot-2018
```

Pokud systémový Python nemá PyMySQL, použít stávající venv; nevypisovat heslo ani obsah souboru CNF.

Výstupy: `wh_chmi_annual_groups.csv`, `wh_chmi_monthly_groups.csv`, `evidence.json`.

## Jak výstupy interpretovat

Zdroj WH1080 je v 75 074 původně nalezených timestampích 2016–18 totožný s old_weewx; **tato shoda není nezávislý fyzikální důkaz**. Při srovnání ČHMÚ se rozlišují staniční a hladinové tlaky. Diagnostický suchý hypsometrický model používá současnou lokální teplotu a nemusí přesně odpovídat skutečnému vzdušnému sloupci. Hodinový SYNOP a pětiminutový archivní záznam navíc nemají nutně shodnou časovou reprezentaci.

Zprvu vyhodnotit odchylku WH-vs-ČHMÚ zvlášť pro `target_pressure_NULL` a `target_pressure_present`, jednotlivé měsíce i obě ČHMÚ stanice. Pokud chybějící období mají jinou kalibraci, nedělat žádný automatický import.

**NO-GO na APPLY/ROLLBACK/UPDATE/INSERT**; produkční DB, živý WeeWX v jiném LXC, denní souhrny a chráněné období 2018 Q1 se nemění.

**Ověření:** čtyři syntetické Python testy prošly lokálně. Přímé spuštění skriptu proti LXC a lokální ČHMÚ cache **dosud neproběhlo**; report výsledných mediánů není zatím k dispozici.
