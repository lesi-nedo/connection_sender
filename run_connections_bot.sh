#!/bin/bash

# Set script directory as working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"
FILE_NAME="main_connections.py"
DISPLAY=$(env | grep -E '^DISPLAY')
WEEK=$(date +%V)
FILE_PATH_WEEK="weeks/reached_limit_week-${WEEK}.txt"


set -e
set -o pipefail

source "$SCRIPT_DIR/.env"

# Create logs directory if it doesn't exist
if [ ! -d "$LOGS_DIR" ]; then
    mkdir -p "$LOGS_DIR"
fi

LOG_FILE_CRON="$LOGS_DIR/run_connections_bot.log"

# Function for logging
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE_CRON"
    echo "$1"
}


check_virtual_env() {
    local log_message="${1:-echo}"

    # Check if already in a virtual environment
    if [ -n "$VIRTUAL_ENV" ]; then
        $log_message "Running in virtualenv/venv: $VIRTUAL_ENV"
        return 0
    fi

    # Check for Conda environment
    if [ -n "$CONDA_PREFIX" ]; then
        $log_message "Running in conda environment: $CONDA_PREFIX"
        return 0
    fi

    # Check for Poetry's local venv
    if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
        $log_message "Poetry virtual environment detected"
        return 0
    fi

    # Check for Pipenv
    if [ -n "$PIPENV_ACTIVE" ]; then
        $log_message "Running in Pipenv environment"
        return 0
    fi

    $log_message "Error: No virtual environment detected"
    return 1
}

kill_chrome_processes() {
    local chrome_pids
    local driver_pid
    set +e
    # Find and kill headless Chrome processes
    chrome_pids=$(ps aux | grep -E "chrome .* --headless=new .*" | grep -v grep | awk '{print $2}')
    if [ -n "$chrome_pids" ]; then
        log_message "Killing headless Chrome processes: $chrome_pids"
        echo "$chrome_pids" | xargs kill -9 2>/dev/null
    fi

    
    # Find and kill chromedriver
    driver_pid=$(pgrep -f "chromedriver")
    if [ -n "$driver_pid" ]; then
        log_message "Killing chromedriver process: $driver_pid"
        kill -9 "$driver_pid" 2>/dev/null
    fi

    
    # Backup: use pkill for any remaining processes
    pkill -f "chromedriver" 2>/dev/null
    pkill -f "chrome.*--headless=new" 2>/dev/null
    
    # Check if any processes remain
    if pgrep -f "chromedriver|chrome.*--headless=new" >/dev/null; then
        log_message "Failed to kill all Chrome processes"
        return 1
    fi
    
    log_message "All Chrome processes terminated"
    set -e
    return 0
}


kill_chrome_processes

# Usage in your script:
if ! check_virtual_env "log_message"; then
    log_message "Please activate a virtual environment first"
    exit 1
fi


# Exit if the file exists
if [ -f "$SCRIPT_DIR/$FILE_PATH_WEEK" ]; then
    log_message "File $FILE_PATH_WEEK exists. Which means this week we reached the Linkedin limit. Exiting..."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    log_message "Error: Python3 is not installed"
    exit 1
fi

if ! command -v Xvfb &> /dev/null; then
    log_message "Error: Xvfb is not installed. Install with: sudo apt-get install xvfb"
    exit 1
fi


# Check for required environment variables
if [ "$HEADLESS" != "True" ]; then
    log_message "Error: HEADLESS environment variable must be set to 'True' (.env file)"
    exit 1
fi

# Check for virtual environments and set Python path
PYTHON_PATH="/usr/bin/python3"

# Check for venv
if [ -d "venv" ] && [ -f "venv/bin/python" ]; then
    PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"
    log_message "Found venv virtual environment"
# Check for virtualenv
elif [ -d ".virtualenv" ] && [ -f ".virtualenv/bin/python" ]; then
    PYTHON_PATH="$SCRIPT_DIR/.virtualenv/bin/python"
    log_message "Found virtualenv environment"
# Check for conda environment
elif [ -n "$CONDA_PREFIX" ] && [ -f "$CONDA_PREFIX/bin/python" ]; then
    PYTHON_PATH="$CONDA_PREFIX/bin/python"
    log_message "Found conda environment: $CONDA_PREFIX"
fi

# Verify the Python interpreter works
if ! $PYTHON_PATH --version &> /dev/null; then
    log_message "Error: Selected Python interpreter ($PYTHON_PATH) is not working"
    exit 1
fi


if [ ! -f "$SCRIPT_DIR/$FILE_NAME" ]; then
    log_message "Error: $FILE_NAME not found in $SCRIPT_DIR"
    exit 1
fi


# Get current hour (0-23)
CURRENT_HOUR="$(date +%H)"
CURRENT_HOUR=$((10#$CURRENT_HOUR))


# Calculate maximum possible offset
MAX_HOUR=21
HOURS_LEFT=$((MAX_HOUR - CURRENT_HOUR))


if [ $HOURS_LEFT -lt 0 ]; then
    log_message "Current hour ($CURRENT_HOUR) is past the maximum allowed hour ($MAX_HOUR). Script will run tomorrow."
    exit 0
fi


# Generate random hour offset (0 to hours left)
RANDOM_OFFSET=$((RANDOM % (HOURS_LEFT + 1)))

# Calculate final random hour and minutes
RANDOM_HOUR=$((CURRENT_HOUR + RANDOM_OFFSET))
RANDOM_MINUTES=$((RANDOM % 60))
RANDOM_MINUTES=$(printf "%02d" $RANDOM_MINUTES)


# Create temporary cron file
TEMP_CRON=$(mktemp)
crontab -l > "$TEMP_CRON" 2>/dev/null || true

# Remove any existing cron job for this script
sed -i "/$FILE_NAME/d" "$TEMP_CRON"

log_message "Script directory: $SCRIPT_DIR"

XVFB_PIDS=$(pgrep -f 'Xvfb :99 -screen 0 1920x1080x24 -ac' 2>/dev/null || echo "")

if [ -n "$XVFB_PIDS" ]; then
    log_message "Killing existing Xvfb processes: $XVFB_PIDS"
    echo "$XVFB_PIDS" | xargs -r kill -9
    # Wait briefly to ensure processes are terminated
    sleep 1
    # Verify termination
    if pgrep -f "Xvfb :99" > /dev/null; then
        log_message "Warning: Some Xvfb processes may still be running"
    fi
fi

# Modify the cron job line to include random minutes:
echo "$RANDOM_MINUTES $RANDOM_HOUR * * * SHELL=/bin/bash && ( \
    DISPLAY=:99 && \
    cd $SCRIPT_DIR && \
    (trap 'kill -9 \$XVFB_PID 2>/dev/null || true' EXIT; \
    Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset & \
    XVFB_PID=\$! && \
    $PYTHON_PATH $SCRIPT_DIR/$FILE_NAME >> $LOGS_DIR/linkedin.log 2>&1) \
) >> $LOG_FILE_CRON" >> "$TEMP_CRON"


# Install new cron job
if crontab "$TEMP_CRON"; then
    log_message "Successfully installed cron job to run at $RANDOM_HOUR:$RANDOM_MINUTES daily"
else
    log_message "Error: Failed to install cron job"
    rm "$TEMP_CRON"
    exit 1
fi

# Clean up
rm "$TEMP_CRON"

log_message "Setup completed successfully"
