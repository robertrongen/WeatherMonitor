#!/bin/bash
# export_db.sh
DB_PATH="sky_data.db"
EXPORT_PATH="/home/robert/github/skymonitor/sky_data_backup.sql"

# Create backup directory if it doesn't exist
mkdir -p "$(dirname "$EXPORT_PATH")"

# Export the database
sqlite3 "$DB_PATH" .dump > "$EXPORT_PATH"

echo "Database exported to $EXPORT_PATH"
