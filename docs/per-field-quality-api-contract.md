# API kontrakt kvality měření po veličině — issue #25

**Stav:** vývojový návrh a izolované syntetické testy. Bez DB migrace, bez integrace do živého webu, bez přepisu archive.

## Zamýšlené entity (ERD)

- `sensor_epoch (id, physical_sensor_ref, driver_version, start_utc, end_utc, unit_system, evidence_ref, verified)` 1:N `observation_raw_ref`.
- `observation_raw_ref (id, source_database, source_table, source_timestamp_utc, interval_min, field, raw_value, source_sha256, sensor_epoch_id)`.
- `measurement_qc (target_time_utc, variable, measurement_value, display_value, quality_state, flags, diagnosis_confidence, replacement_confidence, source_raw_id, manifest_ref, method_version, reviewed_at)` s klíčem **(target_time_utc,variable)**; různé veličiny v témže řádku mohou mít různé QC.
- `reconstruction_manifest (batch_id, version, immutable_payload_sha256, expected_old, proposed_new, source_raw_id, explicit_approval, before_image_sha256, rollback_ref)` jako záznam samostatného řízeného schvalování, nikdy automatická aplikace z API.

Všechny identifikátory `source_ref`, `epoch_ref`, `change_ref` musí odkazovat na skutečné důkazy, nikoli na vymyšlené nebo implicitně zkonstruované změny. SQL DDL se tímto PR **neprovádí**; izolovanou vývojovou migraci a soulad se současnými tabulkami teprve vyžaduje #25.

## Stav v JSON výstupu `loucka-field-qc-v1`

Model rozlišuje `MEASURED`, `CORRECTED`, `ESTIMATED`, `MISSING`, `NOT_INSTALLED`, `SENSOR_ERROR`. API uchovává `measurement_value`, `display_value`, stav, zdrojový a senzorový odkaz, důvěry diagnózy a náhrady odděleně, explicitní auditní `change_ref` a příznaky QC. Hodnota **0 není totéž co NULL**.

- `CORRECTED` a `ESTIMATED` bez `approved=true` a `change_ref` neprojdou validací. Tato validace **neověřuje existenci** schválení v databázi — integrující adapter musí ověřit podpis/hash manifestu proti per-value auditní evidenci.
- `NOT_INSTALLED` vyžaduje doklad instalační epochy. Bez něj je stav nesprávný; chybějící stará data nesmějí být mechanicky označena jako nepřítomnost senzoru.
- `MISSING`, `SENSOR_ERROR`, `NOT_INSTALLED` nesmějí dostat `display_value`; `ESTIMATED` nepropojuje grafovou linii. Na dlouhých výpadcích se nesmí vykreslit falešná spojnice.
- Kandidát extrému se v této konzervativní výchozí politice vybere pouze ze senzorově ověřených `MEASURED` bez QC flagů. Opravy a odhady nelze automaticky zahrnout do rekordů; přísnější fyzikální validace je samostatná.
- Pro občanský den Europe/Prague vrací `civil_day_bounds` epochy koncových hranic WeeWX `(start,end]`. Testy jarního dne s 23 h, podzimního dne s 25 h, dvou různých lokálních 02:30 a nulové hodnoty.

## Omezení a následné kroky

Žádný existující archivní řádek tímto kódem nezískává automaticky status `MEASURED`. Je třeba založit referenční metadata, doplnit testovací DB migraci, důkazní adapter, API integraci, klientské UI a přesné zveřejňovací limity. Kterýkoli z těchto kroků může odhalit další historické konflikty. Dokončení celé issue #25 nyní není deklarováno.
