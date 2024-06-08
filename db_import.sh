#!/bin/bash
# import_db.sh
DB_PATH="sky_data.db"
EXPORT_PATH="/home/robert/github/skymonitor/sky_data_export.sql"

# Check if export file exists
if [ ! -f "$EXPORT_PATH" ]; then
    echo "Export file $EXPORT_PATH does not exist."
    exit 1
fi

# Remove the current database
rm -f "$DB_PATH"

# Set up the new database
python3 -c "
from store_data import setup_database
setup_database()
"

# Import the data
sqlite3 "$DB_PATH" < "$EXPORT_PATH"

echo "Database imported from $EXPORT_PATH"
