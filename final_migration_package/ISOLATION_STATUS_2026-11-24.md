# Izolace migračního testu — revize 2026-11-24

MIGRATION_TEST_MANIFEST_SAME_SERVER_v2.json z 2026-11-17 pinoval pocasi-loucka.eu a loucka_migration_test na hostu lo-infra-db-mariadb01, obojí server_id=1. To jsou dvě samostatná databázová schémata v jedné MariaDB instanci; není to izolovaná instance ani test klon mimo produkční host. Historický manifest a jeho schválení zůstávají zachovány, ale nesplňují nynější požadavek odděleného serveru.

Aktuální prostředí je LXC klient, nikoli Proxmox node. Příkazy/API pct, pvesh, pveversion, pveam chybí; /etc/pve a /dev/pve nejsou připojené; effective capabilities jsou prázdné. df a free ukazují jen limity klientského CT. Proxmox uzel, storage kapacitu, cluster permissions ani schválení tvorby nového CT zde nelze ověřit. Neproběhlo žádné provisioning volání. Ačkoli `loucka_web_ro` může na produkčním schematu jen SELECT, stále umí zapisovat do rekonstrukčního schematu; všechny živé audity v této relaci výslovně použily read-only transakci.

Podrobný kapacitní preflight, příkazy a fail-closed setup jsou v ISOLATED_TEST_PROVISIONING_2026-11-24.md. Závěr: provisioning zde není dostupný/schválený; test restore a migration zůstávají blokovány do infra/DBA provisioningu.
