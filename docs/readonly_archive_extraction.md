# Bounded archive extraction

Use scripts/readonly_archive_extract.py for repeatable local CSV extracts when an existing SQL report cannot be run through the extraction harness.

The command accepts one of the six configured archive databases, only the archive table, unique simple column names, a UTC Unix interval (start, end] no longer than 366 days, and at most 100,000 output rows. The meteo_audit.db adapter restricts the statement to one SELECT and runs it in a READ ONLY transaction. Credentials are read from the existing protected .env or DB_* environment variables and are never written to output.

Example:

    python3 scripts/readonly_archive_extract.py \
      --database old_weewx \
      --start-utc 1388534400 \
      --end-utc 1388620800 \
      --fields dateTime,usUnits,interval,outTemp,outHumidity \
      --output reports/local-extract.csv

The lower time bound is exclusive, the upper bound inclusive. The tool refuses to overwrite an existing output and fails when a result reaches the row limit, so a caller must narrow the period before exporting a large cohort. This is an offline CLI addition; no database query was run during its creation.
