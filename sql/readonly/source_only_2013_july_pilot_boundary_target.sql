-- READ-ONLY full current target row used to check that the outTemp update preserves all other fields.
START TRANSACTION READ ONLY;
SELECT * FROM `loucka_reconstruction`.archive WHERE dateTime=1373320800;
