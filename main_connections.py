import os
import time

from urllib3 import HTTPConnectionPool

from linkedin import Linkedin

from dotenv import load_dotenv





if __name__ == "__main__":
    load_dotenv()
    try:
        linkedin = Linkedin(os.getenv("LINKEDIN_USER_MAIL"), os.getenv("LINKEDIN_PASS"))
        linkedin.logger.info("Loaded environment variables and created Linkedin object")
        linkedin.send_connection_request()
    except Exception as e:
        pass 