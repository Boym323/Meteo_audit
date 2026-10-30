# Bezpečnost databázového přístupu

## Očekávání nástroje

`meteo_audit.db.query()` přijímá jen jeden příkaz začínající `SELECT` nebo `SHOW`. Odmítá více příkazů, terminátor, SQL komentáře, proměnné, přiřazení, `INTO`, zámky a známé funkce s vedlejšími účinky. Identifikátor databáze musí přesně odpovídat pevné allowlist sadě šesti schémat. Hodnoty epochů skládá program jako celá čísla z interních datetime hranic.

Klient spustí příkaz v `START TRANSACTION READ ONLY` a po úspěchu provede `ROLLBACK`. To chrání proti běžným zápisům, ale není náhradou DB oprávnění: Uživatel zvolil existující účet `loucka_audit`, který má v `loucka_reconstruction` rovněž zápisová práva. Analytické CLI omezuje jen své vlastní SQL; nemůže změnit granty tohoto účtu. Jako silnější ochranu lze dobrovolně použít SELECT-only účet. Transakční READ ONLY sama nepokrývá každý možný plugin/UDF a dlouhý výpis může stále zatížit server; proto se čte po měsících a s timeoutem nejvýše 600 sekund.

Připojení bere z `.env` pouze `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, případně stejné proměnné prostředí. Přístup k `.env` je na POSIX odmítnut, pokud práva dovolují čtení skupině nebo ostatním. Heslo se předává přes dočasný MariaDB option file s režimem 0600, který se po příkazu odstraní. Chybové hlášení neobsahuje příkaz ani obsah konfiguračního souboru. Heslo se nikdy nedává do parametrů procesu, logu, Markdownu nebo Gitu.

## Volitelná varianta: SELECT-only účet

Vytvoření nového účtu **není nutné**. `sql/admin/create_meteo_audit_ro.sql` zůstává volitelným runbookem pro správce; aplikace jej nespouští. Správce musí nahradit schválený host klienta a dosadit heslo přímo v zabezpečené administrační relaci ze správce hesel, nikoliv z Gitu. Přidělují se pouze `SELECT` na tabulky `archive` v šesti schématech potřebných k porovnání historie. Jestliže se skutečně používá jen měsíční srovnání dvou hlavních databází, lze zúžit grant na tyto dvě tabulky.

Po vytvoření ověřte `SHOW GRANTS FOR ...` a `SELECT CURRENT_USER(), CURRENT_ROLE()`. Zkontrolujte, že účet nemá zděděné globální oprávnění ani roli dovolující zápis. Neprovádějte žádný GRANT ani změnu účtu z tohoto repozitáře automaticky. CLI používá stávající přihlašovací údaje. Spouštějte ho jako neprivilegovaný OS účet `meteo-audit`, jen pro schválené read-only analýzy; stejná DB identita může mimo tento klient stále zapisovat.

## CI a tajemství

GitHub Actions běží bez databázových tajemství a bez spojení k DB. `scripts/check_repo_secrets.py` kontroluje sledované soubory na prostředí a běžné vzory přihlašovacích údajů/connection stringů. `.env`, `.env.*` (mimo bezpečný příklad), dumpy a surové exporty patří mimo Git. Workflow nepřikládá artefakty.
