-- Read-only registry snapshot; execute one SELECT through information_schema.
SELECT station_id, provider, station_name, source_url, location_description,
       elevation_m, timezone_name, access_status, notes
FROM loucka_reconstruction.reference_stations
ORDER BY station_id;
