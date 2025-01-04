#!/bin/bash

# Set script directory as working directory
SCRIPT_DIR=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))
LOGS_DIR_NAME='logs'
LOGS_DIR="$SCRIPT_DIR/$LOGS_DIR_NAME"
LOGROTATE_CONF_DIR='conf_logrotate'
LOGROTATE_CONF="${LOGROTATE_CONF_DIR}/linkedin_bot"
LOGROTATE_STATE_FILE="${LOGROTATE_CONF_DIR}/.logrotate-state"

source "$SCRIPT_DIR/.env"

echo "Running in the virtual environment: $BOT_VENV_NAME"

mkdir -p "$LOGROTATE_CONF_DIR"
chmod 755 "$LOGROTATE_CONF_DIR"

# Create logs directory if it doesn't exist
if [ ! -d "$LOGS_DIR" ]; then
    mkdir -p "$LOGS_DIR"
fi


# Create logrotate state file if it doesn't exist
if [ ! -f "$LOGROTATE_STATE_FILE" ]; then
    touch "$LOGROTATE_STATE_FILE"
fi

# Create logrotate configuration
tee "$LOGROTATE_CONF" > /dev/null << EOF
$LOGS_DIR/*.log {
    monthly
    rotate 2
    size 10M
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
}
EOF

# Verify logrotate configuration
if ! /usr/sbin/logrotate --state="$SCRIPT_DIR/$LOGROTATE_STATE_FILE" "$LOGROTATE_CONF"; then
    echo "Error: Invalid logrotate configuration"
    exit 1
fi

# Create temporary cron file
TEMP_CRON=$(mktemp)
crontab -l > "$TEMP_CRON" 2>/dev/null || true

# Remove any existing cron job for the LinkedIn bot script
sed -i "\|/usr/sbin/logrotate --force --state=$SCRIPT_DIR/$LOGROTATE_STATE_FILE $LOGROTATE_CONF|d" "$TEMP_CRON"
sed -i "/run_connections_bot.sh/d" "$TEMP_CRON"

echo "SCRIPT_DIR: $SCRIPT_DIR"

echo "0 0 * * * /usr/sbin/logrotate --force --state=$SCRIPT_DIR/$LOGROTATE_STATE_FILE $LOGROTATE_CONF > $LOGS_DIR/logrotate.log" >> "$TEMP_CRON"


if command -v conda &> /dev/null; then
    echo "0 7 * * * SHELL=/bin/bash && ( \
        echo \"=== Starting job at \$(date) ===\" && \
        echo \"Conda location: \$(which conda)\" && \
        . ~/.bashrc && \
        . $(dirname $(dirname $(which conda)))/etc/profile.d/conda.sh && \
        echo \"Changed to directory: \$(pwd)\" && \
        cd $SCRIPT_DIR && \
        echo \"Activating conda env: $BOT_VENV_NAME\" && \
        conda activate $BOT_VENV_NAME && \
        echo \"Python location: \$(which python)\" && \
        echo \"Python version: \$(python --version)\" && \
        echo \"Running bot script\" && \
        /bin/bash $SCRIPT_DIR/run_connections_bot.sh \
        ) >> $LOGS_DIR/run_connections_cron.log 2>&1" >> "$TEMP_CRON"
else
    # For venv/virtualenv

    echo "0 7 * * * SHELL=/bin/bash && ( \
        echo \"=== Starting job at \$(date) ===\" && \
        . ~/.bashrc && \
        . $(dirname $(dirname $(which conda)))/etc/profile.d/conda.sh && \
        echo \"Changed to directory: \$(pwd)\" && \
        cd $SCRIPT_DIR && \
        echo \"Activating venv: $BOT_VENV_NAME\" && \
        source $HOME/.virtualenvs/$BOT_VENV_NAME/bin/activate && \
        echo \"Python location: \$(which python)\" && \
        echo \"Python version: \$(python --version)\" && \
        echo \"Running bot script\" && \
        /bin/bash $SCRIPT_DIR/run_connections_bot.sh \
        ) >> $LOGS_DIR/run_cron_job.log 2>&1" >> "$TEMP_CRON"
fi

# Install new cron job
if crontab "$TEMP_CRON"; then
    echo "Successfully installed cron job to run at 7:00 AM daily"
else
    echo "Error: Failed to install cron job"
    rm "$TEMP_CRON"
    exit 1
fi

# Clean up
rm "$TEMP_CRON"

echo "Setup completed successfully"
chmod +x "$SCRIPT_DIR/run_connections_bot.sh"
