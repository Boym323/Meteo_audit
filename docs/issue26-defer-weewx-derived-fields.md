# Rozhodnutí vlastníka — C001 dewpoint až v závěrečné WeeWX fázi

**23. 11. 2026. Rozsah:** issue #26, pouze plánování; žádná změna
meteorologických údajů, žádné nové účty/databázové instance nebo PBS kroky.

## Rozhodnutí

Rosný bod (dewpoint) je odvozen z teploty a relativní vlhkosti.
V rámci nynější rekonstrukce **NEPŘIPRAVOVAT další per-field
opravy C001**. Zaměřit se na původní archivní měření.
Zachovat dosavadní read-only důkazy o zastaralých odvozeninách.

Po dokončení rekonstrukce a schválení vstupních T/RH provést samostatně
řízený přepočet historických odvozených veličin pomocí WeeWX.
Nevkládat opravy dewpoint do schvalovacích batchů nyní.

## Technická podmínka, nikoli nový blokátor issue #26

WeeWX StdWXCalculate počítá nové odvozené hodnoty dle konfigurace,
ale **nepřepočítává automaticky zpětně** staré SQL archivní řádky.
WeeWX příkaz `weectl database calc-missing` existuje,
jeho účelem jsou **chybějící** odvozené veličiny. Samostatný
`weectl database rebuild-daily` přepočítává denní souhrny
z archivních řádků, **ne staré uložené `archive.dewpoint`**.

Proto musí závěrečný plán explicitně rozlišit:
- záznamy s existujícím, ale zastaralým dewpoint (včetně
  1 077 výrazně odlišných vůči nové RH);
- záznamy dewpoint NULL po doplnění RH;
- záznamy RH NULL se stále vyplněným starým dewpoint.

Před finální WeeWX reprocess fází ověřit binding na zamýšlenou
pracovní databázi, hodnoty usUnits a mechaniku **vynuceného
přepočtu stávajících nenulových derived hodnot**; neprovádět
to nevědomky na produkčním archivu. Poté teprve případně
znovu sestavit denní přehledy podle již existujícího plánu WeeWX.

Odkazy:
- https://weewx.com/docs/latest/reference/weewx-options/stdwxcalculate/
- https://www.weewx.com/docs/latest/utilities/weectl-database/

**C001 status:** DEFERRED / NON-BLOCKING for issue #26.
Dosavadní diagnostika zůstává validní; náhradní hodnoty
se nyní nepovolují ani nepřipravují.
