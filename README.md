# Linkedin Bot

This project is a Linkedin bot that automates the process of sending connection requests, withdrawing sent requests using Selenium.

## Features

- Send connection requests to Linkedin users.
- Withdraw sent connection requests.
- Handle Linkedin login, including captcha and email/phone verification.
- Send email notifications for errors and connection limits.

## Setup

### Prerequisites

- Python 3.8+
- Google Chrome
- ChromeDriver
- Environment variables set up in a `.env` file

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/linkedin-bot.git
    cd linkedin-bot
    ```
2. Download and Install 'google-chrome' stable package

    ```bash
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo apt-get install -y ./google-chrome-stable_current_amd64.deb
    ```
3. Check the version of the installed Google Chrome

    ```bash
    google-chrome --version
    ```
4. Download the compatible ChromeDriver version from [here](https://googlechromelabs.github.io/chrome-for-testing/) and extract the file.

    ```bash
    wget https://storage.googleapis.com/chrome-for-testing-public/{YOUR_IP}_/linux64/chromedriver-linux64.zip
    unzip chromedriver-linux64.zip
    cd chromedriver-linux64
    sudo mv chromedriver /usr/local/bin/
    ```

5. Install virtual display for running chrome in headless mode

    ```bash
    sudo apt-get install -y xvfb
    ```
6. Install the required Python packages in a virtual environment:

    ```bash
    pip install -r requirements.txt
    ```

7. Create a `.env` file in the root directory with the following variables:

    ```env
    LINKEDIN_PASS=your_linkedin_password
    LINKEDIN_USER_MAIL=your_linkedin_email
    LINKEDIN_MAILBOX_PASS=your_email_app_password
    LINKEDIN_INBOX_FOLDER=INBOX
    EMAIL_SERVER_HOST_LINKEDIN=outlook.office365.com  # or imap.gmail.com for Gmail
    PHONE_NUMBER=your_phone_number
    EMAIL_LINKEDIN_CODE=security-noreply@linkedin.com
    
    SENDER=your_notification_email
    SENDER_INBOX_FOLDER=inbox
    SENDER_PASS=your_notification_email_password
    EMAIL_SERVER_HOST_SENDER=imap.gmail.com
    SMTP_SERVER_SENDER=smtp.gmail.com
    SMTP_PORT_SENDER=465
    
    RECEIVER=email_to_receive_notifications
    
    WAITING_BEFORE_CHECK=40
    HEADLESS=True
    MAX_REQUESTS_PER_DAY=24
    MIN_REQUESTS_PER_DAY=15
    MIN_CONNECTIONS_PENDING=300
    TOTAL_SCROLL_TIMES=20
    
    CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
    BOT_VENV_NAME=linkedin
    ```

## Executable Files Explanation

### Main Connections Script (main_connections.py)

The `main_connections.py` script is the main entry point for sending connection requests. Here are its key components:

#### Core Functionality
- Initializes Linkedin bot instance with credentials
- Manages environment variable loading
- Handles main connection request flow

#### Error Handling
- Implements graceful shutdown on errors
- Ensures browser cleanup on exit
- Maintains detailed logging of execution

#### Environment Integration
- Uses dotenv for configuration loading
- Validates required environment variables
- Supports multiple environment types

#### Process Flow
1. Loads environment variables
2. Initializes Linkedin bot with credentials
3. Initiates connection request process
4. Handles any exceptions during execution
5. Ensures clean browser shutdown
6. Logs execution status

#### Usage Example
```bash
# Direct execution
python main_connections.py
```

### Main Withdraw Script (main_withdraw.py)

The `main_withdraw.py` script handles the withdrawal of pending connection requests. Here are its key components:

#### Core Functionality
- Initializes Linkedin bot instance with credentials
- Manages automatic withdrawal of pending requests
- Respects configured withdrawal limits and thresholds

#### Withdrawal Logic
- Only processes withdrawals when pending connections exceed minimum threshold
- Implements percentage-based withdrawal strategy
- Maintains connection request hygiene

#### Safety Features
- Implements withdrawal rate limiting
- Handles withdrawal confirmation dialogs
- Prevents accidental mass withdrawals
- Respects minimum connection thresholds

#### Error Handling
- Manages network connectivity issues
- Handles session timeouts gracefully
- Reports withdrawal limit exceptions
- Ensures clean browser shutdown

#### Usage Example
```bash
python main_withdraw.py
```


### Bot Execution Script (run_connections_bot.sh)

The `run_connections_bot.sh` script handles the actual bot execution with several key features:

#### Virtual Display Management

- Sets up Xvfb virtual display for headless operation
- Configures display resolution to 1920x1080
- Automatically cleans up previous Xvfb instances

#### Process Management

- Terminates existing Chrome and ChromeDriver processes before starting
- Implements graceful shutdown with trap handlers
- Verifies process termination to prevent zombie processes

#### Environment Handling

- Supports multiple virtual environment types:
  - Conda environments
  - Python virtualenv
  - Poetry environments
  - Pipenv
- Auto-detects active virtual environment
- Validates Python interpreter availability

#### Execution Timing

- Implements random execution delays
- Restricts execution to before 9 PM (21:00)
- Calculates optimal timing based on current hour
- Adds random offset to avoid predictable patterns

#### Safety Checks

- Verifies weekly limit hasn't been reached
- Ensures all required directories exist
- Validates environment variables
- Checks for required system dependencies
  - Python3
  - Xvfb
  - Chrome
  - ChromeDriver

#### Logging

- Maintains detailed execution logs
- Records start/end times
- Captures environment information
- Logs process IDs and cleanup operations

#### Error Handling

- Implements error trapping for cleanup
- Handles process termination signals
- Reports detailed error messages
- Maintains exit status codes

#### Usage Example

The script can be run directly or via cron:

```bash
# Direct execution
./run_connections_bot.sh

# Viewing logs
tail -f logs/run_connections_bot.log
```

- Sets up a cron job to run the python script daily at random times between `current_time` and 9:59 PM

### Cron Job Setup Script (run_cron_job.sh)

The `run_cron_job.sh` script handles the initial setup and configuration of the bot's automated execution. Here are its key components:

#### Directory Structure Setup
- Creates required directories for logs and configuration
- Sets up logrotate configuration directory
- Establishes proper permissions and ownership

#### Log Rotation Configuration
- Creates logrotate configuration file
- Sets monthly rotation schedule
- Configures log compression
- Sets maximum log size to 10MB
- Preserves 2 rotations of log history

#### Environment Management
- Sources environment variables from `.env`
- Verifies virtual environment configuration
- Supports both Conda and standard Python virtual environments
- Validates environment setup before proceeding

#### Cron Job Configuration
- Removes existing bot-related cron jobs
- Configures two primary cron tasks:
  1. Log rotation task (daily at midnight)
  2. Bot execution task (daily at 7 AM)
- Includes comprehensive logging of cron job execution
- Captures environment details and Python configuration

#### Virtual Environment Integration
- Detects and uses the appropriate virtual environment
- Supports multiple environment types:
  - Conda environments
  - Python virtualenv
  - Poetry environments
- Ensures correct Python interpreter selection

#### Execution Verification
- Validates cron job installation
- Checks logrotate configuration
- Verifies script permissions
- Confirms environment accessibility

#### Usage Example
```bash
# Make script executable
chmod +x run_cron_job.sh

# Run setup
./run_cron_job.sh

# Verify cron installation
crontab -l
```

- Runs daily at 7:00 AM the `run_connections_bot.sh` script


#### Usage Example
```bash
# Direct execution
python main_withdraw.py

# View withdrawal logs
tail -f logs/linkedin.log
```

### Troubleshooting

1. Chromedriver Issues
   - Ensure Chrome and Chromedriver versions match
   - Verify Chromedriver path in `.env`
   - Check Chrome installation

2. Email Authentication
   - Verify email credentials in `.env`
   - Enable less secure app access for Gmail
   - Use app-specific passwords if 2FA is enabled

3. Connection Issues
   - Check internet connection
   - Verify LinkedIn credentials
   - Ensure proxy settings if using one

4. Cron Job Problems
   - Check crontab entries: `crontab -l`
   - Verify script permissions
   - Check log files in `logs/` directory

### Maintenance

1. Log Rotation
   - Logs are automatically rotated monthly
   - Keeps 2 rotations
   - Compresses old logs
   - Maximum log size: 10MB

2. Clean Up
   - Old screenshots are automatically deleted
   - Temporary files are removed after use
   - Weekly/daily limit files are managed automatically

### Security Considerations

1. Credentials
   - Store sensitive data in `.env` file
   - Never commit credentials to version control
   - Use environment variables for secrets

2. Rate Limiting
   - Respects LinkedIn's connection limits
   - Implements random delays between actions
   - Stops automatically when limits are reached

3. Detection Prevention
   - Uses stealth mode
   - Implements human-like behavior
   - Randomizes actions and delays

## Usage

### Manual Usage

1. Make the script executable:
    ```bash
    chmod +x run_cron_job.sh
    ```

2. Run the setup script:
    ```bash
    ./run_cron_job.sh
    ```

This will:
- Create necessary directories for logs
- Set up log rotation
- Configure and install a cron job to run daily at 7:00 AM
- `run_cron_job.sh` cron job will execute the `run_connections_bot.sh` script
- `run_connections_bot.sh` will set another cron job to run the bot daily at random times between the 7:00 AM and 9:59 PM
- `run_connections_bot.sh` cron job will execute the `main_connections.py` script




### Sending Connection/Withdrawing Requests Right Away
1. For sending connection requests:
    ```bash
    python main_connections.py
    ```

2. For withdrawing pending connection requests:
    ```bash
    python main_withdraw.py
    ```

## Configuration

### Connection Request Settings
- `MAX_REQUESTS_PER_DAY`: Maximum number of connection requests per day (default: 24)
- `MIN_REQUESTS_PER_DAY`: Minimum number of connection requests per day (default: 15)
- `MIN_CONNECTIONS_PENDING`: Minimum number of pending connections before withdrawing (default: 300)

### Bot Behavior
- `WAITING_BEFORE_CHECK`: Time to wait between checks for the captcha email response in seconds (default: 40)
- `HEADLESS`: Run Chrome in headless mode (default: True)
- `TOTAL_SCROLL_TIMES`: Number of times to scroll through people search (default: 20). In companies/universities alumni/people section there is a scrollable page with profiles. This settings limits the total scroll down, which means the number of profiles explored in that company/university. 

## Safety Features

1. LinkedIn Connection Limits
   - Respects LinkedIn's weekly connection request limits
   - Automatically stops when reaching the limit
   - Sends notification emails when limits are reached

2. Security Handling
   - Handles LinkedIn security checks
   - Supports email verification codes
   - Supports phone verification
   - Handles CAPTCHA challenges with email notifications

3. Error Recovery
   - Automatically handles connection errors
   - Retries failed operations with exponential backoff
   - Sends error notification emails

## Notifications

The bot sends email notifications for:
- CAPTCHA challenges that need manual intervention
- Reaching connection request limits
- Security verifications needed
- Critical errors

## Directory Structure

```
linkedin-bot/
├── logs/                  # Log files
├── htmls/                 # HTML snapshots for debugging
├── weeks/                 # Weekly limit tracking
├── days/                  # Daily limit tracking
├── conf_logrotate/       # Log rotation configuration
├── main_connections.py    # Connection requests script
├── main_withdraw.py      # Connection withdrawal script
├── run_cron_job.sh       # Cron job setup script
├── run_connections_bot.sh # Bot execution script
└── .env                  # Environment variables
```