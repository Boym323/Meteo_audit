# Návrhy oprav — Fáze A (review 2026-10-30)

**Stav:** pouze evidenční návrhy. Nic nebylo aplikováno tímto během. Produkční databáze zůstává nedotčena.

Návrhy jsou převzaty z existujících kandidátů `reconstruction_candidates`; jejich batch je `pending`. `rainRate` v roce 2025 má současně starší aplikovanou změnu v pracovní DB, proto jde o konflikt k posouzení, ne schválení. Časy jsou uvedeny v místním čase i UTC a epochě. Zdroj kandidáta je `pocasi-loucka.eu_GW1000`; raw čítačové vzorky 2010/2011 byly nezávisle porovnány s `old_weewx` a `weewx_WH1080`.

| ID / batch ordinal | Místní čas | UTC | `dateTime` s | Veličina | Původní | Návrh | Jistota | Důkaz / omezení |
|---|---|---|---:|---|---:|---:|---|---|
| `loucka-rain-phaseA-201006-review-20261030-v1/0` | 2010-06-01 12:40 | 2010-06-01T10:40:00Z | 1275388800 | rain | 1.554 | 0 | SUSPECTED | raw counter 174.9; CHMI confirms regional rain, not this impulse |
| `loucka-rain-phaseA-201006-review-20261030-v1/1` | 2010-06-01 12:45 | 2010-06-01T10:45:00Z | 1275389100 | rain | 2.331 | 0 | SUSPECTED | raw counter 408; CHMI daily only |
| `loucka-rain-phaseA-201006-review-20261030-v1/2` | 2010-06-01 13:10 | 2010-06-01T11:10:00Z | 1275390600 | rain | 2.568 | 0 | SUSPECTED | raw counter 256.8 after prior jump; no 2010 subdaily CHMI |
| `loucka-rain-phaseA-201006-review-20261030-v1/3` | 2010-06-01 23:15 | 2010-06-01T21:15:00Z | 1275426900 | rain | 1.536 | 0 | SUSPECTED | raw counter 290.1; event rain confirmed regionally |
| `loucka-rain-phaseA-201006-review-20261030-v1/4` | 2010-06-01 23:20 | 2010-06-01T21:20:00Z | 1275427200 | rain | 0.384 | 0 | SUSPECTED | raw counter 328.5 |
| `loucka-rain-phaseA-201006-review-20261030-v1/5` | 2010-06-02 02:00 | 2010-06-02T00:00:00Z | 1275436800 | rain | 0.705 | 0 | SUSPECTED | raw counter 70.5 |
| `loucka-rain-phaseA-201006-review-20261030-v1/6` | 2010-06-02 14:50 | 2010-06-02T12:50:00Z | 1275483000 | rain | 0.606 | 0 | SUSPECTED | raw counter 60.6 |
| `loucka-rain-phaseA-201006-review-20261030-v1/7` | 2010-06-03 12:10 | 2010-06-03T10:10:00Z | 1275559800 | rain | 0.384 | 0 | SUSPECTED | raw counter 38.4; rainRate 9.216 cm/h flagged separately |
| `loucka-rain-phaseA-201006-review-20261030-v1/8` | 2010-06-03 12:15 | 2010-06-03T10:15:00Z | 1275560100 | rain | 0.576 | 0 | SUSPECTED | raw counter 96; rainRate 13.808 cm/h flagged separately |
| `loucka-rain-phaseA-201006-review-20261030-v1/9` | 2010-06-03 15:10 | 2010-06-03T13:10:00Z | 1275570600 | rain | 0.768 | 0 | SUSPECTED | raw counter 76.8 |
| `loucka-rain-phaseA-201006-review-20261030-v1/10` | 2010-06-03 15:50 | 2010-06-03T13:50:00Z | 1275573000 | rain | 0.768 | 0 | SUSPECTED | raw counter 76.8 |
| `loucka-rain-phaseA-201006-review-20261030-v1/11` | 2010-06-03 16:05 | 2010-06-03T14:05:00Z | 1275573900 | rain | 0.576 | 0 | SUSPECTED | raw counter 57.6 |
| `loucka-rain-phaseA-201006-review-20261030-v1/12` | 2010-06-03 16:10 | 2010-06-03T14:10:00Z | 1275574200 | rain | 0.384 | 0 | SUSPECTED | raw counter 96 |
| `loucka-rain-phaseA-201006-review-20261030-v1/13` | 2010-06-03 17:50 | 2010-06-03T15:50:00Z | 1275580200 | rain | 0.384 | 0 | SUSPECTED | raw counter 38.4 |
| `loucka-rain-phaseA-201006-review-20261030-v1/14` | 2010-06-03 21:10 | 2010-06-03T19:10:00Z | 1275592200 | rain | 0.768 | 0 | SUSPECTED | raw counter 96 |
| `loucka-rain-phaseA-201006-review-20261030-v1/15` | 2010-06-03 21:25 | 2010-06-03T19:25:00Z | 1275593100 | rain | 0.768 | 0 | SUSPECTED | raw counter 96 |
| `loucka-rain-phaseA-confirmed-20261030-v1/0` | 2011-03-28 08:50 | 2011-03-28T06:50:00Z | 1301295000 | rain | 3.072 | 0 | HIGH_CONFIDENCE | isolated; WH1080/old_weewx counter 0→307.2→384, adjacent rain 0; CHMI SRA 0/trace mm |
| `loucka-rain-phaseA-confirmed-20261030-v1/1` | 2025-02-27 21:15 | 2025-02-27T20:15:00Z | 1740687300 | rain | 3.05 | 0 | HIGH_CONFIDENCE | outdoor outage; references 8.81/8.45 mm; local daily sum 38.9→8.4 mm; CHMI SRA 5.6/7.4 mm |
| `loucka-rain-phaseA-confirmed-20261030-v1/2` | 2025-02-27 21:15 | 2025-02-27T20:15:00Z | 1740687300 | rainRate | 0.005333… in reconstruction | 0 | UNRESOLVED | pending candidate conflicts with previously applied rainRate restoration; production remains 0 |

| `loucka-high-rainrate-manual-review-1-20261029-v1` | 2010-06-03 12:10 | 2010-06-03T10:10:00Z | 1275559800 | rainRate | 0 (production) | NULL / unresolved | UNRESOLVED | GW1000 source candidate 9.216 cm/h; exact rainRate semantics are unknown. |
| `loucka-high-rainrate-manual-review-1-20261029-v1` | 2010-06-03 12:15 | 2010-06-03T10:15:00Z | 1275560100 | rainRate | 0 (production) | NULL / unresolved | UNRESOLVED | GW1000 source candidate 13.808 cm/h; exact rainRate semantics are unknown. |

## Apply/rollback contract (not executable)

Před jakýmkoli zápisem je nutné schválení a samostatný SQL návrh. Kontrola aktuální hodnoty musí přesně odpovídat výše uvedené původní hodnotě; při neshodě se batch zastaví. Před aplikací uložit přesný `dateTime`, `rain`, `rainRate`, `usUnits`, `interval` do zálohy a doložit počet zasažených řádků. Změny aplikovat pouze do `loucka_reconstruction.archive`, v transakci a s počtem řádků přesně odpovídajícím schválenému návrhu. Po zápisu ověřit hodnoty, součty a záznam auditu. Rollback smí obnovit zálohované hodnoty pouze tehdy, pokud aktuální hodnoty stále odpovídají schváleným novým hodnotám. Produkční archiv zůstává mimo rozsah zásahů.
