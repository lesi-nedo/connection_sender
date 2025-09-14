import os
import time

from urllib3 import HTTPConnectionPool

from linkedin import Linkedin

from dotenv import load_dotenv

from exceptions import ReachedWithdrawLimitException

load_dotenv()


if __name__ == "__main__":
    linkedin = Linkedin(os.getenv("LINKEDIN_USER_MAIL"), os.getenv("LINKEDIN_PASS"))

    try:
        linkedin.withdraw_connection()

    except ReachedWithdrawLimitException as e:
        linkedin.send_email("Withdraw limit reached", "Linkedin Bot - Withdraw limit reached")

    except HTTPConnectionPool as e:
        linkedin.logger.error(f"HTTPConnectionPool error: {e}")
        pass
    except Exception as e:
        linkedin.logger.error(f"Error sending connection request: {e}")
        linkedin.send_error_email(str(e))
    finally:
        linkedin.close_browser()
        linkedin.logger.info("Driver closed")
        linkedin.logger.info("Exiting...")
        exit(0) 