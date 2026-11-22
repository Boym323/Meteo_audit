-- READ-ONLY exact history detail for endpoint timestamps flagged in the bounded gap screen.
SELECT * FROM loucka_reconstruction.reconstruction_changes
WHERE target_time IN (1559223300,1589384400,1589387400,1589402100)
ORDER BY target_time;
