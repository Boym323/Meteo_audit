# Issue #26: transakční zapisovač/rollback — pouze po schválení dávky

Tento dokument doplňuje PR #74 (přesné individuální schválení).
**Zálohy a PBS jsou z rozhodnutí vlastníka mimo rozsah projektu.**
Stále neexistuje důkaz disaster-recovery celého serveru; tato výjimka
neznamená schválení neověřené hromadné opravy.

## Co implementuje nový Python modul

Soubor src/meteo_audit/issue26_transaction.py obsahuje tři funkce:

1. sql_preflight(connection,batch): pouze SELECT, nikdy nic nezapisuje.
   Ověřuje pevně vybranou databázi loucka_reconstruction, existenci
   auditních tabulek, InnoDB, původní data, legacy audit, již aplikované
   dávky, NULL-safe předobrazy a červenec 2021 (42,567 mm).
2. apply_approved_batch(...): přesný nový HMAC owner approval vázaný
   na batch ID + payload SHA-256 + before-image SHA-256, transakční
   GET_LOCK, SELECT FOR UPDATE, opětovné CAS a UPDATE s NULL-safe
   podmínkou hodnoty (<=>). Je-li cokoli neshodné, vrátí celou transakci
   včetně auditních událostí.
3. rollback_approved_batch(...): vyžaduje nově platný podpis stejné
   dávky a další explicitní frázi VRATIT-DAVKU:ID:HASH:BEFORE_HASH.
   Čte původní APPLY audit, nepřipustí dříve rollbackovanou dávku,
   provede post-image CAS a append-only ROLLBACK události.

Souběžné běhy tohoto nástroje serializuje MariaDB GET_LOCK.
Externí zapisovače jiných nástrojů tím ale nejsou blokovány; CAS
díky tomu chrání před zastaralými hodnotami, nezajišťuje jejich
výlučné vlastnictví.

## Databázová struktura

DDL návrh je v sql/issue26_transactional_audit_schema.sql.
Obsahuje dvě nové InnoDB auditní tabulky:
- issue26_batch_events: metadata jedné APPLY/ROLLBACK události
  s konkrétním schváleným SHA a identitou deklarovaného operátora.
- issue26_field_events: zdroj, jednotková epocha, stará/nová
  hodnota a výsledek jednotlivých veličin. Duplicity chrání indexy.

Kód auditní události **nevypisuje ani nemění**, ale doporučený DB
uživatel pro auditní tabulky má mít jen SELECT a INSERT, nikdy
UPDATE nebo DELETE. Privilegium UPDATE na archive má být omezené
výhradně na pracovní schéma. DDL se automaticky neaplikuje.

## Provozní posloupnost

1. Nezávisle posoudit konkrétní návrh a surové zdroje.
2. Vytvořit přesný per-field manifest a získat read-only SQL
   preflight z aktuálních hodnot na stávající rekonstrukční DB.
3. Vlastník explicitně schválí výzvu obsahující ID dávky
   a otisky manifestu a before-image; podepíše receipt.
4. Před zamýšleným SQL apply ověřit oprávnění používaného
   databázového účtu, shodu auditních schémat a kontrolu
   skutečného serveru. Schválení tohoto PR/issue nestačí.
5. Writer v transakci zopakuje kontrolu evidence a hodnot.
6. Pokud je potřeba vrácení, vlastník samostatně schválí
   rollback. Při neshodě s po-opravným obrazem jej
   transakce automaticky odmítne.
7. Uchovat auditní otisky a read-only ověřit konečné hodnoty,
   rain 2021 a Fázi A. Denní extrémy nepřepočítávat ručně:
   později je obnoví WeeWX.

## Co se NESTALO

- Žádný zápis ani DDL do živé MariaDB; žádný automatický
  deployment na lo-infra-db-mariadb01.
- Žádný zápis do původního produkčního archivu nebo archive_day_*.
- Žádná kontrola či obnova záloh PBS a žádná trvalá nová
  MariaDB instance.
- Žádné schválení aplikace konkrétní dávky na živých datech.

Testování bylo provedeno proti syntetické dočasné MariaDB
11.8 v GitHub Actions. CI není potvrzením provozního
nasazení skutečného zapisovače.

## Zbývá před definitivním uzavřením #26

- Nezávisle zkontrolovat a provozně schválit DDL a SQL identitu
  pro stávající pracovní DB. Není třeba další MariaDB instance.
- Připojit existující schvalovací workflow na ověřený
  read-only export přímo z DB, nikoli na ručně připravený JSON.
- Vytvořit ovládaný provozní režim se skutečným read-only
  náhledem a následným explicitním APPLY/ROLLBACK.
- Znovu ověřit Fázi A a historii mimo původní invariant rain.
- Neautomatizovat neschválené nebo karanténní hodnoty.
