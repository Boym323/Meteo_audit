# Issue #26: Proxmox Backup Server jako schválený model obnovy

**Rozhodnutí vlastníka, 23. 11. 2026:** další instanci MariaDB nezřizujeme.
Zachováváme stávající instanci databáze a její zálohování přes existující
Proxmox Backup Server (PBS). Samostatný SQL restore drill z PR #72 zůstává
historicky otestovanou **nepovinnou** možností; není požadavkem pro issue #26
ani důvodem zřizovat novou instanci.

## Co PBS prokazuje a co ne

- Úspěšný zálohovací job znamená, že hypervizor vytvořil zálohovací snapshot.
- Úspěšná PBS **Verify** kontrola prokazuje integritu uložených dat/chunků.
- Pouhé SUCCESS/Verify **neprokazuje**, že byly zahrnuty všechny MariaDB
  soubory, že zachycený běžící SQL server je aplikačně konzistentní,
  ani že obnovená DB nastartuje a zachová rekonstruovaná data.
- Tento zbytkový rozdíl mezi integritou archivu a reálným spuštěním
  databáze musí být v issue #26 výslovně evidován; nesmí se nazvat
  úspěšným databázovým restore testem.

Oficiální dokumentace:
- https://pbs.proxmox.com/docs/maintenance.html (PBS Verify).
- https://github.com/proxmox/pve-docs/blob/master/vzdump.adoc
  (VM guest agent/fsfreeze, LXC snapshot, vyloučené mount pointy).

## Přijatelná důkazní cesta bez nové instance MariaDB

1. **Identifikovat konkrétního hosta databáze**: VM nebo LXC, VMID/CTID,
   Proxmox node, PBS storage/datastore a backup group; ověřit, zda záloha
   opravdu cílí na hosta, kde fyzicky leží datadir MariaDB.
2. **Ověřit pokrytí všech úložišť databáze**:
   na DB hostu zjistit read-only SQL dotazem SELECT @@datadir;
   pro LXC v PVE zkontrolovat konfiguraci pomocí pct config <CTID>:
   rootfs, mpX, backup=0/1, bind/device mounty. LXC bind/device mount
   Proxmox vzdump nezahrnuje; další volume mounty mohou být vyloučeny.
   Pro VM použít qm config <VMID>, zkontrolovat disky s backup=0
   a případné externí mounty uvnitř VM.
3. **Potvrdit zálohování a ověření**: nejnovější úspěšný vzdump job
   konkrétního VMID/CTID, snapshot existující na správném PBS datastore,
   poslední úspěšný PBS Verify pro tento snapshot a platnou retenci.
   Bez skutečného logu a snapshot ID označit stav NEOVĚŘENO.
4. **Zdokumentovat konzistenci**: mode stop/snapshot/suspend, zda je
   MariaDB v LXC nebo VM, v případě VM stav QEMU guest agenta/fsfreeze
   a jestli je InnoDB crash-recovery z garantovaného snapshotu dostačující.
   Záznam logu nebo snapshotu bez spolehlivého zachycení SQL stavu nesmí
   získat označení DATABASE_RESTORE_VERIFIED.
5. **Bez zásahu do běžící DB** lze z PBS File Restore otevřít snapshot,
   prohlédnout cestu k MariaDB datadir, příslušné konfigurační soubory,
   a zkušebně stáhnout neškodný soubor do bezpečné privátní cesty
   mimo produkční DB. Jde o zkoušku čitelnosti snapshotu,
   nikoli o kompletní obnovení databáze.
6. **Před opravnou dávkou** vytvořit neměnný per-batch before-image
   (přesné UTC timestampy, veličiny, old/new, zdroj a SHA256), ověřit
   zachovanou poslední zálohu, provést dry-run CAS a explicitní owner
   schválení **jednoho konkrétního batch ID + hash**.
   Rollback jednotlivých oprav je transakční (post-image CAS + append-only
   audit), PBS slouží jako disaster recovery celého hosta, ne jako
   běžný rollback každé hodnoty.
7. **Po záloze** read-only potvrdit invariantu července 2021 42,567 mm,
   počet záznamů a relevantní historii Fáze A a naposledy
   aplikované QC změny. Výsledek těchto live SQL kontrol je
   odlišný od ověření dat uvnitř PBS snapshotu.

## Povolené závěrečné stavy (nesměšovat)

- PBS_BACKUP_UNVERIFIED: uživatel zálohování uvádí, ale doklady
  snapshotu, rozsahu a Verify nebyly nahlédnuty.
- PBS_INTEGRITY_VERIFIED: konkrétní zálohovaný host, pokrytí dat,
  úspěšný job a PBS Verify jsou doloženy.
- PBS_FILE_RECOVERY_CHECKED: navíc bylo bezpečně ověřeno
  otevření/stáhnutí souboru ze snapshotu.
- DATABASE_RESTORE_VERIFIED: prokázáno pouze skutečným obnovením
  a úspěšnou kontrolou MariaDB; v aktuální cestě se **nevyžaduje**
  a bez restore ho nesmíme tvrdit.

## Co zůstává blokující pro uzavření issue #26

- Doložení PBS backup + Verify + plného zahrnutí datadir/mountů
  pro **skutečný DB host**, včetně dokumentované úrovně konzistence.
- Provozní schvalování přesného opravného manifestu s owner souhlasem
  a reálně ověřený transakční per-batch rollback. Simulátor a
  syntetické MariaDB CI testy nejsou provozní schválení.
- Potvrzení chráněné Fáze A a července 2021 proti živé rekonstrukci.
- Historické QUARANTINE změny se neodemykají; produkční archiv
  zůstává beze změny. Denní extrémy později přepočítá WeeWX.

V tomto dokumentačním kroku **neproběhlo** žádné spojení s Proxmoxem
ani PBS. Skutečný stav záloh není z GitHub repozitáře ověřen.
