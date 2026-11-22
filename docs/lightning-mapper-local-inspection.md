# Bezpečná identifikace nasazeného WeeWX/Ecowitt lightning mapperu (#17)

Provedený databázový audit potvrdil 54 031 epoch-like hodnot `lightning_disturber_count` a 179/179 `lightning_noise_count = lightning_strike_count`. Webová ochrana proti publikaci chybných čítačů byla implementována ve [webovém PR #168](https://github.com/Boym323/Loucka_weather/pull/168). Kořenová příčina v nasazeném WeeWX driveru zatím nebyla autenticky načtena.

Nový **lokální read-only inspektor** `scripts/inspect_lightning_mapper_readonly.py` byl vytvořen proto, aby se v dalším kroku mohl bezpečně spustit přímo tam, kde je skutečný `weewx.conf` a aktivní driver, bez zpřístupňování hesel, passkeys, IP ani obsahu celého konfiguračního souboru.

Příklad pouze pro operátora na skutečném WeeWX hostu, kde soubory existují:

```bash
python3 scripts/inspect_lightning_mapper_readonly.py --weewx-conf /etc/weewx/weewx.conf
```

Volitelně lze uvést `--driver-source /skutecna/cesta/k/aktivnimu-driveru.py`. Výstup je pouze agregovaná allowlist identifikace klíčů a možných aliasů, žádná kompletní config řádka, raw payload nebo credential. Nenahrazuje autentický gateway LOOP/MQTT/LAN payload. Neověřuje, že `weewx.conf` obsahuje veškerý runtime mapping, který může být uvnitř driveru nebo v dalších extension/config souborech.

**Bez nového důkazu** nelze rozhodnout, zda u každého původního řádku byl `lightning_time`/last strike epoch vložen do counteru chybným driverem, následným importem, nebo dalším mezikrokem. Inspektor žádnou korekci neautorizuje, nic nezapisuje, nemění WeeWX a nikdy nevypisuje tajný atribut. Po ověření datového toku je nutné přidat syntetickou fixture odpovídající **sanitizovanému** autentickému payloadu, opravit konkrétní mapper a projít jeho regresní testy, pak teprve hodnotit historickou obnovitelnost.
