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
    unzip chromedriver_linux64.zip
    cd chromedriver_linux64
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
    LINKEDIN_USER_MAIL=your_linkedin_email
    LINKEDIN_PASS=your_linkedin_password
    SENDER=your_email (for sending email notifications. Can be the same as LINKEDIN_USER_MAIL)
    SENDER_PASS=your_email_password (for sending email notifications. Must be an app password if using Gmail. See [here](https://support.google.com/mail/answer/185833))
    RECEIVER=receiver_email (where you want to receive email notifications)
    SMTP_SERVER_SENDER=smtp_server (e.g., smtp.gmail.com. Sends email notifications)
    SMTP_PORT_SENDER=smtp_port (e.g., 465)
    WAITING_BEFORE_CHECK=waiting_time_in_seconds (waiting time before checking the email inbox)
    EMAIL_SERVER_HOST_SENDER=email_server_host (e.g., imap.gmail.com. Receives email notifications)
    SENDER_INBOX_FOLDER=inbox_folder (e.g., inbox for Gmail. INBOX for outlook)
    EMAIL_SERVER_HOST_LINKEDIN=linkedin_email_server_host 
    LINKEDIN_MAILBOX_PASS=linkedin_email_password
    LINKEDIN_INBOX_FOLDER=linkedin_inbox_folder
    EMAIL_LINKEDIN_CODE=linkedin_code_email
    PHONE_NUMBER=your_phone_number
    ```

### Usage

1. Run the bot:

    ```bash
    python main.py
    ```

2. The bot will start sending connection requests. If an error occurs, it will send an email notification and close the browser.

### Customization

- Modify the `main.py` file to change the bot's behavior.
- Adjust the settings in the `.env` file to match your requirements.

### Logging

Logs are generated using the `logger` module and can be found in the log files created in the project directory.

### Troubleshooting

- Ensure that all environment variables are correctly set in the `.env` file.
- Make sure that ChromeDriver is compatible with your installed version of Google Chrome.
- Check the log files for detailed error messages.

## Contributing

Feel free to submit issues or pull requests if you find any bugs or have suggestions for improvements.

## License

This project is licensed under the MIT License.