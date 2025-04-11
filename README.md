# 🤖 LinkedIn Bot

A bot that automates LinkedIn connections using Selenium.

## 🚀 Quick Start

The `run_cron_job.sh` script creates a daily job that runs between 7:00 AM and 9:59 PM. The bot sends connection requests to users from companies/universities listed in `org/orgs.csv`.

## ✨ Features

- 🔗 Send connection requests automatically
- 🔍 Find users from companies/universities in `orgs.csv`
- 🔄 Each organization usable once every 2 months
- ❌ Withdraw pending connection requests
- 🔐 Handle login security (captcha, email/phone verification)
- 📧 Send error notifications via email

## 🛠️ Setup

### Requirements

| Requirement | Version |
|-------------|---------|
| Python      | 3.8+    |
| Google Chrome | Latest |
| ChromeDriver | Match Chrome |

### Installation Steps

1. **Get the code**:
   ```bash
   wget https://github.com/lesi-nedo/connection_sender/archive/refs/tags/v1.0.0.tar.gz
   unzip main.zip && rm main.zip
   cd connection_sender-main
   ```

2. **Install Chrome**:
   ```bash
   wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
   sudo apt-get install -y ./google-chrome-stable_current_amd64.deb
   rm google-chrome-stable_current_amd64.deb
   ```

3. **Check Chrome version**:
   ```bash
   google-chrome --version
   ```

4. **Install matching ChromeDriver**:
   ```bash
   wget https://storage.googleapis.com/chrome-for-testing-public/{YOUR_VERSION}/linux64/chromedriver-linux64.zip
   unzip chromedriver-linux64.zip
   sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
   ```

5. **Install virtual display**:
   ```bash
   sudo apt-get install -y xvfb
   ```

6. **Setup Python environment**:
   ```bash
   conda create -n linkedin python=3.12
   conda activate linkedin
   pip install -r requirements.txt
   ```

7. **Create `.env` file** with these variables:

   | Variable | Description |
   |----------|-------------|
   | LINKEDIN_PASS | LinkedIn password |
   | LINKEDIN_USER_MAIL | LinkedIn email |
   | LINKEDIN_MAILBOX_PASS | Email app password |
   | LINKEDIN_INBOX_FOLDER | Email folder (e.g., "INBOX") |
   | EMAIL_SERVER_HOST_LINKEDIN | IMAP server (e.g., "imap.gmail.com") |
   | PHONE_NUMBER | Phone for verification |
   | SENDER | Notification email |
   | RECEIVER | Email to receive notifications |
   | MAX_REQUESTS_PER_DAY | Max connections per day (default: 24) |
   | MIN_REQUESTS_PER_DAY | Min connections per day (default: 15) |
   | HEADLESS | Run Chrome headless (True/False) |

## 🚀 Running the Bot

### Manual Execution

```bash
# Send connection requests
python main_connections.py

# Withdraw pending requests
python main_withdraw.py
```

### Automated Setup

```bash
# Make executable
chmod +x run_cron_job.sh

# Setup automation
./run_cron_job.sh

# Check logs
tail -f logs/linkedin.log
```

## ⚙️ Configuration

### Key Settings

| Setting | Description | Default |
|---------|-------------|---------|
| MAX_REQUESTS_PER_DAY | Max connections daily | 24 |
| MIN_REQUESTS_PER_DAY | Min connections daily | 15 |
| MIN_CONNECTIONS_PENDING | Min pending connections to keep | 300 |
| TOTAL_SCROLL_TIMES | Profile search scroll count | 20 |
| HEADLESS | Run without visible browser | True |

## 🛡️ Safety Features

- ✅ Respects LinkedIn's weekly limits
- 🔄 Handles security checks automatically
- 🚫 Stops when limits reached
- 📱 Supports email/phone verification
- 🤖 Uses human-like behavior

## 📂 Directory Structure

```markdown
linkedin-bot/
├── logs/                 # Log files
├── htmls/                # Debug snapshots
├── weeks/                # Weekly limit tracking
├── days/                 # Daily limit tracking
├── main_connections.py   # Main bot script
├── main_withdraw.py      # Withdrawal script
├── run_cron_job.sh       # Setup script
└── .env                  # Configuration
```
