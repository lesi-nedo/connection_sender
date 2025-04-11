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
   tar -xvf v1.0.0.tar.gz && rm v1.0.0.tar.gz
   cd connection_sender-1.0.0
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

   ```env
    LINKEDIN_PASS=your_linkedin_password
    LINKEDIN_USER_MAIL=your_linkedin_email, i.e the login email
    LINKEDIN_MAILBOX_PASS=your_email_app_password, i.e the password for the email account used in the login. Some email providers require an app password for third-party apps. Example: for Gmail, you can create an app password in your Google account settings.
    LINKEDIN_INBOX_FOLDER=INBOX # depends on your email provider, for Gmail it is INBOX. If you use Outlook, it is "inbox" (lowercase).
    EMAIL_SERVER_HOST_LINKEDIN=outlook.office365.com  # or imap.gmail.com for Gmail. This is the IMAP server for your email provider.
    PHONE_NUMBER=your_phone_number # for phone verification
    EMAIL_LINKEDIN_CODE=security-noreply@linkedin.com # the email from which the security code is sent. This is the email address used by LinkedIn to send security codes for verification. Probably, Should not be changed.
    
    SENDER=your_notification_email # the email from which the notifications are sent, like screenshots, errors, etc. Could be the same as the one used for LinkedIn login.
    SENDER_INBOX_FOLDER=inbox # same as above
    SENDER_PASS=your_notification_email_password # again, some email providers require an app password for third-party apps.
    SMTP_SERVER_SENDER=smtp.gmail.com # or smtp-mail.outlook.com for Outlook. This is the SMTP server for your email provider.
    SMTP_PORT_SENDER=465
    EMAIL_SERVER_HOST_SENDER=imap.gmail.com # or imap-mail.outlook.com for Outlook. This is the IMAP server for your email provider. It will be used to check the inbox for the captcha number, security code, etc.
    
    RECEIVER=email_to_receive_notifications # the email to which the notifications are sent
    
    WAITING_BEFORE_CHECK=40 # This is the time to wait between checks for the response email, i.e. SENDER sends the email to RECEIVER and it waits for the response email to arrive. This is the time to wait before checking the inbox for the captcha number, security code, etc.
    HEADLESS=True # Run Chrome in headless mode. If you want to see the browser, set it to False.
    MAX_REQUESTS_PER_DAY=24 # The maximum number of possible connection requests per day.
    MIN_REQUESTS_PER_DAY=15 # The minimum number of possible connection requests per day. The final number of requests is a random number between MIN_REQUESTS_PER_DAY and MAX_REQUESTS_PER_DAY.
    TOTAL_SCROLL_TIMES=20 # The number of times to scroll through people search. In companies/universities alumni/people section there is a scrollable page with profiles. This settings limits the total scroll down, which means the number of profiles explored in that company/university.
    PAGES_BEFORE_QUIT=30 # The number of pages to search for connectable people before quitting. The algorithm will click at most 30 times on the next button. If the number of pages is less than 30, it will click on all of them.
    MAX_WEBDRIVER_WAIT_TIME=10 # The maximum time to wait for a page element to load. This is the maximum time to wait for a page element to load. The final wait time is a random number between MIN_WEBDRIVER_WAIT_TIME and MAX_WEBDRIVER_WAIT_TIME. WebDriverWait function uses it.
    MIN_WEBDRIVER_WAIT_TIME=5

    MIN_CONNECTIONS_PENDING=300 # The minimum number of pending connections active (won't go below). This is the number of pending connection requests that the bot will keep. If the number of pending requests goes below this number, the bot will stop withdrawing requests.
    
    CHROMEDRIVER_PATH=/usr/local/bin/chromedriver # The path to the ChromeDriver executable. This is the path to the ChromeDriver executable. It should be the same as the one used in the installation step.
    BOT_VENV_NAME=linkedin # The name of the virtual environment. This is the name of the virtual environment that you created in the installation step. It should be the same as the one used in the installation step.
    ```

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
