# Dočasná skutečně izolovaná MariaDB test instance

## Zjištěný stav tohoto klienta

Aktuální shell běží uvnitř Debian 13 LXC zl-dev-frontendPocasi, nikoli na Proxmox uzlu. Příkazy pct, pvesh, pveversion a pveam nejsou instalovány; /etc/pve, /dev/pve a /var/lib/vz zde nejsou dostupné. Efektivní capability set je prázdný. df -h / hlásí 14 GB svazek s přibližně 4,1 GB volného místa; free ukazuje prostředky tohoto kontejneru, nikoli Proxmox uzlu. Nelze z těchto údajů potvrdit 30 GB storage, 2 vCPU/4 GB RAM rezervu na uzlu ani oprávnění Proxmox API. Není zde tedy bezpečné ani možné LXC provisionovat.

Klientský apt index nabízí MariaDB 1:11.8.9+ds-0+deb13u1, ne požadovanou 11.8.6. Použít pouze podepsaný repozitář nebo archivní Debian balíčky odpovídající existujícímu serveru 11.8.6-MariaDB-0+deb13u1; pokud přesná verze není dostupná, provisioning zastavit. Verzi bez schválení nenahrazovat.

## Předpoklady a fail-closed preflight na Proxmox uzlu

Spustit jako operátor s oprávněním vytvořit LXC a alokovat storage. Následující proměnné se doplní až podle výstupů infrastruktury; nedosazovat odhadované názvy storage/bridge.

~~~bash
set -euo pipefail
NODE='<pve-node-name>'
STORAGE='<storage-id-with-rootdir-and-vztmpl>'
CTID='<unused-3-or-4-digit-id>'

pveversion -v
pvesh get /nodes
pvesh get "/nodes/$NODE/status"
pvesm status --storage "$STORAGE"
pvesh get "/nodes/$NODE/storage/$STORAGE/content" --content rootdir
pveam available --section system | grep 'debian-13-standard'
pveum user permissions / --userid '<operator@realm>'
test -x /usr/sbin/pct
test -d /etc/pve
pvesh get "/cluster/resources" --type vm
~~~

Ověřit nejméně 32 GiB volných pro 30 GiB root disk plus rezervu; u thin/LVM/ZFS ověřit i skutečně volnou kapacitu poolu (lvs -o vg_name,lv_name,lv_size,data_percent,metadata_percent / zpool list -p). Ověřit uzlovou paměť z pvesh get /nodes/$NODE/status a ponechat nejméně 2 GiB pro host nad 4 GiB přidělenými CT. Ověřit, že CTID není používán (pct status "$CTID" musí selhat jako neexistující ID), a stáhnout/součtově ověřit oficiální Debian 13 template přes pveam download. Pokud kterýkoli kapacitní, oprávňovací nebo síťový předpoklad nevychází, nepokračovat.

Testovací bridge musí být bez fyzického uplinku a bez default gateway; CT nesmí routovat do produkční sítě. MariaDB se naváže pouze na loopback. Na uzlu musí existovat již vytvořený izolovaný vmbr bez uplinku, jinak jej musí samostatně připravit síťová/virtualizační správa. Neschválený bridge ani firewall pravidla nevytvářet odhadem.

## Vytvoření a ověření CT

Po výše uvedených kontrolách:

~~~bash
TEMPLATE='<storage>:vztmpl/debian-13-standard_<verified-version>_amd64.tar.zst'
pct create "$CTID" "$TEMPLATE" \
  --hostname loucka-mariadb-test-99 \
  --cores 2 --memory 4096 --swap 2048 \
  --rootfs "$STORAGE:30" \
  --unprivileged 1 --onboot 0 --start 0 \
  --description 'Ephemeral isolated Loucka migration verification; no production route'
pct start "$CTID"
pct exec "$CTID" -- cat /etc/os-release
pct exec "$CTID" -- nproc
pct exec "$CTID" -- free -b
pct exec "$CTID" -- df -B1 /
~~~

CT záměrně nemá net0; pro WeeWX i MariaDB stačí loopback. Pokud organizace potřebuje řízený přenos, použít jen schválený offline přenos přes Proxmox host. Neotevírat cestu z CT do produkční sítě.

## MariaDB 11.8.6 a unikátní identita

V CT aktualizovat Debian 13 a nainstalovat MariaDB pouze z verifikovaného podepsaného zdroje přesně ve verzi odpovídající 11.8.6-MariaDB-0+deb13u1. Ověřit dostupnou verzi před instalací:

~~~bash
apt-cache madison mariadb-server mariadb-server-core mariadb-client
~~~

Pinovat přesné ověřené package version; nepoužívat latest. Poté vytvořit /etc/mysql/mariadb.conf.d/99-loucka-test.cnf:

~~~ini
[mariadbd]
server_id=99
bind-address=127.0.0.1
port=3306
skip_name_resolve=1
~~~

Soubor nastavit root:root 0644, restartovat službu a ověřit přes klienta SELECT @@hostname,@@server_id,@@version,@@bind_address;. Požadovaný výsledek: server_id=99, verze 11.8.6, naslouchá pouze loopback. Ověřit, že z CT neexistuje cesta na lo-infra-db-mariadb01:3306.

## Restore a test migrace po vytvoření instance

1. Přenést existující reconstruction backup a samostatný čerstvý konsistentní dump produkční DB jako soubory; ověřit SHA-256 před importem. Stávající reconstruction backup sama o sobě není produkční pre-migration clone.
2. pct push oba soubory do CT, obnovit reconstruction databázi a ověřit přes všech 26 tabulek přesné počty, schéma/indexy a obsahové hashe. Vytvořit oddělenou databázi pocasi_loucka_testclone z produkčního dumpu; původní produkční schema do CT importovat nesmí.
3. V CT vytvořit test-only uživatele s omezenými právy pouze na clone schema. Zamezit produkčním grantům. Test driver musí před zápisem ověřovat @@server_id=99, hostname a přesný clone schema.
4. Před testem uložit checksumy celého klonu a všech archive_day_*. Aplikovat manifest v testovací transakci; porovnat každý postimage s diffem a plně přepočítat dotčené denní statistiky pouze pomocí lokálního test config WeeWX. Nezapínat reporty ani publikaci.
5. Idempotenci ověřit druhým dry-run jako „žádné operace/už aplikováno“, bez druhého zápisu. Potom provést rollback celého testovacího klonu obnovou uloženého pre-migration dumpu do čistého schema/instance; ověřit shodné schema, row counts a obsahové hashe všech tabulek včetně archive_day_*.
6. Odstranit dočasný CT až po uložení test reportu a schváleném retenčním okně; produkce se nikdy nepřipojuje k WeeWX test config ani k test skriptu.

Poznámka: současný migrační manifest klasifikuje každou operaci jako NOT_APPROVED pro produkci. Test-only použití na izolovaném klonu není produkční schválení. Veškeré pressure estimates zůstávají mimo archive i denní statistiky.
