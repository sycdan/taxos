# To Do: Taxos Development

## Today's Task

we would like to have a consistent backup/restore process. currently there is backup-specific output format (single-file). we would like to mirror the format in ./0698977c1678796580004fd00bf76736 with the exception that we need to handle the legacy vendor_ref (reference) field.

another small cahnge would be that we want to store the vendor guid instead of the name in the vendor field in receipt state files when backing up. we'd also like to add an option to zip up the backup files.

when we backup, we want to store the data in data/backups/<tenant_name>_<timestamp>[.zip] as either a zip or a folder

we would like to output the data to a tmp dir, and then either zip it and move the zip to backups, or move the temp dir to backups

we also want dev.clean to remove backups older than 1 hour

when restoring a backup, we should inject the vendor guid not name when creating receipts
