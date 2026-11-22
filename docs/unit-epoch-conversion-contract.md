# Bezpečný převod historických jednotek (issue #21)

Modul meteo_audit.epoch_units neotevírá databázi a nepřepisuje archive. Pro převod vyžaduje právě jednu ověřenou epochu zdroje, číslo usUnits odpovídající záznamu a doložený odkaz evidence_ref. Mezera, překryv, neznámá nebo nepotvrzená epocha znamená selhání bez odhadu.

Každá epocha používá polootevřený rozsah UTC timestampu konce WeeWX archivu [start_utc,end_utc), fyzickou číselnou jednotku větru a sémantiku rain. Samotné usUnits=17 nestačí k odhadu: starší číselné větry mohly být v km/h i při deklarovaném METRICWX, později v m/s. Regresní syntetické testy demonstrují poměr 1 v 2011 a 3,6 v 2019; přesná hranice změny v roce 2013 NENÍ v modulu tvrzena.

Starý dešťový čítač se nikdy nekonvertuje jako intervalová srážka. Neznámá sémantika rain a chybějící evidence blokují převod. Funkce také nikdy nedopočítává rainRate z rain, zachovává NULL vs měřenou nulu a odmítá záporné, nečíselné a nefinite hodnoty.

Testovací epochy nejsou skutečným produkčním registry: dosud chybí autentické konfigurace WeeWX, driverů a senzorů pro duben 2013, září 2020 a srpen 2022. Modul je ochranný stavební prvek, nikoli schválení historického importu nebo dokončení celého issue #21.
