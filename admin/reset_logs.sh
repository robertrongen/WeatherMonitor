#!/bin/bash

# Paths to log files
LOCATION="/home/robert/github/skymonitor/logs"
LOG_FILES=(
    "${LOCATION}/control.log"
    "${LOCATION}/app.log"
    "${LOCATION}/fetch_data.log"
    "${LOCATION}/store_data.log"
    "${LOCATION}/database_operations.log"
    "${LOCATION}/rain.log"
)

# Services to reset journals
SERVICES=(
    "control.service"
    "app.service"
)

# Function to truncate log files
truncate_logs() {
    for LOG_FILE in "${LOG_FILES[@]}"; do
        if [ -f "$LOG_FILE" ]; then
            echo "Truncating $LOG_FILE..."
            > "$LOG_FILE"
            echo "$LOG_FILE truncated."
        else
            echo "$LOG_FILE does not exist."
        fi
    done
}

# Function to reset systemd journals
reset_journals() {
    for SERVICE in "${SERVICES[@]}"; do
        echo "Resetting journal for $SERVICE..."
        sudo journalctl --rotate
        sudo journalctl --vacuum-time=1s
        sudo systemctl restart $SERVICE
        echo "Journal for $SERVICE reset."
    done
}

# Run the functions
truncate_logs
reset_journals

echo "Log files and journals have been reset."

# Note: Ensure the paths to the log files are correct and update them accordingly.
# Also, make sure the script has the necessary permissions to access the log files and run systemd commands.
