REMOTE_USER="bitnami"
REMOTE_IP="3.67.160.120"
REMOTE_PORT="2222"
REMOTE_DIR="/opt/bitnami/projects/linkedin"
PEM_FILE="/home/lesi-nedo/Desktop/website/mywebsite/nedo.pem"
SSH_OPTIONS="-p $REMOTE_PORT -i $PEM_FILE"
# REMOTE_STOP_COMMAND="/home/bitnami/stop.sh"
# REMOTE_RESTART_COMMAND="/home/bitnami/rest.sh"
REMOTE_VENV_DIR="/home/bitnami/.conda/envs/linkedin"
PYTHON="python3"

source "$PWD/.env"

if [ "$HEADLESS" = "False" ]; then
  echo "Firstly, set HEADLESS=True in .env file"
  exit 1
fi

ITEMS_TO_TRANSFER=(
  "requirements.txt"
  "exceptions"
  "linkedin"
  "logger"
  "notebooks"
  "org"
  ".env"
  "main_connections.py"
  "main_withdraw.py"
  "run_connections_bot.sh"
  "run_cron_job.sh"
  "README.md"
)

RSYNC_OPTIONS=(
  "-avz"
  "--progress"
  "--exclude=__pycache__"
  "--exclude=.git"
  "--exclude=.idea"
  "--exclude=*.pyc"
  "--exclude=*.pyo"
  "--exclude=.pytest_cache/"
  "--exclude=.coverage"
  "--exclude=.vscode/"
  "--exclude=remote.sh"
  "--exclude=*.html"
)

set -e

item_exists() {
  if [ ! -e "$1" ]; then
    echo "Error: $1 does not exist"
    return 1
  fi
  return 0
}

check_pem_file() {
  if [ ! -f "$PEM_FILE" ]; then
    echo "Error: PEM file does not exist"
    exit 1
  fi
  if [ "$(stat -c %a "$PEM_FILE")" != "600" ]; then
    echo "Warning: Incorrect permissions for PEM file. It should be 600. Changing permissions..."
    chmod 600 "$PEM_FILE"
  fi
}


echo "Starting file transfer to remote machine using rsync..."

# Call the check_pem_file function
check_pem_file

for item in "${ITEMS_TO_TRANSFER[@]}"; do
  if item_exists "$item"; then
    echo "Transferring $item..."
    rsync "${RSYNC_OPTIONS[@]}" -e "ssh $SSH_OPTIONS" "$item" "$REMOTE_USER@$REMOTE_IP:$REMOTE_DIR"
    if [ $? -eq 0 ]; then
      echo "Successfully transferred $item"
    else
      echo "Error: failed to transfer $item"
    fi
  fi
done

set +e

echo "File transfer complete"